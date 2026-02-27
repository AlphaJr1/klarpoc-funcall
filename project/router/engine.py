import json
import os
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

TREND_KEYWORDS = ["trend", "comparison", "compare", "vs", "month", "bulanan", "bulan"]
PRODUCT_KEYWORDS = ["product", "produk", "top", "terlaris", "employee", "staff", "karyawan"]


def _detect_state(question: str) -> tuple[str, str]:
    q = question.lower()
    for k in TREND_KEYWORDS:
        if k in q:
            return "TREND_ANALYSIS", k
    for k in PRODUCT_KEYWORDS:
        if k in q:
            return "PRODUCT_PERFORMANCE", k
    return "SALES_REVENUE", "(default)"


def _execute_tool(name: str, inputs: dict) -> str:
    try:
        if name == "get_daily_summary":
            result = lv.get_daily_summary(**inputs)
        elif name == "get_date_range_metrics":
            result = lv.get_date_range_metrics(**inputs)
        elif name == "get_top_products":
            result = lv.get_top_products(**inputs)
        elif name == "get_employee_performance":
            result = lv.get_employee_performance(**inputs)
        else:
            return json.dumps({"error": f"Tool '{name}' tidak dikenal."})

        if not result:
            return json.dumps({"error": "Data tidak ditemukan untuk parameter yang diberikan."})
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})


def _make_client() -> OpenAI:
    return OpenAI(
        api_key=os.environ.get("OLLAMA_API_KEY", ""),
        base_url=f"{OLLAMA_BASE_URL}/v1",
    )


def _build_system_prompt(state: str, store_id: str) -> str:
    return (
        f"Kamu adalah AI analyst untuk data POS Loyverse. State aktif: {state}. "
        f"Store ID yang boleh diakses: {store_id}. "
        "Jawab dalam Bahasa Indonesia, ringkas dan akurat. "
        "Sertakan angka spesifik dari data. "
        "Di akhir jawaban, tambahkan baris: CONFIDENCE: <angka 60-99> "
        "berdasarkan kelengkapan data (lengkap=90-99, parsial=80-89, tidak cukup=60-79)."
    )


def route(task: dict) -> dict:
    question = task["task_name"]
    brand = task["custom_fields"].get("Brand", "")
    task_id = task["task_id"]
    date_range = task["custom_fields"].get("Date Range", "")

    try:
        store_id = get_store_id(brand)
    except BrandAccessError as e:
        return {
            "state": "ERROR",
            "ai_response": str(e),
            "confidence_score": 0,
            "resolution_status": "Escalated",
            "escalation_task": None,
            "tool_calls": [],
        }

    state, matched_keyword = _detect_state(question)
    user_content = (
        f"Pertanyaan: {question}\n"
        f"Brand: {brand} | Store: {store_id}\n"
        f"Rentang tanggal: {date_range}\n\n"
        "Gunakan tools yang tersedia untuk menjawab. "
        "Untuk TREND_ANALYSIS: coba get_date_range_metrics terlebih dahulu."
    )

    client = _make_client()
    messages = [
        {"role": "system", "content": _build_system_prompt(state, store_id)},
        {"role": "user", "content": user_content},
    ]
    tool_calls_log = []

    for _ in range(5):
        response = client.chat.completions.create(
            model=OLLAMA_MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
        )
        msg = response.choices[0].message
        finish_reason = response.choices[0].finish_reason

        if finish_reason == "stop" or not msg.tool_calls:
            messages.append({"role": "assistant", "content": msg.content or ""})
            break

        messages.append(msg)
        for tc in msg.tool_calls:
            try:
                inputs = json.loads(tc.function.arguments)
                result_str = _execute_tool(tc.function.name, inputs)
                tool_calls_log.append({
                    "tool": tc.function.name,
                    "input": inputs,
                    "result": json.loads(result_str),
                })
            except Exception as e:
                result_str = json.dumps({"error": str(e)})
                tool_calls_log.append({"tool": tc.function.name, "input": {}, "result": {"error": str(e)}})
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result_str})

    final_text = (
        messages[-1].get("content", "") if isinstance(messages[-1], dict)
        else (messages[-1].content or "")
    )

    confidence_score = 85
    clean_lines = []
    for line in final_text.strip().split("\n"):
        if line.strip().startswith("CONFIDENCE:"):
            try:
                confidence_score = int(line.split(":")[1].strip())
            except ValueError:
                pass
        else:
            clean_lines.append(line)

    ai_response = "\n".join(clean_lines).strip()
    resolution_status = "AI Direct Send" if confidence_score >= ESCALATION_THRESHOLD else "AM Review Required"

    cu.update_task(task_id, ai_response, confidence_score, resolution_status)

    tools_summary = ", ".join(
        f"{t['tool']}({list(t.get('input', {}).values())})" for t in tool_calls_log
    ) or "tidak ada tool dipanggil"
    confidence_breakdown = (
        "Data lengkap" if confidence_score >= RESOLVED_THRESHOLD
        else "Data parsial" if confidence_score >= ESCALATION_THRESHOLD
        else "Data tidak mencukupi / historical"
    )
    comment = (
        f"🤖 AI Agent Reasoning\n"
        f"State: {state}\n"
        f"Tools dipanggil: {tools_summary}\n"
        f"Confidence: {confidence_score}% — {confidence_breakdown}\n"
        f"Resolution: {resolution_status}"
    )
    try:
        cu.add_comment(task_id, comment)
    except Exception:
        pass

    escalation_task = None
    if confidence_score < ESCALATION_THRESHOLD:
        reason = (
            f"Confidence score {confidence_score}% di bawah threshold {ESCALATION_THRESHOLD}%. "
            "Data tidak mencukupi untuk analisis yang diminta."
        )
        escalation_task = cu.create_escalation_task(task_id, question, brand, reason)

    return {
        "state": state,
        "matched_keyword": matched_keyword,
        "ai_response": ai_response,
        "confidence_score": confidence_score,
        "resolution_status": resolution_status,
        "escalation_task": escalation_task,
        "tool_calls": tool_calls_log,
    }
