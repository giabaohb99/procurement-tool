"""nhieu_so_dien_thoai_ho_so: them cot extra_phones (so dien thoai khac) vao ho so nhan su (duoc-CR-694)

Revision ID: emp_phones01
Revises: emp_salary01
Create Date: 2026-10-29

`tab_employee.phone` van la SO CHINH. Them `phone_label` (nhan so chinh) va `extra_phones` JSON NOT NULL (danh sach `{"number","label"}`,
toi da 4 phan tu) — cac dong cu duoc dien `[]`.

VIET TAY (khong autogenerate): repo nay autogenerate troi ~650 dong moi lan.
MySQL khong cho DEFAULT literal tren cot JSON nen: them cot cho phep NULL -> dien `[]` -> doi sang NOT NULL.
Kiem ton tai cot truoc khi them / xoa de chay lai an toan.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "emp_phones01"
down_revision: Union[str, None] = "emp_salary01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "tab_employee"


def _columns() -> set[str]:
    return {c["name"] for c in sa.inspect(op.get_bind()).get_columns(TABLE)}


def upgrade() -> None:
    if "extra_phones" not in _columns():
        op.add_column(TABLE, sa.Column("extra_phones", sa.JSON(), nullable=True))
    op.execute(sa.text(f"UPDATE {TABLE} SET extra_phones = CAST('[]' AS JSON) WHERE extra_phones IS NULL"))
    op.alter_column(TABLE, "extra_phones", existing_type=sa.JSON(), nullable=False)
    #  Nhan cua SO CHINH (`phone`): String(50) NOT NULL mac dinh ''.
    if "phone_label" not in _columns():
        op.add_column(TABLE, sa.Column("phone_label", sa.String(50), nullable=False, server_default=""))


def downgrade() -> None:
    have = _columns()
    for col in ("phone_label", "extra_phones"):
        if col in have:
            op.drop_column(TABLE, col)
