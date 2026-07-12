from dataclasses import dataclass
from decimal import Decimal

from rich.panel import Panel
from rich.table import Table
from psycopg.rows import class_row
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit import prompt
from validators import PriceValidator, NonEmptyValidator, YesNoValidator, PositiveIntValidator, ChoiceValidator

from console import console, render_error
from db import get_conn

from commands import command, CATEGORY_ROUTES
from auth import auth_user, ROLE_WORKER, ROLE_INVENTORY_MANAGER

from prompt_toolkit.shortcuts import choice
from .warehouses import get_list_warehouses, _get_city_id_by_name, _get_city_validator, _get_city_completer

from sqlalchemy.dialects.oracle import dictionary



@dataclass
class Route:
    from_city_id: int
    to_city_id: int
    duration: int
    total_threshold: Decimal

def _render_route(route: Route):  # pylint: disable=unused-argument
    table = Table(show_header=False, box=None, padding=(0, 2))

    table.add_column("Поле", style="bold cyan", width=15)
    table.add_column("Значение", style="white")

    table.add_row("From", str(route.from_city_id))
    table.add_row("To", str(route.to_city_id))
    table.add_row("Duration", str(route.duration))
    table.add_row("Total threshold", str(route.total_threshold))

    panel = Panel(
        table,
        expand=False,
        title=f"[bold green]Route {route.from_city_id} -> {route.to_city_id}[/bold green]",
        border_style="green",
    )

    console.print(panel)

@command("list routes", "список всех routes", CATEGORY_ROUTES, [ROLE_INVENTORY_MANAGER, ROLE_WORKER])
def list_routes() -> None:
    conn = get_conn()
    table = Table(title="Routes", show_header=True, header_style="bold cyan")

    table.add_column("From", style="green", min_width=20)
    table.add_column("To", style="yellow", min_width=30)
    table.add_column("Duration", style="magenta", min_width=15)
    table.add_column("Total threshold", style="blue", min_width=20)

    with conn.cursor(row_factory=class_row(Route)) as cur:
        cur.execute("SELECT c1.city as from_city_id, c2.city as to_city_id, r.duration, r.total_threshold FROM inventory.routes r " \
        "LEFT JOIN catalog.cities c1 ON r.from_city_id = c1.id " \
        "LEFT JOIN catalog.cities c2 ON r.to_city_id = c2.id ")
        routes: list[Route] = cur.fetchall()

    for route in routes:
        table.add_row(
            str(route.from_city_id),
            str(route.to_city_id),
            str(route.duration),
            str(route.total_threshold)
        )
    console.print(table)

@command("show route", "информация о route", CATEGORY_ROUTES, [ROLE_INVENTORY_MANAGER, ROLE_WORKER])
def show_route() -> None:
    from_name = prompt("Город отправления: ", validator=_get_city_validator(), completer=_get_city_completer()).strip()
    from_ = _get_city_id_by_name(from_name)
    to_name = prompt("Город прибытия: ", validator=_get_city_validator(), completer=_get_city_completer()).strip()
    to_ = _get_city_id_by_name(to_name)         

    conn = get_conn()
    with conn.cursor(row_factory=class_row(Route)) as cur:
        cur.execute("SELECT c1.city as from_city_id, c2.city as to_city_id, r.duration, r.total_threshold FROM inventory.routes r " 
        "LEFT JOIN catalog.cities c1 ON r.from_city_id = c1.id " 
        "LEFT JOIN catalog.cities c2 ON r.to_city_id = c2.id " 
        "WHERE from_city_id = %s AND to_city_id = %s", (from_, to_))
        route: Route | None = cur.fetchone()

    if route is None:
        render_error(f"Route из {from_name} в {to_name} не найден")
        return

    _render_route(route)


@command("add route", "добавить route (интерактивно)", CATEGORY_ROUTES, [ROLE_INVENTORY_MANAGER, ROLE_WORKER])
def add_route() -> None:
    conn = get_conn()

    from_name = prompt("Город отправления: ", validator=_get_city_validator(), completer=_get_city_completer()).strip()
    from_ = _get_city_id_by_name(from_name)
    to_name = prompt("Город прибытия: ", validator=_get_city_validator(), completer=_get_city_completer()).strip()
    to_ = _get_city_id_by_name(to_name)

    duration = prompt("Delivery time in sec: ", validator=PositiveIntValidator()).strip() 
    total_threshold = prompt("Min order summ: ", validator=PriceValidator()).strip()
    
    conn.execute(
        "INSERT INTO inventory.routes (from_city_id, to_city_id, duration, total_threshold) VALUES (%s, %s, %s, %s)",
        (from_, to_, duration, total_threshold),
    )

    console.print(f"[green]Route из {from_name} в {to_name} добавлен [/green]")

@command("edit route", "редактировать route", CATEGORY_ROUTES, [ROLE_INVENTORY_MANAGER, ROLE_WORKER])
def edit_route() -> None:
    from_name = prompt("Город отправления: ", validator=_get_city_validator(), completer=_get_city_completer()).strip()
    from_ = _get_city_id_by_name(from_name)
    to_name = prompt("Город прибытия: ", validator=_get_city_validator(), completer=_get_city_completer()).strip()
    to_ = _get_city_id_by_name(to_name)

    conn = get_conn()
    with conn.cursor(row_factory=class_row(Route)) as cur:
        cur.execute("SELECT from_city_id, to_city_id, duration, total_threshold FROM inventory.routes " \
        "WHERE from_city_id = %s AND to_city_id = %s", 
        (from_, to_))
        route: Route | None = cur.fetchone()

    if route is None:
        render_error(f"Route из {from_} в {to_} не найден")
        return

    duration = prompt("Delivery time: ", default=route.duration, validator=PositiveIntValidator()), 
    total_threshold = prompt("Min order summ: ", default=route.total_threshold, validator=PriceValidator())

    conn.execute(
        """UPDATE inventory.routes SET duration = %s, total_threshold = %s 
        WHERE from_city_id = %s AND to_city_id = %s""",
        (duration, total_threshold, route.from_city_id, route.to_city_id),
    )

    console.print(f"[green]Route {route.id} обновлен [/green]")


@command("delete route", "удалить route", CATEGORY_ROUTES, [ROLE_INVENTORY_MANAGER, ROLE_WORKER])
def delete_route() -> None:
    from_name = prompt("Город отправления: ", validator=_get_city_validator(), completer=_get_city_completer()).strip()
    from_ = _get_city_id_by_name(from_name)
    to_name = prompt("Город прибытия: ", validator=_get_city_validator(), completer=_get_city_completer()).strip()
    to_ = _get_city_id_by_name(to_name)

    conn = get_conn()
    with conn.cursor(row_factory=class_row(Route)) as cur:
        cur.execute("SELECT from_city_id, to_city_id, duration, total_threshold FROM inventory.routes " \
        "WHERE from_city_id = %s AND to_city_id = %s", 
        (from_, to_))
        route: Route | None = cur.fetchone()

    if route is None:
        render_error(f"Route из {from_name} в {to_name} не найден")
        return

    _render_route(route)

    answer = prompt("Вы уверены? (y/n, д/н): ", validator=YesNoValidator())

    if YesNoValidator.is_yes(answer): #TO DO 'cascade' delete
        conn.execute("DELETE FROM inventory.routes WHERE from_city_id = %s AND to_city_id = %s", (route.from_city_id, route.to_city_id))
        console.print(f"[green]Route from {route.from_city_id} to {route.to_city_id} удален [/green]")
