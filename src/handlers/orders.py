from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime, timezone

from rich.panel import Panel
from rich.table import Table
from psycopg.rows import class_row
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.shortcuts import choice

from commands import command, CATEGORY_ORDERS
from console import console, render_error
from db import get_conn
from validators import PriceValidator, NonEmptyValidator, YesNoValidator, ChoiceValidator, PositiveIntValidator

from .warehouses import get_list_warehouses
from .products import get_list_products


states = [
    'unpublished',
    'new', 
    'processing', 
    'pending', 
    'packing', 
    'shipped'
]

states_completer = WordCompleter(states, ignore_case=True, sentence=True)
states_validator = ChoiceValidator(
    states, message="Статус должен быть из списка. Используйте Tab для автодополнения."
)

@dataclass
class Order:
    id: int
    status: str
    total_amount: Decimal
    created_at: datetime
    warehouse_id: int

@dataclass
class Order_item:
    id: int
    price: Decimal
    quantity: int
    product_id: int
    order_id: int

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

    table = Table(title="Order_items", show_header=True, header_style="bold cyan")

    table.add_column("ID", style="dim", width=6, justify="right")
    table.add_column("Price", style="green", min_width=20)
    table.add_column("Quantity", style="yellow", min_width=30)
    table.add_column("Product_id", style="magenta", min_width=15)
    table.add_column("Order_id", style="blue", min_width=20)

    conn = get_conn()
    with conn.cursor(row_factory=class_row(Order_item)) as cur:
        cur.execute("SELECT * FROM sales.order_items WHERE order_id = %s", (order.id,))
        order_items: list[Order_item] = cur.fetchall()

    for items in order_items:
        table.add_row(
            str(items.id),
            str(items.price),
            str(items.quantity),
            str(items.product_id),
            str(items.order_id),
        )
    console.print(table)

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
        cur.execute("SELECT * FROM sales.orders")
        orders: list[Order] = cur.fetchall()

    for order in orders:
        table.add_row(
            str(order.id),
            order.status,
            str(order.total_amount),
            str(order.created_at),
            str(order.warehouse_id),
        )
    console.print(table)

@command("show order", "информация о заказе", CATEGORY_ORDERS)
def show_order(_id: str) -> None:
    conn = get_conn()
    with conn.cursor(row_factory=class_row(Order)) as cur:
        cur.execute("SELECT * FROM sales.orders WHERE id = %s", (_id,))
        order: Order | None = cur.fetchone()

    if order is None:
        render_error(f"Заказ с ID {_id} не найден")
        return

    _render_order(order)


@command("add order", "добавить заказ (интерактивно)", CATEGORY_ORDERS)
def add_order() -> None:
    conn = get_conn()
    status = prompt("Статус: ", validator=states_validator, completer=states_completer, default='unpublished').strip()
    total_amount = prompt("Стоимость: ", validator=PriceValidator()).strip()
    created_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S") # Output: 2026-06-11T12:40:00.123456+00:00
    #prompt("Дата создания: ", validator=DateValidator()).strip() # TO DO date validator
    warehouse_id = choice(
        message="Склад: ",
        options= get_list_warehouses(),
        default="",
    )
    conn.execute(
        "INSERT INTO sales.orders (status, total_amount, created_at, warehouse_id) VALUES (%s, %s, %s, %s)",
        (status, total_amount, created_at, warehouse_id),
    )
    
    console.print(f"[green]Заказ добавлен [/green]")


@command("edit order", "редактировать заказ", CATEGORY_ORDERS)
def edit_order(_id: str) -> None:
    conn = get_conn()
    with conn.cursor(row_factory=class_row(Order)) as cur:
        cur.execute("SELECT * FROM sales.orders WHERE id = %s", (_id,))
        order: Order | None = cur.fetchone()

    if order is None:
        render_error(f"Заказ с ID {_id} не найден")
        return
    
    if order.status != 'unpublished':
        console.print(f"[yellow]Заказ {order.id} не может быть отредактирован [/yellow]")
        return

    total_amount = prompt("Стоимость: ", validator=PriceValidator()).strip()
    warehouse_id = choice(
        message="Склад: ",
        options= get_list_warehouses(),
        default="",
    )

    conn.execute(
        """UPDATE sales.orders SET  total_amount = %s, warehouse_id = %s
        WHERE id = %s""",
        (total_amount, warehouse_id, _id),
    )

    console.print(f"[green]Заказ {order.id} обновлен [/green]")


@command("delete order", "удалить заказ", CATEGORY_ORDERS)
def delete_order(_id: str) -> None:
    conn = get_conn()
    with conn.cursor(row_factory=class_row(Order)) as cur:
        cur.execute("SELECT * FROM sales.orders WHERE id = %s", (_id,))
        order: Order | None = cur.fetchone()

    if order is None:
        render_error(f"Заказ с ID {_id} не найден")
        return

    _render_order(order)

    if order.status != 'unpublished':
        console.print(f"[yellow]Заказ {order.id} не может быть удален [/yellow]")
        return

    answer = prompt("Вы уверены? (y/n, д/н): ", validator=YesNoValidator())

    if YesNoValidator.is_yes(answer):
        conn.execute("DELETE FROM sales.orders WHERE id = %s", (_id,))
        console.print(f"[green]Заказ {order.id} удален [/green]")


@command("publish order", "опубликовать заказ", CATEGORY_ORDERS)
def publish_order(_id: str) -> None:
    conn = get_conn()
    with conn.cursor(row_factory=class_row(Order)) as cur:
        cur.execute("SELECT * FROM sales.orders WHERE id = %s", (_id,))
        order: Order | None = cur.fetchone()

    if order is None:
        render_error(f"Заказ с ID {_id} не найден")
        return
        
    answer = prompt("Вы уверены? (y/n, д/н): ", validator=YesNoValidator())

    if YesNoValidator.is_yes(answer):
        conn.execute(
            """UPDATE sales.orders SET  status = %s WHERE id = %s""", ('new', _id),
        )
        console.print(f"[green]Заказ {order.id} опубликован [/green]")

@command("add order_item", "добавить позицию в заказ", CATEGORY_ORDERS)
def add_order_item(order_id: str) -> None:  
    conn = get_conn()

    product_id = choice(
        message="Товар: ",
        options= get_list_products(),
        default="",
    )

    price = Decimal()

    with conn.cursor() as cur:
        cur.execute("SELECT price FROM catalog.products WHERE id = %s", (product_id,))
        row = cur.fetchone()
        if(row):
            price = row[0]

    #price = prompt("Стоимость: ", validator=PriceValidator()).strip()
    quantity = prompt("Количество: ", validator=PositiveIntValidator()).strip()

    conn.execute(
        "INSERT INTO sales.order_items (price, quantity, product_id, order_id) VALUES (%s, %s, %s, %s)",
        (price, quantity, product_id, order_id),
    )
    
    console.print(f"[green]Позиция добавлена [/green]")

    recalc_order(order_id)

def recalc_order(order_id: str) -> None: 
    conn = get_conn()
    total_amount = 0.
    with conn.cursor() as cur:
        cur.execute("SELECT price, quantity FROM sales.order_items WHERE order_id = %s", (order_id,))
        rows = cur.fetchall()
        for row in rows:
            total_amount += int(row[0]) * Decimal(row[1])

        conn.execute(
            """UPDATE sales.orders SET total_amount = %s WHERE id = %s""", (total_amount, order_id),
        )
