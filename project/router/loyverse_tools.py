import json
from collections import defaultdict
from .config import LOYVERSE_FILE


def _load() -> dict:
    with open(LOYVERSE_FILE) as f:
        return json.load(f)


def get_daily_summary(store_id: str, date: str) -> dict | None:
    data = _load()
    for s in data.get("daily_summary", []):
        if s["store_id"] == store_id and s["date"] == date:
            return s
    return None


def get_date_range_metrics(store_id: str, start_date: str, end_date: str) -> dict:
    data = _load()
    txns = [
        t for t in data.get("transactions", [])
        if t["store_id"] == store_id and start_date <= t["date"] <= end_date
    ]
    if not txns:
        return {}

    total_revenue = sum(t["total_idr"] for t in txns)
    total_transactions = len(txns)
    total_items = sum(sum(item["qty"] for item in t["items"]) for t in txns)
    dates_covered = sorted({t["date"] for t in txns})

    return {
        "store_id": store_id,
        "start_date": start_date,
        "end_date": end_date,
        "dates_with_data": dates_covered,
        "total_transactions": total_transactions,
        "total_revenue_idr": total_revenue,
        "total_items_sold": total_items,
        "avg_transaction_value_idr": total_revenue // total_transactions,
    }


def get_top_products(store_id: str, date: str, limit: int = 5) -> list[dict]:
    data = _load()
    txns = [
        t for t in data.get("transactions", [])
        if t["store_id"] == store_id and t["date"] == date
    ]
    product_totals: dict[str, dict] = defaultdict(lambda: {"qty": 0, "subtotal_idr": 0})
    for t in txns:
        for item in t["items"]:
            name = item["product_name"]
            product_totals[name]["qty"] += item["qty"]
            product_totals[name]["subtotal_idr"] += item["subtotal_idr"]

    return sorted(
        [{"product_name": k, **v} for k, v in product_totals.items()],
        key=lambda x: x["subtotal_idr"],
        reverse=True,
    )[:limit]


def get_employee_performance(store_id: str, date: str) -> dict:
    data = _load()
    txns = [
        t for t in data.get("transactions", [])
        if t["store_id"] == store_id and t["date"] == date
    ]
    emp_map = {e["employee_id"]: e["employee_name"] for e in data.get("employees", [])}
    perf: dict[str, dict] = defaultdict(lambda: {"transactions": 0, "total_revenue": 0})
    for t in txns:
        emp_name = emp_map.get(t["employee_id"], t["employee_id"])
        perf[emp_name]["transactions"] += 1
        perf[emp_name]["total_revenue"] += t["total_idr"]
    return dict(perf)
