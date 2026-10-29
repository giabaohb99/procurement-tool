"""o_luong_ho_so_nhan_su: them luong / phu cap len ho so nhan su (duoc-CR-693)

Revision ID: emp_salary01
Revises: hcplan05
Create Date: 2026-10-29

Them 3 cot vao `tab_employee`: `salary_monthly` (luong, dong/thang), `allowance_monthly` (phu cap, dong/thang)
— BIGINT NOT NULL mac dinh 0 — va `salary_updated_at` (DATETIME, NULL). Bao cao Quy luong doc so tu day.
Chi chinh nhan su do xem duoc so (xem `employee/sensitive.py`).

VIET TAY (khong autogenerate): repo nay autogenerate troi ~650 dong moi lan.
Kiem ton tai cot truoc khi them / xoa de chay lai an toan.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "emp_salary01"
down_revision: Union[str, None] = "hcplan05"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "tab_employee"


def _columns() -> set[str]:
    return {c["name"] for c in sa.inspect(op.get_bind()).get_columns(TABLE)}


def upgrade() -> None:
    have = _columns()
    if "salary_monthly" not in have:
        op.add_column(TABLE, sa.Column("salary_monthly", sa.BigInteger(), nullable=False, server_default="0"))
    if "allowance_monthly" not in have:
        op.add_column(TABLE, sa.Column("allowance_monthly", sa.BigInteger(), nullable=False, server_default="0"))
    if "salary_updated_at" not in have:
        op.add_column(TABLE, sa.Column("salary_updated_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    have = _columns()
    for col in ("salary_updated_at", "allowance_monthly", "salary_monthly"):
        if col in have:
            op.drop_column(TABLE, col)
