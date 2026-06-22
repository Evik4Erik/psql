from dataclasses import dataclass
from decimal import Decimal

from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from psycopg.rows import class_row

from rich.panel import Panel
from rich.table import Table

from console import console, render_error
from db import get_conn
from validators import NonEmptyValidator, YesNoValidator
from commands import command, CATEGORY_PRODUCT_CATEGORY

from auth import ROLE_CATALOG_MANAGER, ROLE_SALES_MANAGER


@dataclass
class Product_Category:
    id: int
    name: str

def _render_category(category: Product_Category) -> None:
    table = Table(show_header=False, box=None, padding=(0, 2))

    table.add_column("Поле", style="bold cyan", width=15)
    table.add_column("Значение", style="white")

    table.add_row("ID", str(category.id))
    table.add_row("Имя", category.name)

    panel = Panel(
        table,
        expand=False,
        title=f"[bold green]Склад #{category.id}[/bold green]",
        border_style="green",
    )

    console.print(panel)

def _get_list_category() -> list[tuple[str,str]]:
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT id, name FROM catalog.product_categories")
        categories: list[Product_Category] = cur.fetchall()
        list_tupl= [
            (str(cat[0]), str(cat[1]))
            for cat in categories
        ]

        return list_tupl

@command("list product_category", "список всех категорий", CATEGORY_PRODUCT_CATEGORY, [ROLE_CATALOG_MANAGER, ROLE_SALES_MANAGER])
def list_category() -> None:
    conn = get_conn()
    table = Table(title="Категории", show_header=True, header_style="bold cyan")

    table.add_column("ID", style="dim", width=6, justify="right")
    table.add_column("Имя", style="green", min_width=20)

    with conn.cursor(row_factory=class_row(Product_Category)) as cur:
        cur.execute("SELECT * FROM catalog.product_categories")
        categories: list[Product_Category] = cur.fetchall()

    for category in categories:
        table.add_row(
            str(category.id),
            category.name,
        )
    console.print(table)


@command("show product_category", "информация о категории", CATEGORY_PRODUCT_CATEGORY, [ROLE_CATALOG_MANAGER, ROLE_SALES_MANAGER])
def show_category(_id: str) -> None:
    conn = get_conn()
    with conn.cursor(row_factory=class_row(Product_Category)) as cur:
        cur.execute("SELECT * FROM catalog.product_categories WHERE id = %s", (_id,))
        category: Product_Category | None = cur.fetchone()

    if category is None:
        render_error(f"Категория с ID {_id} не найдена")
        return

    _render_category(category)


@command("add product_category", "добавить категорию", CATEGORY_PRODUCT_CATEGORY, [ROLE_CATALOG_MANAGER])
def add_category() -> None:
    conn = get_conn()
    name = prompt("Наименование: ", validator=NonEmptyValidator()).strip()
    conn.execute(
        "INSERT INTO catalog.product_categories (name) VALUES (%s)",
        (name,),
    )

    console.print(f"[green]Категория добавлена [/green]")


@command("edit product_category", "редактировать склад", CATEGORY_PRODUCT_CATEGORY, [ROLE_CATALOG_MANAGER])
def edit_category(_id: str) -> None:
    conn = get_conn()
    with conn.cursor(row_factory=class_row(Product_Category)) as cur:
        cur.execute("SELECT * FROM catalog.product_categories WHERE id = %s", (_id,))
        category: Product_Category | None = cur.fetchone()

    if category is None:
        render_error(f"Категория с ID {_id} не найдена")
        return
    
    name = prompt(
        "Наименование: ", default=category.name, validator=NonEmptyValidator()
    ).strip()

    conn.execute(
        """UPDATE catalog.product_categories SET name = %s
        WHERE id = %s""",
        (name,_id),
    )

    console.print(f"[green]Категория обновлена [/green]")


@command("delete product_category", "удалить категорию", CATEGORY_PRODUCT_CATEGORY, [ROLE_CATALOG_MANAGER])
def delete_category(_id: str) -> None:
    conn = get_conn()
    with conn.cursor(row_factory=class_row(Product_Category)) as cur:
        cur.execute("SELECT * FROM catalog.product_categories WHERE id = %s", (_id,))
        category: Product_Category | None = cur.fetchone()

    if category is None:
        render_error(f"Категория с ID {_id} не найдена")
        return

    _render_category(category)

    answer = prompt("Вы уверены? (y/n, д/н): ", validator=YesNoValidator())

    if YesNoValidator.is_yes(answer):
        conn.execute("DELETE FROM catalog.product_categories WHERE id = %s", (_id,))

        console.print(f"[green]Категория {category.name} удалена [/green]")

