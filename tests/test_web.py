import pytest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from web.server import app
from web.i18n import EN, FR
from src.config import DB_PATH
from src.db import get_db, init_db


@pytest.fixture(autouse=True)
def clean_db():
    """Remove stale DB and ensure schema is initialized before each test class."""
    DB_PATH.unlink(missing_ok=True)


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


class TestPageRoutes:
    def test_home_page_en(self, client):
        response = client.get("/", cookies={"lang": "en"})
        assert response.status_code == 200
        assert "MeatPrice Tracker" in response.text
        assert "Find the Best Meat Prices" in response.text

    def test_home_page_fr(self, client):
        response = client.get("/", cookies={"lang": "fr"})
        assert response.status_code == 200
        assert "SuiviPrix Viandes" in response.text
        assert "Meilleurs Prix de Viande" in response.text

    def test_home_page_default_lang(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert "MeatPrice Tracker" in response.text

    def test_products_page(self, client):
        response = client.get("/products", cookies={"lang": "en"})
        assert response.status_code == 200
        assert "Meat Products" in response.text or "products" in response.text.lower()

    def test_products_page_fr(self, client):
        response = client.get("/products", cookies={"lang": "fr"})
        assert response.status_code == 200
        assert "Produits de Viande" in response.text

    def test_stores_page(self, client):
        response = client.get("/stores")
        assert response.status_code == 200
        assert "Participating Stores" in response.text

    def test_history_page(self, client):
        response = client.get("/history")
        assert response.status_code == 200
        assert "Price History" in response.text


class TestAPIRoutes:
    def test_health(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_api_products(self, client):
        response = client.get("/api/products?lang=en")
        assert response.status_code == 200
        data = response.json()
        assert "products" in data
        assert len(data["products"]) >= 3

    def test_api_products_fr(self, client):
        response = client.get("/api/products?lang=fr")
        assert response.status_code == 200
        data = response.json()
        product_names = [p["name"] for p in data["products"]]
        assert "Picanha (Couverture de surlonge)" in product_names

    def test_api_stores(self, client):
        response = client.get("/api/stores")
        assert response.status_code == 200
        data = response.json()
        assert len(data["stores"]) == 9
        store_ids = [s["id"] for s in data["stores"]]
        assert "maxi" in store_ids
        assert "costco" in store_ids

    def test_api_stores_fr(self, client):
        response = client.get("/api/stores?lang=fr")
        assert response.status_code == 200
        data = response.json()
        assert len(data["stores"]) == 9


class TestLanguageDetection:
    def test_cookie_preference(self, client):
        response = client.get("/", cookies={"lang": "fr"})
        assert "SuiviPrix Viandes" in response.text

    def test_accept_language_header(self, client):
        response = client.get("/", headers={"accept-language": "fr-CA,fr;q=0.9"})
        assert "SuiviPrix Viandes" in response.text

    def test_cookie_en_overrides_fr_header(self, client):
        response = client.get(
            "/",
            cookies={"lang": "en"},
            headers={"accept-language": "fr-CA,fr;q=0.9"},
        )
        assert "MeatPrice Tracker" in response.text


class TestUIElementsInPortuguese:
    """Verifica que a interface tem estrutura correta (bilingue EN/FR)."""

    def test_navigation_present(self, client):
        response = client.get("/", cookies={"lang": "en"})
        assert "Home" in response.text
        assert "Products" in response.text
        assert "Stores" in response.text
        assert "History" in response.text

    def test_navigation_fr(self, client):
        response = client.get("/", cookies={"lang": "fr"})
        assert "Accueil" in response.text
        assert "Produits" in response.text
        assert "Magasins" in response.text
        assert "Historique" in response.text

    def test_lang_switcher_buttons(self, client):
        response = client.get("/")
        assert 'data-lang="en"' in response.text
        assert 'data-lang="fr"' in response.text

    def test_footer_present(self, client):
        response = client.get("/")
        assert "Helping you save on groceries since 2025" in response.text

    def test_features_section_en(self, client):
        response = client.get("/", cookies={"lang": "en"})
        assert "Real-Time Prices" in response.text
        assert "Bilingual" in response.text
        assert "Price History" in response.text
        assert "Free &amp; Open" in response.text

    def test_features_section_fr(self, client):
        response = client.get("/", cookies={"lang": "fr"})
        assert "Prix en Temps Réel" in response.text
        assert "Bilingue" in response.text
        assert "Historique des Prix" in response.text
        assert "Gratuit" in response.text

    def test_cta_button_en(self, client):
        response = client.get("/", cookies={"lang": "en"})
        assert "View Current Deals" in response.text

    def test_cta_button_fr(self, client):
        response = client.get("/", cookies={"lang": "fr"})
        assert "Voir les Offres" in response.text

    def test_static_css_served(self, client):
        response = client.get("/static/css/styles.css")
        assert response.status_code == 200
        assert "MeatPrice Tracker" in response.text or "--primary" in response.text

    def test_static_js_served(self, client):
        response = client.get("/static/js/app.js")
        assert response.status_code == 200
        assert "MeatPrice Tracker" in response.text


class TestAPIEdgeCases:
    def test_prices_empty_db(self, client):
        response = client.get("/api/prices")
        assert response.status_code == 200
        data = response.json()
        assert data["prices"] == []
        assert data["count"] == 0

    def test_prices_with_filter(self, client):
        response = client.get("/api/prices?product=picanha&store=maxi")
        assert response.status_code == 200

    def test_history_invalid_days(self, client):
        response = client.get("/api/history/picanha?days=0")
        assert response.status_code == 422

    def test_history_too_many_days(self, client):
        response = client.get("/api/history/picanha?days=400")
        assert response.status_code == 422

    def test_api_prices_lang_param(self, client):
        response = client.get("/api/prices?lang=fr")
        assert response.status_code == 200
