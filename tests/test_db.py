import pytest
import aiosqlite
from src.db import (
    get_db,
    init_db,
    seed_products,
    seed_stores,
    insert_prices,
    get_latest_prices,
    get_price_history,
    upsert_branch,
    get_branches,
    get_circuit_breaker_status,
)
from src.config import DB_PATH


@pytest.fixture
async def db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = await aiosqlite.connect(str(DB_PATH))
    conn.row_factory = aiosqlite.Row
    await init_db(conn)
    yield conn
    await conn.close()
    DB_PATH.unlink(missing_ok=True)


PRODUCTS = [
    {"slug": "picanha", "name_pt": "Picanha", "aliases_json": '{"flipp": ["picanha"]}'},
    {"slug": "chicken_breast", "name_pt": "Peito de Frango", "aliases_json": '{"flipp": ["poitrine de poulet"]}'},
]

STORES = [
    {"id": "maxi", "name": "Maxi", "base_url": "https://maxi.ca", "scraper_type": "api", "active": True},
    {"id": "costco", "name": "Costco", "base_url": "https://costco.ca", "scraper_type": "playwright", "active": True},
]


@pytest.mark.asyncio
async def test_init_db(db):
    cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [r["name"] for r in await cursor.fetchall()]
    assert "stores" in tables
    assert "products" in tables
    assert "prices" in tables
    assert "store_branches" in tables


@pytest.mark.asyncio
async def test_seed_products(db):
    await seed_products(db, PRODUCTS)
    cursor = await db.execute("SELECT slug, name_pt FROM products ORDER BY slug")
    rows = await cursor.fetchall()
    assert len(rows) == 2
    assert rows[0]["slug"] == "chicken_breast"
    assert rows[1]["slug"] == "picanha"


@pytest.mark.asyncio
async def test_seed_products_idempotent(db):
    await seed_products(db, PRODUCTS)
    await seed_products(db, PRODUCTS)
    cursor = await db.execute("SELECT count(*) as c FROM products")
    row = await cursor.fetchone()
    assert row["c"] == 2


@pytest.mark.asyncio
async def test_seed_stores(db):
    await seed_stores(db, STORES)
    cursor = await db.execute("SELECT id, name, active FROM stores ORDER BY id")
    rows = await cursor.fetchall()
    assert len(rows) == 2
    assert rows[0]["id"] == "costco"
    assert rows[1]["name"] == "Maxi"


@pytest.mark.asyncio
async def test_insert_prices(db):
    await seed_products(db, PRODUCTS)
    await seed_stores(db, STORES)
    prices = [
        {
            "product_slug": "picanha",
            "store_id": "maxi",
            "price_cad": 12.99,
            "unit_price": 14.99,
            "unit_type": "kg",
            "package_size": "~1 kg",
            "brand": "AAA",
            "is_on_sale": True,
            "original_price": 16.99,
            "url": "https://example.com/picanha",
            "product_name": "Picanha AAA",
            "branch_name": "Maxi Rachel",
        },
        {
            "product_slug": "chicken_breast",
            "store_id": "costco",
            "price_cad": 19.99,
        },
    ]
    count = await insert_prices(db, prices)
    assert count == 2

    cursor = await db.execute("SELECT count(*) as c FROM prices")
    row = await cursor.fetchone()
    assert row["c"] == 2


@pytest.mark.asyncio
async def test_insert_prices_dedup(db):
    """UNIQUE constraint includes scraped_at (auto-timestamp), so duplicate product_slug+store_id is allowed at different times."""
    await seed_products(db, PRODUCTS)
    await seed_stores(db, STORES)
    price = [{"product_slug": "picanha", "store_id": "maxi", "price_cad": 12.99}]
    await insert_prices(db, price)
    # Second insert succeeds because scraped_at is different
    count = await insert_prices(db, price)
    assert count == 1  # Different timestamp → not a duplicate


@pytest.mark.asyncio
async def test_get_latest_prices(db):
    await seed_products(db, PRODUCTS)
    await seed_stores(db, STORES)
    prices = [
        {"product_slug": "picanha", "store_id": "maxi", "price_cad": 12.99},
        {"product_slug": "chicken_breast", "store_id": "maxi", "price_cad": 8.99},
    ]
    await insert_prices(db, prices)

    results = await get_latest_prices(db, max_age_hours=9999)
    assert len(results) == 2


@pytest.mark.asyncio
async def test_get_latest_prices_filter_product(db):
    await seed_products(db, PRODUCTS)
    await seed_stores(db, STORES)
    prices = [
        {"product_slug": "picanha", "store_id": "maxi", "price_cad": 12.99},
        {"product_slug": "chicken_breast", "store_id": "maxi", "price_cad": 8.99},
    ]
    await insert_prices(db, prices)

    results = await get_latest_prices(db, product_slug="picanha", max_age_hours=9999)
    assert len(results) == 1
    assert results[0]["product_slug"] == "picanha"


@pytest.mark.asyncio
async def test_get_price_history(db):
    await seed_products(db, PRODUCTS)
    await seed_stores(db, STORES)
    prices = [{"product_slug": "picanha", "store_id": "maxi", "price_cad": 12.99}]
    await insert_prices(db, prices)

    results = await get_price_history(db, "picanha", days=30)
    assert len(results) == 1
    assert results[0]["price_cad"] == 12.99


@pytest.mark.asyncio
async def test_get_price_history_empty(db):
    await seed_products(db, PRODUCTS)
    results = await get_price_history(db, "nonexistent", days=30)
    assert results == []


@pytest.mark.asyncio
async def test_upsert_branch(db):
    branch = {
        "store_id": "maxi",
        "external_id": "1190",
        "name": "Maxi Rachel",
        "address": "3200 Rue Rachel E",
        "postal_code": "H1W1A3",
        "latitude": 45.55,
        "longitude": -73.55,
        "distance_km": 3.2,
    }
    await upsert_branch(db, branch)

    branches = await get_branches(db, "maxi")
    assert len(branches) == 1
    assert branches[0]["name"] == "Maxi Rachel"
    assert branches[0]["distance_km"] == 3.2


@pytest.mark.asyncio
async def test_get_branches_empty(db):
    branches = await get_branches(db, "nonexistent")
    assert branches == []


@pytest.mark.asyncio
async def test_circuit_breaker_status(db):
    await seed_stores(db, STORES)
    status = await get_circuit_breaker_status(db)
    assert status["maxi"] is True
    assert status["costco"] is True
