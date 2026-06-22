"""task4

Revision ID: 15ff6ed40b8e
Revises: e554c0eb3459
Create Date: 2026-06-17 20:16:34.494290

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '15ff6ed40b8e'
down_revision: Union[str, None] = 'e554c0eb3459'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with open(f"alembic/sql/{revision}/up.sql") as file:
        op.execute(file.read())


def downgrade() -> None:
    with open(f"alembic/sql/{revision}/down.sql") as file:
        op.execute(file.read())