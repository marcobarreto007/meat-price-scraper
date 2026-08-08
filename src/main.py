"""
Meat Price Scraper - Montreal 50km Radius

Uses the Flipp public API (backflipp.wishabi.com) to fetch
meat deals from ALL Quebec stores in a single batch.

Usage:
    python -m src.main scrape
    python -m src.main scrape --products picanha,filet_mignon --output json
    python -m src.main history --product picanha --days 30
"""

import argparse
import asyncio
import logging

from dotenv import load_dotenv

load_dotenv()

from src.db import get_db, init_db, seed_products, seed_stores, insert_prices, get_price_history
from src.models import ScrapeResult
from src.products import PRODUCTS_SEED, STORES_SEED
from src.reporter import print_history_table, print_results_json, print_results_table
from src.scrapers.flipp import FlippScraper, SEARCH_TERMS

logger = logging.getLogger(__name__)

ALL_PRODUCTS = [p["slug"] for p in PRODUCTS_SEED]


async def cmd_scrape(args: argparse.Namespace) -> None:
    products = args.products.split(",") if args.products else ALL_PRODUCTS

    db = await get_db()
    await init_db(db)
    await seed_products(db, PRODUCTS_SEED)
    await seed_stores(db, STORES_SEED)

    if args.output != "json":
        print(f"Fetching {len(products)} products from Quebec stores...\n")

    flipp = FlippScraper()
    tasks = []
    for slug in products:
        terms = SEARCH_TERMS.get(slug, [slug])
        tasks.append(flipp.run(slug, terms))

    results: list[ScrapeResult] = list(await asyncio.gather(*tasks))

    # Merge results
    merged: dict[str, ScrapeResult] = {}
    for r in results:
        if r.store_id not in merged:
            merged[r.store_id] = ScrapeResult(
                store_id=r.store_id,
                store_name=r.store_name,
                prices=[],
                duration_ms=0,
            )
        merged[r.store_id].prices.extend(r.prices)
        merged[r.store_id].duration_ms += r.duration_ms
        if r.error:
            merged[r.store_id].error = (
                f"{merged[r.store_id].error}; {r.error}"
                if merged[r.store_id].error
                else r.error
            )

    merged_results = list(merged.values())

    # Save to DB
    all_price_dicts = []
    for r in merged_results:
        for p in r.prices:
            all_price_dicts.append({
                "product_slug": p.product_slug,
                "store_id": p.store_id,
                "price_cad": p.price_cad,
                "unit_price": p.unit_price,
                "unit_type": p.unit_type,
                "package_size": p.package_size,
                "brand": p.brand,
                "is_on_sale": p.is_on_sale,
                "original_price": p.original_price,
                "url": p.url,
                "product_name": p.product_name,
                "branch_name": p.branch_name,
            })

    if all_price_dicts:
        count = await insert_prices(db, all_price_dicts)
        logger.info("Saved %d prices to DB", count)

    if args.output == "json":
        print_results_json(merged_results)
    else:
        print_results_table(merged_results)

    await db.close()


async def cmd_history(args: argparse.Namespace) -> None:
    db = await get_db()
    await init_db(db)

    prices = await get_price_history(db, args.product, days=args.days)
    print_history_table(prices, args.days)

    await db.close()


def main():
    parser = argparse.ArgumentParser(
        description="Meat Price Comparison - Montreal 50km Radius",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command")

    p_scrape = sub.add_parser("scrape", help="Fetch prices from all stores")
    p_scrape.add_argument("--products", help="Products (e.g. picanha,filet_mignon)")
    p_scrape.add_argument("--output", choices=["table", "json"], default="table")
    p_scrape.add_argument("--verbose", action="store_true")

    p_hist = sub.add_parser("history", help="Price history")
    p_hist.add_argument("--product", required=True, help="Product slug")
    p_hist.add_argument("--days", type=int, default=30)

    args = parser.parse_args()

    verbose = getattr(args, "verbose", False)
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)

    if args.command is None:
        parser.print_help()
        return

    if args.command == "scrape":
        asyncio.run(cmd_scrape(args))
    elif args.command == "history":
        asyncio.run(cmd_history(args))


if __name__ == "__main__":
    main()
