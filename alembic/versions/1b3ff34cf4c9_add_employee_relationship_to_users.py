"""add employee relationship to users

Revision ID: 1b3ff34cf4c9
Revises: 
Create Date: 2026-09-24 20:12:15.287174

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1b3ff34cf4c9'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "users",
        sa.Column("employee_id", sa.Integer(), nullable=True)
    )

    op.create_unique_constraint(
        "uq_users_employee_id",
        "users",
        ["employee_id"]
    )

    op.create_foreign_key(
        "fk_users_employee_id",
        "users",
        "employees",
        ["employee_id"],
        ["id"]
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "fk_users_employee_id",
        "users",
        type_="foreignkey"
    )

    op.drop_constraint(
        "uq_users_employee_id",
        "users",
        type_="unique"
    )

    op.drop_column(
        "users",
        "employee_id"
    )