import json
import sys
from datetime import datetime, timezone

from rich.console import Console
from rich.table import Table

from src.models import Price, ScrapeResult
from src.products import get_product_name_pt

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
                "produto": p.product_slug,
                "nome_produto": p.product_name,
                "loja": r.store_name,
                "filial": p.branch_name,
                "preco_cad": p.price_cad,
                "preco_kg": p.unit_price,
                "tamanho": p.package_size,
                "marca": p.brand,
                "oferta": p.is_on_sale,
                "preco_original": p.original_price,
                "url": p.url,
            })
    json.dump(output, sys.stdout, indent=2, ensure_ascii=False)
    print()


def print_results_table(results: list[ScrapeResult]) -> None:
    all_prices = [p for r in results for p in r.prices]
    products_found: set[str] = {p.product_slug for p in all_prices}

    if not all_prices:
        console.print("\n[red]Nenhum resultado encontrado.[/red]\n")
        return

    now = datetime.now(timezone.utc).astimezone()
    tz_name = now.tzname() or "EST"

    for slug in ["chicken_breast", "picanha", "filet_mignon"]:
        if slug not in products_found:
            continue

        name_pt = get_product_name_pt(slug)
        console.print(f"\n[bold yellow]  {name_pt}[/bold yellow]")

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Pos", style="dim", width=4)
        table.add_column("Loja / Produto", style="white")
        table.add_column("Preco/kg", justify="right")
        table.add_column("Preco", justify="right")
        table.add_column("Oferta", justify="center", width=6)

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

            sale = "[green]SIM[/green]" if p.is_on_sale else ""

            table.add_row(medal, f"{store_display}\n[dim]{product_display}[/dim]", u_price, total, sale)

        console.print(table)

    # Summary line
    console.print()
    console.print(f"[dim]Atualizado: {now.strftime('%d/%m/%Y %H:%M')} {tz_name}[/dim]")

    # Errors
    errors = [r for r in results if r.error]
    if errors:
        console.print("\n[red]Lojas com erro:[/red]")
        for r in errors:
            console.print(f"  [red]{r.store_name}:[/red] {r.error}")

    console.print()


def print_history_table(prices: list[dict], days: int) -> None:
    if not prices:
        console.print("[red]Nenhum historico encontrado.[/red]")
        return

    table = Table(header_style="bold cyan")
    table.add_column("Data")
    table.add_column("Loja")
    table.add_column("Produto")
    table.add_column("Preco/kg", justify="right")
    table.add_column("Preco", justify="right")
    table.add_column("Oferta")

    for p in prices[:50]:
        scraped = p.get("scraped_at", "")[:16]
        store = p.get("store_name", p.get("store_id", ""))
        name = p.get("product_name", "")[:40]
        up = format_unit_price(p.get("unit_price"))
        total = format_price(p.get("price_cad", 0))
        sale = "[green]SIM[/green]" if p.get("is_on_sale") else ""

        table.add_row(scraped, store, name, up, total, sale)

    console.print(table)
    console.print(f"[dim]{len(prices)} registros (ultimos {days} dias)[/dim]")


def print_stores_list(branches: list[dict]) -> None:
    table = Table(header_style="bold cyan")
    table.add_column("Loja")
    table.add_column("Filial")
    table.add_column("Endereco")
    table.add_column("Distancia", justify="right")

    for b in branches:
        store = b.get("store_id", "")
        name = b.get("name", "")
        address = b.get("address", "")[:50]
        dist = f"{b.get('distance_km', '?')}km"

        table.add_row(store, name, address, dist)

    console.print(table)
