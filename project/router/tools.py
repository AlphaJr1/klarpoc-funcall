import json
from . import loyverse_tools as lv
from clickup_sync.clickup_api import (
    get_project_status,
    get_overdue_tasks,
    get_tasks_by_assignee,
)


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
    {
        "type": "function",
        "function": {
            "name": "get_store_info",
            "description": "Ambil metadata toko: nama, brand, lokasi, currency, timezone.",
            "parameters": {
                "type": "object",
                "properties": {
                    "store_id": {"type": "string", "description": "ID toko Loyverse"},
                },
                "required": ["store_id"],
            },
        },
    },
    # ── State 3: ClickUp read tools ──────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "get_project_status",
            "description": (
                "Ambil status dan progress project management dari ClickUp. "
                "Gunakan untuk query tentang progress project, milestone, atau breakdown task per project."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "ClickUp list_id project. WAJIB gunakan Project ID yang sudah disediakan di context. Jangan gunakan 'all'.",
                    },
                },
                "required": ["project_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_overdue_tasks",
            "description": (
                "Ambil semua task yang overdue (melewati due date) dari ClickUp. "
                "Gunakan untuk query tentang task terlambat, deadline terlewat, atau backlog."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "ClickUp list_id project. WAJIB gunakan Project ID yang sudah disediakan di context. Jangan gunakan 'all'.",
                    },
                },
                "required": ["project_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_tasks_by_assignee",
            "description": (
                "Ambil semua task ClickUp yang di-assign ke satu orang tertentu. "
                "Gunakan untuk query tentang workload anggota tim, task seseorang minggu ini, dll."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "assignee": {"type": "string", "description": "Nama atau username assignee"},
                    "week": {
                        "type": "string",
                        "description": "Rentang minggu, misal '2026-03-03 to 2026-03-07' (opsional)",
                    },
                    "status_filter": {
                        "type": "string",
                        "description": "Filter status task, misal 'in progress', 'to do' (opsional)",
                    },
                },
                "required": ["assignee"],
            },
        },
    },
]

TOOL_REGISTRY = {
    "get_daily_summary": lv.get_daily_summary,
    "get_date_range_metrics": lv.get_date_range_metrics,
    "get_top_products": lv.get_top_products,
    "get_employee_performance": lv.get_employee_performance,
    "get_store_info": lv.get_store_info,
    # State 3 — ClickUp read tools
    "get_project_status": get_project_status,
    "get_overdue_tasks": get_overdue_tasks,
    "get_tasks_by_assignee": get_tasks_by_assignee,
}


def execute_tool(name: str, inputs: dict) -> str:
    fn = TOOL_REGISTRY.get(name)
    if not fn:
        return json.dumps({"error": f"Tool '{name}' tidak dikenal."})
    try:
        result = fn(**inputs)
        if not result and result != 0:
            return json.dumps({"error": "Data tidak ditemukan."})
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})

