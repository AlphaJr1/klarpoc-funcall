import json
import requests
import time
import os

LOY_TOKEN = "9cc64c142fdf4223ace454aa9f04c8f7"
LOY_HEADERS = {"Authorization": f"Bearer {LOY_TOKEN}", "Content-Type": "application/json"}
LOY_BASE = "https://api.loyverse.com/v1.0"
DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "loyverse.json")

def load_dummy():
    with open(DATA_FILE) as f:
        return json.load(f)

def cleanup_items(dummy_data):
    dummy_skus = {p["sku"] for p in dummy_data["products"]}
    print(f"[Items] Dummy SKUs: {dummy_skus}")
    
    resp = requests.get(f"{LOY_BASE}/items", headers=LOY_HEADERS)
    if resp.status_code != 200:
        print("Failed to fetch items")
        return
        
    items = resp.json().get("items", [])
    seen_skus = set()
    
    for item in items:
        variants = item.get("variants", [])
        if not variants:
            continue
        
        sku = variants[0].get("sku", "")
        if sku not in dummy_skus or sku in seen_skus:
            print(f"  ❌ Menghapus item '{item.get('item_name')}' (SKU: {sku}) ...")
            requests.delete(f"{LOY_BASE}/items/{item['id']}", headers=LOY_HEADERS)
            time.sleep(0.3)
        else:
            seen_skus.add(sku)
            print(f"  ✅ Keep item '{item.get('item_name')}' (SKU: {sku})")

def cleanup_employees(dummy_data):
    dummy_names = {e["employee_name"] for e in dummy_data["employees"]}
    print(f"\n[Employees] Dummy Names: {dummy_names}")
    
    resp = requests.get(f"{LOY_BASE}/employees", headers=LOY_HEADERS)
    if resp.status_code != 200:
        print("Failed to fetch employees")
        return
        
    employees = resp.json().get("employees", [])
    seen = set()
    
    for emp in employees:
        if emp.get("is_owner"):
            print(f"  👑 Keep owner '{emp.get('name')}'")
            continue
            
        name = emp.get("name", "")
        if name not in dummy_names or name in seen:
            print(f"  ❌ Menghapus employee '{name}' ...")
            requests.delete(f"{LOY_BASE}/employees/{emp['id']}", headers=LOY_HEADERS)
            time.sleep(0.3)
        else:
            seen.add(name)
            print(f"  ✅ Keep employee '{name}'")

if __name__ == "__main__":
    dummy = load_dummy()
    cleanup_items(dummy)
    cleanup_employees(dummy)
    print("\nSelesai membersihkan data di API Loyverse!")
