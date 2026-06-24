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
    _handle_list_stocks(f"SELECT id, warehouse_id, product_id, quantity FROM inventory.stocks WHERE warehouse_id = {warehouse_id}")

@command("view product stocks", "список всех stocks товара", CATEGORY_ORDERS, [ROLE_INVENTORY_MANAGER])
def list_warehouse_stock() -> None:
    handlers.products.products_list.clear()
    products_tmp: dictionary = get_list_products()

    for key, value in products_tmp.items():
        handlers.products.products_list.append(value)

    product: str = prompt(
            "Product: ",
            validator=handlers.products.products_validator,
            completer=handlers.products.products_completer,
        ).strip()
    product_id = next((k for k, v in products_tmp.items() if v == product))
    _handle_list_stocks(f"SELECT id, warehouse_id, product_id, quantity FROM inventory.stocks WHERE product_id = {product_id}")

@command("list stocks", "список всех stocks", CATEGORY_ORDERS, [ROLE_INVENTORY_MANAGER])
def list_stocks() -> None:
    _handle_list_stocks("SELECT id, warehouse_id, product_id, quantity FROM inventory.stocks")

@command("show stock", "информация о stock", CATEGORY_ORDERS, [ROLE_INVENTORY_MANAGER])
def show_stock(_id: str) -> None:
    conn = get_conn()
    with conn.cursor(row_factory=class_row(Stock)) as cur:
        cur.execute("SELECT id, warehouse_id, product_id, quantity FROM inventory.stocks WHERE id = %s", (_id,))
        stock: Stock | None = cur.fetchone()

    if stock is None:
        render_error(f"Stock с ID {_id} не найден")
        return

    _render_stock(stock)


@command("add stock", "добавить сток", CATEGORY_ORDERS, [ROLE_INVENTORY_MANAGER])
def add_stock() -> None:
    conn = get_conn()

    handlers.products.products_list.clear()
    products_tmp: dictionary = get_list_products()

    for key, value in products_tmp.items():
        handlers.products.products_list.append(value)

    enter_product = True

    while enter_product:
        warehouse_id = choice(
            message="Склад: ",
            options=get_list_warehouses(),
            default="",
        )
            
        product: str = prompt(
            "Product: ",
            validator=handlers.products.products_validator,
            completer=handlers.products.products_completer,
        ).strip()

        product_id = next((k for k, v in products_tmp.items() if v == product))

        quantity = prompt("Количество: ", validator=PositiveIntValidator()).strip() 
    
        conn.execute(
            "INSERT INTO inventory.stocks (warehouse_id, product_id, quantity) VALUES (%s, %s, %s)",
            (warehouse_id, product_id, quantity),
        )

    console.print(f"[green]Заказ добавлен [/green]")

@command("edit stock", "редактировать stock", CATEGORY_ORDERS, [ROLE_INVENTORY_MANAGER])
def edit_stock(_id: str) -> None:
    conn = get_conn()
    with conn.cursor(row_factory=class_row(Stock)) as cur:
        cur.execute("SELECT id, warehouse_id, product_id, quantity FROM catalog.products WHERE id = %s", (_id,))
        stock: Stock | None = cur.fetchone()

    if stock is None:
        render_error(f"Stock с ID {_id} не найден")
        return

    quantity = prompt("Количество: ", default=stock.quantity, validator=PositiveIntValidator()).strip() 

    conn.execute("""UPDATE inventory.stocks SET quantity = %s WHERE id = %s""", (quantity,  _id),)

    console.print(f"[green]Stock {_id} обновлен [/green]")

@command("delete stock", "удалить stock", CATEGORY_ORDERS, [ROLE_INVENTORY_MANAGER])
def delete_stock(_id: str) -> None:
    conn = get_conn()
    with conn.cursor(row_factory=class_row(Stock)) as cur:
        cur.execute("SELECT id, warehouse_id, product_id, quantity FROM inventory.stocks WHERE id = %s", (_id,))
        stock: Stock | None = cur.fetchone()

    if stock is None:
        render_error(f"Товар с ID {_id} не найден")
        return

    _render_stock(stock)

    answer = prompt("Вы уверены? (y/n, д/н): ", validator=YesNoValidator())

    if YesNoValidator.is_yes(answer):
        conn.execute("DELETE FROM catalog.products WHERE id = %s", (_id,))
        console.print(f"[green]Stock of {stock.product_id} from {stock.warehouse_id} удален [/green]")
