# State Machine Router — ClickUp × Loyverse × Claude

POC sederhana yang menghubungkan ClickUp task dengan data Loyverse POS menggunakan Claude API sebagai otak routing-nya.

## Setup

```bash
cd project
pip install anthropic rich
export ANTHROPIC_API_KEY=sk-ant-...
```

## Cara Run

```bash
python main.py
```

Demo akan memproses 3 task dari `data/clickup.json`:

- `task_003` → Trend analysis (confidence rendah → eskalasi)
- `task_006` → Retention analysis
- `task_001` → Daily revenue (confidence tinggi → AI Direct Send)

## Struktur

| File                 | Peran                                  |
| -------------------- | -------------------------------------- |
| `main.py`            | Entry point & demo runner              |
| `router.py`          | State machine + Claude agentic loop    |
| `loyverse_tools.py`  | Simulasi Loyverse API dari JSON        |
| `clickup_tools.py`   | Simulasi ClickUp API (baca/tulis JSON) |
| `brand_guard.py`     | Validasi akses brand → store           |
| `config.py`          | Konstanta & mapping                    |
| `data/loyverse.json` | Sample data POS                        |
| `data/clickup.json`  | Sample tasks ClickUp                   |

## State Machine

```
Query → detect_state() → [SALES_REVENUE | PRODUCT_PERFORMANCE | TREND_ANALYSIS]
                              ↓
                    Claude API + tool_use
                              ↓
                    confidence score?
                    ≥80% → AI Direct Send
                    <80% → AM Review + create_escalation_task()
```
