import os
import yaml

# Brand mapping di-load langsung dari brands.yaml untuk hindari circular import
_BRANDS_PATH = os.path.join(os.path.dirname(__file__), "brands.yaml")
with open(_BRANDS_PATH) as _f:
    _BRANDS_DATA = yaml.safe_load(_f)["brands"]

BRAND_STORE_MAP = {bid: d["store_id"] for bid, d in _BRANDS_DATA.items()}
BRAND_PROJECT_MAP = {bid: d["project_id"] for bid, d in _BRANDS_DATA.items()}


ESCALATION_THRESHOLD = 80
RESOLVED_THRESHOLD = 95
MAX_LLM_ITERATIONS = 5

OLLAMA_MODEL = "minimax-m2.5:cloud"
SHADOW_CHECK_MODEL = "gpt-oss:120b"
OLLAMA_BASE_URL = "https://ollama.com"

# Mapping nama field ClickUp → internal key
# Ubah di sini jika nama field di ClickUp berubah, tanpa sentuh engine
TASK_FIELD_MAP = {
    "brand":      "Brand",
    "date_range": "Date Range",
    "priority":   "Priority",
    "resolution": "Resolution Status",
    "confidence": "AI Confidence Score",
}

# Path absolut relatif ke root project (parent dari folder ini)
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(_ROOT, "data")
LOYVERSE_FILE = os.path.join(DATA_DIR, "loyverse.json")
CLICKUP_FILE = os.path.join(DATA_DIR, "clickup.json")
CLICKUP_BACKUP_FILE = os.path.join(DATA_DIR, "clickup.backup.json")
