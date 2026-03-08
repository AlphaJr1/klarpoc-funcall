import json
from collections import defaultdict
from .config import LOYVERSE_FILE
from .loyverse_api_hub import fetch_receipts, get_employees


def _load() -> dict:
    with open(LOYVERSE_FILE) as f:
        return json.load(f)


def get_daily_summary(store_id: str, date: str) -> dict | None:
    # Coba via API dulu
    receipts = fetch_receipts(store_id, date, date)
    if receipts:
        # Kalkulasi daily summary sederhana dari receipt API
        total_revenue = sum(r.get("total_money", 0) for r in receipts)
        total_items = sum(sum(item.get("quantity", 0) for item in r.get("line_items", [])) for r in receipts)
        
        # Cari top product
        product_totals = defaultdict(int)
        for r in receipts:
            for item in r.get("line_items", []):
                product_totals[item.get("item_name", "Unknown")] += item.get("quantity", 0)
        def _get_val(k: str) -> int:
            return product_totals[k]
        top_product = max(product_totals, key=_get_val) if product_totals else None
        
        return {
            "_data_source": "Loyverse API v1.0",
            "store_id": "store_001 (API: Klar)", 
            "date": date,
            "total_transactions": len(receipts),
            "total_revenue_idr": total_revenue,
            "total_items_sold": total_items,
            "top_product": top_product,
            "avg_transaction_value_idr": total_revenue // len(receipts) if receipts else 0
        }

    # Fallback ke Dummy
    data = _load()
    for s in data.get("daily_summary", []):
        if s["store_id"] == store_id and s["date"] == date:
            s["_data_source"] = "Local Dummy Database"
            return s
            
    return None


def get_date_range_metrics(store_id: str, start_date: str, end_date: str) -> dict:
    receipts = fetch_receipts(store_id, start_date, end_date)
    if receipts:
        total_revenue = sum(r.get("total_money", 0) for r in receipts)
        total_items = sum(sum(item.get("quantity", 0) for item in r.get("line_items", [])) for r in receipts)
        
        dates_covered = sorted(list(set(r.get("receipt_date", "").split("T")[0] for r in receipts if r.get("receipt_date"))))

        return {
            "_data_source": "Loyverse API v1.0",
            "store_id": "store_001 (API: Klar)",
            "start_date": start_date,
            "end_date": end_date,
            "dates_with_data": dates_covered,
            "total_transactions": len(receipts),
            "total_revenue_idr": total_revenue,
            "total_items_sold": total_items,
            "avg_transaction_value_idr": total_revenue // len(receipts) if receipts else 0,
        }

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
        "_data_source": "Local Dummy Database",
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
    receipts = fetch_receipts(store_id, date, date)
    if receipts:
        product_totals = defaultdict(lambda: {"qty": 0, "subtotal_idr": 0})
        for r in receipts:
            for item in r.get("line_items", []):
                name = item.get("item_name", "Unknown")
                product_totals[name]["qty"] += item.get("quantity", 0)
                product_totals[name]["subtotal_idr"] += item.get("total_money", 0)
                
        results = sorted(
            [{"product_name": k, "qty": v["qty"], "subtotal_idr": v["subtotal_idr"], "_data_source": "Loyverse API v1.0"} for k, v in product_totals.items()],
            key=lambda x: int(x["subtotal_idr"]),
            reverse=True,
        )
        return results[:limit]

    data = _load()
    txns = [
        t for t in data.get("transactions", [])
        if t["store_id"] == store_id and t["date"] == date
    ]
    product_totals_dummy = defaultdict(lambda: {"qty": 0, "subtotal_idr": 0})
    for t in txns:
        for item in t["items"]:
            name = str(item["product_name"])
            product_totals_dummy[name]["qty"] += item["qty"]
            product_totals_dummy[name]["subtotal_idr"] += item["subtotal_idr"]

    results_dummy = sorted(
        [{"product_name": k, "qty": v["qty"], "subtotal_idr": v["subtotal_idr"], "_data_source": "Local Dummy Database"} for k, v in product_totals_dummy.items()],
        key=lambda x: int(x["subtotal_idr"]),
        reverse=True,
    )
    return results_dummy[:limit]


def get_employee_performance(store_id: str, date: str) -> dict:
    receipts = fetch_receipts(store_id, date, date)
    if receipts:
        # Load real employees cached
        get_employees("")
        from .loyverse_api_hub import EMPLOYEES_CACHE
        perf = defaultdict(lambda: {"transactions": 0, "total_revenue": 0})
        for r in receipts:
            emp_id = r.get("employee_id")
            emp_name = EMPLOYEES_CACHE.get(emp_id, emp_id or "Unknown")
            perf[emp_name]["transactions"] += 1
            perf[emp_name]["total_revenue"] += r.get("total_money", 0)
        
        from typing import Any
        res: dict[str, Any] = {k: dict(v) for k, v in perf.items()}
        res["_data_source"] = "Loyverse API v1.0"
        return res
        
    data = _load()
    txns = [
        t for t in data.get("transactions", [])
        if t["store_id"] == store_id and t["date"] == date
    ]
    emp_map = {e["employee_id"]: e["employee_name"] for e in data.get("employees", [])}
    perf_dummy = defaultdict(lambda: {"transactions": 0, "total_revenue": 0})
    for t in txns:
        emp_name = str(emp_map.get(t["employee_id"], t["employee_id"]))
        perf_dummy[emp_name]["transactions"] += 1
        perf_dummy[emp_name]["total_revenue"] += t["total_idr"]
    
    from typing import Any
    res_dummy: dict[str, Any] = {k: dict(v) for k, v in perf_dummy.items()}
    res_dummy["_data_source"] = "Local Dummy Database"
    return res_dummy


def get_store_info(store_id: str) -> dict | None:
    data = _load()
    for store in data.get("stores", []):
        if store["store_id"] == store_id:
            return {**store, "_data_source": "Local Dummy Database"}
    return None
