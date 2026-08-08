import json
import sys
from datetime import datetime, timezone

from rich.console import Console
from rich.table import Table

from src.models import Price, ScrapeResult
from src.products import get_product_name_en

console = Console()


def format_price(price_cad: float) -> str:
    return f"${price_cad:,.2f}"


def format_unit_price(unit_price: float | None) -> str:
    if unit_price is None:
        return "—"
    return f"${unit_price:,.2f}/kg"


def print_results_json(results: list[ScrapeResult]) -> None:
    output = []
    for r in results:
        for p in r.prices:
            output.append({
                "product": p.product_slug,
                "product_name": p.product_name,
                "store": r.store_name,
                "branch": p.branch_name,
                "price_cad": p.price_cad,
                "price_kg": p.unit_price,
                "package_size": p.package_size,
                "brand": p.brand,
                "on_sale": p.is_on_sale,
                "original_price": p.original_price,
                "url": p.url,
            })
    json.dump(output, sys.stdout, indent=2, ensure_ascii=False)
    print()


def print_results_table(results: list[ScrapeResult]) -> None:
    all_prices = [p for r in results for p in r.prices]
    products_found: set[str] = {p.product_slug for p in all_prices}

    if not all_prices:
        console.print("\n[red]No results found.[/red]\n")
        return

    now = datetime.now(timezone.utc).astimezone()
    tz_name = now.tzname() or "EST"

    for slug in ["chicken_breast", "picanha", "filet_mignon"]:
        if slug not in products_found:
            continue

        name_en = get_product_name_en(slug)
        console.print(f"\n[bold yellow]  {name_en}[/bold yellow]")

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Rank", style="dim", width=4)
        table.add_column("Store / Product", style="white")
        table.add_column("Price/kg", justify="right")
        table.add_column("Price", justify="right")
        table.add_column("Sale", justify="center", width=6)

        prices = sorted(
            [p for p in all_prices if p.product_slug == slug],
            key=lambda x: x.unit_price if x.unit_price else x.price_cad,
        )

        for i, p in enumerate(prices[:8], 1):
            medal = ""
            if i == 1:
                medal = "[yellow]1[/yellow]"
            elif i == 2:
                medal = "[dim]2[/dim]"
            elif i == 3:
                medal = "[dim]3[/dim]"
            else:
                medal = str(i)

            store_display = f"[bold]{p.store_id.upper()}[/bold]"
            if p.branch_name:
                store_display += f" - {p.branch_name}"
            product_display = p.product_name or ""
            if p.package_size:
                product_display += f" ({p.package_size})"
            product_display = product_display[:55]

            u_price = format_unit_price(p.unit_price)
            total = format_price(p.price_cad)

            sale = "[green]YES[/green]" if p.is_on_sale else ""

            table.add_row(medal, f"{store_display}\n[dim]{product_display}[/dim]", u_price, total, sale)

        console.print(table)

    # Summary line
    console.print()
    console.print(f"[dim]Updated: {now.strftime('%Y-%m-%d %H:%M')} {tz_name}[/dim]")

    # Errors
    errors = [r for r in results if r.error]
    if errors:
        console.print("\n[red]Stores with errors:[/red]")
        for r in errors:
            console.print(f"  [red]{r.store_name}:[/red] {r.error}")

    console.print()


def print_history_table(prices: list[dict], days: int) -> None:
    if not prices:
        console.print("[red]No history found.[/red]")
        return

    table = Table(header_style="bold cyan")
    table.add_column("Date")
    table.add_column("Store")
    table.add_column("Product")
    table.add_column("Price/kg", justify="right")
    table.add_column("Price", justify="right")
    table.add_column("Sale")

    for p in prices[:50]:
        scraped = p.get("scraped_at", "")[:16]
        store = p.get("store_name", p.get("store_id", ""))
        name = p.get("product_name", "")[:40]
        up = format_unit_price(p.get("unit_price"))
        total = format_price(p.get("price_cad", 0))
        sale = "[green]YES[/green]" if p.get("is_on_sale") else ""

        table.add_row(scraped, store, name, up, total, sale)

    console.print(table)
    console.print(f"[dim]{len(prices)} records (last {days} days)[/dim]")


def print_stores_list(branches: list[dict]) -> None:
    table = Table(header_style="bold cyan")
    table.add_column("Store")
    table.add_column("Branch")
    table.add_column("Address")
    table.add_column("Distance", justify="right")

    for b in branches:
        store = b.get("store_id", "")
        name = b.get("name", "")
        address = b.get("address", "")[:50]
        dist = f"{b.get('distance_km', '?')}km"

        table.add_row(store, name, address, dist)

    console.print(table)
