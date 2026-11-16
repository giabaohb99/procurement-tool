"""xep_ca_theo_ngay: tab_work_shift_day + tab_work_shift_segment (duoc-CR-761)

Revision ID: wshift758
Revises: kn756a
Create Date: 2026-11-16

Xep ca theo tieng cho tung nguoi x tung ngay (Truong phong / Nhan su). Ngay co dong o `tab_work_shift_day` THANG moi cap
gan lich; khong co khung o `tab_work_shift_segment` = nghi do xep ca. Thiet ke:
`doc/erp/hrm/plans/261116-xep-ca-theo-tieng-duoc-cr-761/plan.md`.

VIET TAY (autogenerate repo nay troi ~650 dong moi lan: NOT NULL created_at/updated_at cua hai chuc bang + doi ten chi muc);
chi dung hai bang cua CR nay, khong dung khoa quyen moi (dung `work_schedule` va `work_schedule_personal` co san).
FK mem (khong ForeignKey thuc) theo quy uoc repo. Khung gio la gio TRON: start_hour 0..23, end_hour 1..24 (24 = het ngay).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "wshift758"
down_revision: Union[str, None] = "kn756a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tab_work_shift_day",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("employee_id", sa.BigInteger(), nullable=False),
        sa.Column("work_date", sa.Date(), nullable=False),
        sa.Column("note", sa.String(255), nullable=False, server_default=""),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("employee_id", "work_date", name="uq_work_shift_day"),
    )
    op.create_index("ix_tab_work_shift_day_employee_id", "tab_work_shift_day", ["employee_id"])
    op.create_table(
        "tab_work_shift_segment",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("shift_day_id", sa.BigInteger(), nullable=False),
        sa.Column("start_hour", sa.SmallInteger(), nullable=False),
        sa.Column("end_hour", sa.SmallInteger(), nullable=False),
        sa.Column("sort_order", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tab_work_shift_segment_shift_day_id", "tab_work_shift_segment", ["shift_day_id"])


def downgrade() -> None:
    op.drop_index("ix_tab_work_shift_segment_shift_day_id", table_name="tab_work_shift_segment")
    op.drop_table("tab_work_shift_segment")
    op.drop_index("ix_tab_work_shift_day_employee_id", table_name="tab_work_shift_day")
    op.drop_table("tab_work_shift_day")
