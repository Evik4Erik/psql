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


def _handle_list_stocks(query: str, args: tuple):
    conn = get_conn()
    table = Table(title="Stocks", show_header=True, header_style="bold cyan")

    table.add_column("ID", style="dim", width=6, justify="right")
    table.add_column("warehouse_id", style="green", min_width=20)
    table.add_column("product_id", style="yellow", min_width=30)
    table.add_column("quantity", style="magenta", min_width=15)

    with conn.cursor(row_factory=class_row(Stock)) as cur:
        cur.execute(query, args)
        stocks: list[Stock] = cur.fetchall()

    for stock in stocks:
        table.add_row(
            str(stock.id),
            str(stock.warehouse_id),
            str(stock.product_id),
            str(stock.quantity)
        )
    console.print(table)

@dataclass
class Stock_w_view:
    id: int
    product_name: str
    common_quantity: int
    reserved: int
    available: int

@command("view warehouse stocks", "список всех stocks на складе", CATEGORY_ORDERS, [ROLE_INVENTORY_MANAGER])
def list_warehouse_stock() -> None:
    warehouse_id = choice(
        message="Склад: ",
        options=get_list_warehouses(),
        default="",
    )

    conn = get_conn()
    table = Table(title=f"Warehouse stocks #id {warehouse_id}", show_header=True, header_style="bold cyan")

    table.add_column("ID", style="dim", width=6, justify="right")
    table.add_column("product_name", style="dim", min_width=20, justify="right")
    table.add_column("common_quantity", style="green", min_width=6)
    table.add_column("reserved", style="yellow", min_width=6)
    table.add_column("available", style="magenta", min_width=6)

    with conn.cursor(row_factory=class_row(Stock_w_view)) as cur:
        cur.execute("""
                    WITH c_quantity AS (
                        SELECT quantity AS common_quantity, product_id
                        FROM inventory.stocks  
                        WHERE warehouse_id = %s
                    ),
					res AS (
                        SELECT quantity AS reserved, product_id 
                        FROM inventory.reserves
                        WHERE warehouse_id = %s
                    )
                    
                    SELECT p.id, p.name AS product_name, 
                    COALESCE(common_quantity, 0) AS common_quantity,
                    COALESCE(reserved, 0) AS reserved, 
                    COALESCE(common_quantity, 0) - COALESCE(reserved, 0) AS available 
                    FROM catalog.products p
					LEFT JOIN c_quantity c ON p.id = c.product_id
					LEFT JOIN res r ON p.id = r.product_id
					ORDER BY p.id """, (warehouse_id, warehouse_id))
        stocks: list[Stock_w_view] = cur.fetchall()

    for stock in stocks:
        table.add_row(
            str(stock.id),
            str(stock.product_name),
            str(stock.common_quantity),
            str(stock.reserved),
            str(stock.available)
        )
    console.print(table)

@dataclass
class Stock_p_view:
    id: int
    city: str
    address: str
    is_central: str
    common_quantity: int
    reserved: int
    available: int

@command("view product stocks", "список всех stocks товара", CATEGORY_ORDERS, [ROLE_INVENTORY_MANAGER])
def list_warehouse_stock() -> None:
    product_name: str = prompt(
        "Product: ",
        validator=handlers.products._get_product_validator(),
        completer=handlers.products._get_product_completer(),
    ).strip()
    product_id = handlers.products._get_product_id_by_name(product_name)

    conn = get_conn()
    table = Table(title=f"Product stocks {product_name}", show_header=True, header_style="bold cyan")

    table.add_column("ID", style="dim", width=6, justify="right")
    table.add_column("city", style="dim", min_width=20, justify="right")
    table.add_column("address", style="dim", min_width=20, justify="right")
    table.add_column("is_central", style="dim", min_width=20, justify="right")
    table.add_column("common_quantity", style="green", min_width=6)
    table.add_column("reserved", style="yellow", min_width=6)
    table.add_column("available", style="magenta", min_width=6)

    with conn.cursor(row_factory=class_row(Stock_p_view)) as cur:
        cur.execute("""WITH common_quantity AS 
                            (
                                SELECT quantity, warehouse_id 
                                FROM inventory.stocks 
                                WHERE product_id = %s
                            ),
                            reserves AS 
                            (
                                SELECT quantity, warehouse_id 
                                FROM inventory.reserves 
                                WHERE product_id = %s
                            )


                        SELECT w.id, cities.city, w.address, w.is_central, 
                        COALESCE(c.quantity, 0) AS common_quantity,   
                        COALESCE(r.quantity, 0) AS reserved,
                        COALESCE(c.quantity, 0) - COALESCE(r.quantity, 0) AS available
                        FROM catalog.warehouses w
                        LEFT JOIN common_quantity c ON w.id = c.warehouse_id
                        LEFT JOIN reserves r ON w.id = r.warehouse_id
                        LEFT JOIN catalog.cities cities ON w.city_id = cities.id""", (product_id, product_id))
        stocks: list[Stock_p_view] = cur.fetchall()

    for stock in stocks:
        table.add_row(
            str(stock.id),
            str(stock.city),
            str(stock.address),
            str(stock.is_central),
            str(stock.common_quantity),
            str(stock.reserved),
            str(stock.available)
        )
    console.print(table)


@command("list stocks", "список всех stocks", CATEGORY_ORDERS, [ROLE_INVENTORY_MANAGER])
def list_stocks() -> None:
    conn = get_conn()
    table = Table(title="Stocks", show_header=True, header_style="bold cyan")

    table.add_column("ID", style="dim", width=6, justify="right")
    table.add_column("warehouse_id", style="green", min_width=20)
    table.add_column("product_id", style="yellow", min_width=30)
    table.add_column("quantity", style="magenta", min_width=15)

    with conn.cursor(row_factory=class_row(Stock)) as cur:
        cur.execute("SELECT warehouse_id, product_id, quantity FROM inventory.stocks")
        stocks: list[Stock] = cur.fetchall()

    for stock in stocks:
        table.add_row(
            str(stock.id),
            str(stock.warehouse_id),
            str(stock.product_id),
            str(stock.quantity)
        )
    console.print(table)

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
        cur.execute(
            "SELECT warehouse_id, product_id, quantity "
            "FROM inventory.stocks "
            "WHERE warehouse_id = %s AND product_id = %s",
            (warehouse_id, product_id))
        stock: Stock | None = cur.fetchone()

    if stock is None:
        render_error(f"Stock {product_name} в {warehouse_id} не найден")
        return

    _render_stock(stock)
