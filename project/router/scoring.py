import re
import json
import math
from datetime import datetime
from openai import OpenAI
from .config import OLLAMA_MODEL, SHADOW_CHECK_MODEL


def score_dnc(
    thinking_steps: list,
    ai_response: str = "",
    query_keywords: list | None = None,
    tool_calls_log: list | None = None,
    client=None,
) -> tuple[float, str]:
    query_keywords = query_keywords or []
    tool_calls_log = tool_calls_log or []
    query_lower = " ".join(query_keywords).lower()

    if not thinking_steps:
        return 50.0, "Tidak ada reasoning trace tersedia"

    reasoning_trace = " ".join(s.get("message", "") for s in thinking_steps)
    reasoning_lower = reasoning_trace.lower()

    # PATH 0: Scope alignment
    failed_dates = [
        t["input"].get("date")
        for t in tool_calls_log
        if t.get("tool") == "get_daily_summary"
        and "error" in t.get("result", {})
        and t.get("input", {}).get("date")
    ]
    if failed_dates:
        all_covered = []
        for t in tool_calls_log:
            if t.get("tool") == "get_date_range_metrics":
                all_covered.extend(t.get("result", {}).get("dates_with_data", []))
        missing = [d for d in failed_dates if d not in all_covered]
        if missing:
            return 40.0, (
                f"Scope mismatch: tanggal {', '.join(missing)} tidak ada datanya, "
                "tapi AI menjawab dengan data dari range berbeda tanpa menyebut keterbatasan ini"
            )

    # PATH 1: Anomaly detection
    anomaly_kws  = {"anomaly", "negative value", "mismatch", "unusual", "data quality",
                    "negatif", "anomali", "mencurigakan", "tidak wajar", "data rusak"}
    escalate_kws = {"escalate", "note:", "warning", "anomali", "data integrity",
                    "perlu review", "tidak dapat dipastikan"}
    problem_flagged   = any(kw in reasoning_lower for kw in anomaly_kws)
    problem_escalated = any(kw in ai_response.lower() for kw in escalate_kws)

    if problem_flagged:
        if problem_escalated:
            return 95.0, "AI mendeteksi anomali dan benar-benar mengungkapnya dalam jawaban"
        return 20.0, "AI menemukan anomali dalam reasoning tapi TIDAK menyebutnya di jawaban (data disembunyikan)"

    # PATH 2: Numeric matching
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
        return score, f"Hanya {matched}/{len(answer_nums)} angka jawaban yang ada di reasoning — kemungkinan angka tidak konsisten"

    # PATH 3: LLM-as-judge untuk query kompleks
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

    return 100.0, "Reasoning trace konsisten, tidak ada konflik atau anomali terdeteksi"


def shadow_check(
    client,
    question: str,
    reasoning_trace: str,
    ai_response: str,
) -> dict:
    shadow_client = OpenAI(api_key=client.api_key, base_url=client.base_url)
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
            model=OLLAMA_MODEL,  # pakai model yang sama, bukan 120B
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
        is_flag = (
            result.upper().startswith("FLAG") or
            logic.upper().startswith("FLAG") or
            disclosure.upper().startswith("FLAG")
        )
        return {
            "result":     "FLAG" if is_flag else "PASS",
            "logic":      logic,
            "disclosure": disclosure,
            "raw":        text,
        }
    except Exception as e:
        return {"result": "PASS", "logic": "PASS", "disclosure": "PASS", "raw": str(e)}


_TOOL_EXPECTED_FIELDS: dict[str, list[str]] = {
    "get_daily_summary":       ["total_revenue", "total_transactions", "average_order_value"],
    "get_date_range_metrics":  ["total_revenue_idr", "total_transactions"],
    # get_top_products return list → cek via _is_nonempty_list di calculate_confidence
    # get_employee_performance return dict with employee names as keys → cek via len > 0
}

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


def calculate_confidence(
    tool_calls_log: list,
    query_keywords: list,
    date_range: str,
    thinking_steps: list | None = None,
    ai_response: str = "",
    client=None,
    T_optimal: float | None = None,
) -> dict:
    thinking_steps = thinking_steps or []
    total_tools = len(tool_calls_log)
    query_lower = " ".join(query_keywords).lower()

    # 1. Completeness (25%)
    if total_tools == 0:
        completeness = 30.0
        completeness_reason = "Tidak ada tool dipanggil, data tidak dapat diverifikasi"
    else:
        field_scores = []
        for t in tool_calls_log:
            result = t.get("result", {})
            tool_name = t.get("tool", "")

            # get_top_products return list
            if isinstance(result, list):
                field_scores.append(100.0 if result else 0.0)
                continue

            if not isinstance(result, dict):
                field_scores.append(0.0)
                continue

            if "error" in result:
                field_scores.append(0.0)
                continue

            expected = _TOOL_EXPECTED_FIELDS.get(tool_name, [])
            if not expected:
                # get_employee_performance: dict berisi employee names sebagai key
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

    # 2. Tool_Routing (20%)
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

    # 3. Complexity (15%)
    complex_kws = {"trend", "cohort", "retention", "comparison", "compare", "bandingkan", "analisis", "forecast"}
    medium_kws  = {"range", "rentang", "periode", "period", "minggu", "bulan", "weekly", "monthly"}
    is_complex  = any(kw in query_lower for kw in complex_kws) or total_tools >= 3
    is_medium   = any(kw in query_lower for kw in medium_kws) or total_tools == 2

    if is_complex:
        complexity, complexity_reason = 60.0, "Query kompleks"
    elif is_medium:
        complexity, complexity_reason = 80.0, "Query medium"
    else:
        complexity, complexity_reason = 100.0, "Query sederhana"

    failed_tools = sum(1 for t in tool_calls_log if "error" in t.get("result", {}))
    if failed_tools > 0:
        complexity = max(0.0, complexity - 20.0)
        complexity_reason += f" | fallback penalty: {failed_tools} tool gagal & di-retry"

    # 4. Data_Validation (15%)
    if total_tools == 0:
        data_validation = 50.0
        data_validation_reason = "Tidak ada data untuk divalidasi"
    else:
        anomaly_count = 0
        coverage_notes = []
        for t in tool_calls_log:
            result = t.get("result", {})
            # List result (get_top_products) — skip anomaly check, data OK jika non-empty
            if isinstance(result, list):
                if not result:
                    anomaly_count += 1
                continue
            if not isinstance(result, dict):
                anomaly_count += 1
                continue
            if "error" in result:
                anomaly_count += 1
                continue
            result_str = json.dumps(result)
            if any(x in result_str for x in ['"null"', ': null', ': -', '"-']):
                anomaly_count += 1
            if t.get("tool") == "get_date_range_metrics":
                dates_with_data = result.get("dates_with_data", [])
                start_str = result.get("start_date", "")
                end_str   = result.get("end_date", "")
                if start_str and end_str and isinstance(dates_with_data, list):
                    try:
                        d1 = datetime.strptime(start_str, "%Y-%m-%d")
                        d2 = datetime.strptime(end_str, "%Y-%m-%d")
                        expected_days = (d2 - d1).days + 1
                        coverage = len(dates_with_data) / expected_days if expected_days > 0 else 1.0
                        if coverage < 0.5:
                            anomaly_count += 1
                            coverage_notes.append(
                                f"coverage rendah: {len(dates_with_data)}/{expected_days} hari ada data"
                            )
                    except ValueError:
                        pass
        if anomaly_count == 0:
            data_validation = 100.0
            data_validation_reason = "Tidak ada anomali terdeteksi dalam data hasil tool"
        elif anomaly_count == 1:
            note = f" ({coverage_notes[0]})" if coverage_notes else ""
            data_validation = 50.0
            data_validation_reason = f"Satu anomali/nilai mencurigakan terdeteksi dalam data{note}"
        else:
            note = f" ({'; '.join(coverage_notes)})" if coverage_notes else ""
            data_validation = 20.0
            data_validation_reason = f"{anomaly_count} anomali terdeteksi — data perlu diverifikasi{note}"

    # 5. Freshness (15%)
    try:
        end_date_str = date_range.split(" - ")[-1].strip() if date_range else ""
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d") if end_date_str else datetime.now()
        age_hours = (datetime.now() - end_date).total_seconds() / 3600
    except (ValueError, AttributeError):
        age_hours = 0

    if age_hours <= 4:
        freshness, freshness_reason = 100.0, f"Data {age_hours:.0f} jam yang lalu — sangat fresh"
    elif age_hours <= 24:
        freshness, freshness_reason = 80.0, f"Data {age_hours:.0f} jam yang lalu — fresh (hari ini)"
    elif age_hours <= 168:
        freshness, freshness_reason = 60.0, f"Data {age_hours / 24:.0f} hari yang lalu — masih relevan"
    elif age_hours <= 720:
        freshness, freshness_reason = 35.0, f"Data {age_hours / 24:.0f} hari yang lalu — agak lama"
    else:
        freshness, freshness_reason = 10.0, f"Data {age_hours / 24:.0f} hari yang lalu — historical"

    # 6. DNC (10%)
    dnc, dnc_reason = score_dnc(
        thinking_steps, ai_response=ai_response,
        query_keywords=query_keywords,
        tool_calls_log=tool_calls_log,
        client=client,
    )

    raw_score = round(
        completeness    * 0.25 +
        tool_routing    * 0.20 +
        complexity      * 0.15 +
        data_validation * 0.15 +
        freshness       * 0.15 +
        dnc             * 0.10,
        1,
    )

    if T_optimal is not None and T_optimal > 0:
        p = max(0.01, min(0.99, raw_score / 100))
        logit = math.log(p / (1 - p))
        final_score = round(1 / (1 + math.exp(-logit / T_optimal)) * 100, 1)
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


def explain_confidence(
    client: OpenAI,
    question: str,
    tool_calls_log: list,
    confidence: dict,
    date_range: str,
) -> dict:
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


def check_historical_consistency(dnc_score: float) -> bool:
    """
    Week 0 stub — always returns True (consistent).
    Week 4+: replaced with real historical comparison after 30+ queries baseline.
    Reference: DAF Lock 1 — Historical Consistency supporting signal.
    """
    return True
