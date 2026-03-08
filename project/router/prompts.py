def build_system_prompt(store_id: str) -> str:
    return (
        f"Kamu adalah AI analyst untuk data POS Loyverse. "
        f"Store ID yang boleh diakses: {store_id}. "
        "Analisis pertanyaan user dan gunakan tools yang paling relevan secara mandiri. "
        "Jawab dalam Bahasa Indonesia, ringkas dan akurat. Sertakan angka spesifik dari data."
    )


def build_user_prompt(question: str, brand: str, store_id: str, date_range: str, **extra_ctx) -> str:
    """
    Template prompt user. Tambah context baru cukup lewat extra_ctx kwarg,
    tanpa perlu ubah engine.py.
    """
    lines = [
        f"Pertanyaan: {question}",
        f"Brand: {brand} | Store: {store_id}",
        f"Rentang tanggal: {date_range}",
    ]
    for key, val in extra_ctx.items():
        if val:
            lines.append(f"{key}: {val}")
    lines.append("")
    lines.append("Gunakan tools yang paling relevan untuk menjawab pertanyaan ini.")
    return "\n".join(lines)


def build_summary_comment(
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
        stage_icon  = {"understanding": "🔍", "reasoning": "⚙️", "inner_monologue": "💭"}
        stage_label = {"understanding": "Understand", "reasoning": "Reason", "inner_monologue": "Thought"}
        for step in thinking_steps:
            s = step.get("stage", "")
            parts.append(f"- {stage_icon.get(s, '•')} **{stage_label.get(s, s)}:** {step.get('message', '')}")
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
