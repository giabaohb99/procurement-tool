"""qua_trinh_cong_tac_nhan_su: bang tab_employee_work_history

Revision ID: wkhist01
Revises: rptacc01
Create Date: 2026-10-03

Lich su cong tac THEO NGUOI, HR ghi tay tung dong (tuyen dung, dieu chuyen,
bo nhiem, kiem nhiem, mien nhiem, thoi viec...). Khong phieu nhieu nguoi,
khong duyet. Thiet ke: `frontend-v2/plans/261003-0837-qua-trinh-lam-viec-nhan-su/
phase-01-backend-model-bo-ma-migration.md`.

VIET TAY, khong autogenerate -- repo nay autogenerate troi ~650 dong moi lan.

`employee_id` la FK MEM (khong co ForeignKey thuc, cung khuon
`tab_employee_department`) -- xoa ho so don bang nay o tang service, khong co
CASCADE cua MySQL.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "wkhist01"
down_revision: Union[str, None] = "rptacc01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tab_employee_work_history",
        sa.Column("employee_id", sa.BigInteger(), nullable=False),
        # WorkEventType (app/core/hr_work_history_codes.py).
        sa.Column("event_type", sa.SmallInteger(), nullable=False),
        # = ngay hieu luc (Q1 chot GOP 03/10/2026) -- khong co cot effective_date rieng.
        sa.Column("from_date", sa.Date(), nullable=False),
        # NULL = dang hieu luc.
        sa.Column("to_date", sa.Date(), nullable=True),
        sa.Column("company_id", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("department_id", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("position_id", sa.BigInteger(), nullable=False, server_default="0"),
        # Nhan CHUP luc luu -- khop String(100) cua tab_employee.position, CO Y
        # khong propagate_rename.
        sa.Column("position_label", sa.String(100), nullable=False, server_default=""),
        sa.Column("decision_no", sa.String(50), nullable=False, server_default=""),
        sa.Column("decision_date", sa.Date(), nullable=True),
        sa.Column("note", sa.String(500), nullable=False, server_default=""),
        # Lan AP VAO HO SO gan nhat -- NULL = chua ap.
        sa.Column("applied_at", sa.DateTime(), nullable=True),
        sa.Column("applied_by", sa.BigInteger(), nullable=False, server_default="0"),

        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"),
                  nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"),
                  nullable=False),
        sa.Column("updated_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
    )
    # Moi truy van loc theo nguoi, xep theo ngay -- khong UNIQUE (mot ngay co
    # the vua bo nhiem vua kiem nhiem).
    op.create_index(
        "ix_employee_work_history_emp_from",
        "tab_employee_work_history",
        ["employee_id", "from_date"],
    )


def downgrade() -> None:
    op.drop_index("ix_employee_work_history_emp_from", table_name="tab_employee_work_history")
    op.drop_table("tab_employee_work_history")
