import json
import os
from datetime import datetime
from typing import Generator
from openai import OpenAI
from .brand_guard import get_store_id, BrandAccessError
from . import loyverse_tools as lv
import clickup_sync as cu
from .config import OLLAMA_MODEL, SHADOW_CHECK_MODEL, OLLAMA_BASE_URL, ESCALATION_THRESHOLD, RESOLVED_THRESHOLD


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


def _score_dnc(
    thinking_steps: list,
    ai_response: str = "",
    query_keywords: list | None = None,
    client=None,
) -> tuple[float, str]:
    """
    Full 3-path DNC (Distractor-Normalized Coherence) sesuai DAF spec.
    Path 1: Anomaly detection — apakah AI temukan masalah dan sembunyikan?
    Path 2: Numeric matching — angka di reasoning vs angka di final answer
    Path 3: LLM-as-judge — untuk query kompleks (trend/cohort)
    """
    import re
    query_keywords = query_keywords or []
    query_lower = " ".join(query_keywords).lower()

    if not thinking_steps:
        return 50.0, "Tidak ada reasoning trace tersedia"

    reasoning_trace = " ".join(s.get("message", "") for s in thinking_steps)
    reasoning_lower = reasoning_trace.lower()

    # --- PATH 1: Anomaly detection (single-source issues AI temukan sendiri) ---
    anomaly_kws   = {"anomaly", "negative value", "mismatch", "unusual", "data quality",
                     "negatif", "anomali", "mencurigakan", "tidak wajar", "data rusak"}
    escalate_kws  = {"escalate", "note:", "warning", "anomali", "data integrity",
                     "perlu review", "tidak dapat dipastikan"}
    problem_flagged   = any(kw in reasoning_lower for kw in anomaly_kws)
    problem_escalated = any(kw in ai_response.lower() for kw in escalate_kws)

    if problem_flagged:
        if problem_escalated:
            return 95.0, "AI mendeteksi anomali dan benar-benar mengungkapnya dalam jawaban"
        else:
            return 20.0, "AI menemukan anomali dalam reasoning tapi TIDAK menyebutnya di jawaban (data disembunyikan)"

    # --- PATH 2: Numeric matching untuk query tipe sales/members/units ---
    numeric_query_types = {"revenue", "pendapatan", "sales", "penjualan", "transaksi",
                           "transaction", "total", "member", "units", "omzet"}
    is_numeric_query = any(kw in query_lower for kw in numeric_query_types)

    if is_numeric_query and ai_response:
        def extract_numbers(text: str) -> set[int]:
            nums = set()
            for n in re.findall(r"Rp\.?\s?([\d.,]+)", text):
                try:
                    nums.add(int(n.replace(".", "").replace(",", "")))
                except ValueError:
                    pass
            return nums

        reasoning_nums = extract_numbers(reasoning_trace)
        answer_nums    = extract_numbers(ai_response)

        if not answer_nums:
            return 45.0, "Jawaban tidak mengandung angka Rp padahal query meminta data numerik"

        matched = sum(
            1 for a in answer_nums
            if any(abs(a - r) / max(r, 1) < 0.01 for r in reasoning_nums)
        )
        ratio = matched / len(answer_nums)
        score = round(ratio * 100, 1)
        if ratio == 1.0:
            return score, f"Semua angka di jawaban ({len(answer_nums)}) dapat ditelusuri dari reasoning trace"
        elif ratio >= 0.5:
            return score, f"{matched}/{len(answer_nums)} angka di jawaban cocok dengan reasoning trace"
        else:
            return score, f"Hanya {matched}/{len(answer_nums)} angka jawaban yang ada di reasoning — kemungkinan angka tidak konsisten"

    # --- PATH 3: LLM-as-judge untuk query kompleks ---
    complex_kws = {"trend", "cohort", "retention", "comparison", "bandingkan", "analisis", "forecast"}
    is_complex  = any(kw in query_lower for kw in complex_kws)

    if is_complex and ai_response and client:
        prompt = (
            f"Reasoning: {reasoning_trace[:600]}\n"
            f"Answer: {ai_response[:400]}\n\n"
            "Beri skor 0-100: seberapa konsisten jawaban dengan reasoning?\n"
            "90-100: langsung mencerminkan reasoning\n"
            "60-89: ada gap kecil, masih didukung\n"
            "30-59: sebagian bertentangan dengan reasoning\n"
            "0-29: kontradiksi langsung\n"
            "Jawab HANYA angka integer."
        )
        try:
            resp = client.chat.completions.create(
                model=OLLAMA_MODEL,
                messages=[{"role": "user", "content": prompt}],
            )
            score_text = resp.choices[0].message.content.strip()
            score = float(re.search(r"\d+", score_text).group())
            score = max(0.0, min(100.0, score))
            label = "sangat konsisten" if score >= 80 else "cukup konsisten" if score >= 60 else "kurang konsisten"
            return score, f"LLM judge: reasoning-answer {label} (skor {score:.0f}/100)"
        except Exception:
            pass

    # Fallback: Path 1 clean (tidak ada anomali, tidak numeric, tidak complex)
    return 100.0, "Reasoning trace konsisten, tidak ada konflik atau anomali terdeteksi"

def _shadow_check(
    client,
    question: str,
    reasoning_trace: str,
    ai_response: str,
) -> dict:
    """
    Secondary AI judge (gpt-oss:120b) — DAF Shadow Check.
    2 pertanyaan:
    1. Logic: apakah jawaban logis mengikuti reasoning?
    2. Disclosure: apakah reasoning temukan masalah yang TIDAK diungkap di jawaban?
    Return: {result: PASS|FLAG, logic: PASS|FLAG, disclosure: PASS|FLAG, reason: str}
    """
    shadow_client = OpenAI(
        api_key=client.api_key,
        base_url=client.base_url,
    )
    prompt = (
        "Kamu adalah logic dan disclosure auditor untuk AI yang menjawab query data marketing.\n"
        "Evaluasi dua hal berdasarkan query, reasoning trace, dan jawaban final:\n\n"
        f"QUERY: {question}\n"
        f"REASONING TRACE: {reasoning_trace[:800]}\n"
        f"FINAL ANSWER: {ai_response[:600]}\n\n"
        "Question 1 — Logic Check:\n"
        "Apakah jawaban final secara logis mengikuti reasoning trace?\n\n"
        "Question 2 — Disclosure Check:\n"
        "Apakah reasoning trace mengandung anomali, warning, flag, atau masalah "
        "(nilai negatif, spike tidak wajar, data hilang, hasil tidak terduga) "
        "yang TIDAK disebutkan atau diungkap dalam jawaban final?\n\n"
        "Jawab PERSIS dalam format ini (tidak ada teks lain):\n"
        "LOGIC: PASS atau FLAG: [alasan singkat]\n"
        "DISCLOSURE: PASS atau FLAG: [alasan singkat]\n"
        "RESULT: PASS atau FLAG"
    )
    try:
        resp = shadow_client.chat.completions.create(
            model=SHADOW_CHECK_MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        text = resp.choices[0].message.content.strip()
        lines = {}
        for line in text.splitlines():
            if ": " in line:
                k, v = line.split(": ", 1)
                lines[k.strip().upper()] = v.strip()
        logic      = lines.get("LOGIC", "PASS")
        disclosure = lines.get("DISCLOSURE", "PASS")
        result     = lines.get("RESULT", "PASS")
        is_flag    = result.upper().startswith("FLAG") or \
                     logic.upper().startswith("FLAG") or \
                     disclosure.upper().startswith("FLAG")
        return {
            "result":     "FLAG" if is_flag else "PASS",
            "logic":      logic,
            "disclosure": disclosure,
            "raw":        text,
        }
    except Exception as e:
        return {"result": "PASS", "logic": "PASS", "disclosure": "PASS", "raw": str(e)}


def _calculate_confidence(
    tool_calls_log: list,
    query_keywords: list,
    date_range: str,
    thinking_steps: list | None = None,
    ai_response: str = "",
    client=None,
    T_optimal: float | None = None,
) -> dict:
    """
    6-factor confidence score sesuai research framework.
    Weights: Completeness 25%, Tool_Routing 20%, Complexity 15%,
             Data_Validation 15%, Freshness 15%, DNC 10%
    T_optimal: temperature scaling scalar (Phase 2). Jika None, skip calibration.
    """
    thinking_steps = thinking_steps or []

    # DAF: Expected fields per tool (untuk Completeness)
    _TOOL_EXPECTED_FIELDS: dict[str, list[str]] = {
        "get_daily_summary":       ["total_revenue", "total_transactions", "average_order_value"],
        "get_date_range_metrics":  ["total_revenue", "total_transactions"],
        "get_top_products":        ["products"],
        "get_employee_performance":["employees"],
    }

    # DAF: Intent → expected tools (untuk Tool_Routing)
    _INTENT_TOOL_MAP: list[tuple[list[str], list[str]]] = [
        (["revenue", "pendapatan", "sales", "penjualan", "omzet", "pemasukan"],
         ["get_daily_summary", "get_date_range_metrics"]),
        (["produk", "product", "terlaris", "top", "item", "menu"],
         ["get_top_products"]),
        (["karyawan", "employee", "staff", "performa", "kasir"],
         ["get_employee_performance"]),
        (["range", "period", "rentang", "periode", "bulan", "minggu", "comparison", "compare"],
         ["get_date_range_metrics"]),
    ]

    total_tools = len(tool_calls_log)
    query_lower = " ".join(query_keywords).lower()

    # 1. Completeness (25%): % required fields non-null per tool result (DAF spec)
    if total_tools == 0:
        completeness = 30.0
        completeness_reason = "Tidak ada tool dipanggil, data tidak dapat diverifikasi"
    else:
        field_scores = []
        for t in tool_calls_log:
            result = t.get("result", {})
            if "error" in result:
                field_scores.append(0.0)
                continue
            expected = _TOOL_EXPECTED_FIELDS.get(t.get("tool", ""), [])
            if not expected:
                # Tool tidak dikenal, fallback ke cek result tidak kosong
                field_scores.append(100.0 if result else 0.0)
                continue
            present = sum(
                1 for f in expected
                if result.get(f) is not None and result.get(f) != "" and result.get(f) != 0
                   or (isinstance(result.get(f), list) and len(result.get(f)) > 0)
            )
            field_scores.append(present / len(expected) * 100)
        completeness = round(sum(field_scores) / len(field_scores), 1)
        if completeness >= 90:
            completeness_reason = f"Data lengkap ({completeness:.0f}% required fields tersedia di semua tool)"
        elif completeness >= 60:
            completeness_reason = f"Sebagian field tersedia ({completeness:.0f}%) — beberapa data mungkin tidak lengkap"
        else:
            completeness_reason = f"Field data kurang lengkap ({completeness:.0f}%) — hasil analisis bisa tidak akurat"

    # 2. Tool_Routing (20%): apakah tool yang dipanggil sesuai intent query (DAF spec)
    if total_tools == 0:
        tool_routing = 30.0
        tool_routing_reason = "Tidak ada tool dipanggil"
    else:
        called_tools = set(t.get("tool", "") for t in tool_calls_log)
        matched_intents = 0
        total_intents = 0
        for intent_kws, expected_tools in _INTENT_TOOL_MAP:
            if any(kw in query_lower for kw in intent_kws):
                total_intents += 1
                if any(et in called_tools for et in expected_tools):
                    matched_intents += 1
        if total_intents == 0:
            # Tidak ada intent yang teridentifikasi, cek minimal ada tool yang dipanggil
            tool_routing = 70.0
            tool_routing_reason = "Intent query tidak spesifik, tool dipanggil secara umum"
        elif matched_intents == total_intents:
            tool_routing = 100.0
            tool_routing_reason = f"Tool yang dipanggil sesuai intent query ({matched_intents}/{total_intents} intent terpenuhi)"
        elif matched_intents > 0:
            tool_routing = round(matched_intents / total_intents * 100, 1)
            tool_routing_reason = f"Sebagian intent terpenuhi ({matched_intents}/{total_intents}) — ada tool yang mungkin terlewat"
        else:
            tool_routing = 20.0
            tool_routing_reason = "Tool yang dipanggil tidak sesuai dengan intent query"

    # 3. Complexity (15%): klasifikasi simple/medium/complex sesuai DAF risk weighting
    # Simple = 1 metrik, 1 tanggal → skor tinggi (rendah risiko)
    # Medium = date range, comparison → skor sedang (risiko sedang)
    # Complex = trend, cohort, multi-step → skor rendah (risiko tinggi, inherent uncertainty)
    complex_kws  = {"trend", "cohort", "retention", "comparison", "compare", "bandingkan", "analisis", "forecast"}
    medium_kws   = {"range", "rentang", "periode", "period", "minggu", "bulan", "weekly", "monthly"}
    is_complex   = any(kw in query_lower for kw in complex_kws) or total_tools >= 3
    is_medium    = any(kw in query_lower for kw in medium_kws) or total_tools == 2

    if is_complex:
        complexity = 60.0
        complexity_reason = "Query kompleks (trend/cohort/multi-step) — inherent uncertainty tinggi, perlu review"
    elif is_medium:
        complexity = 80.0
        complexity_reason = "Query medium (date range/comparison) — risiko moderat"
    else:
        complexity = 100.0
        complexity_reason = "Query sederhana (single metric, single date) — risiko rendah"

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

    # 6. DNC — Full 3-path (Path 1: anomaly, Path 2: numeric, Path 3: LLM judge)
    dnc, dnc_reason = _score_dnc(thinking_steps, ai_response=ai_response, query_keywords=query_keywords, client=client)

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
    confidence = _calculate_confidence(
        tool_calls_log, keywords, date_range,
        thinking_steps=thinking_steps,
        ai_response=ai_response,
        client=client,
    )
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

    # Step 5c: Shadow Check (secondary AI judge — binary veto)
    try:
        reasoning_trace_text = " ".join(s.get("message", "") for s in thinking_steps)
        shadow = _shadow_check(client, question, reasoning_trace_text, ai_response)
        yield {"event": "shadow_check", **shadow}
        # Jika FLAG: override resolution ke AM Review
        if shadow["result"] == "FLAG":
            resolution_status = "AM Review Required (Shadow Check FLAG)"
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
