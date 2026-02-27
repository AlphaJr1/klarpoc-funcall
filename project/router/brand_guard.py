from .config import BRAND_STORE_MAP


class BrandAccessError(Exception):
    pass


def get_store_id(brand_id: str) -> str:
    if brand_id not in BRAND_STORE_MAP:
        raise BrandAccessError(f"Brand '{brand_id}' tidak ditemukan dalam sistem.")
    return BRAND_STORE_MAP[brand_id]


def validate_brand_access(brand_id: str, store_id: str) -> bool:
    expected = get_store_id(brand_id)
    if expected != store_id:
        raise BrandAccessError(
            f"Akses ditolak: brand '{brand_id}' tidak memiliki akses ke store '{store_id}'."
        )
    return True
