from src.models import Price, Product, ScrapeResult, Store, StoreBranch


class TestPrice:
    def test_create_minimal(self):
        p = Price(product_slug="picanha", store_id="maxi", price_cad=12.99)
        assert p.product_slug == "picanha"
        assert p.store_id == "maxi"
        assert p.price_cad == 12.99
        assert p.unit_type == "kg"
        assert p.is_on_sale is False
        assert p.unit_price is None
        assert p.brand is None

    def test_create_full(self):
        p = Price(
            product_slug="chicken_breast",
            store_id="costco",
            price_cad=19.99,
            unit_price=8.99,
            unit_type="kg",
            package_size="2 kg",
            brand="Kirkland",
            is_on_sale=True,
            original_price=24.99,
            url="https://example.com",
            product_name="Poitrine de poulet",
            branch_name="Costco Montreal",
        )
        assert p.price_cad == 19.99
        assert p.unit_price == 8.99
        assert p.brand == "Kirkland"
        assert p.is_on_sale is True
        assert p.original_price == 24.99
        assert p.product_name == "Poitrine de poulet"

    def test_defaults(self):
        p = Price(product_slug="picanha", store_id="maxi", price_cad=10.0)
        assert p.package_size is None
        assert p.url is None
        assert p.branch_name is None
        assert p.scraped_at is None


class TestScrapeResult:
    def test_with_prices(self):
        prices = [
            Price(product_slug="picanha", store_id="maxi", price_cad=12.99),
            Price(product_slug="chicken_breast", store_id="maxi", price_cad=8.99),
        ]
        r = ScrapeResult(
            store_id="maxi",
            store_name="Maxi",
            prices=prices,
            duration_ms=150.0,
        )
        assert len(r.prices) == 2
        assert r.store_name == "Maxi"
        assert r.error is None
        assert r.duration_ms == 150.0

    def test_empty_result(self):
        r = ScrapeResult.empty(store_id="costco", store_name="Costco", error="timeout")
        assert r.store_id == "costco"
        assert r.prices == []
        assert r.error == "timeout"

    def test_empty_result_no_error(self):
        r = ScrapeResult.empty("maxi")
        assert r.error == ""
        assert r.prices == []


class TestStore:
    def test_create(self):
        s = Store(id="maxi", name="Maxi", base_url="https://maxi.ca", scraper_type="api")
        assert s.id == "maxi"
        assert s.active is True

    def test_inactive(self):
        s = Store(id="iga", name="IGA", base_url="https://iga.ca", scraper_type="playwright", active=False)
        assert s.active is False


class TestStoreBranch:
    def test_create(self):
        b = StoreBranch(
            store_id="maxi",
            external_id="1190",
            name="Maxi Rachel",
            address="3200 Rue Rachel E",
            postal_code="H1W1A3",
        )
        assert b.external_id == "1190"
        assert b.postal_code == "H1W1A3"
        assert b.latitude is None


class TestProduct:
    def test_create(self):
        p = Product(slug="picanha", name_pt="Picanha")
        assert p.slug == "picanha"
        assert p.name_pt == "Picanha"
        assert p.aliases == {}
