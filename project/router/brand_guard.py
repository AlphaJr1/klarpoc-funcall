from .brand_resolution import resolve_brand, get_brand_info, BRANDS


class BrandAccessError(Exception):
    pass


def get_store_id(brand_id: str) -> str:
    info = get_brand_info(brand_id)
    if not info:
        raise BrandAccessError(f"Brand '{brand_id}' tidak ditemukan dalam sistem.")
    return info["store_id"]


def get_project_id(brand_id: str) -> str:
    info = get_brand_info(brand_id)
    if not info:
        raise BrandAccessError(f"Brand '{brand_id}' tidak ditemukan dalam sistem.")
    return info["project_id"]
