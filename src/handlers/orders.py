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
    created_by: str


@dataclass
class Order_item:
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
    table.add_row("Created_by", str(order.created_by))

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

    conn = get_conn()
    with conn.cursor(row_factory=class_row(Order_item)) as cur:
        cur.execute("SELECT * FROM sales.order_items WHERE order_id = %s", (order.id,))
        order_items: list[Order_item] = cur.fetchall()

    for items in order_items:
        table.add_row(
            str(items.order_id),
            str(items.product_id),
            str(items.quantity),
            str(items.price),
        )
    console.print(table)


def _handle_list_orders(query: str):
    conn = get_conn()
    table = Table(title="Orders", show_header=True, header_style="bold cyan")

    table.add_column("ID", style="dim", width=6, justify="right")
    table.add_column("Status", style="green", min_width=20)
    table.add_column("Total amount", style="yellow", min_width=30)
    table.add_column("Created at", style="magenta", min_width=15)
    table.add_column("Warehouse", style="blue", min_width=20)
    table.add_column("Created by", style="red", min_width=20)

    with conn.cursor(row_factory=class_row(Order)) as cur:
        cur.execute(query)
        orders: list[Order] = cur.fetchall()

    for order in orders:
        table.add_row(
            str(order.id),
            order.status,
            str(order.total_amount),
            str(order.created_at),
            str(order.warehouse_id),
            str(order.created_by),
        )
    console.print(table)

@command("list orders", "список всех orders", CATEGORY_ORDERS, [ROLE_SALES_MANAGER, ROLE_INVENTORY_MANAGER])
def list_orders() -> None:
    _handle_list_orders("SELECT o.id, o.status, o.total_amount, o.created_at, c.city as warehouse_id, u.username as created_by " \
                        "FROM sales.orders o " \
                        "LEFT JOIN auth.users u ON o.created_by = u.id " \
                        "LEFT JOIN catalog.warehouses w ON o.warehouse_id = w.id " \
                        "LEFT JOIN catalog.cities c ON w.city = c.id")

@command("list orders new", "список всех orders new", CATEGORY_ORDERS, [ROLE_SALES_MANAGER, ROLE_INVENTORY_MANAGER])
def list_orders_new() -> None:
    _handle_list_orders("SELECT o.id, o.status, o.total_amount, o.created_at, c.city as warehouse_id, u.username as created_by " \
                    "FROM sales.orders o " \
                    "LEFT JOIN auth.users u ON o.created_by = u.id " \
                    "LEFT JOIN catalog.warehouses w ON o.warehouse_id = w.id " \
                    "LEFT JOIN catalog.cities c ON w.city = c.id " \
                    "WHERE o.status = 'new'")
    
@command("list orders processing", "список всех orders processing", CATEGORY_ORDERS, [ROLE_SALES_MANAGER, ROLE_INVENTORY_MANAGER])
def list_orders_processing() -> None:
    _handle_list_orders("SELECT o.id, o.status, o.total_amount, o.created_at, c.city as warehouse_id, u.username as created_by " \
                    "FROM sales.orders o " \
                    "LEFT JOIN auth.users u ON o.created_by = u.id " \
                    "LEFT JOIN catalog.warehouses w ON o.warehouse_id = w.id " \
                    "LEFT JOIN catalog.cities c ON w.city = c.id " \
                    "WHERE o.status = 'processing'")
    
@command("list orders my", "список всех orders my", CATEGORY_ORDERS, [ROLE_SALES_MANAGER, ROLE_INVENTORY_MANAGER])
def list_orders_my() -> None:
    _handle_list_orders("SELECT o.id, o.status, o.total_amount, o.created_at, c.city as warehouse_id, u.username as created_by " \
                    "FROM sales.orders o " \
                    "LEFT JOIN auth.users u ON o.created_by = u.id " \
                    "LEFT JOIN catalog.warehouses w ON o.warehouse_id = w.id " \
                    "LEFT JOIN catalog.cities c ON w.city = c.id " \
                    "WHERE o.created_by = %s", (auth._USER.id,))

def _render_order_item(item: Order_item):
    table = Table(show_header=False, box=None, padding=(0, 2))

    table.add_column("Поле", style="bold cyan", width=15)
    table.add_column("Значение", style="white")

    table.add_row("Order_ID", str(item.order_id))
    table.add_row("Product_id", str(item.product_id))
    table.add_row("Quantity", str(item.quantity))
    table.add_row("Price", str(item.price))

    panel = Panel(
        table,
        expand=False,
        title=f"[bold green]Item Order #{item.order_id} product #{item.product_id}[/bold green]",
        border_style="green",
    )

    console.print(panel)

@command("show order", "информация о заказе", CATEGORY_ORDERS, [ROLE_SALES_MANAGER])
def show_order(_id: str) -> None:
    conn = get_conn()
    with conn.cursor(row_factory=class_row(Order)) as cur:
        cur.execute("SELECT * FROM sales.orders WHERE id = %s", (_id,))
        order: Order | None = cur.fetchone()

    if order is None:
        render_error(f"Заказ с ID {_id} не найден")
        return

    _render_order(order)


@command("add order", "добавить заказ (интерактивно)", CATEGORY_ORDERS, [ROLE_SALES_MANAGER])
def add_order() -> None:
    conn = get_conn()
    status = prompt("Статус: ", validator=states_validator, completer=states_completer, default='unpublished').strip()
    total_amount: Decimal = 0
    created_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")  # Output: 2026-06-11T12:40:00.123456+00:00
    warehouse_id = choice(
        message="Склад: ",
        options=get_list_warehouses(),
        default="",
    )

    created_by: int = auth._USER.id
    
    conn.execute(
        "INSERT INTO sales.orders (status, total_amount, created_at, warehouse_id, created_by) VALUES (%s, %s, %s, %s, %s)",
        (status, total_amount, created_at, warehouse_id, created_by),
    )

    console.print(f"[green]Заказ добавлен [/green]")


@command("edit order", "редактировать заказ", CATEGORY_ORDERS, [ROLE_SALES_MANAGER])
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
        options=get_list_warehouses(),
        default="",
    )

    conn.execute(
        """UPDATE sales.orders SET  total_amount = %s, warehouse_id = %s
        WHERE id = %s""",
        (total_amount, warehouse_id, _id),
    )

    console.print(f"[green]Заказ {order.id} обновлен [/green]")


@command("delete order", "удалить заказ", CATEGORY_ORDERS, [ROLE_SALES_MANAGER])
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
        conn.execute("DELETE FROM sales.order_items WHERE order_id = %s", (_id,))
        conn.execute("DELETE FROM sales.orders WHERE id = %s", (_id,))
        console.print(f"[green]Заказ {order.id} удален [/green]")


@command("publish order", "опубликовать заказ", CATEGORY_ORDERS, [ROLE_SALES_MANAGER])
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


@command("add order_item", "добавить позицию в заказ", CATEGORY_ORDERS, [ROLE_SALES_MANAGER])
def add_order_item(order_id: str) -> None:
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT status FROM sales.orders WHERE id = %s", (order_id,))
        status: str | None = cur.fetchone()

    if status is None:
        render_error(f"Order с ID {order_id} не найден")
        return

    status = status[0]
    if status != 'unpublished':
        console.print(f"[yellow]Позиция в заказе {order_id} не может быть добавлена [/yellow]")
        return
        
    products.products_list.clear()

    products_tmp: dictionary = get_list_products()

    for key, value in products_tmp.items():
        products.products_list.append(value)

    enter_product = True

    while enter_product:
        product: str = prompt(
            "Product: ",
            validator=products.products_validator,
            completer=products.products_completer,
        ).strip()

        product_id = next((k for k, v in products_tmp.items() if v == product))

        price = Decimal()

        with conn.cursor() as cur:
            cur.execute("SELECT price FROM catalog.products WHERE id = %s", (product_id,))
            row = cur.fetchone()
            if row:
                price = row[0]

        quantity = prompt("Количество: ", validator=PositiveIntValidator()).strip()

        conn.execute(
            "INSERT INTO sales.order_items (price, quantity, product_id, order_id) VALUES (%s, %s, %s, %s)",
            (price, quantity, product_id, order_id),
        )

        console.print(f"[green]Позиция добавлена [/green]")

        answer = prompt("Wanna continue adding items? (y/n, д/н): ", validator=YesNoValidator())
        enter_product = YesNoValidator.is_yes(answer)

    recalc_order(order_id)

def recalc_order(order_id: str) -> None:
    conn = get_conn()
    total_amount: Decimal = 0
    with conn.cursor() as cur:
        cur.execute("SELECT price, quantity FROM sales.order_items WHERE order_id = %s", (order_id,))
        rows = cur.fetchall()
        for row in rows:
            total_amount += int(row[0]) * Decimal(row[1])

        conn.execute(
            """UPDATE sales.orders SET total_amount = %s WHERE id = %s""", (total_amount, order_id),
        )

@command("edit order_item", "изменить позицию в заказе", CATEGORY_ORDERS, [ROLE_SALES_MANAGER])
def edit_order_item(order_id: str, product_id: str) -> None:  
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT status FROM sales.orders WHERE id = %s", (order_id,))
        status: str | None = cur.fetchone()

    if status is None:
        render_error(f"Order с ID {order_id} не найден")
        return
    
    status = status[0]
    if status != 'unpublished':
        console.print(f"[yellow]Позиция в заказе {order_id} не может быть изменена [/yellow]")
        return
    
    with conn.cursor(row_factory=class_row(Order_item)) as cur:
        cur.execute("SELECT * FROM sales.order_items WHERE order_id = %s AND product_id = %s", 
                    (order_id, product_id))
        item: Order_item | None = cur.fetchone()

    if item is None:
        render_error(f"Позиция с order ID {order_id} product id {product_id} не найдена")
        return

    _render_order_item(item)

    # if the price in the catalog has changed
    price: Decimal = 0

    with conn.cursor() as cur:
        cur.execute("SELECT price FROM catalog.products WHERE id = %s", (product_id,))
        row = cur.fetchone()
        if(row):
            price = row[0]

    quantity = prompt("Количество: ", default=str(item.quantity), validator=PositiveIntValidator()).strip()

    conn.execute(
        "UPDATE sales.order_items SET price = %s, quantity = %s WHERE order_id = %s AND product_id = %s",
        (price, quantity, order_id, product_id, ),
    )
    
    console.print(f"[green]Позиция edited [/green]")

    recalc_order(order_id)

@command("delete order_item", "добавить позицию в заказ", CATEGORY_ORDERS, [ROLE_SALES_MANAGER])
def delete_order_item(order_id: str, product_id: str) -> None:  
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT status FROM sales.orders WHERE id = %s", (order_id,))
        status: str | None = cur.fetchone()

    if status is None:
        render_error(f"Order с ID {order_id} не найден")
        return

    status = status[0]
    if status != 'unpublished':
        console.print(f"[yellow]Позиция в заказе {order_id} не может быть удалена [/yellow]")
        return
    
    with conn.cursor(row_factory=class_row(Order_item)) as cur:
        cur.execute("SELECT * FROM sales.order_items WHERE order_id = %s AND product_id = %s", 
                    (order_id, product_id))
        item: Order_item | None = cur.fetchone()

    if item is None:
        render_error(f"Позиция с order ID {order_id} product id {product_id} не найдена")
        return
    
    _render_order_item(item)

    answer = prompt("Вы уверены? (y/n, д/н): ", validator=YesNoValidator())

    if YesNoValidator.is_yes(answer):
        conn.execute("DELETE FROM sales.order_items WHERE order_id = %s AND product_id = %s", (order_id, product_id))
        recalc_order(order_id)

@command("mark order processing", "изменить статус заказа to processing", CATEGORY_ORDERS, [ROLE_INVENTORY_MANAGER])
def mark_order_processing(_id: str) -> None:
    conn = get_conn()
    with conn.cursor(row_factory=class_row(Order)) as cur:
        cur.execute("SELECT * FROM sales.orders WHERE id = %s", (_id,))
        order: Order | None = cur.fetchone()

    if order is None:
        render_error(f"Заказ с ID {_id} не найден")
        return

    answer = prompt("Вы уверены? (y/n, д/н): ", validator=YesNoValidator())

    if YesNoValidator.is_yes(answer):
        conn.execute("""UPDATE sales.orders SET  status = 'processing' WHERE id = %s""", (_id,))
        console.print(f"[green]Статус заказа {order.id} изменен на 'processing' [/green]")

