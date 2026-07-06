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

from commands import command, CATEGORY_TRANSFERS
from console import console, render_error
from db import get_conn
from validators import PriceValidator, NonEmptyValidator, YesNoValidator, ChoiceValidator, PositiveIntValidator

from .warehouses import get_list_warehouses, get_list_warehouses_for_routes
from .products import get_list_products

from auth import ROLE_INVENTORY_MANAGER
import auth
import handlers.products
import handlers.stock
from handlers.orders import _get_order_list, list_orders

transfer_states = [
    'planned',
    'shipping',
    'in_transit',
    'arrived',
    'received'
]

transfer_item_states = [
    'planned',
    'shipped',
    'received'
]

@dataclass
class Transfer:
    id: int
    order_id: int
    from_warehouse_id: int
    to_warehouse_id: int
    created_at: datetime
    status: str 
    updated_at: datetime
    started_at: datetime
    arriving_at: datetime
    received_at: datetime

@dataclass
class Transfer_item:
    id: int
    transfer_id: int
    product_id: int
    status: str 
    quantity: int
    updated_at: datetime
    requested_by: int
    reserve_id: int


def _render_transfer(transfer: Transfer):  # pylint: disable=unused-argument
    table = Table(show_header=False, box=None, padding=(0, 2))

    table.add_column("Поле", style="bold cyan", width=15)
    table.add_column("Значение", style="white")

    table.add_row("ID", str(transfer.id))
    table.add_row("Order_id", str(transfer.order_id))
    table.add_row("from_warehouse_id", str(transfer.from_warehouse_id))
    table.add_row("to_warehouse_id", str(transfer.to_warehouse_id))
    table.add_row("created_at", str(transfer.created_at))
    table.add_row("status", str(transfer.status))
    table.add_row("updated_at", str(transfer.updated_at))
    table.add_row("started_at", str(transfer.started_at))
    table.add_row("arriving_at", str(transfer.arriving_at))
    table.add_row("received_at", str(transfer.received_at))

    panel = Panel(
        table,
        expand=False,
        title=f"[bold green]transfer #{transfer.id}[/bold green]",
        border_style="green",
    )

    console.print(panel)

    table = Table(title="Transfer_items", show_header=True, header_style="bold cyan")

    table.add_column("Transfer_item_id", style="blue", min_width=20)
    table.add_column("transfer_id", style="magenta", min_width=15)
    table.add_column("Product_id", style="magenta", min_width=15)
    table.add_column("Status", style="yellow", min_width=30)
    table.add_column("Quantity", style="yellow", min_width=30)
    table.add_column("updated_at", style="magenta", min_width=15)
    table.add_column("requested_by", style="magenta", min_width=15)
    table.add_column("reserve_id", style="magenta", min_width=15)

    conn = get_conn()
    with conn.cursor(row_factory=class_row(Transfer_item)) as cur:
        cur.execute("SELECT * FROM inventory.transfer_items WHERE transfer_id = %s", (transfer.id,))
        transfer_items: list[Transfer_item] = cur.fetchall()

    for items in transfer_items:
        table.add_row(
            str(items.id),
            str(items.transfer_id),
            str(items.product_id),
            items.status,
            str(items.quantity),
            str(items.updated_at),
            str(items.requested_by),
            str(items.reserve_id)
        )
    console.print(table)

def _render_transfer_item(item: Transfer_item):
    table = Table(show_header=False, box=None, padding=(0, 2))

    table.add_column("Поле", style="bold cyan", width=15)
    table.add_column("Значение", style="white")

    table.add_row("Transfer_item_id", str(item.id))
    table.add_row("transfer_id", str(item.transfer_id))
    table.add_row("Product_id", str(item.product_id))
    table.add_row("Status", item.status)
    table.add_row("Quantity", str(item.quantity))
    table.add_row("updated_at", str(item.updated_at))
    table.add_row("requested_by", str(item.requested_by))
    table.add_row("reserve_id", str(item.reserve_id))

    panel = Panel(
        table,
        expand=False,
        title=f"[bold green]Item transfer #{item.transfer_id} product #{item.product_id}[/bold green]",
        border_style="green",
    )

    console.print(panel)

@command("list transfer_planned", "список всех запланированных перемещений", CATEGORY_TRANSFERS, [ROLE_INVENTORY_MANAGER])
def list_transfer_planned() -> None:
    conn = get_conn()
    table = Table(title="Перемещения", show_header=True, header_style="bold cyan")

    table.add_column("ID")
    table.add_column("Order_id")
    table.add_column("from_warehouse_id")
    table.add_column("to_warehouse_id")
    table.add_column("created_at")
    table.add_column("status")
    table.add_column("updated_at")
    table.add_column("started_at")
    table.add_column("arriving_at")
    table.add_column("received_at")

    with conn.cursor(row_factory=class_row(Transfer)) as cur:
        cur.execute("""SELECT id, order_id, from_warehouse_id, to_warehouse_id, created_at, status,  
                    updated_at, started_at, arriving_at, received_at  
                    FROM inventory.transfers
                    WHERE status = 'planned'""")
        transfers: list[Transfer] = cur.fetchall()

    for transfer in transfers:
        table.add_row(
                str(transfer.id),
                str(transfer.order_id),
                str(transfer.from_warehouse_id),
                str(transfer.to_warehouse_id),
                str(transfer.created_at),
                str(transfer.status), 
                str(transfer.updated_at),
                str(transfer.started_at),
                str(transfer.arriving_at),
                str(transfer.received_at)
        )
    console.print(table)

@command("start shipping", "отправить перемещение", CATEGORY_TRANSFERS, [ROLE_INVENTORY_MANAGER])
def start_shipping(transfer_id: int) -> None:
    conn = get_conn()

    with conn.cursor(row_factory=class_row(Transfer)) as cur:
        cur.execute("""SELECT id, order_id, from_warehouse_id, to_warehouse_id, created_at, status,  
                    updated_at, started_at, arriving_at, received_at  
                    FROM inventory.transfers WHERE id = %s""", (transfer_id,))
        transfer: Transfer | None = cur.fetchone()

    if transfer is None:
        render_error(f"Трансфер с ID {transfer_id} не найден")
        return

    answer = prompt("Вы уверены? (y/n, д/н): ", validator=YesNoValidator())

    if YesNoValidator.is_yes(answer):
        with conn.transaction():
            conn.execute(
                """ UPDATE inventory.transfers SET status = 'shipping' WHERE id = %s""", 
                (transfer_id,)
            )
            conn.execute(
                """ UPDATE inventory.transfer_items SET status = 'shipping' WHERE transfer_id = %s""", 
                (transfer_id,)
            )

        console.print(f"[green]Статус перемещения {transfer.id} изменен на 'shipping' [/green]")


@command("add transfer_item", "добавить позицию в перемещение", CATEGORY_TRANSFERS, [ROLE_INVENTORY_MANAGER])
def add_transfer_item() -> None:
    from_warehouse_id = choice(
        message="Склад: ",
        options=get_list_warehouses_for_routes("from"),
        default="",
    )

    to_warehouse_id = choice(
        message="Склад: ",
        options=get_list_warehouses_for_routes("to"),
        default="",
    )

    conn = get_conn()

    with conn.cursor() as cur:
        cur.execute("SELECT id FROM inventory.transfers " \
        "WHERE status = 'planned' AND from_warehouse_id = %s AND to_warehouse_id = %s", 
        (from_warehouse_id, to_warehouse_id))
        row: int | None = cur.fetchone()

    status = 'planned'
    requested_by = auth.auth_user().id

    if(row is not None ):
        console.print(f"[yellow]Плановый трансфер из {from_warehouse_id} в {to_warehouse_id} уже существует[/yellow]")
        transfer_id = row[0]
    else:
        list_orders()
        orders = _get_order_list()
        order_id = prompt(
            message="Заказ: ",
            validator=ChoiceValidator(orders, message="Заказ должен быть из списка. Tab для автодополнения."),
            completer=WordCompleter(orders, ignore_case=True, sentence=True),
        )

        created_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S") 
        
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO inventory.transfers "
                    "(order_id, from_warehouse_id, to_warehouse_id, status, created_at) " \
                    "VALUES (%s, %s, %s, %s, %s) "
                    "RETURNING id",
                    (order_id, from_warehouse_id, to_warehouse_id, status, created_at),
                )
                transfer_id: int = cur.fetchone()[0]
        
    enter_product = True

    while enter_product:
        stocks = handlers.stock.get_stocks_list(from_warehouse_id)

        if len(stocks) == 0:
            render_error(f"На складе {from_warehouse_id} отсутствует остаток по всем продуктам, выберете другой склад")
            return;

        product_name: str = prompt(
            "Product: ",
            validator = ChoiceValidator(stocks, message="Используйте Tab для автодополнения."),
            completer = WordCompleter(stocks, ignore_case=True, sentence=True),
        ).strip()

        product_id = handlers.products._get_product_id_by_name(product_name.split()[0])
        with conn.cursor() as cur:
            cur.execute("""SELECT quantity FROM inventory.stocks WHERE warehouse_id = %s AND product_id = %s""", 
            (from_warehouse_id, product_id))
            row: int = cur.fetchone()
            prev_quantity: int = row[0]

            if prev_quantity == 0:
                console.print(f"[red]Остаток нулевой, выберите другую позицию[/red]")
                answer = prompt("Хотите выбрать другую позицию? (y/n, д/н): ", validator=YesNoValidator())
                enter_product = YesNoValidator.is_yes(answer)
                continue
           
        quantity: str = prompt("Количество: ", validator=PositiveIntValidator(max_val=prev_quantity + 1), default=str(prev_quantity))
        updated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")  # Output: 2026-06-11T12:40:00.123456+00:00
        
        reserve_id = None

        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute("""SELECT quantity FROM inventory.stocks WHERE warehouse_id = %s AND product_id = %s FRO UPDATE""", 
                (from_warehouse_id, product_id))
                row: int = cur.fetchone()
                prev_quantity: int = row[0]

            with conn.cursor() as cur:
                cur.execute("SELECT status FROM inventory.transfers WHERE id = %s", (transfer_id))
                row: str = cur.fetchone()
                status: str = row[0]

            if(status != 'planned' ):
                console.print(f"[red] Статус трансфера был изменен другим пользователем с 'planned' на {row[0]}[/red")
                return

            if prev_quantity - int(quantity) >= 0:
                conn.execute(
                    "INSERT INTO inventory.transfer_items "
                    "(transfer_id, product_id, status, quantity, updated_at, requested_by, reserve_id) " \
                    "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (transfer_id, product_id, status, quantity, updated_at, requested_by, reserve_id),
                )

                conn.execute(
                    """ UPDATE inventory.stocks SET quantity = %s WHERE warehouse_id = %s AND product_id = %s""", 
                    (prev_quantity - int(quantity), from_warehouse_id, product_id)
                )

        console.print(f"[green]Позиция добавлена [/green]")

        answer = prompt("Wanna continue adding items? (y/n, д/н): ", validator=YesNoValidator())
        enter_product = YesNoValidator.is_yes(answer)


@command("remove transfer_item", "удалить позицию из перемещения", CATEGORY_TRANSFERS, [ROLE_INVENTORY_MANAGER])
def remove_transfer_item() -> None:  
    transfer_list: list[str, str] = []
    conn = get_conn()

    with conn.cursor() as cur:
        cur.execute("""
                    WITH transfer_warehouses AS
                    (
                        SELECT t.id, 
                        (SELECT city FROM catalog.cities WHERE id = w1.city_id) as city_from, 
                        w1.address as address_from, 
                        (SELECT city FROM catalog.cities WHERE id = w2.city_id) as city_to, 
                        w2.address as address_to
                        FROM inventory.transfers t
                        LEFT JOIN catalog.warehouses w1 ON t.from_warehouse_id = w1.id
                        LEFT JOIN catalog.warehouses w2 ON t.to_warehouse_id = w2.id
                    )

                    SELECT DISTINCT ti.transfer_id, t.city_from, t.address_from, t.city_to, t.address_to  
                    FROM inventory.transfer_items ti
                    LEFT JOIN transfer_warehouses t ON ti.transfer_id = t.id
                    WHERE ti.requested_by = %s""", 
                    (auth.auth_user().id,))
        for id, city_from, address_from, city_to, address_to in cur.fetchall():
            transfer_list.append([str(id), str(city_from + ' ' + address_from + ' -> ' + city_to + ' ' + address_to)])


    if len(transfer_list) == 0:
        console.print(f"Не найден трансфер с requested_by = {auth.auth_user().id}")
        return
    
    transfer_id = choice(
        message="Трансфер: ",
        options= transfer_list,
        default="",
    )

    with conn.cursor(row_factory=class_row(Transfer)) as cur:
        cur.execute("""SELECT id, order_id, from_warehouse_id, to_warehouse_id, 
                       created_at, status, updated_at, started_at, arriving_at, received_at 
                    FROM inventory.transfers WHERE id = %s FOR UPDATE""", (transfer_id,))
        transfer: Transfer = cur.fetchone()

    if transfer is None:
        render_error("Cannot get transfer")
        return

    _render_transfer(transfer)

    if transfer.status in ['in transit', 'arrived']:
        render_error(f"Cannot delete transfer in status {transfer.status}")
        return

    with conn.cursor() as cur:
        cur.execute("SELECT id FROM inventory.transfer_items WHERE transfer_id = %s", (transfer_id,))
        transfer_items: list[str] = [str(row[0]) for row in cur.fetchall()]

    transfer_item_id = prompt(
            "Transfer item для удаления: ",
            validator =  ChoiceValidator(transfer_items, message="Трансфер должен быть из списка. Используйте Tab для автодополнения."),
            completer = WordCompleter(transfer_items, ignore_case=True, sentence=True),
        ).strip()
    
    with conn.cursor() as cur:
        cur.execute("""SELECT quantity FROM inventory.transfer_items WHERE id = %s FOR UPDATE""", (transfer_item_id, ))
        row: int = cur.fetchone()
        prev_quantity: int | None = row[0] if row else None

    quantity = prompt("Какое кол-во удалить? : ", validator=PositiveIntValidator(max_val=prev_quantity + 1), default=str(prev_quantity)).strip()

    answer = prompt("Вы уверены? (y/n, д/н): ", validator=YesNoValidator())

    if YesNoValidator.is_yes(answer):
        if prev_quantity - int(quantity) > 0:
            with conn.transaction():
                conn.execute(
                """ UPDATE inventory.transfer_items SET quantity = %s WHERE id = %s""", 
                (prev_quantity - int(quantity), transfer_item_id)
                )
        else:
            with conn.transaction():
                conn.execute("DELETE FROM inventory.transfer_items WHERE id = %s", (transfer_item_id,))

