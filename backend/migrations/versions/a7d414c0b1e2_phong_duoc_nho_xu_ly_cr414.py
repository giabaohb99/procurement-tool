"""Them cot "phong duoc nho xu ly" (handler_dept_id) tren ba chung tu thu mua (bao-CR-414)

Revision ID: a7d414c0b1e2
Revises: f1c3a7b52d48
Create Date: 2026-09-17

Phong ban tu mua hang (nha may) — giai doan 1. Ca bai toan nam o PHAM VI:
- bac pham vi moi `dept_proc` = `proc` NHUNG chi trong phong minh;
- phieu cua phong nay co the NHO phong khac xu ly (nha may nho thu mua chung, hoac
  nguoc lai). Cot `handler_dept_id` ghi phong duoc nho, 0 = khong nho.

`core/scoping._dept_match` coi "phieu thuoc phong minh" = phong lap phieu HOAC phong
duoc nho, nen bac `dept`, o "Phong ban duoc xem" va bac `dept_proc` deu tu thay
phieu duoc nho. O "Loai tru phong ban" KHONG chan phieu nho cho phong minh.

Khong dien lui du lieu cu: phieu cu chua nho ai, 0 la dung.
"""

from alembic import op
import sqlalchemy as sa

revision = "a7d414c0b1e2"
down_revision = "f1c3a7b52d48"
branch_labels = None
depends_on = None

_TABLES = ("tab_purchase_request", "tab_survey_request", "tab_purchase_order")


def upgrade() -> None:
    for table in _TABLES:
        op.add_column(table, sa.Column("handler_dept_id", sa.BigInteger(), nullable=False,
                                       server_default="0"))
        op.create_index(f"ix_{table}_handler_dept_id", table, ["handler_dept_id"])


def downgrade() -> None:
    for table in reversed(_TABLES):
        op.drop_index(f"ix_{table}_handler_dept_id", table_name=table)
        op.drop_column(table, "handler_dept_id")
