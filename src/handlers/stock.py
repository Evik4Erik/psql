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

from auth import ROLE_INVENTORY_MANAGER
import auth
import handlers.products

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
        title=f"[bold green]stock #{stock.id}[/bold green]",
        border_style="green",
    )

    console.print(panel)

def _handle_list_stocks(query: str):
    conn = get_conn()
    table = Table(title="Stocks", show_header=True, header_style="bold cyan")

    table.add_column("ID", style="dim", width=6, justify="right")
    table.add_column("warehouse_id", style="green", min_width=20)
    table.add_column("product_id", style="yellow", min_width=30)
    table.add_column("quantity", style="magenta", min_width=15)

    with conn.cursor(row_factory=class_row(Stock)) as cur:
        cur.execute(query)
        stocks: list[Stock] = cur.fetchall()

    for stock in stocks:
        table.add_row(
            str(stock.id),
            str(stock.warehouse_id),
            str(stock.product_id),
            str(stock.quantity)
        )
    console.print(table)

@command("view warehouse stocks", "список всех stocks на складе", CATEGORY_ORDERS, [ROLE_INVENTORY_MANAGER])
def list_warehouse_stock() -> None:
    warehouse_id = choice(
            message="Склад: ",
            options=get_list_warehouses(),
            default="",
        )
    _handle_list_stocks(f"SELECT warehouse_id, product_id, quantity FROM inventory.stocks WHERE warehouse_id = {warehouse_id}")

@command("view product stocks", "список всех stocks товара", CATEGORY_ORDERS, [ROLE_INVENTORY_MANAGER])
def list_warehouse_stock() -> None:
    product_name: str = prompt(
            "Product: ",
            validator=handlers.products._get_product_validator(),
            completer=handlers.products._get_product_completer(),
        ).strip()
    product_id = handlers.products._get_product_id_by_name(product_name)
    _handle_list_stocks(f"SELECT warehouse_id, product_id, quantity FROM inventory.stocks WHERE product_id = {product_id}")

@command("list stocks", "список всех stocks", CATEGORY_ORDERS, [ROLE_INVENTORY_MANAGER])
def list_stocks() -> None:
    _handle_list_stocks("SELECT warehouse_id, product_id, quantity FROM inventory.stocks")

@command("show stock", "информация о stock", CATEGORY_ORDERS, [ROLE_INVENTORY_MANAGER])
def show_stock() -> None:
    conn = get_conn()
    warehouse_id = choice(
            message="Склад: ",
            options=get_list_warehouses(),
            default="",
    )
    product_name: str = prompt(
            "Product: ",
            validator=handlers.products._get_product_validator(),
            completer=handlers.products._get_product_completer(),
    )
    product_id = handlers.products._get_product_id_by_name(product_name)
    with conn.cursor(row_factory=class_row(Stock)) as cur:
        cur.execute("SELECT warehouse_id, product_id, quantity FROM inventory.stocks WHERE warehouse_id = %s AND product_id = %s", (warehouse_id,product_id))
        stock: Stock | None = cur.fetchone()

    if stock is None:
        render_error(f"Stock {product_name} в {warehouse_id} не найден")
        return

    _render_stock(stock)


@command("add stock", "добавить сток", CATEGORY_ORDERS, [ROLE_INVENTORY_MANAGER])
def add_stock() -> None:
    conn = get_conn()

    enter_product = True

    while enter_product:
        warehouse_id = choice(
            message="Склад: ",
            options=get_list_warehouses(),
            default="",
        )
            
        product_name: str = prompt(
            "Product: ",
            validator=handlers.products._get_product_validator(),
            completer=handlers.products._get_product_completer(),
        ).strip()

        product_id = handlers.products._get_product_id_by_name(product_name) 

        quantity = prompt("Количество: ", validator=PositiveIntValidator()).strip() 
    
        conn.execute(
            "INSERT INTO inventory.stocks (warehouse_id, product_id, quantity) VALUES (%s, %s, %s)",
            (warehouse_id, product_id, quantity),
        )

    console.print(f"[green]Stok добавлен [/green]")
