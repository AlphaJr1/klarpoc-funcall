import asyncio
from openai import OpenAI
from project.router.gates import gate0_check, extract_or_clarify
import os
from dotenv import load_dotenv

load_dotenv("project/.env")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

today = "2026-03-09"
q1 = "Berapa total revenue tanggal Feb 24?"

res = gate0_check(client, q1, today)
print("gate0_check:", res)

res2 = extract_or_clarify(client, q1, today)
print("extract_or_clarify:", res2)
