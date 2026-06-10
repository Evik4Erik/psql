from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime

from rich.panel import Panel
from rich.table import Table
from psycopg.rows import class_row
from prompt_toolkit import prompt

from commands import command, CATEGORY_ORDERS
from console import console, render_error
from db import get_conn
from validators import PriceValidator, NonEmptyValidator, YesNoValidator


@dataclass
class Order:
    id: int
    status: str
    total_amount: Decimal
    created_at: datetime
    warehouse_id: int

def _render_order(order: Order):  # pylint: disable=unused-argument
    table = Table(show_header=False, box=None, padding=(0, 2))

    table.add_column("Поле", style="bold cyan", width=15)
    table.add_column("Значение", style="white")

    table.add_row("ID", str(order.id))
    table.add_row("Status", order.status)
    table.add_row("Total amount", str(order.total_amount))
    table.add_row("Created at", str(order.created_at))
    table.add_row("Warehouse", str(order.warehouse_id))

    panel = Panel(
        table,
        expand=False,
        title=f"[bold green]Order #{order.id}[/bold green]",
        border_style="green",
    )

    console.print(panel)

@command("list orders", "список всех orders", CATEGORY_ORDERS)
def list_products() -> None:
    conn = get_conn()
    table = Table(title="Orders", show_header=True, header_style="bold cyan")

    table.add_column("ID", style="dim", width=6, justify="right")
    table.add_column("Status", style="green", min_width=20)
    table.add_column("Total amount", style="yellow", min_width=30)
    table.add_column("Created at", style="magenta", min_width=15)
    table.add_column("Warehouse", style="blue", min_width=20)

    with conn.cursor(row_factory=class_row(Order)) as cur:
        cur.execute("SELECT * FROM catalog.products")
        products: list[Order] = cur.fetchall()

    for product in products:
        table.add_row(
            str(product.id),
            product.status,
            str(product.total_amount),
            str(product.created_at),
            str(product.warehouse_id),
        )
    console.print(table)