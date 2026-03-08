import os
import yaml
from openai import OpenAI
from .config import OLLAMA_MODEL

_BRANDS_PATH = os.path.join(os.path.dirname(__file__), "brands.yaml")

def _load_brands() -> dict:
    with open(_BRANDS_PATH, "r") as f:
        return yaml.safe_load(f)["brands"]

BRANDS = _load_brands()


def resolve_brand(query: str, client: OpenAI | None = None) -> dict | None:
    """
    Resolve brand dari query text.
    Fast path: alias match (case-insensitive).
    Slow path: Haiku fallback jika tidak ada alias yang cocok.
    Return: { brand_id, store_id, project_id } atau None jika uncertain.
    """
    q_lower = query.lower()

    # Fast path — alias match
    for brand_id, data in BRANDS.items():
        if brand_id.lower() in q_lower:
            return {"brand_id": brand_id, "store_id": data["store_id"], "project_id": data["project_id"]}
        for alias in data.get("aliases", []):
            if alias.lower() in q_lower:
                return {"brand_id": brand_id, "store_id": data["store_id"], "project_id": data["project_id"]}

    # Slow path — Haiku fallback
    if client is None:
        return None

    brand_list = "\n".join(
        f"- {bid}: aliases={', '.join(d.get('aliases', []))}"
        for bid, d in BRANDS.items()
    )
    prompt = (
        f"Which brand does this query refer to? Choose from the list below. "
        f"If unclear, return exactly: BRAND: uncertain\n\n"
        f"Brands:\n{brand_list}\n\n"
        f"Query: \"{query}\"\n\n"
        f"Respond only with: BRAND: [brand_id | uncertain]"
    )
    resp = client.chat.completions.create(
        model=OLLAMA_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=20,
    )
    text = (resp.choices[0].message.content or "").strip()
    brand_id = text.replace("BRAND:", "").strip()

    if brand_id == "uncertain" or brand_id not in BRANDS:
        return None

    data = BRANDS[brand_id]
    return {"brand_id": brand_id, "store_id": data["store_id"], "project_id": data["project_id"]}


def get_brand_info(brand_id: str) -> dict | None:
    """Ambil store_id + project_id dari brand_id."""
    data = BRANDS.get(brand_id)
    if not data:
        return None
    return {"brand_id": brand_id, "store_id": data["store_id"], "project_id": data["project_id"]}
