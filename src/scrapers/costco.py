"""
Costco Same-Day scraper via Playwright com interceptacao de GraphQL.

Abordagem:
1. Abre sameday.costco.com, clica "Browse as a guest"
2. Navega para search URL
3. Intercepta as respostas GraphQL do tipo "Items" que contem precos
4. Extrai dados limpos: nome, preco, tamanho, preco por unidade
"""

import logging
import re

from playwright.async_api import async_playwright

from src.config import TIMEOUT_SECONDS
from src.models import Price
from src.scrapers.base import AbstractScraper

logger = logging.getLogger(__name__)

# Termos de busca especificos por produto
PRODUCT_SEARCH_TERMS: dict[str, list[str]] = {
    "chicken_breast": ["chicken breast", "poitrine de poulet"],
    "picanha": ["picanha", "top sirloin cap", "sirloin cap", "couvre-filet"],
    "filet_mignon": ["beef tenderloin", "filet mignon"],
}

# Palavras-chave para filtrar resultados relevantes por produto
PRODUCT_FILTERS: dict[str, list[str]] = {
    "chicken_breast": ["chicken breast", "poitrine", "chicken breast"],
    "picanha": ["picanha", "sirloin cap", "couvre-filet", "top sirloin"],
    "filet_mignon": ["tenderloin", "filet mignon", "filet de"],
}

# Palavras para excluir (falsos positivos)
EXCLUDE_WORDS: dict[str, list[str]] = {
    "chicken_breast": ["crab", "tuna", "salmon", "seafood", "sausage", "noodle", "soup", "dog", "party wings", "thigh"],
}


class CostcoScraper(AbstractScraper):
    store_id = "costco"
    store_name = "Costco (Same-Day)"

    async def search_product(self, product_slug: str, search_terms: list[str]) -> list[Price]:
        results: list[Price] = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"],
            )
            context = await browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/127.0.0.0 Safari/537.36"
                ),
            )
            page = await context.new_page()

            # Intercepta GraphQL Items responses
            items_responses: list[dict] = []

            async def capture_items(response):
                if "graphql" in response.url.lower() and "operationName=Items" in response.url:
                    try:
                        body = await response.json()
                        items = body.get("data", {}).get("items", [])
                        for item in items:
                            if isinstance(item, dict):
                                items_responses.append(item)
                    except Exception:
                        pass

            page.on("response", capture_items)

            try:
                # Setup: guest mode
                await page.goto("https://sameday.costco.com", wait_until="domcontentloaded", timeout=20000)
                await page.wait_for_timeout(2000)
                try:
                    guest = await page.wait_for_selector("text=Browse as a guest", timeout=5000)
                    await guest.click()
                    await page.wait_for_timeout(3000)
                except Exception:
                    pass  # Ja pode estar logado como guest

                # Busca cada termo
                for term in search_terms[:2]:
                    url = f"https://sameday.costco.com/store/costco/search?q={term.replace(' ', '+')}"
                    try:
                        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
                        await page.wait_for_timeout(5000)
                    except Exception as e:
                        logger.warning("Costco search nav error: %s", e)

            except Exception as e:
                logger.error("Costco error: %s", e)
            finally:
                await browser.close()

        # Processa items capturados
        filters = PRODUCT_FILTERS.get(product_slug, [])
        for item in items_responses:
            price_info = _extract_price_from_item(item, product_slug, filters)
            if price_info:
                results.append(price_info)

        # Deduplica e ordena
        seen = set()
        unique: list[Price] = []
        for p in sorted(results, key=lambda x: x.unit_price or x.price_cad):
            key = (p.product_name, p.price_cad)
            if key not in seen:
                seen.add(key)
                unique.append(p)

        return unique[:10]


def _extract_price_from_item(item: dict, product_slug: str, filters: list[str]) -> Price | None:
    name = item.get("name", "")
    if not name:
        return None

    # Filtra por relevancia ao produto buscado
    name_lower = name.lower()
    if filters and not any(f.lower() in name_lower for f in filters):
        return None

    # Exclui falsos positivos
    excludes = EXCLUDE_WORDS.get(product_slug, [])
    if excludes and any(e.lower() in name_lower for e in excludes):
        return None

    # Extrai preco do JSON aninhado (caminho: viewSection → price → ...)
    price_str = _deep_find(item, "priceString")
    if not price_str or not isinstance(price_str, str):
        return None

    price_cad = _parse_dollar(price_str)
    if price_cad is None or price_cad <= 0:
        return None

    size = item.get("size", "")

    # Preco por unidade (ex: "$X.XX / lb")
    unit_price = None
    per_unit_str = _deep_find(item, "pricePerUnitString")
    if per_unit_str and isinstance(per_unit_str, str):
        unit_price = _parse_price_per_unit(per_unit_str)

    # Se nao tem pricePerUnitString, estima do tamanho
    if unit_price is None and size:
        unit_price = _calc_unit_price(price_cad, size)

    # Detecta promocao
    is_on_sale = False
    original_price = None
    full_price_str = _deep_find(item, "fullPriceString")
    if full_price_str and isinstance(full_price_str, str):
        orig = _parse_dollar(full_price_str)
        if orig and orig > price_cad:
            original_price = orig
            is_on_sale = True

    brand = item.get("brandName", "")
    product_id = item.get("productId", "")

    return Price(
        product_slug=product_slug,
        store_id="costco",
        price_cad=price_cad,
        unit_price=unit_price,
        unit_type="kg",
        package_size=size,
        brand=brand,
        is_on_sale=is_on_sale,
        original_price=original_price,
        url=f"https://sameday.costco.com/store/costco/products/{product_id}" if product_id else None,
        product_name=name[:80],
        branch_name="Costco Montreal",
    )


def _deep_find(obj, key: str) -> object:
    """Busca recursiva por uma chave no JSON aninhado."""
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for v in obj.values():
            result = _deep_find(v, key)
            if result is not None:
                return result
    elif isinstance(obj, list):
        for item in obj:
            result = _deep_find(item, key)
            if result is not None:
                return result
    return None


def _parse_dollar(val: str) -> float | None:
    """Converte string de preco para float: '$31.18' -> 31.18"""
    if not val:
        return None
    match = re.search(r'\$?([\d,]+\.?\d*)', str(val).replace(",", ""))
    if match:
        return float(match.group(1))
    return None


def _parse_price_per_unit(val: str) -> float | None:
    """Converte '$10.20 / lb' ou 'About $3.73 each' para CAD/kg."""
    if not val:
        return None
    val_lower = val.lower()
    price = _parse_dollar(val)
    if price is None:
        return None

    if "lb" in val_lower:
        return price / 0.453592  # lb → kg
    if "each" in val_lower or "ea" in val_lower or "ct" in val_lower:
        return None  # Preco por unidade, nao por peso — nao podemos converter
    if "kg" in val_lower:
        return price
    return None


def _calc_unit_price(price: float, size: str) -> float | None:
    if not size:
        return None
    size_clean = size.lower().replace(",", ".").strip()
    match = re.match(r"([\d.]+)\s*(g|kg|lb|lbs)", size_clean)
    if not match:
        return None
    amount = float(match.group(1))
    unit = match.group(2)
    if unit == "g":
        kg = amount / 1000
    elif unit in ("lb", "lbs"):
        kg = amount * 0.453592
    else:
        kg = amount
    if kg <= 0:
        return None
    return price / kg
