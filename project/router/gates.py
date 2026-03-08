import json
import os
import yaml
from datetime import datetime
from openai import OpenAI
from .config import OLLAMA_MODEL, BRAND_STORE_MAP

_STATES_PATH = os.path.join(os.path.dirname(__file__), "states.yaml")

def _load_states() -> dict:
    with open(_STATES_PATH) as f:
        return yaml.safe_load(f)["states"]


def extract_or_clarify(client: OpenAI, question: str, today: str) -> dict:
    """
    LLM single-pass:
    - Coba ekstrak brand + date dari query
    - Kalau berhasil → {"result": "EXTRACTED", "brand": ..., "date_range": ...}
    - Kalau tidak → {"result": "CLARIFY", "question": ..., "slots": [{"label": ..., "options": [...]}]}
      Options dibuat LLM secara konteks-aware, bukan dari hardcoded list.
    """
    brands_str = ", ".join(BRAND_STORE_MAP.keys())
    prompt = (
        "You are a context extraction assistant for a marketing data AI.\n"
        f"Today's date: {today}\n"
        f"Known brands in the system: {brands_str}\n"
        f"Query: {question}\n\n"
        "Task: Try to identify the brand and date range from the query.\n\n"
        "If BOTH can be determined with high confidence:\n"
        '  {"result": "EXTRACTED", "brand": "<exact brand name>", "date_range": "<YYYY-MM-DD or YYYY-MM-DD to YYYY-MM-DD>"}\n\n'
        "If one or more CANNOT be determined, generate a clarification with intelligent options:\n"
        '  {"result": "CLARIFY", "question": "<one concise question to the user>",\n'
        '   "slots": [\n'
        '     {"label": "<slot name, e.g. Brand or Date Range>",\n'
        '      "options": ["<option 1>", "<option 2>", "<option 3>"]}\n'
        '   ]}\n\n'
        "Rules:\n"
        "- For brand: suggest 2-4 options from known brands that are most likely given the query context. "
        "Add any brand name mentioned in the query as first option even if not in the known list.\n"
        "- For date: suggest 2-4 concrete absolute date options (YYYY-MM-DD) inferred from context "
        "(e.g. 'yesterday' = specific date, 'last week' = range). Include a 'Custom range' option if needed.\n"
        "- Do NOT hardcode or list all brands blindly. Be smart — only suggest what's contextually relevant.\n"
        "- Respond JSON only, no other text."
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
        start, end = text.find("{"), text.rfind("}") + 1
        data = json.loads(text[start:end]) if start >= 0 and end > start else {}

        if data.get("result") == "EXTRACTED":
            brand = data.get("brand") or ""
            date_range = data.get("date_range") or ""
            # Validasi brand ada di sistem
            if brand not in BRAND_STORE_MAP:
                brand = ""
            if brand and date_range:
                return {"result": "EXTRACTED", "brand": brand, "date_range": date_range}

        # Fallback ke CLARIFY
        return {
            "result": "CLARIFY",
            "question": data.get("question", "Mohon lengkapi informasi berikut:"),
            "slots": data.get("slots", []),
        }
    except Exception:
        return {
            "result": "CLARIFY",
            "question": "Sistem tidak dapat menentukan konteks query. Mohon lengkapi:",
            "slots": [],
        }




def gate0_check(client: OpenAI, question: str, today: str) -> dict:
    prompt = (
        "System: You are a query intent validator for a marketing data AI.\n\n"
        "Given the query and today's date, check for HARD contradictions only:\n"
        "- Date references that conflict with each other\n"
        "  (e.g., \"yesterday\" vs. an explicit date that does not match yesterday)\n"
        "- Explicit date ranges that are impossible\n"
        "  (e.g., a future date range when the data cannot exist yet)\n"
        "- Scope references that directly contradict each other\n\n"
        "Do NOT flag soft ambiguity or questions answerable with reasonable defaults.\n"
        "Only flag when the contradiction would produce two meaningfully different answers\n"
        "and there is no way to pick one without asking the user.\n\n"
        f"Today's date: {today}\n"
        f"Query: {question}\n\n"
        "If CLARIFY is needed, also provide 2-4 concrete options for the user to pick from.\n"
        "Respond in this exact format (JSON only, no other text):\n"
        '{\"result\": \"VALID\"}\n'
        "or\n"
        '{\"result\": \"CLARIFY\", \"contradiction\": \"<one sentence>\", '
        '\"clarification_question\": \"<short question to ask the user>\", '
        '\"options\": [\"<option 1>\", \"<option 2>\", \"<option 3 if needed>\"]}'
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
        start, end = text.find("{"), text.rfind("}") + 1
        data = json.loads(text[start:end]) if start >= 0 and end > start else {}
        if data.get("result", "").upper() == "CLARIFY":
            return {
                "result":   "CLARIFY",
                "message":  data.get("contradiction", "Query mengandung kontradiksi."),
                "question": data.get("clarification_question", "Mohon klarifikasi:"),
                "options":  data.get("options", []),
            }
        return {"result": "VALID", "message": "", "question": "", "options": []}
    except Exception as e:
        return {"result": "VALID", "message": f"Gate 0 error (fail-open): {e}", "question": "", "options": []}


def synthesize_query(client: OpenAI, original_query: str, clarification: str) -> str:
    prompt = (
        "You are a query refinement assistant for a marketing data AI.\n"
        "Given the original query (which may have ambiguity or contradiction) and "
        "the user's clarification answer, rewrite the query into a single, clear, "
        "unambiguous question that incorporates the clarification.\n\n"
        f"Original query: {original_query}\n"
        f"User clarification: {clarification}\n\n"
        "Return ONLY the refined query — one sentence, no explanation, no quotes."
    )
    try:
        resp = client.chat.completions.create(
            model=OLLAMA_MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        refined = resp.choices[0].message.content.strip().strip('"').strip("'")
        return refined if refined else f"{original_query} [{clarification}]"
    except Exception:
        return f"{original_query} [{clarification}]"


def intent_classify(client: OpenAI, question: str) -> dict:
    """
    Classification call — return { result, state, confidence, reasoning, skip_brand_isolation }.
    confidence < 0.7 atau state = unknown → result = CLARIFY.
    States dibaca dari states.yaml — tambah state baru tanpa ubah code ini.
    """
    states = _load_states()
    states_prompt = "\n".join(
        f"- {name}: {data['description'].strip()}"
        for name, data in states.items()
    )
    state_names = " | ".join(states.keys())

    prompt = (
        f"Classify this query into exactly one state.\n"
        f'Query: "{question}"\n\n'
        f"States:\n{states_prompt}\n\n"
        f'Return JSON: {{"state": "{state_names}", "confidence": 0.0-1.0, "reasoning": "one sentence"}}\n'
        'If confidence < 0.7, return {"state": "unknown", "confidence": ..., "reasoning": "..."}\n'
        "Respond JSON only, no other text."
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
        start, end = text.find("{"), text.rfind("}") + 1
        data = json.loads(text[start:end]) if start >= 0 and end > start else {}

        state = data.get("state", "unknown")
        confidence = float(data.get("confidence", 0.0))
        reasoning = data.get("reasoning", "")

        if state == "unknown" or confidence < 0.7 or state not in states:
            return {"result": "CLARIFY", "state": "unknown", "confidence": confidence, "reasoning": reasoning}

        skip_brand = states[state].get("skip_brand_isolation", False)
        return {
            "result": "CLASSIFIED",
            "state": state,
            "confidence": confidence,
            "reasoning": reasoning,
            "skip_brand_isolation": skip_brand,
        }
    except Exception as e:
        return {"result": "CLASSIFIED", "state": "State 1", "confidence": 0.5,
                "reasoning": f"fallback: {e}", "skip_brand_isolation": False}
