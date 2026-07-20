"""them import_line_key cho dong khao sat NCC + SP (khoa idempotent khi import)

Revision ID: 6f4d2c8a1b30
Revises: 5e3c7a1b9d20
Create Date: 2026-07-18
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "6f4d2c8a1b30"
down_revision: Union[str, None] = "5e3c7a1b9d20"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLES = ["tab_survey_supplier_line", "tab_survey_product_line"]


def upgrade() -> None:
    for t in _TABLES:
        op.add_column(t, sa.Column("import_line_key", sa.String(length=200), nullable=False, server_default=""))
        op.create_index(op.f(f"ix_{t}_import_line_key"), t, ["import_line_key"])


def downgrade() -> None:
    for t in _TABLES:
        op.drop_index(op.f(f"ix_{t}_import_line_key"), table_name=t)
        op.drop_column(t, "import_line_key")
