import json
import logging
from datetime import datetime, timedelta, timezone

import aiosqlite

from src.config import CACHE_TTL_HOURS, DB_PATH

logger = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS stores (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    base_url    TEXT NOT NULL,
    scraper_type TEXT NOT NULL,
    active      INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS store_branches (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    store_id    TEXT NOT NULL REFERENCES stores(id),
    external_id TEXT NOT NULL,
    name        TEXT NOT NULL,
    address     TEXT NOT NULL,
    postal_code TEXT NOT NULL,
    latitude    REAL,
    longitude   REAL,
    distance_km REAL,
    UNIQUE(store_id, external_id)
);

CREATE TABLE IF NOT EXISTS products (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    slug        TEXT UNIQUE NOT NULL,
    name_pt     TEXT NOT NULL,
    aliases_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS prices (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    product_slug TEXT NOT NULL,
    store_id    TEXT NOT NULL,
    branch_id   INTEGER REFERENCES store_branches(id),
    price_cad   REAL NOT NULL,
    unit_price  REAL,
    unit_type   TEXT DEFAULT 'kg',
    package_size TEXT,
    brand       TEXT,
    is_on_sale  INTEGER DEFAULT 0,
    original_price REAL,
    url         TEXT,
    product_name TEXT,
    branch_name TEXT,
    scraped_at  TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(product_slug, store_id, branch_id, scraped_at)
);

CREATE INDEX IF NOT EXISTS idx_prices_product_store ON prices(product_slug, store_id);
CREATE INDEX IF NOT EXISTS idx_prices_scraped ON prices(scraped_at);
CREATE INDEX IF NOT EXISTS idx_prices_lookup
    ON prices(product_slug, store_id, branch_id, scraped_at DESC);
"""


async def get_db() -> aiosqlite.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = await aiosqlite.connect(str(DB_PATH))
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA synchronous=NORMAL")
    await db.execute("PRAGMA busy_timeout=5000")
    await db.execute("PRAGMA foreign_keys=ON")
    db.row_factory = aiosqlite.Row
    return db


async def init_db(db: aiosqlite.Connection) -> None:
    await db.executescript(SCHEMA)
    await db.commit()
    logger.info("Database initialized at %s", DB_PATH)


async def seed_products(db: aiosqlite.Connection, products: list[dict]) -> None:
    for p in products:
        await db.execute(
            "INSERT OR IGNORE INTO products (slug, name_pt, aliases_json) VALUES (?, ?, ?)",
            (p["slug"], p["name_pt"], p["aliases_json"]),
        )
    await db.commit()


async def seed_stores(db: aiosqlite.Connection, stores: list[dict]) -> None:
    for s in stores:
        await db.execute(
            "INSERT OR IGNORE INTO stores (id, name, base_url, scraper_type, active) "
            "VALUES (?, ?, ?, ?, ?)",
            (s["id"], s["name"], s["base_url"], s["scraper_type"], int(s.get("active", True))),
        )
    await db.commit()


async def upsert_branch(db: aiosqlite.Connection, branch: dict) -> None:
    await db.execute(
        "INSERT OR REPLACE INTO store_branches "
        "(store_id, external_id, name, address, postal_code, latitude, longitude, distance_km) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            branch["store_id"],
            branch["external_id"],
            branch["name"],
            branch["address"],
            branch["postal_code"],
            branch.get("latitude"),
            branch.get("longitude"),
            branch.get("distance_km"),
        ),
    )
    await db.commit()


async def get_branches(db: aiosqlite.Connection, store_id: str) -> list[dict]:
    cursor = await db.execute(
        "SELECT * FROM store_branches WHERE store_id = ?", (store_id,)
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def insert_prices(db: aiosqlite.Connection, prices: list[dict]) -> int:
    count = 0
    for p in prices:
        try:
            await db.execute(
                "INSERT OR IGNORE INTO prices "
                "(product_slug, store_id, branch_id, price_cad, unit_price, unit_type, "
                "package_size, brand, is_on_sale, original_price, url, product_name, branch_name) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    p["product_slug"],
                    p["store_id"],
                    p.get("branch_id"),
                    p["price_cad"],
                    p.get("unit_price"),
                    p.get("unit_type", "kg"),
                    p.get("package_size"),
                    p.get("brand"),
                    int(p.get("is_on_sale", False)),
                    p.get("original_price"),
                    p.get("url"),
                    p.get("product_name"),
                    p.get("branch_name"),
                ),
            )
            count += 1
        except Exception:
            pass  # skip duplicates
    await db.commit()
    return count


async def get_latest_prices(
    db: aiosqlite.Connection,
    product_slug: str | None = None,
    store_id: str | None = None,
    max_age_hours: int = CACHE_TTL_HOURS,
) -> list[dict]:
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=max_age_hours)).isoformat()
    query = """
        SELECT p.*, s.name as store_name
        FROM prices p
        JOIN stores s ON p.store_id = s.id
        WHERE p.scraped_at >= ?
    """
    params: list = [cutoff]

    if product_slug:
        query += " AND p.product_slug = ?"
        params.append(product_slug)
    if store_id:
        query += " AND p.store_id = ?"
        params.append(store_id)

    query += " ORDER BY p.unit_price ASC, p.price_cad ASC"

    cursor = await db.execute(query, params)
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def get_price_history(
    db: aiosqlite.Connection,
    product_slug: str,
    days: int = 30,
) -> list[dict]:
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    cursor = await db.execute(
        """
        SELECT p.*, s.name as store_name
        FROM prices p
        JOIN stores s ON p.store_id = s.id
        WHERE p.product_slug = ? AND p.scraped_at >= ?
        ORDER BY p.scraped_at DESC
        """,
        (product_slug, since),
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def get_circuit_breaker_status(db: aiosqlite.Connection) -> dict[str, bool]:
    """Retorna stores que estao com circuit breaker ativo (5+ falhas consecutivas)."""
    cursor = await db.execute("SELECT id, active FROM stores")
    rows = await cursor.fetchall()
    return {r["id"]: bool(r["active"]) for r in rows}
