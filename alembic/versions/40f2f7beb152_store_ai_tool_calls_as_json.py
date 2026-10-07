"""store ai tool calls as json

Revision ID: 40f2f7beb152
Revises: df735d08f184
Create Date: 2026-09-25 17:56:32.777758

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '40f2f7beb152'
down_revision: Union[str, Sequence[str], None] = 'df735d08f184'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("TRUNCATE TABLE ai_tool_calls RESTART IDENTITY")

    op.alter_column(
        "ai_tool_calls",
        "arguments",
        existing_type=sa.VARCHAR(),
        type_=sa.JSON(),
        postgresql_using="arguments::json",
    )

    op.alter_column(
        "ai_tool_calls",
        "result",
        existing_type=sa.VARCHAR(),
        type_=sa.JSON(),
        postgresql_using="result::json",
    )


def downgrade() -> None:
    op.alter_column(
        "ai_tool_calls",
        "arguments",
        existing_type=sa.JSON(),
        type_=sa.VARCHAR(),
        postgresql_using="arguments::text",
    )

    op.alter_column(
        "ai_tool_calls",
        "result",
        existing_type=sa.JSON(),
        type_=sa.VARCHAR(),
        postgresql_using="result::text",
    )