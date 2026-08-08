"""
Flipp Scraper via the public backflipp.wishabi.com API.

Aggregates flyers from ALL stores in a single HTTP call.
No auth, no known rate-limit, clean JSON response.
"""

import logging
import re

import aiohttp

from src.config import TIMEOUT_SECONDS
from src.models import Price
from src.scrapers.base import AbstractScraper

logger = logging.getLogger(__name__)

FLIPP_API = "https://backflipp.wishabi.com/flipp/items/search"
LOCALE = "fr-ca"
POSTAL_CODE = "H2T1S8"

# Target store names to filter results
TARGET_MERCHANTS = [
    "maxi", "super c", "metro", "iga", "walmart", "costco",
    "mayrand", "adonis", "provigo", "supermarche",
]

# French search terms for Quebec Flipp flyers
SEARCH_TERMS: dict[str, list[str]] = {
    "chicken_breast": [
        "poitrine de poulet",
        "poitrine poulet",
    ],
    "picanha": [
        "picanha",
        "culotte de surlonge",
        "top sirloin cap",
    ],
    "filet_mignon": [
        "filet mignon boeuf",
        "filet de boeuf",
        "tenderloin boeuf",
    ],
}


class FlippScraper(AbstractScraper):
    store_id = "flipp"
    store_name = "Flipp (All Stores)"

    async def search_product(self, product_slug: str, search_terms: list[str]) -> list[Price]:
        results: list[Price] = []

        async with aiohttp.ClientSession() as session:
            for term in search_terms[:3]:
                prices = await self._search_term(session, product_slug, term)
                results.extend(prices)

        # Deduplicate by (store, product, price)
        seen = set()
        unique: list[Price] = []
        for p in sorted(results, key=lambda x: x.unit_price or x.price_cad):
            key = (p.store_id, p.product_name, p.price_cad)
            if key not in seen:
                seen.add(key)
                unique.append(p)

        return unique[:20]

    async def _search_term(
        self, session: aiohttp.ClientSession, product_slug: str, term: str
    ) -> list[Price]:
        results: list[Price] = []
        params = {
            "locale": LOCALE,
            "postal_code": POSTAL_CODE,
            "q": term,
        }

        try:
            async with session.get(
                FLIPP_API,
                params=params,
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=aiohttp.ClientTimeout(total=TIMEOUT_SECONDS),
            ) as resp:
                if resp.status != 200:
                    logger.warning("Flipp API returned %s for '%s'", resp.status, term)
                    return []
                data = await resp.json()
        except Exception as e:
            logger.error("Flipp API error for '%s': %s", term, e)
            return []

        items = data.get("items", [])
        for item in items:
            price_info = _parse_flipp_item(item, product_slug)
            if price_info:
                results.append(price_info)

        return results


def _parse_flipp_item(item: dict, product_slug: str) -> Price | None:
    name = item.get("name", "")
    if not name:
        return None

    merchant = item.get("merchant_name", "Inconnu")

    # Extract price
    price_str = item.get("current_price")
    price_cad: float | None = None

    if price_str is not None and str(price_str).strip():
        try:
            price_cad = float(str(price_str).replace(",", ".").strip())
        except (ValueError, TypeError):
            pass

    # If no numeric price, try the sale_story text
    sale_story = item.get("sale_story", "")
    if price_cad is None and sale_story:
        # Ex: "2 pour 10$", "5$ chaque"
        match = re.search(r'(\d+\.?\d*)\s*\$', sale_story)
        if match:
            price_cad = float(match.group(1))

    if price_cad is None or price_cad <= 0:
        return None

    # Unit price
    post_text = (item.get("post_price_text") or "").lower()
    pre_text = (item.get("pre_price_text") or "").lower()
    unit_price = _parse_unit_price(price_cad, post_text, name)

    # Detecta promocao
    is_on_sale = True  # Flipp so mostra itens em promocao (flyer)
    original_price_str = item.get("original_price")
    original_price = None
    if original_price_str and str(original_price_str).strip():
        try:
            original_price = float(str(original_price_str).replace(",", "."))
        except (ValueError, TypeError):
            pass

    # Datas
    valid_from = str(item.get("valid_from", ""))[:10]
    valid_to = str(item.get("valid_to", ""))[:10]

    # Size extracted from product name (e.g. "CHICKEN BREAST, 3 un.")
    package_size = _extract_size(name)

    # URL do flyer
    flyer_id = item.get("flyer_id", "")

    return Price(
        product_slug=product_slug,
        store_id=merchant.lower().replace(" ", "_"),
        price_cad=price_cad,
        unit_price=unit_price,
        unit_type="kg",
        package_size=package_size or post_text or None,
        brand="",
        is_on_sale=is_on_sale,
        original_price=original_price,
        url=f"https://flipp.com/fr/item/{item.get('flyer_item_id', '')}" if item.get("flyer_item_id") else None,
        product_name=name[:80],
        branch_name=merchant,
    )


def _parse_unit_price(price: float, post_text: str, name: str) -> float | None:
    """Convert price to CAD/kg based on post_price_text."""
    if not post_text:
        return None

    # "/lb" or "lb" → convert to /kg
    if "/lb" in post_text or re.search(r'\blb\b', post_text):
        return price / 0.453592

    # "le 100 g" or "/100g" → convert to /kg
    if "100 g" in post_text or "/100g" in post_text:
        return price * 10

    # "/kg" → ja esta em kg
    if "/kg" in post_text:
        return price

    return None


def _extract_size(name: str) -> str | None:
    """Extract package size from product name (e.g. 'CHICKEN BREAST, 3 un.' → '3 un.')."""
    # Peso: "500 g", "1.5 kg", "2 lb"
    match = re.search(r'(\d+\.?\d*\s*(g|kg|lb|lbs))', name, re.IGNORECASE)
    if match:
        return match.group(1)

    # Quantidade: "3 un.", "4 pack"
    match = re.search(r'(\d+\s*un\.?)', name, re.IGNORECASE)
    if match:
        return match.group(1)

    # Tamanho entre parenteses no final
    match = re.search(r'\((\d+[^)]+)\)\s*$', name)
    if match:
        return match.group(1)

    return None
