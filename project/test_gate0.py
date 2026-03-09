import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from router.llm import get_llm_client
from router.gates import gate0_check, extract_or_clarify

client = get_llm_client()

today = "2026-03-09"
q1 = "Berapa total revenue tanggal Feb 24 untuk klar?"

try:
    res = gate0_check(client, q1, today)
    print("gate0_check:", res)
except Exception as e:
    print("Error gate0_check:", e)

try:
    res2 = extract_or_clarify(client, q1, today)
    print("extract_or_clarify:", res2)
except Exception as e:
    print("Error extract_or_clarify:", e)
