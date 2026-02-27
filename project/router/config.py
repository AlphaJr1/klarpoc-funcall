import os

BRAND_STORE_MAP = {
    "Kopi_Brand_A": "store_001",
    "Fashion_Brand_B": "store_002",
    "Electronics_Brand_C": "store_003",
}

ESCALATION_THRESHOLD = 80
RESOLVED_THRESHOLD = 95

OLLAMA_MODEL = "minimax-m2.5:cloud"
OLLAMA_BASE_URL = "https://ollama.com"

# Path absolut relatif ke root project (parent dari folder ini)
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(_ROOT, "data")
LOYVERSE_FILE = os.path.join(DATA_DIR, "loyverse.json")
CLICKUP_FILE = os.path.join(DATA_DIR, "clickup.json")
CLICKUP_BACKUP_FILE = os.path.join(DATA_DIR, "clickup.backup.json")
