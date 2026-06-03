from dataclasses import dataclass
from decimal import Decimal

from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from psycopg.rows import class_row

from rich.panel import Panel
from rich.table import Table

from console import console, render_error

from commands import command, CATEGORY_PRODUCT_CATEGORY


@dataclass
class Product_Category:
    id: int
    name: str

def _render_category(category: Product_Category) -> None:
    table = Table(show_header=False, box=None, padding=(0, 2))

    table.add_column("Поле", style="bold cyan", width=15)
    table.add_column("Значение", style="white")

    table.add_row("ID", str(category.id))
    table.add_row("Name", category.name)

    panel = Panel(
        table,
        expand=False,
        title=f"[bold green]Склад #{category.id}[/bold green]",
        border_style="green",
    )

    console.print(panel)
