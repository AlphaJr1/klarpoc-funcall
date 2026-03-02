import json
import os
from datetime import datetime
from typing import Generator
from openai import OpenAI
from .brand_guard import get_store_id, BrandAccessError
from . import loyverse_tools as lv
import clickup_sync as cu
from .config import OLLAMA_MODEL, OLLAMA_BASE_URL, ESCALATION_THRESHOLD, RESOLVED_THRESHOLD


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_daily_summary",
            "description": "Ambil ringkasan penjualan harian untuk satu toko pada tanggal tertentu.",
            "parameters": {
                "type": "object",
                "properties": {
                    "store_id": {"type": "string", "description": "ID toko Loyverse"},
                    "date": {"type": "string", "description": "Tanggal format YYYY-MM-DD"},
                },
                "required": ["store_id", "date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_date_range_metrics",
            "description": "Ambil metrik agregat transaksi dalam rentang tanggal.",
            "parameters": {
                "type": "object",
                "properties": {
                    "store_id": {"type": "string"},
                    "start_date": {"type": "string", "description": "YYYY-MM-DD"},
                    "end_date": {"type": "string", "description": "YYYY-MM-DD"},
                },
                "required": ["store_id", "start_date", "end_date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_top_products",
            "description": "Ambil produk terlaris berdasarkan subtotal revenue pada tanggal tertentu.",
            "parameters": {
                "type": "object",
                "properties": {
                    "store_id": {"type": "string"},
                    "date": {"type": "string", "description": "YYYY-MM-DD"},
                    "limit": {"type": "integer", "default": 5},
                },
                "required": ["store_id", "date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_employee_performance",
            "description": "Ambil performa karyawan (jumlah transaksi & total revenue) pada tanggal tertentu.",
            "parameters": {
                "type": "object",
                "properties": {
                    "store_id": {"type": "string"},
                    "date": {"type": "string", "description": "YYYY-MM-DD"},
                },
                "required": ["store_id", "date"],
            },
        },
    },
]

TOOL_REGISTRY = {
    "get_daily_summary": lv.get_daily_summary,
    "get_date_range_metrics": lv.get_date_range_metrics,
    "get_top_products": lv.get_top_products,
    "get_employee_performance": lv.get_employee_performance,
}


def _execute_tool(name: str, inputs: dict) -> str:
    fn = TOOL_REGISTRY.get(name)
    if not fn:
        return json.dumps({"error": f"Tool '{name}' tidak dikenal."})
    try:
        result = fn(**inputs)
        if not result:
            return json.dumps({"error": "Data tidak ditemukan."})
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})


def _score_dnc(thinking_steps: list) -> tuple[float, str]:
    """DNC stub: cek reasoning trace coherence. Returns (score 0-100, reason)."""
    if not thinking_steps:
        return 50.0, "Tidak ada reasoning trace tersedia"
    conflict_keywords = {"error", "tidak bisa", "tidak tahu", "ambigu", "bingung", "conflict", "mismatch", "kontradiksi"}
    messages = " ".join(s.get("message", "").lower() for s in thinking_steps)
    hits = sum(1 for kw in conflict_keywords if kw in messages)
    if hits == 0:
        return 100.0, "Reasoning trace konsisten, tidak ada konflik terdeteksi"
    elif hits == 1:
        return 60.0, f"Satu indikasi ambiguitas terdeteksi dalam reasoning trace"
    else:
        return 20.0, f"{hits} konflik/ambiguitas terdeteksi dalam reasoning trace"


def _calculate_confidence(
    tool_calls_log: list,
    query_keywords: list,
    date_range: str,
    thinking_steps: list | None = None,
    T_optimal: float | None = None,
) -> dict:
    """
    6-factor confidence score sesuai research framework.
    Weights: Completeness 25%, Tool_Routing 20%, Complexity 15%,
             Data_Validation 15%, Freshness 15%, DNC 10%
    T_optimal: temperature scaling scalar (Phase 2). Jika None, skip calibration.
    """
    thinking_steps = thinking_steps or []

    # 1. Completeness (25%): rasio tool call sukses
    total_tools = len(tool_calls_log)
    if total_tools == 0:
        completeness = 30.0
        completeness_reason = "Tidak ada tool dipanggil, data tidak dapat diverifikasi"
    else:
        success = sum(1 for t in tool_calls_log if "error" not in t.get("result", {}))
        ratio = success / total_tools
        completeness = ratio * 100
        if ratio == 1.0:
            completeness_reason = f"Semua {total_tools} tool call berhasil"
        elif ratio >= 0.5:
            completeness_reason = f"{success}/{total_tools} tool call sukses, sebagian data tersedia"
        else:
            completeness_reason = f"Hanya {success}/{total_tools} tool call sukses, mayoritas error"

    # 2. Tool_Routing (20%): apakah tool yang dipanggil relevan & tidak redundan
    if total_tools == 0:
        tool_routing = 30.0
        tool_routing_reason = "Tidak ada tool dipanggil"
    else:
        tool_names = [t.get("tool", "") for t in tool_calls_log]
        unique_ratio = len(set(tool_names)) / total_tools
        has_error = any("error" in t.get("result", {}) for t in tool_calls_log)
        if unique_ratio >= 0.8 and not has_error:
            tool_routing = 100.0
            tool_routing_reason = f"{len(set(tool_names))} tool unik dipanggil tanpa redundansi"
        elif unique_ratio >= 0.5:
            tool_routing = 65.0
            tool_routing_reason = f"Beberapa tool redundan atau ada error pada routing"
        else:
            tool_routing = 30.0
            tool_routing_reason = f"Tool routing tidak efisien — banyak duplikasi"

    # 3. Complexity (15%): estimasi kompleksitas query dari keyword & jumlah tool
    kw_count = len(query_keywords)
    if kw_count >= 4 and total_tools >= 2:
        complexity = 100.0
        complexity_reason = f"Query spesifik ({kw_count} keyword) dengan multi-tool — kompleksitas tinggi tapi terjawab"
    elif kw_count >= 2:
        complexity = 70.0
        complexity_reason = f"{kw_count} keyword terdeteksi — query cukup jelas"
    elif kw_count == 1:
        complexity = 40.0
        complexity_reason = f"Query kurang spesifik ({kw_count} keyword)"
    else:
        complexity = 10.0
        complexity_reason = "Query terlalu umum, intent tidak terdeteksi"

    # 4. Data_Validation (15%): cek anomali dalam result (nilai negatif, null)
    if total_tools == 0:
        data_validation = 50.0
        data_validation_reason = "Tidak ada data untuk divalidasi"
    else:
        anomaly_count = 0
        for t in tool_calls_log:
            result = t.get("result", {})
            if "error" in result:
                anomaly_count += 1
                continue
            result_str = json.dumps(result)
            if any(x in result_str for x in ['"null"', ': null', ': -', '"-']):
                anomaly_count += 1
        if anomaly_count == 0:
            data_validation = 100.0
            data_validation_reason = "Tidak ada anomali terdeteksi dalam data hasil tool"
        elif anomaly_count == 1:
            data_validation = 50.0
            data_validation_reason = "Satu anomali/nilai mencurigakan terdeteksi dalam data"
        else:
            data_validation = 20.0
            data_validation_reason = f"{anomaly_count} anomali terdeteksi — data perlu diverifikasi"

    # 5. Freshness (15%): per-jam untuk POS data
    try:
        end_date_str = date_range.split(" - ")[-1].strip() if date_range else ""
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d") if end_date_str else datetime.now()
        age_hours = (datetime.now() - end_date).total_seconds() / 3600
    except (ValueError, AttributeError):
        age_hours = 0

    if age_hours <= 4:
        freshness = 100.0
        freshness_reason = f"Data {age_hours:.0f} jam yang lalu — sangat fresh"
    elif age_hours <= 24:
        freshness = 80.0
        freshness_reason = f"Data {age_hours:.0f} jam yang lalu — fresh (hari ini)"
    elif age_hours <= 168:  # 7 hari
        freshness = 60.0
        freshness_reason = f"Data {age_hours / 24:.0f} hari yang lalu — masih relevan"
    elif age_hours <= 720:  # 30 hari
        freshness = 35.0
        freshness_reason = f"Data {age_hours / 24:.0f} hari yang lalu — agak lama"
    else:
        freshness = 10.0
        freshness_reason = f"Data {age_hours / 24:.0f} hari yang lalu — historical"

    # 6. DNC — Reasoning Trace Coherence (10%)
    dnc, dnc_reason = _score_dnc(thinking_steps)

    raw_score = round(
        completeness   * 0.25 +
        tool_routing   * 0.20 +
        complexity     * 0.15 +
        data_validation * 0.15 +
        freshness      * 0.15 +
        dnc            * 0.10,
        1,
    )

    # Calibration hook: temperature scaling (Phase 2)
    if T_optimal is not None and T_optimal > 0:
        # Transform: score_calibrated = 1 / (1 + exp(-logit(score/100) / T)) * 100
        import math
        p = max(0.01, min(0.99, raw_score / 100))
        logit = math.log(p / (1 - p))
        calibrated = 1 / (1 + math.exp(-logit / T_optimal)) * 100
        final_score = round(calibrated, 1)
    else:
        final_score = raw_score

    label = "high" if final_score >= 80 else "medium" if final_score >= 50 else "low"

    return {
        "score": final_score,
        "label": label,
        "breakdown": {
            "completeness":    {"score": round(completeness, 1),    "weight": "25%", "reason": completeness_reason},
            "tool_routing":    {"score": round(tool_routing, 1),    "weight": "20%", "reason": tool_routing_reason},
            "complexity":      {"score": round(complexity, 1),      "weight": "15%", "reason": complexity_reason},
            "data_validation": {"score": round(data_validation, 1), "weight": "15%", "reason": data_validation_reason},
            "freshness":       {"score": round(freshness, 1),       "weight": "15%", "reason": freshness_reason},
            "dnc":             {"score": round(dnc, 1),             "weight": "10%", "reason": dnc_reason},
        },
    }


def _make_client() -> OpenAI:
    return OpenAI(
        api_key=os.environ.get("OLLAMA_API_KEY", ""),
        base_url=f"{OLLAMA_BASE_URL}/v1",
    )


def _explain_confidence(
    client: OpenAI,
    question: str,
    tool_calls_log: list,
    confidence: dict,
    date_range: str,
) -> dict:
    """LLM call khusus: minta model jelaskan tiap faktor confidence secara detail."""
    tools_summary = "\n".join(
        f"- {tc['tool']}({list(tc.get('input', {}).keys())}): "
        f"{str(tc.get('result', {}))[:300]}"
        for tc in tool_calls_log
    ) or "- Tidak ada tool call dilakukan"

    factor_list = "\n".join(
        f"- {k}: score={v['score']}%, weight={v['weight']}, alasan_singkat=\"{v['reason']}\""
        for k, v in confidence["breakdown"].items()
    )

    prompt = (
        f"Kamu adalah AI analyst. Berikan penjelasan DETAIL per-faktor mengapa skor confidence seperti ini.\n\n"
        f"QUERY: {question}\n"
        f"DATE RANGE: {date_range}\n\n"
        f"TOOL CALLS & HASIL:\n{tools_summary}\n\n"
        f"CONFIDENCE BREAKDOWN:\n{factor_list}\n\n"
        f"TOTAL SCORE: {confidence['score']}% ({confidence['label']})\n\n"
        "Untuk setiap faktor, tulis 2-3 kalimat dalam Bahasa Indonesia yang menjelaskan:\n"
        "1. Mengapa skor itu diberikan berdasarkan konteks query & data nyata\n"
        "2. Apa yang menyebabkan nilai tidak 100% (jika < 100%)\n\n"
        "PENTING: Jawab HANYA JSON valid ini, tanpa teks lain:\n"
        '{"completeness":"...","tool_routing":"...","complexity":"...","data_validation":"...","freshness":"...","dnc":"..."}'
    )

    try:
        resp = client.chat.completions.create(
            model=OLLAMA_MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        text = resp.choices[0].message.content.strip()
        # Bersihkan jika LLM wrap dengan markdown code block
        if "```" in text:
            parts = text.split("```")
            text = parts[1] if len(parts) > 1 else parts[0]
            if text.startswith("json"):
                text = text[4:].strip()
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
    except Exception:
        pass
    return {}


def _check_clarification(question: str, brand: str, date_range: str) -> list[str]:
    """Return list pertanyaan klarifikasi jika input ambigu. Kosong = siap proses."""
    issues = []
    if not brand or brand.strip() == "":
        issues.append("Brand belum dipilih. Pilih brand mana yang ingin dianalisis?")
    if not date_range or date_range.strip() == "":
        issues.append("Rentang tanggal belum diisi. Periode mana yang ingin dianalisis? (contoh: 2024-01-01 - 2024-01-31)")
    if len(question.split()) < 4:
        issues.append(f"Pertanyaan '{question}' terlalu singkat. Bisa diperjelas maksudnya?")
    return issues


def _build_system_prompt(store_id: str) -> str:
    return (
        f"Kamu adalah AI analyst untuk data POS Loyverse. "
        f"Store ID yang boleh diakses: {store_id}. "
        "Analisis pertanyaan user dan gunakan tools yang paling relevan secara mandiri. "
        "Jawab dalam Bahasa Indonesia, ringkas dan akurat. Sertakan angka spesifik dari data."
    )

def _build_summary_comment(
    question: str,
    thinking_steps: list[dict],
    tool_calls_log: list[dict],
    confidence: dict,
    resolution_status: str,
    ai_response: str,
) -> str:
    parts = []

    parts.append("## 🤖 AI Agent Execution Summary\n")
    parts.append(f"**Task:** {question}\n")

    if thinking_steps:
        parts.append("---\n### 🧠 Thinking Process\n")
        stage_icon = {"understanding": "🔍", "reasoning": "⚙️", "inner_monologue": "💭"}
        stage_label = {"understanding": "Understand", "reasoning": "Reason", "inner_monologue": "Thought"}
        for step in thinking_steps:
            s = step.get("stage", "")
            icon = stage_icon.get(s, "•")
            label = stage_label.get(s, s)
            parts.append(f"- {icon} **{label}:** {step.get('message', '')}")
        parts.append("")

    if tool_calls_log:
        parts.append(f"---\n### 🔧 Tool Calls ({len(tool_calls_log)} calls)\n")
        for i, tc in enumerate(tool_calls_log, 1):
            args = ", ".join(f"`{k}`=`{v}`" for k, v in tc.get("input", {}).items())
            parts.append(f"**{i}. `{tc['tool']}`** ({args})\n")
            result = tc.get("result", {})
            if "error" in result:
                parts.append(f"> ❌ Error: {result['error']}\n")
            else:
                keys = list(result.keys())[:5]
                parts.append("| Key | Value |")
                parts.append("|-----|-------|")
                for k in keys:
                    parts.append(f"| {k} | {result[k]} |")
                parts.append("")

    bd = confidence["breakdown"]
    score = int(confidence["score"])
    label = confidence["label"].upper()
    bar = "🟢" if score >= 80 else "🟡" if score >= 50 else "🔴"
    parts.append(f"---\n### 📊 Confidence Score: {bar} **{score}%** `{label}`\n")
    parts.append("| Dimension | Weight | Score | Reason |")
    parts.append("|-----------|--------|-------|--------|")
    for dim, val in bd.items():
        parts.append(f"| {dim.capitalize()} | {val['weight']} | {val['score']}% | {val['reason']} |")
    parts.append("")

    res_icon = "✅" if "Direct" in resolution_status else "⚠️"
    parts.append(f"---\n**Resolution:** {res_icon} {resolution_status}\n")

    parts.append("---\n### 💬 Final Answer\n")
    parts.append(ai_response)

    return "\n".join(parts)



def route_stream(task: dict, force: bool = False) -> Generator[dict, None, None]:
    """Generator yang yield SSE events secara real-time saat AI memproses task."""
    question = task["task_name"]

    brand = task["custom_fields"].get("Brand", "")
    task_id = task["task_id"]
    date_range = task["custom_fields"].get("Date Range", "")

    # Cek cache — jika sudah ada ai_response dan tidak force, replay execution_trace
    if not force and task.get("ai_response"):
        trace = task.get("execution_trace", {})
        yield {"event": "cached", "message": "Menggunakan hasil analisis sebelumnya"}
        for step in trace.get("thinking_steps", []):
            yield {"event": "thinking", **step}
        for tc in trace.get("tool_calls", []):
            yield {"event": "tool_call", "tool": tc["tool"], "input": tc["input"]}
            yield {"event": "tool_result", "tool": tc["tool"], "result": tc["result"]}
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
        }
        return

    clarification_needed = _check_clarification(question, brand, date_range)
    if clarification_needed:
        yield {
            "event": "clarification_needed",
            "questions": clarification_needed,
            "message": "Butuh info tambahan sebelum analisis bisa dilakukan.",
        }
        return

    try:
        store_id = get_store_id(brand)
    except BrandAccessError as e:
        yield {"event": "error", "message": str(e)}
        return

    thinking_steps = []
    step_understanding = {"stage": "understanding", "message": f"Memahami pertanyaan: \"{question}\"", "context": {"brand": brand, "store_id": store_id, "date_range": date_range}}
    thinking_steps.append(step_understanding)
    yield {"event": "thinking", **step_understanding}

    user_content = (
        f"Pertanyaan: {question}\n"
        f"Brand: {brand} | Store: {store_id}\n"
        f"Rentang tanggal: {date_range}\n\n"
        "Gunakan tools yang paling relevan untuk menjawab pertanyaan ini."
    )

    client = _make_client()
    messages = [
        {"role": "system", "content": _build_system_prompt(store_id)},
        {"role": "user", "content": user_content},
    ]
    tool_calls_log = []
    iteration = 0

    for _ in range(5):
        iteration += 1

        step_reasoning = {"stage": "reasoning", "message": f"[Iterasi {iteration}] Menentukan tool yang tepat..."}
        thinking_steps.append(step_reasoning)
        yield {"event": "thinking", **step_reasoning}

        response = client.chat.completions.create(
            model=OLLAMA_MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
        )
        msg = response.choices[0].message
        finish_reason = response.choices[0].finish_reason

        if msg.content and msg.content.strip():
            step_mono = {"stage": "inner_monologue", "message": msg.content.strip()}
            thinking_steps.append(step_mono)
            yield {"event": "thinking", **step_mono}

        if finish_reason == "stop" or not msg.tool_calls:
            messages.append({"role": "assistant", "content": msg.content or ""})
            break

        messages.append(msg)
        for tc in msg.tool_calls:
            try:
                inputs = json.loads(tc.function.arguments)
            except Exception:
                inputs = {}

            # Step 3: Tool call transparan
            yield {
                "event": "tool_call",
                "tool": tc.function.name,
                "input": inputs,
            }

            result_str = _execute_tool(tc.function.name, inputs)
            result_obj = json.loads(result_str)
            tool_calls_log.append({
                "tool": tc.function.name,
                "input": inputs,
                "result": result_obj,
            })

            # Step 4: Tool result transparan
            yield {
                "event": "tool_result",
                "tool": tc.function.name,
                "result": result_obj,
            }

            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result_str})

    final_text = (
        messages[-1].get("content", "") if isinstance(messages[-1], dict)
        else (messages[-1].content or "")
    )
    ai_response = final_text.strip()

    keywords = [w for w in question.lower().split() if len(w) > 3]
    confidence = _calculate_confidence(tool_calls_log, keywords, date_range, thinking_steps=thinking_steps)
    confidence_score = int(confidence["score"])
    confidence_breakdown = confidence["breakdown"]
    resolution_status = "AI Direct Send" if confidence_score >= ESCALATION_THRESHOLD else "AM Review Required"

    # Step 5: Confidence score
    yield {
        "event": "confidence",
        "score": confidence_score,
        "label": confidence["label"],
        "breakdown": confidence_breakdown,
    }

    # Step 5b: LLM explanation per-faktor
    try:
        explanations = _explain_confidence(client, question, tool_calls_log, confidence, date_range)
        if explanations:
            yield {"event": "confidence_explanation", "explanations": explanations}
    except Exception:
        pass

    try:
        cu.update_task(
            task_id, ai_response, confidence_score, resolution_status,
            execution_trace={
                "thinking_steps": thinking_steps,
                "tool_calls": tool_calls_log,
                "confidence": confidence,
            }
        )
    except Exception:
        pass

    escalation_task = None
    if confidence_score < ESCALATION_THRESHOLD:
        reason = (
            f"Confidence score {confidence_score}% di bawah threshold {ESCALATION_THRESHOLD}%. "
            "Data tidak mencukupi untuk analisis yang diminta."
        )
        try:
            escalation_task = cu.create_escalation_task(task_id, question, brand, reason)
        except Exception:
            pass

    comment = ""
    try:
        comment = _build_summary_comment(
            question=question,
            thinking_steps=thinking_steps,
            tool_calls_log=tool_calls_log,
            confidence=confidence,
            resolution_status=resolution_status,
            ai_response=ai_response,
        )
        cu.add_comment(task_id, comment)
    except Exception:
        pass

    # Step 6: Final answer
    yield {
        "event": "done",
        "resolution": resolution_status,
        "response": ai_response,
        "escalation_task": escalation_task,
        "summary": comment,
    }


def route(task: dict) -> dict:
    """Blocking wrapper, kumpulkan semua events dari route_stream."""
    tool_calls_log = []
    result = {}
    for event in route_stream(task):
        if event["event"] == "tool_result":
            tool_calls_log.append({"tool": event["tool"], "result": event["result"]})
        elif event["event"] == "confidence":
            result["confidence_score"] = event["score"]
            result["confidence_label"] = event["label"]
            result["confidence_breakdown"] = event["breakdown"]
        elif event["event"] == "done":
            result["ai_response"] = event["response"]
            result["resolution_status"] = event["resolution"]
            result["escalation_task"] = event["escalation_task"]
    result["tool_calls"] = tool_calls_log
    return result
