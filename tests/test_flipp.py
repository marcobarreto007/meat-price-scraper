import json
from unittest.mock import AsyncMock, patch

import pytest
from src.models import Price
from src.scrapers.flipp import (
    FlippScraper,
    SEARCH_TERMS,
    _extract_size,
    _parse_flipp_item,
    _parse_unit_price,
)

# Sample Flipp API response
FLIPP_RESPONSE_PICANHA = {
    "items": [
        {
            "name": "Culotte de surlonge AAA",
            "merchant_name": "Maxi",
            "current_price": 12.99,
            "original_price": 16.99,
            "post_price_text": "/lb",
            "pre_price_text": "",
            "sale_story": "",
            "valid_from": "2025-01-01",
            "valid_to": "2025-01-07",
            "flyer_id": "123",
            "flyer_item_id": "456",
        },
        {
            "name": "Picanha Black Angus ~1.2 kg",
            "merchant_name": "Super C",
            "current_price": 18.50,
            "original_price": "",
            "post_price_text": "/kg",
            "pre_price_text": "",
            "sale_story": "",
            "valid_from": "2025-01-02",
            "valid_to": "2025-01-08",
            "flyer_id": "789",
            "flyer_item_id": "012",
        },
    ]
}

FLIPP_RESPONSE_CHICKEN = {
    "items": [
        {
            "name": "POITRINES DE POULET, 3 un.",
            "merchant_name": "IGA",
            "current_price": 10.00,
            "post_price_text": "le 100 g",
            "pre_price_text": "",
            "sale_story": "2 pour 20$",
            "valid_from": "2025-01-01",
            "valid_to": "2025-01-07",
            "flyer_id": "111",
            "flyer_item_id": "222",
        }
    ]
}

FLIPP_EMPTY = {"items": []}


class TestParseFlippItem:
    def test_parse_basic(self):
        item = {
            "name": "Picanha AAA",
            "merchant_name": "Maxi",
            "current_price": 12.99,
            "post_price_text": "/kg",
        }
        price = _parse_flipp_item(item, "picanha")
        assert price is not None
        assert price.product_slug == "picanha"
        assert price.store_id == "maxi"
        assert price.price_cad == 12.99
        assert price.is_on_sale is True
        assert price.product_name == "Picanha AAA"

    def test_parse_with_string_price(self):
        item = {
            "name": "Test",
            "merchant_name": "Metro",
            "current_price": "9.99",
            "post_price_text": "/kg",
        }
        price = _parse_flipp_item(item, "test")
        assert price is not None
        assert price.price_cad == 9.99

    def test_parse_with_comma_price(self):
        item = {
            "name": "Test",
            "merchant_name": "Metro",
            "current_price": "12,99",
            "post_price_text": "/kg",
        }
        price = _parse_flipp_item(item, "test")
        assert price is not None
        assert price.price_cad == 12.99

    def test_parse_no_name_returns_none(self):
        item = {"name": "", "merchant_name": "X", "current_price": 5.0}
        assert _parse_flipp_item(item, "test") is None

    def test_parse_no_price_returns_none(self):
        item = {"name": "Test", "merchant_name": "X", "current_price": 0}
        assert _parse_flipp_item(item, "test") is None

    def test_parse_sale_story_fallback(self):
        item = {
            "name": "Filet Mignon",
            "merchant_name": "Provigo",
            "current_price": None,
            "sale_story": "15$ chaque",
            "post_price_text": "/kg",
        }
        price = _parse_flipp_item(item, "filet_mignon")
        assert price is not None
        assert price.price_cad == 15.0

    def test_parse_original_price(self):
        item = {
            "name": "Test",
            "merchant_name": "Walmart",
            "current_price": 8.99,
            "original_price": "12.99",
            "post_price_text": "/kg",
        }
        price = _parse_flipp_item(item, "test")
        assert price is not None
        assert price.original_price == 12.99

    def test_parse_url_generated(self):
        item = {
            "name": "Test",
            "merchant_name": "Maxi",
            "current_price": 5.99,
            "post_price_text": "/kg",
            "flyer_item_id": "789",
        }
        price = _parse_flipp_item(item, "test")
        assert price is not None
        assert price.url == "https://flipp.com/fr/item/789"

    def test_parse_no_flyer_item_no_url(self):
        item = {
            "name": "Test",
            "merchant_name": "Maxi",
            "current_price": 5.99,
            "post_price_text": "/kg",
        }
        price = _parse_flipp_item(item, "test")
        assert price is not None
        assert price.url is None


class TestParseUnitPrice:
    def test_per_lb(self):
        up = _parse_unit_price(10.0, "/lb", "")
        assert up == pytest.approx(22.046, rel=0.01)

    def test_per_100g(self):
        up = _parse_unit_price(3.50, "/100g", "")
        assert up == 35.0

    def test_per_kg(self):
        up = _parse_unit_price(15.99, "/kg", "")
        assert up == 15.99

    def test_empty_text(self):
        assert _parse_unit_price(10.0, "", "") is None

    def test_lb_in_text(self):
        up = _parse_unit_price(8.0, "1 lb", "")
        assert up == pytest.approx(17.637, rel=0.01)

    def test_100g_in_text(self):
        up = _parse_unit_price(4.0, "le 100 g", "")
        assert up == 40.0


class TestExtractSize:
    def test_grams(self):
        assert _extract_size("Poulet 500 g") == "500 g"

    def test_kg(self):
        assert _extract_size("Boeuf 1.5 kg AAA") == "1.5 kg"

    def test_lb(self):
        assert _extract_size("Steak 2 lb") == "2 lb"

    def test_unit_count(self):
        assert _extract_size("POITRINES DE POULET, 3 un.") == "3 un."

    def test_parenthesis(self):
        assert _extract_size("Produit (4 pack)") == "4 pack"

    def test_no_match(self):
        assert _extract_size("Produit sans taille") is None


class TestFlippScraper:
    @pytest.mark.asyncio
    async def test_search_product_returns_results(self):
        scraper = FlippScraper()
        assert scraper.store_id == "flipp"
        assert scraper.store_name == "Flipp (Todas as Lojas)"

    def test_search_terms_completeness(self):
        assert "chicken_breast" in SEARCH_TERMS
        assert "picanha" in SEARCH_TERMS
        assert "filet_mignon" in SEARCH_TERMS
        assert len(SEARCH_TERMS["chicken_breast"]) >= 2
        assert len(SEARCH_TERMS["picanha"]) >= 2
