import os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(_ROOT, "data")
CLICKUP_FILE = os.path.join(DATA_DIR, "clickup.json")
CLICKUP_BACKUP_FILE = os.path.join(DATA_DIR, "clickup.backup.json")

ESCALATION_THRESHOLD = 80
RESOLVED_THRESHOLD = 95
