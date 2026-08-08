import json

PRODUCTS_SEED: list[dict] = [
    {
        "slug": "chicken_breast",
        "name_en": "Chicken Breast",
        "aliases_json": json.dumps({
            "flipp": ["poitrine de poulet", "poitrine poulet"],
        }),
    },
    {
        "slug": "picanha",
        "name_en": "Picanha (Top Sirloin Cap)",
        "aliases_json": json.dumps({
            "flipp": ["picanha", "culotte de surlonge", "top sirloin cap"],
        }),
    },
    {
        "slug": "filet_mignon",
        "name_en": "Filet Mignon",
        "aliases_json": json.dumps({
            "flipp": ["filet mignon boeuf", "filet de boeuf", "tenderloin boeuf"],
        }),
    },
]

STORES_SEED: list[dict] = [
    {
        "id": "flipp",
        "name": "Flipp (All Stores)",
        "base_url": "https://flipp.com",
        "scraper_type": "api",
        "active": True,
    },
]


def get_aliases(product_slug: str, store_id: str) -> list[str]:
    for p in PRODUCTS_SEED:
        if p["slug"] == product_slug:
            aliases = json.loads(p["aliases_json"])
            return aliases.get(store_id, [])
    return []


def get_product_name_en(slug: str) -> str:
    for p in PRODUCTS_SEED:
        if p["slug"] == slug:
            return p["name_en"]
    return slug
