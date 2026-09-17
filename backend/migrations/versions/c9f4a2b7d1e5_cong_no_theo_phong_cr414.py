"""Cong no + yeu cau thanh toan them cot phong ban (bao-CR-414 giai doan 4)

Revision ID: c9f4a2b7d1e5
Revises: b8e5f2a1c7d3
Create Date: 2026-09-17

Phong ban tu mua hang — giai doan 4. Khoan cong no (tab_payable) ghi phong DANG XU LY
don hang luc no sinh ra; phieu yeu cau thanh toan (tab_payment_request) ghi phong cua
cac khoan no gan vao, khong gan no thi ghi phong nguoi lap. Hai cot deu an, chi de
pham vi dept_proc / dept / loai tru phong bat duoc cong no cua phong minh.

Du lieu cu giu department_id = 0 (thu mua chung), KHONG backfill.
"""

from alembic import op
import sqlalchemy as sa

revision = "c9f4a2b7d1e5"
down_revision = "b8e5f2a1c7d3"
branch_labels = None
depends_on = None

_TABLES = ("tab_payable", "tab_payment_request")


def upgrade() -> None:
    for table in _TABLES:
        op.add_column(table, sa.Column("department_id", sa.BigInteger(), nullable=False,
                                       server_default="0"))
        op.create_index(f"ix_{table}_department_id", table, ["department_id"])


def downgrade() -> None:
    for table in _TABLES:
        op.drop_index(f"ix_{table}_department_id", table_name=table)
        op.drop_column(table, "department_id")
