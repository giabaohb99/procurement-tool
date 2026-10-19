"""Danh sách biến mẫu HĐLĐ: tab_labor_contract_variable + tab_labor_contract.custom_values (duoc-CR-630)

Revision ID: lbvar01
Revises: lbrct02

Viết tay (autogenerate repo này trôi ~650 dòng). KHÔNG import mã ứng dụng và KHÔNG chèn dữ liệu:
48 dòng biến hệ thống do seed lo (insert-only, D-018) — tránh chữ Việt trong migration.
⚠️ Downgrade MẤT giá trị biến tùy chỉnh đã nhập: dump `tab_labor_contract(id, custom_values)` trước.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "lbvar01"
down_revision: Union[str, None] = "lbrct02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "tab_labor_contract_variable"
CONTRACT = "tab_labor_contract"
UNIQUE = "uq_labor_contract_variable_code"
INDEX = "ix_labor_contract_variable_pick"


def upgrade() -> None:
    insp = sa.inspect(op.get_bind())
    if TABLE not in insp.get_table_names():
        op.create_table(
            TABLE,
            sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
            sa.Column("created_by", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
            sa.Column("updated_by", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("code", sa.String(40), nullable=False),
            sa.Column("source", sa.SmallInteger(), nullable=False),
            sa.Column("value_type", sa.SmallInteger(), nullable=False, server_default="1"),
            sa.Column("label", sa.String(200), nullable=False),
            sa.Column("description", sa.String(500), nullable=False, server_default=""),
            sa.Column("example", sa.String(255), nullable=False, server_default=""),
            sa.Column("default_value", sa.String(2000), nullable=False, server_default=""),
            sa.Column("is_required", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("is_hidden", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("sort_order", sa.SmallInteger(), nullable=False, server_default="0"),
            sa.UniqueConstraint("code", name=UNIQUE),
        )
        op.create_index(INDEX, TABLE, ["source", "is_active", "sort_order"])
    if "custom_values" not in {c["name"] for c in insp.get_columns(CONTRACT)}:
        op.add_column(CONTRACT, sa.Column("custom_values", sa.JSON(), nullable=True))


def downgrade() -> None:
    insp = sa.inspect(op.get_bind())
    if "custom_values" in {c["name"] for c in insp.get_columns(CONTRACT)}:
        op.drop_column(CONTRACT, "custom_values")
    if TABLE in insp.get_table_names():
        op.drop_table(TABLE)
