import logging

import aiohttp

from src.auth.pcexpress_auth import get_access_token
from src.config import (
    PCEXPRESS_API_BASE,
    PCEXPRESS_API_KEY,
    PCEXPRESS_TENANT_ID,
    RADIUS_KM,
)
from src.geo import distance_from_center, is_within_radius
from src.models import Price
from src.scrapers.base import AbstractScraper

logger = logging.getLogger(__name__)

BFF_BASE = f"{PCEXPRESS_API_BASE}/pcx-bff/api/v1"
DEFAULT_STORE_ID = "1190"  # Maxi Montreal - 3200 Rue Rachel E


class MaxiScraper(AbstractScraper):
    store_id = "maxi"
    store_name = "Maxi"

    async def _get_headers(self) -> dict:
        token = await get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "x-apikey": PCEXPRESS_API_KEY,
            "Business-User-Agent": "PCXWEB",
            "Site-Banner": "maxi",
            "x-application-type": "Web",
            "x-loblaw-tenant-id": PCEXPRESS_TENANT_ID,
            "Content-Type": "application/json",
        }

    async def discover_stores(self) -> list[dict]:
        """Discover Maxi stores within 50km radius of center."""
        headers = await self._get_headers()
        stores = []

        async with aiohttp.ClientSession() as session:
            # Get pickup locations near center
            async with session.get(
                f"{BFF_BASE}/pickup-locations",
                params={
                    "banner": "maxi",
                    "postalCode": "H2T1S8",
                    "maxResults": "50",
                },
                headers=headers,
            ) as resp:
                data = await resp.json()
                logger.info("Pickup locations status: %s", resp.status)

            locations = data.get("locations", data.get("results", [])) if isinstance(data, dict) else []

            for loc in locations:
                lat = loc.get("latitude")
                lon = loc.get("longitude")
                if lat and lon:
                    lat_f, lon_f = float(lat), float(lon)
                    if is_within_radius(lat_f, lon_f):
                        dist = distance_from_center(lat_f, lon_f)
                        stores.append({
                            "store_id": "maxi",
                            "external_id": str(loc.get("storeId", loc.get("id", ""))),
                            "name": loc.get("name", f"Maxi - {loc.get('address', '')}"),
                            "address": loc.get("address", ""),
                            "postal_code": loc.get("postalCode", ""),
                            "latitude": lat_f,
                            "longitude": lon_f,
                            "distance_km": round(dist, 1),
                        })

        logger.info("Found %d Maxi stores within %dkm", len(stores), RADIUS_KM)
        return stores

    async def search_product(self, product_slug: str, search_terms: list[str]) -> list[Price]:
        headers = await self._get_headers()
        results: list[Price] = []

        async with aiohttp.ClientSession() as session:
            for term in search_terms[:3]:  # Max 3 terms per search
                prices = await self._search_single(session, headers, product_slug, term)
                results.extend(prices)

        # Deduplicate and sort by unit_price
        seen = set()
        unique: list[Price] = []
        for p in sorted(results, key=lambda x: x.unit_price or x.price_cad):
            key = (p.branch_name, p.product_name, p.price_cad)
            if key not in seen:
                seen.add(key)
                unique.append(p)

        return unique[:10]

    async def _search_single(
        self,
        session: aiohttp.ClientSession,
        headers: dict,
        product_slug: str,
        term: str,
    ) -> list[Price]:
        results: list[Price] = []

        try:
            # Create cart first to get cartId
            async with session.post(
                f"{BFF_BASE}/cart",
                json={"storeId": DEFAULT_STORE_ID, "banner": "maxi"},
                headers=headers,
            ) as cart_resp:
                cart_data = await cart_resp.json() if cart_resp.status < 400 else {}
                cart_id = cart_data.get("id", "")

            async with session.post(
                f"{BFF_BASE}/products/search",
                json={
                    "lang": "fr",
                    "term": term,
                    "storeId": DEFAULT_STORE_ID,
                    "banner": "maxi",
                    "cartId": cart_id,
                    "pagination": {"from": 0, "size": 48},
                },
                headers=headers,
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    logger.warning("Maxi search '%s' -> %s: %s", term, resp.status, text[:200])
                    return []

                data = await resp.json()

        except aiohttp.ClientError as e:
            logger.error("Maxi HTTP error for '%s': %s", term, e)
            return []

        products = data.get("results", []) if isinstance(data, dict) else []

        for item in products:
            price_info = self._extract_price(item)
            if price_info is None:
                continue

            price_info.product_slug = product_slug
            price_info.store_id = self.store_id
            results.append(price_info)

        return results

    def _extract_price(self, item: dict) -> Price | None:
        prices_list = item.get("prices", [])
        if not prices_list:
            return None

        price_entry = prices_list[0]
        price_cad = price_entry.get("price", 0)
        if not price_cad or float(price_cad) <= 0:
            return None

        name = item.get("name", "")
        package_size = item.get("packageSize", "")
        brand = item.get("brand", "")
        url_slug = item.get("slug", "")

        # Unit price
        unit_price = None
        comparison = price_entry.get("comparisonPrices", [])
        for cp in comparison:
            if cp.get("unit") in ("kg", "100g"):
                up = float(cp.get("price", 0))
                if cp.get("unit") == "100g":
                    up *= 10  # normalizar para /kg
                unit_price = up
                break

        # Se nao tem comparison price, calcula do package size
        if unit_price is None and package_size:
            unit_price = _estimate_unit_price(float(price_cad), package_size)

        # Promocao
        is_on_sale = False
        original_price = None
        deal_price = price_entry.get("dealPrice")
        if deal_price and float(deal_price) > 0 and float(deal_price) != float(price_cad):
            original_price = float(price_cad)
            price_cad = float(deal_price)
            is_on_sale = True
        else:
            price_cad = float(price_cad)

        return Price(
            product_slug="",
            store_id=self.store_id,
            price_cad=price_cad,
            unit_price=unit_price,
            unit_type="kg",
            package_size=package_size,
            brand=brand,
            is_on_sale=is_on_sale,
            original_price=original_price,
            url=f"https://www.maxi.ca/product/{url_slug}" if url_slug else None,
            product_name=name,
            branch_name="Maxi Montreal",
        )


def _estimate_unit_price(price: float, package_size: str) -> float | None:
    """Estimate price per kg from package size string (e.g. '~700 g')."""
    import re

    size_clean = package_size.lower().replace(",", ".").replace("~", "").strip()
    match = re.match(r"([\d.]+)\s*(g|kg|lb|lbs)", size_clean)
    if not match:
        return None

    amount = float(match.group(1))
    unit = match.group(2)

    if unit in ("g",):
        kg = amount / 1000
    elif unit in ("lb", "lbs"):
        kg = amount * 0.453592
    else:
        kg = amount

    if kg <= 0:
        return None

    return price / kg
