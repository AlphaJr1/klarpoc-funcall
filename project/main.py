import os
import sys
import shutil
from datetime import datetime, timezone
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
import clickup_tools as cu
import router
from config import CLICKUP_FILE, CLICKUP_BACKUP_FILE, ESCALATION_THRESHOLD, RESOLVED_THRESHOLD

load_dotenv()

console = Console()

DEMO_TASK_IDS = ["task_003", "task_006", "task_001"]
REPORTS_DIR = "reports"


def restore_clickup() -> None:
    if os.path.exists(CLICKUP_BACKUP_FILE):
        shutil.copy2(CLICKUP_BACKUP_FILE, CLICKUP_FILE)
        console.print("[dim]✓ clickup.json di-restore dari backup[/dim]\n")
    elif os.path.exists(CLICKUP_FILE):
        shutil.copy2(CLICKUP_FILE, CLICKUP_BACKUP_FILE)
        console.print("[dim]✓ Backup clickup.json dibuat[/dim]\n")
    else:
        console.print("[dim]⚠ File clickup.json dan backup tidak ditemukan[/dim]\n")


def print_phase1(result: dict) -> None:
    state_color = {
        "TREND_ANALYSIS": "yellow",
        "PRODUCT_PERFORMANCE": "cyan",
        "SALES_REVENUE": "green",
        "ERROR": "red",
    }.get(result["state"], "white")

    tools_used = ", ".join(t["tool"] for t in result.get("tool_calls", [])) or "—"
    console.print(f"  [bold]State:[/bold] [{state_color}]{result['state']}[/{state_color}]")
    console.print(f"  [bold]Tools dipanggil:[/bold] {tools_used}")


def print_phase2(task_id: str, result: dict) -> None:
    score = result["confidence_score"]
    score_color = "green" if score >= 95 else "yellow" if score >= 80 else "red"

    lifecycle = "resolved" if score >= 95 else "escalated" if score < 80 else "in_review"
    lifecycle_color = "green" if lifecycle == "resolved" else "red" if lifecycle == "escalated" else "yellow"

    console.print(f"  [bold]Confidence:[/bold] [{score_color}]{score}%[/{score_color}]")
    console.print(f"  [bold]Task Status:[/bold] [{lifecycle_color}]{lifecycle}[/{lifecycle_color}]")
    console.print(f"  [bold]update_task({task_id}, ...):[/bold] [green]✓[/green]")
    console.print(f"  [bold]add_comment():[/bold] [green]✓ reasoning breakdown[/green]")

    if result["escalation_task"]:
        esc_id = result["escalation_task"]["task_id"]
        console.print(f"  [bold]create_escalation_task():[/bold] [yellow]✓ ({esc_id})[/yellow]")


def _lifecycle_label(score: int) -> str:
    if score >= RESOLVED_THRESHOLD:
        return "resolved"
    elif score < ESCALATION_THRESHOLD:
        return "escalated"
    return "in_review"


def _build_report(run_ts: str, task_results: list[dict]) -> str:
    lines = [
        "# State Machine Router — Demo Report",
        f"> **Run:** {run_ts}  ",
        f"> **Model:** MiniMax-M2.5 via Ollama Cloud  ",
        f"> **Threshold:** escalate < {ESCALATION_THRESHOLD}% | resolve ≥ {RESOLVED_THRESHOLD}%",
        "",
        "---",
        "",
        "## Ringkasan",
        "",
        "| Task ID | Query | State | Confidence | Status | Eskalasi |",
        "|---------|-------|-------|-----------|--------|---------|",
    ]

    for r in task_results:
        esc = "✅" if r["result"].get("escalation_task") else "—"
        score = r["result"]["confidence_score"]
        lifecycle = _lifecycle_label(score)
        lines.append(
            f"| {r['task_id']} | {r['task_name'][:50]} | {r['result']['state']} "
            f"| {score}% | {lifecycle} | {esc} |"
        )

    lines += ["", "---", ""]

    for r in task_results:
        result = r["result"]
        score = result["confidence_score"]
        lifecycle = _lifecycle_label(score)
        tools_used = ", ".join(f"`{t['tool']}`" for t in result.get("tool_calls", [])) or "—"

        esc_section = ""
        if result.get("escalation_task"):
            et = result["escalation_task"]
            esc_section = (
                f"\n**Escalation Task dibuat:** `{et['task_id']}`  \n"
                f"Assigned to: `{et.get('assigned_to', 'AM Review')}`  \n"
                f"Priority: `{et['custom_fields'].get('Priority', 'Urgent')}`\n"
            )

        lines += [
            f"## TASK `{r['task_id']}`",
            "",
            f"**Query:** {r['task_name']}  ",
            f"**Brand:** {r['brand']} | **Date Range:** {r['date_range']}",
            "",
            "### Phase 1 — Route & Execute",
            f"- **State:** `{result['state']}`",
            f"- **Tools dipanggil:** {tools_used}",
            "",
            "### Phase 2 — Update ClickUp",
            f"- **Confidence Score:** {score}%",
            f"- **Task Lifecycle Status:** `{lifecycle}`",
            f"- **Resolution Status:** {result['resolution_status']}",
            "- `update_task()` ✓",
            "- `add_comment()` ✓ _(reasoning breakdown tersimpan di task)_",
        ]

        if esc_section:
            lines.append(esc_section)

        lines += [
            "",
            "### AI Response",
            "",
            f"```\n{result['ai_response']}\n```",
            "",
            "---",
            "",
        ]

    return "\n".join(lines)


def run_demo() -> list[dict]:
    console.print(Panel.fit(
        "[bold magenta]State Machine Router[/bold magenta]\n"
        "[dim]ClickUp × Loyverse × MiniMax-M2.5 via Ollama Cloud[/dim]",
        border_style="magenta",
    ))

    restore_clickup()

    all_open = {t["task_id"]: t for t in cu.get_open_tasks()}
    task_results = []

    for task_id in DEMO_TASK_IDS:
        task = all_open.get(task_id)
        if not task:
            console.print(f"\n[dim]Task {task_id} tidak ditemukan / sudah closed, skip.[/dim]")
            continue

        console.rule(f"[bold blue]TASK {task_id}[/bold blue]")
        console.print(f"[bold]Query:[/bold] {task['task_name']}")
        console.print(
            f"[bold]Brand:[/bold] {task['custom_fields'].get('Brand')} | "
            f"[bold]Date Range:[/bold] {task['custom_fields'].get('Date Range')}"
        )

        console.print("\n[bold underline]Phase 1 — Route & Execute[/bold underline]")
        with console.status("[dim]Memanggil Ollama Cloud (minimax-m2.5)...[/dim]"):
            result = router.route(task)

        print_phase1(result)

        console.print("\n[bold underline]Phase 2 — Update ClickUp[/bold underline]")
        print_phase2(task_id, result)

        status_color = "green" if result["resolution_status"] == "AI Direct Send" else "yellow"
        console.print(f"\n  [bold]Status Akhir:[/bold] [{status_color}]{result['resolution_status']}[/{status_color}]")

        console.print("\n[bold]AI Response:[/bold]")
        console.print(Panel(result["ai_response"] or "(kosong)", border_style="dim", padding=(0, 1)))

        task_results.append({
            "task_id": task_id,
            "task_name": task["task_name"],
            "brand": task["custom_fields"].get("Brand", ""),
            "date_range": task["custom_fields"].get("Date Range", ""),
            "result": result,
        })

    console.print(Panel.fit("[bold green]Demo selesai.[/bold green]", border_style="green"))
    return task_results


def save_report(task_results: list[dict]) -> str:
    os.makedirs(REPORTS_DIR, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    path = os.path.join(REPORTS_DIR, f"report_{ts}.md")
    content = _build_report(run_ts, task_results)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


if __name__ == "__main__":
    if not os.environ.get("OLLAMA_API_KEY"):
        console.print("[red]Error: OLLAMA_API_KEY tidak ditemukan di environment.[/red]")
        console.print("[dim]Set dengan: export OLLAMA_API_KEY=<your-key>[/dim]")
        sys.exit(1)

    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    results = run_demo()
    report_path = save_report(results)
    console.print(f"\n[dim]📄 Report tersimpan: {report_path}[/dim]")
