from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime, timezone

from rich.panel import Panel
from rich.table import Table
from psycopg.rows import class_row
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.shortcuts import choice
from sqlalchemy.dialects.oracle import dictionary

from commands import command, CATEGORY_ORDERS
from console import console, render_error
from db import get_conn
from validators import PriceValidator, NonEmptyValidator, YesNoValidator, ChoiceValidator, PositiveIntValidator

from .warehouses import get_list_warehouses
from .products import get_list_products

from auth import _USER, ROLE_CATALOG_MANAGER, ROLE_SALES_MANAGER, ROLE_INVENTORY_MANAGER
import auth


@dataclass
class Stock:
    id: int
    warehouse_id: int
    product_id: int
    quantity: int


def _render_stock(stock: Stock):  # pylint: disable=unused-argument
    table = Table(show_header=False, box=None, padding=(0, 2))

    table.add_column("Поле", style="bold cyan", width=15)
    table.add_column("Значение", style="white")

    table.add_row("ID", str(stock.id))
    table.add_row("Warehouse_id", str(stock.warehouse_id))
    table.add_row("Product_id", str(stock.product_id))
    table.add_row("Quantity", str(stock.quantity))

    panel = Panel(
        table,
        expand=False,
        title=f"[bold green]Order #{order.id}[/bold green]",
        border_style="green",
    )

    console.print(panel)

    table = Table(title="Order_items", show_header=True, header_style="bold cyan")

    table.add_column("Order_id", style="blue", min_width=20)
    table.add_column("Product_id", style="magenta", min_width=15)
    table.add_column("Quantity", style="yellow", min_width=30)
    table.add_column("Price", style="green", min_width=20)

@command("add stock", "добавить сток", CATEGORY_ORDERS, [ROLE_INVENTORY_MANAGER])
def add_stock(_id: str) -> None:
