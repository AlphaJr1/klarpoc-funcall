"""
Seed script: push dummy data ke Loyverse (items, employees) dan ClickUp (tasks).
Transactions di Loyverse tidak bisa dibuat via API, tetap di local JSON.

Usage: python scripts/seed_data.py
"""

import json
import requests
import time

# ── Config ──────────────────────────────────────────────────────────────────
LOYVERSE_TOKEN = "9cc64c142fdf4223ace454aa9f04c8f7"
CLICKUP_TOKEN  = "pk_306761696_OM5LL6Q79XPWXYBWL58T3DCMYOPA39R3"

LOY_BASE   = "https://api.loyverse.com/v1.0"
CUP_BASE   = "https://api.clickup.com/api/v2"

# Store "Klar" yang sudah ada di Loyverse real
KLAR_STORE_ID = "4774ea77-6b4c-4769-9959-1adca0cef4e3"

# ClickUp: Team Space (Test's Workspace)
CUP_SPACE_ID   = "901810076825"
CUP_WORKSPACE  = "90182504118"

LOY_HEADERS = {"Authorization": f"Bearer {LOYVERSE_TOKEN}", "Content-Type": "application/json"}
CUP_HEADERS = {"Authorization": CLICKUP_TOKEN, "Content-Type": "application/json"}

DATA_DIR = "data"

# ── Helpers ──────────────────────────────────────────────────────────────────
def log(msg): print(f"  {msg}")
def ok(msg):  print(f"  ✅ {msg}")
def err(msg): print(f"  ❌ {msg}")


# ── 1. Loyverse: Create Categories ───────────────────────────────────────────
def ensure_categories():
    """Map kategori dummy → category_id real Loyverse."""
    print("\n[Loyverse] Cek/buat categories...")

    # Kategori yang sudah ada
    resp = requests.get(f"{LOY_BASE}/categories", headers=LOY_HEADERS)
    existing = {c["name"].lower(): c["id"] for c in resp.json().get("categories", [])}

    needed = {
        "Beverages":   "GREY",
        "Apparel":     "BLUE",
        "Main Course": "RED",
        "Beverage":    "GREEN",
    }

    cat_map = {}
    for name, color in needed.items():
        key = name.lower()
        if key in existing:
            cat_map[name] = existing[key]
            log(f"Category '{name}' sudah ada → {existing[key]}")
        else:
            r = requests.post(f"{LOY_BASE}/categories",
                              headers=LOY_HEADERS,
                              json={"name": name, "color": color})
            if r.status_code in (200, 201):
                cid = r.json()["id"]
                cat_map[name] = cid
                ok(f"Category '{name}' dibuat → {cid}")
            else:
                err(f"Gagal buat category '{name}': {r.text}")
        time.sleep(0.3)

    return cat_map


# ── 2. Loyverse: Create Items (Products) ─────────────────────────────────────
def seed_items(cat_map):
    print("\n[Loyverse] Push items/products...")

    with open(f"{DATA_DIR}/loyverse.json") as f:
        data = json.load(f)

    id_map = {}  # product_id dummy → item_id real

    for p in data["products"]:
        payload = {
            "item_name": p["product_name"],
            "description": f"SKU: {p['sku']} | Barcode: {p['barcode']}",
            "category_id": cat_map.get(p["category"]),
            "variants": [{
                "sku":     p["sku"],
                "barcode": p["barcode"],
                "price":   p["price_idr"],
                "cost":    p["cost_idr"],
                "stores": [{
                    "store_id":           KLAR_STORE_ID,
                    "available_for_sale": True,
                }]
            }]
        }

        r = requests.post(f"{LOY_BASE}/items", headers=LOY_HEADERS, json=payload)
        if r.status_code in (200, 201):
            real_id = r.json()["id"]
            id_map[p["product_id"]] = real_id
            ok(f"Item '{p['product_name']}' → {real_id}")
        else:
            err(f"Gagal '{p['product_name']}': {r.text[:120]}")
        time.sleep(0.4)

    return id_map


# ── 3. Loyverse: Create Employees ─────────────────────────────────────────────
def seed_employees():
    print("\n[Loyverse] Push employees...")

    with open(f"{DATA_DIR}/loyverse.json") as f:
        data = json.load(f)

    for i, e in enumerate(data["employees"]):
        payload = {
            "name":         e["employee_name"],
            "email":        e["email"].replace("@loyverse.test", "@example.com"),
            "phone_number": e.get("phone"),
            "pin":          str(1000 + i),  # PIN unik per employee
            "stores":       [{"store_id": KLAR_STORE_ID, "role": "CASHIER"}],
        }
        r = requests.post(f"{LOY_BASE}/employees", headers=LOY_HEADERS, json=payload)
        if r.status_code in (200, 201):
            ok(f"Employee '{e['employee_name']}' → {r.json()['id']}")
        else:
            err(f"Gagal '{e['employee_name']}': {r.text[:120]}")
        time.sleep(0.4)


# ── 4. ClickUp: Ensure Lists ──────────────────────────────────────────────────
def ensure_clickup_lists():
    print("\n[ClickUp] Buat lists 'Campaign Queries' & 'Client Follow-ups'...")

    r = requests.get(f"{CUP_BASE}/space/{CUP_SPACE_ID}/list", headers=CUP_HEADERS)
    existing = {l["name"]: l["id"] for l in r.json().get("lists", [])}

    list_map = {}
    needed = ["Campaign Queries", "Client Follow-ups"]
    for name in needed:
        if name in existing:
            list_map[name] = existing[name]
            log(f"List '{name}' sudah ada → {existing[name]}")
        else:
            r2 = requests.post(f"{CUP_BASE}/space/{CUP_SPACE_ID}/list",
                               headers=CUP_HEADERS,
                               json={"name": name})
            if r2.status_code in (200, 201):
                lid = r2.json()["id"]
                list_map[name] = lid
                ok(f"List '{name}' dibuat → {lid}")
            else:
                err(f"Gagal buat list '{name}': {r2.text[:120]}")
        time.sleep(0.3)

    return list_map


# ── 5. ClickUp: Push Tasks ────────────────────────────────────────────────────
def seed_clickup_tasks(list_map):
    print("\n[ClickUp] Push tasks...")

    with open(f"{DATA_DIR}/clickup.json") as f:
        data = json.load(f)

    # Map list_id dummy → list_id real
    lid_map = {
        "list_001": list_map.get("Campaign Queries"),
        "list_002": list_map.get("Client Follow-ups"),
    }

    priority_map = {"Low": 4, "Medium": 3, "High": 2, "Urgent": 1}

    pushed = 0
    for task in data["tasks"]:
        # Skip eskalasi tasks (biarkan dibuat otomatis oleh engine)
        if task["task_id"].startswith("esc_"):
            continue

        list_id = lid_map.get(task["list_id"])
        if not list_id:
            err(f"List tidak ditemukan untuk task {task['task_id']}")
            continue

        cf = task.get("custom_fields", {})
        priority_label = cf.get("Priority", "Medium")
        priority_val   = priority_map.get(priority_label, 3)

        status_map = {"open": "to do", "escalated": "in progress", "closed": "complete"}
        payload = {
            "name":        task["task_name"],
            "description": task.get("description", ""),
            "status":      status_map.get(task.get("status", "open"), "to do"),
            "priority":    priority_val,
        }

        # due_date jika ada (ClickUp pakai milliseconds)
        if task.get("date_due"):
            from datetime import datetime, timezone
            try:
                dt = datetime.fromisoformat(task["date_due"].replace("Z", "+00:00"))
                payload["due_date"] = int(dt.timestamp() * 1000)
            except Exception:
                pass

        r = requests.post(f"{CUP_BASE}/list/{list_id}/task",
                          headers=CUP_HEADERS,
                          json=payload)
        if r.status_code in (200, 201):
            tid = r.json()["id"]
            ok(f"Task '{task['task_id']}' → ClickUp ID {tid}: {task['task_name'][:50]}")
            pushed += 1
        else:
            err(f"Gagal task '{task['task_id']}': {r.text[:120]}")
        time.sleep(0.4)

    print(f"\n  Total tasks pushed: {pushed}")


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("SEED DATA: Loyverse (hybrid) + ClickUp (full)")
    print("=" * 60)

    # Loyverse
    cat_map = ensure_categories()
    seed_items(cat_map)
    seed_employees()

    # ClickUp
    list_map = ensure_clickup_lists()
    seed_clickup_tasks(list_map)

    print("\n" + "=" * 60)
    print("SELESAI. Transaksi/receipts Loyverse tetap di local JSON")
    print("(tidak bisa dibuat via API — hanya bisa via Loyverse POS app)")
    print("=" * 60)
