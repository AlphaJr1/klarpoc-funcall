import requests
import datetime
from typing import List, Dict

LOY_TOKEN = "9cc64c142fdf4223ace454aa9f04c8f7"
LOY_HEADERS = {"Authorization": f"Bearer {LOY_TOKEN}", "Content-Type": "application/json"}
LOY_BASE = "https://api.loyverse.com/v1.0"

DUMMY_TO_REAL_STORE = {
    "store_001": "4774ea77-6b4c-4769-9959-1adca0cef4e3" # Klar store
}

EMPLOYEES_CACHE = {}

def get_employees(store_real_id: str) -> dict:
    if store_real_id in EMPLOYEES_CACHE:
        return EMPLOYEES_CACHE[store_real_id]
    try:
        r = requests.get(f"{LOY_BASE}/employees", headers=LOY_HEADERS, timeout=5)
        if r.status_code == 200:
            emps = r.json().get("employees", [])
            for e in emps:
                EMPLOYEES_CACHE[e["id"]] = e["name"]
    except:
        pass
    return EMPLOYEES_CACHE

def fetch_receipts(store_id: str, start_date: str, end_date: str) -> List[Dict]:
    real_store_id = DUMMY_TO_REAL_STORE.get(store_id)
    if not real_store_id:
        return []
        
    try:
        # Loyverse expects ISO 8601 YYYY-MM-DDTHH:MM:SS.000Z
        created_at_min = f"{start_date}T00:00:00.000Z"
        created_at_max = f"{end_date}T23:59:59.999Z"
        
        url = f"{LOY_BASE}/receipts?store_id={real_store_id}&created_at_min={created_at_min}&created_at_max={created_at_max}"
        r = requests.get(url, headers=LOY_HEADERS, timeout=5)
        if r.status_code == 200:
            return r.json().get("receipts", [])
    except Exception as e:
        print(f"API Error: {e}")
        pass
    return []
