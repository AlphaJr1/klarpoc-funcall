import json
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from queue import Queue, Empty
from typing import Generator
from openai import OpenAI

from .brand_guard import get_store_id, BrandAccessError
from .brand_resolution import resolve_brand
try:
    from clickup_sync.clickup_api import (
        update_task as _cu_update,
        add_comment as _cu_comment,
        create_escalation_task as _cu_escalate,
        mark_in_progress as _cu_inprogress,
        update_task_fields as _cu_update_fields,
    )
    class _cu:
        update_task = staticmethod(_cu_update)
        add_comment = staticmethod(_cu_comment)
        create_escalation_task = staticmethod(_cu_escalate)
        mark_in_progress = staticmethod(_cu_inprogress)
        update_task_fields = staticmethod(_cu_update_fields)
    cu = _cu()
except Exception:
    import clickup_sync as cu

from .config import OLLAMA_MODEL, OLLAMA_BASE_URL, ESCALATION_THRESHOLD, MAX_LLM_ITERATIONS, TASK_FIELD_MAP
from .tools import TOOLS, execute_tool
from .scoring import calculate_confidence, explain_confidence, shadow_check
from .gates import extract_or_clarify, gate0_check, synthesize_query, intent_classify, get_tools_for_state
from .prompts import build_system_prompt, build_user_prompt, build_summary_comment


def _make_client():
    from .llm import get_llm_client
    return get_llm_client()


def _get_task_field(task: dict, key: str, default: str = "") -> str:
    """Baca custom_field task via TASK_FIELD_MAP — satu tempat untuk update nama field."""
    field_name = TASK_FIELD_MAP.get(key, key)
    return task.get("custom_fields", {}).get(field_name) or default


_LOG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs", "backend_api.log")
os.makedirs(os.path.dirname(_LOG_PATH), exist_ok=True)

_logger = logging.getLogger("engine")
if not _logger.handlers:
    _fh = logging.FileHandler(_LOG_PATH)
    _fh.setFormatter(logging.Formatter("%(asctime)s %(message)s", datefmt="%Y-%m-%dT%H:%M:%S"))
    _logger.addHandler(_fh)
    _logger.setLevel(logging.INFO)


# ── Post-process hook registry ─────────────────────────────────────────────
# Daftarkan fungsi tambahan di sini tanpa ubah _post_process.
# Signature: fn(client, ctx: dict) -> dict | None  (None = tidak ada event)
_POST_HOOKS: list = []


def register_post_hook(fn):
    """Decorator/function untuk daftarkan hook post-processing."""
    _POST_HOOKS.append(fn)
    return fn


def _ms(start: float) -> int:
    return int((time.perf_counter() - start) * 1000)


def _ck(label: str, t0: float, t_phase: float, extra: str = "") -> str:
    total = _ms(t0)
    phase = _ms(t_phase)
    return f"[{total:>6}ms] CHECKPOINT {label:<30} phase={phase}ms {extra}".rstrip()


def _run_tool_calls(msg, t0: float, iteration: int) -> tuple[list, list]:
    """
    Parse + eksekusi parallel semua tool_calls dari satu LLM message.
    Return: (parsed_tcs, messages_to_append)
    Extracted supaya tidak duplikat antara iter-1 dan iter-2+.
    """
    parsed_tcs = []
    for tc in msg.tool_calls or []:
        try:
            inputs = json.loads(tc.function.arguments)
        except Exception:
            inputs = {}
        parsed_tcs.append((tc, inputs))

    if not parsed_tcs:
        return [], []

    t_tools = time.perf_counter()
    with ThreadPoolExecutor(max_workers=len(parsed_tcs)) as ex:
        futures = {
            ex.submit(execute_tool, tc.function.name, inputs): (tc, inputs)
            for tc, inputs in parsed_tcs
        }
        tc_results = {}
        for future in as_completed(futures):
            tc, inputs = futures[future]
            result_str = future.result()
            result_obj = json.loads(result_str)
            tc_results[tc.id] = (tc, inputs, result_str, result_obj)

    tool_names = [tc.function.name for tc, _ in parsed_tcs]
    _logger.info(_ck(f"tool_execute_iter_{iteration}", t0, t_tools, f"tools={tool_names}"))

    log_entries = []
    msg_entries = []
    for tc, inputs in parsed_tcs:
        _, _, result_str, result_obj = tc_results[tc.id]
        log_entries.append({"tool": tc.function.name, "input": inputs, "result": result_obj})
        msg_entries.append({"role": "tool", "tool_call_id": tc.id, "content": result_str})

    return log_entries, msg_entries


def _post_process(
    client,
    task_id: str,
    question: str,
    brand: str,
    store_id: str,
    tool_calls_log: list,
    thinking_steps: list,
    confidence: dict,
    confidence_score: int,
    resolution_status: str,
    ai_response: str,
    date_range: str,
    out_queue: Queue,
    t0: float,
    ordered_trace: list = None,
):
    reasoning_trace = " ".join(
        s.get("message", "") for s in thinking_steps
        if s.get("stage") != "inner_monologue"
    )
    ctx = {
        "task_id": task_id, "question": question, "brand": brand,
        "tool_calls_log": tool_calls_log, "thinking_steps": thinking_steps,
        "confidence": confidence, "confidence_score": confidence_score,
        "resolution_status": resolution_status, "ai_response": ai_response,
        "date_range": date_range, "reasoning_trace": reasoning_trace,
    }

    shadow_result = None
    explanations_result = None
    _MAX_RETRY = 3
    _RETRY_WAIT = 5  # seconds

    def _retry_shadow():
        for attempt in range(1, _MAX_RETRY + 1):
            out_queue.put({"event": "post_progress", "task": "shadow_check", "attempt": attempt, "max": _MAX_RETRY, "status": "running"})
            try:
                res = shadow_check(client, question, reasoning_trace, ai_response, tool_calls_log, brand, store_id)
                if isinstance(res, dict):
                    return res
            except Exception as e:
                _logger.info(_ck(f"shadow_check_attempt_{attempt}_ERROR", t0, t_pp, str(e)))
            if attempt < _MAX_RETRY:
                time.sleep(_RETRY_WAIT)
        return {"result": "PASS", "logic": f"Fallback pass setelah {_MAX_RETRY}x retry", "disclosure": "N/A - Error setelah semua retry."}

    def _retry_explain():
        for attempt in range(1, _MAX_RETRY + 1):
            out_queue.put({"event": "post_progress", "task": "ai_reasoning", "attempt": attempt, "max": _MAX_RETRY, "status": "running"})
            try:
                res = explain_confidence(client, question, tool_calls_log, confidence, date_range, brand, store_id)
                if isinstance(res, dict) and res:
                    return res
            except Exception as e:
                _logger.info(_ck(f"explain_confidence_attempt_{attempt}_ERROR", t0, t_pp, str(e)))
            if attempt < _MAX_RETRY:
                time.sleep(_RETRY_WAIT)
        return {}

    t_pp = time.perf_counter()
    with ThreadPoolExecutor(max_workers=2) as ex:
        f_shadow  = ex.submit(_retry_shadow)
        f_explain = ex.submit(_retry_explain)

        try:
            shadow_result = f_shadow.result(timeout=_MAX_RETRY * 60)
            _logger.info(_ck("shadow_check", t0, t_pp, f"result={shadow_result.get('result')}"))
            out_queue.put({"event": "shadow_check", **shadow_result})
            if shadow_result.get("result") == "FLAG":
                ctx["resolution_status"] = "AM Review Required (Shadow Check FLAG)"
        except Exception as e:
            _logger.info(_ck("shadow_check_ERROR", t0, t_pp, str(e)))
            shadow_result = {"result": "PASS", "logic": f"Gagal sepenuhnya: {e}", "disclosure": "N/A"}
            out_queue.put({"event": "shadow_check", **shadow_result})

        try:
            t_exp = time.perf_counter()
            explanations_result = f_explain.result(timeout=_MAX_RETRY * 60)
            _logger.info(_ck("explain_confidence", t0, t_exp))
            if explanations_result and isinstance(explanations_result, dict):
                out_queue.put({"event": "confidence_explanation", "explanations": explanations_result})
        except Exception as e:
            _logger.info(_ck("explain_confidence_ERROR", t0, t_pp, str(e)))
            explanations_result = {}

    resolution_status = str(ctx["resolution_status"])

    t_cu = time.perf_counter()
    try:
        cu.update_task(
            task_id, ai_response, confidence_score, resolution_status,
            execution_trace={
                "ordered_trace": ordered_trace or [],
                "thinking_steps": thinking_steps,
                "tool_calls": tool_calls_log,
                "confidence": confidence,
                "shadow_check": shadow_result,
                "confidence_explanation": explanations_result,
            }
        )
        _logger.info(_ck("cu.update_task", t0, t_cu))
    except Exception:
        pass

    if confidence_score < ESCALATION_THRESHOLD:
        reason = (
            f"Confidence score {confidence_score}% di bawah threshold {ESCALATION_THRESHOLD}%. "
            "Data tidak mencukupi untuk analisis yang diminta."
        )
        try:
            t_esc = time.perf_counter()
            cu.create_escalation_task(task_id, question, brand, reason)
            _logger.info(_ck("cu.create_escalation", t0, t_esc))
        except Exception:
            pass

    try:
        t_cmt = time.perf_counter()
        comment = build_summary_comment(
            question=question, thinking_steps=thinking_steps,
            tool_calls_log=tool_calls_log, confidence=confidence,
            resolution_status=resolution_status, ai_response=ai_response,
        )
        cu.add_comment(task_id, comment)
        _logger.info(_ck("cu.add_comment", t0, t_cmt))
    except Exception:
        pass

    # Run registered post-hooks
    for hook in _POST_HOOKS:
        try:
            result = hook(client, ctx)
            if result:
                out_queue.put(result)
        except Exception as e:
            _logger.info("post_hook_ERROR hook=%s err=%s", getattr(hook, '__name__', '?'), e)

    _logger.info("[%6dms] DONE task_id=%s resolution=%r", _ms(t0), task_id, resolution_status)
    out_queue.put(None)


def route_stream(task: dict, force: bool = False, query_override: str | None = None) -> Generator[dict, None, None]:
    t0 = time.perf_counter()
    original_question = task["task_name"]
    task_id = task["task_id"]
    _logger.info("[     0ms] START task_id=%s q=%r", task_id, original_question[:80])

    if query_override and query_override.strip():
        t_synth = time.perf_counter()
        synth_client = _make_client()
        question = synthesize_query(synth_client, original_question, query_override.strip())
        _logger.info(_ck("synthesize_query", t0, t_synth))
        yield {"event": "query_refined", "original": original_question, "clarification": query_override.strip(), "refined": question}
        
        try:
            cu.update_task_fields(task_id, {"name": question})
        except Exception:
            pass
    else:
        question = original_question

    brand      = _get_task_field(task, "brand")
    date_range = _get_task_field(task, "date_range")

    # Cache hit
    if not force and task.get("ai_response"):
        trace = task.get("execution_trace", {})
        yield {"event": "cached", "message": "Menggunakan hasil analisis sebelumnya"}
        
        if "ordered_trace" in trace:
            for evt in trace["ordered_trace"]:
                yield evt
        else:
            for step in trace.get("thinking_steps", []):
                yield {"event": "thinking", **step}
            for tc in trace.get("tool_calls", []):
                yield {"event": "tool_call", "tool": tc["tool"], "input": tc["input"]}
                yield {"event": "tool_result", "tool": tc["tool"], "result": tc["result"]}
                
        if trace.get("shadow_check"):
            yield {"event": "shadow_check", **trace["shadow_check"]}
            
        if trace.get("confidence_explanation"):
            yield {"event": "confidence_explanation", "explanations": trace["confidence_explanation"]}

        if trace.get("confidence"):
            c = trace["confidence"]
            yield {"event": "confidence", "score": c["score"], "label": c["label"], "breakdown": c["breakdown"]}
            
        yield {
            "event": "done",
            "resolution": task["custom_fields"].get("Resolution Status") or "AI Direct Send",
            "response": task["ai_response"],
            "escalation_task": None,
            "summary": "",
            "cached": True,
            "timing_ms": 0,
        }
        return

    # Brand Resolution — fast path alias match, slow path Haiku fallback
    today_str = datetime.now().strftime("%Y-%m-%d")
    t_brand = time.perf_counter()
    _br_client = _make_client()
    brand_info = resolve_brand(question, _br_client)
    _logger.info(_ck("brand_resolution", t0, t_brand, f"result={brand_info}"))

    if brand_info is None:
        from .config import BRAND_STORE_MAP
        yield {
            "event": "clarification_needed",
            "question": "Brand mana yang dimaksud?",
            "slots": [{"label": "Brand", "options": list(BRAND_STORE_MAP.keys())}],
            "message": "Tidak dapat menentukan brand dari query. Mohon sebutkan nama brand.",
        }
        return

    brand      = brand_info["brand_id"]
    store_id   = brand_info["store_id"]
    project_id = brand_info["project_id"]
    yield {"event": "brand_resolved", "brand_id": brand, "store_id": store_id, "project_id": project_id}

    # Intent Classification — step terpisah, return state + confidence
    t_intent = time.perf_counter()
    _ic_client = _make_client()
    intent = intent_classify(_ic_client, question)
    _logger.info(_ck("intent_classify", t0, t_intent,
                     f"state={intent['state']} confidence={intent.get('confidence', '?'):.2f}"))
    yield {"event": "intent_classified", **intent}

    if intent["result"] == "CLARIFY":
        yield {
            "event": "clarification_needed",
            "question": intent.get("question", "Query tidak dapat diklasifikasikan dengan confidence yang cukup."),
            "slots": [{"label": "Topik", "options": intent.get("options", [])}],
            "message": f"Klarifikasi topik: {intent.get('reasoning', '')}",
        }
        return

    # Filter tools sesuai state aktif dari states.yaml
    active_tools = get_tools_for_state(intent["state"], TOOLS)
    _logger.info(_ck("tools_filtered", t0, t_intent,
                     f"state={intent['state']} tools={[t['function']['name'] for t in active_tools]}"))

    # Extract date_range jika masih kosong
    if not date_range:
        t_extract = time.perf_counter()
        _ext_client = _make_client()
        ctx = extract_or_clarify(_ext_client, question, today_str)
        _logger.info(_ck("extract_or_clarify", t0, t_extract, f"result={ctx['result']}"))

        if ctx["result"] == "EXTRACTED":
            date_range = ctx["date_range"] or date_range
            yield {"event": "context_extracted", "brand": brand, "date_range": date_range}
        else:
            yield {
                "event":    "clarification_needed",
                "question": ctx["question"],
                "slots":    ctx["slots"],
                "message":  "Sistem membutuhkan informasi tambahan.",
            }
            return

    # Mark in_progress di ClickUp
    try:
        cu.mark_in_progress(task_id)
    except Exception:
        pass

    # ── Optimistic: gate0 + LLM iter 1 jalan PARALEL ─────────────────────────
    # 99% query = VALID, jadi LLM iter 1 biasanya langsung dipakai
    user_content = build_user_prompt(question, brand, store_id, date_range, project_id=project_id)
    client = _make_client()
    messages_init = [
        {"role": "system", "content": build_system_prompt(store_id)},
        {"role": "user", "content": user_content},
    ]

    def _run_gate0():
        t = time.perf_counter()
        gc = _make_client()
        r = gate0_check(gc, question, datetime.now().strftime("%Y-%m-%d"))
        _logger.info(_ck("gate0_check", t0, t, f"result={r['result']}"))
        return r

    def _run_llm_iter1():
        t = time.perf_counter()
        r = client.chat.completions.create(
            model=OLLAMA_MODEL,
            messages=messages_init,
            tools=active_tools,
            tool_choice="auto",
        )
        _logger.info(_ck("llm_call_iter_1", t0, t,
                         f"finish={r.choices[0].finish_reason} "
                         f"tool_calls={len(r.choices[0].message.tool_calls or [])}"))
        return r

    t_par = time.perf_counter()
    with ThreadPoolExecutor(max_workers=2) as ex:
        f_gate0 = ex.submit(_run_gate0)
        f_llm1  = ex.submit(_run_llm_iter1)
        gate0   = f_gate0.result()
        llm1    = f_llm1.result()
    _logger.info(_ck("parallel_gate0+llm1", t0, t_par,
                     f"gate0={gate0['result']}"))

    yield {"event": "gate0", "result": gate0["result"], "message": gate0["message"]}

    if gate0["result"] == "CLARIFY":
        # Discard LLM result, tanya user dulu
        yield {
            "event": "gate0_clarify",
            "message": gate0["message"],
            "question": gate0["question"],
            "options": gate0["options"],
            "note": "Query mengandung kontradiksi logis. Semua proses downstream di-skip.",
        }
        return

    # gate0 = VALID → pakai LLM iter 1 yang sudah siap
    ordered_trace = []
    thinking_steps = []
    step_understanding = {
        "stage": "understanding",
        "message": f"Memahami pertanyaan: \"{question}\"",
        "context": {
            "brand": brand,
            "store_id": store_id,
            "date_range": date_range,
            "state": intent["state"],
            "state_desc": intent.get("state_desc", ""),
            "state_confidence": f"{intent.get('confidence', 0):.0%}",
            "state_reasoning": intent.get("reasoning", ""),
            "allowed_tools": [t["function"]["name"] for t in active_tools],
        },
    }
    thinking_steps.append(step_understanding)
    ordered_trace.append({"event": "thinking", **step_understanding})
    yield {"event": "thinking", **step_understanding}

    messages = messages_init.copy()
    tool_calls_log = []

    # Proses hasil llm1 langsung (iter 1 sudah selesai)
    step_reasoning = {"stage": "reasoning", "message": "[Iterasi 1] Menentukan tool yang tepat..."}
    thinking_steps.append(step_reasoning)
    ordered_trace.append({"event": "thinking", **step_reasoning})
    yield {"event": "thinking", **step_reasoning}

    # Proses iter-1
    msg1    = llm1.choices[0].message
    finish1 = llm1.choices[0].finish_reason

    if msg1.content and msg1.content.strip():
        step_mono = {"stage": "inner_monologue", "message": msg1.content.strip()}
        thinking_steps.append(step_mono)
        ordered_trace.append({"event": "thinking", **step_mono})
        yield {"event": "thinking", **step_mono}

    iter1_done = finish1 == "stop" or not msg1.tool_calls
    if iter1_done:
        messages.append({"role": "assistant", "content": msg1.content or ""})
    else:
        messages.append(msg1)
        log_entries, msg_entries = _run_tool_calls(msg1, t0, 1)
        for entry in log_entries:
            tool_calls_log.append(entry)
            ordered_trace.append({"event": "tool_call", "tool": entry["tool"], "input": entry["input"]})
            yield {"event": "tool_call", "tool": entry["tool"], "input": entry["input"]}
            ordered_trace.append({"event": "tool_result", "tool": entry["tool"], "result": entry["result"]})
            yield {"event": "tool_result", "tool": entry["tool"], "result": entry["result"]}
        messages.extend(msg_entries)

    # Iterasi lanjutan
    for iteration in (range(2, MAX_LLM_ITERATIONS + 1) if not iter1_done else []):
        step_reasoning = {"stage": "reasoning", "message": f"[Iterasi {iteration}] Menentukan tool yang tepat..."}
        thinking_steps.append(step_reasoning)
        ordered_trace.append({"event": "thinking", **step_reasoning})
        yield {"event": "thinking", **step_reasoning}

        t_llm = time.perf_counter()
        response = client.chat.completions.create(
            model=OLLAMA_MODEL, messages=messages, tools=active_tools, tool_choice="auto",
        )
        msg = response.choices[0].message
        finish_reason = response.choices[0].finish_reason
        _logger.info(_ck(f"llm_call_iter_{iteration}", t0, t_llm,
                         f"finish={finish_reason} tool_calls={len(msg.tool_calls or [])}"))

        if msg.content and msg.content.strip():
            step_mono = {"stage": "inner_monologue", "message": msg.content.strip()}
            thinking_steps.append(step_mono)
            ordered_trace.append({"event": "thinking", **step_mono})
            yield {"event": "thinking", **step_mono}

        if finish_reason == "stop" or not msg.tool_calls:
            messages.append({"role": "assistant", "content": msg.content or ""})
            break

        messages.append(msg)
        log_entries, msg_entries = _run_tool_calls(msg, t0, iteration)
        for entry in log_entries:
            tool_calls_log.append(entry)
            ordered_trace.append({"event": "tool_call", "tool": entry["tool"], "input": entry["input"]})
            yield {"event": "tool_call", "tool": entry["tool"], "input": entry["input"]}
            ordered_trace.append({"event": "tool_result", "tool": entry["tool"], "result": entry["result"]})
            yield {"event": "tool_result", "tool": entry["tool"], "result": entry["result"]}
        messages.extend(msg_entries)

    final_msg = messages[-1]
    ai_response = (final_msg.get("content", "") if isinstance(final_msg, dict) else (final_msg.content or "")).strip()

    # Confidence (no LLM)
    t_conf = time.perf_counter()
    keywords   = [w for w in question.lower().split() if len(w) > 3]
    confidence = calculate_confidence(
        tool_calls_log, keywords, date_range,
        thinking_steps=thinking_steps,
        ai_response=ai_response,
        client=None,
    )
    confidence_score  = int(confidence["score"])
    resolution_status = "AI Direct Send" if confidence_score >= ESCALATION_THRESHOLD else "AM Review Required"
    _logger.info(_ck("calculate_confidence", t0, t_conf, f"score={confidence_score}%"))

    yield {"event": "confidence", "score": confidence_score, "label": confidence["label"], "breakdown": confidence["breakdown"]}

    # ✅ YIELD DONE — jawaban langsung tampil
    answer_ms = _ms(t0)
    _logger.info("[%6dms] *** ANSWER VISIBLE *** task_id=%s", answer_ms, task_id)

    yield {
        "event": "done",
        "resolution": resolution_status,
        "response": ai_response,
        "escalation_task": None,
        "summary": "",
        "timing_ms": answer_ms,
    }

    # Background post-processing
    out_queue: Queue = Queue()
    bg_executor = ThreadPoolExecutor(max_workers=1)
    bg_executor.submit(
        _post_process,
        client, task_id, question, brand, store_id,
        tool_calls_log, thinking_steps, confidence,
        confidence_score, resolution_status, ai_response, date_range,
        out_queue, t0, ordered_trace,
    )

    while True:
        try:
            event = out_queue.get(timeout=60)
        except Empty:
            break
        if event is None:
            break
        yield event

    bg_executor.shutdown(wait=False)


def route(task: dict) -> dict:
    """Blocking wrapper, kumpulkan semua events dari route_stream."""
    tool_calls_log = []
    result = {}
    for event in route_stream(task):
        if event["event"] == "tool_result":
            tool_calls_log.append({"tool": event["tool"], "result": event["result"]})
        elif event["event"] == "confidence":
            result["confidence_score"]     = event["score"]
            result["confidence_label"]     = event["label"]
            result["confidence_breakdown"] = event["breakdown"]
        elif event["event"] == "done":
            result["ai_response"]       = event["response"]
            result["resolution_status"] = event["resolution"]
            result["escalation_task"]   = event["escalation_task"]
    result["tool_calls"] = tool_calls_log
    return result
