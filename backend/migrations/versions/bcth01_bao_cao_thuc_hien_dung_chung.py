"""bao-CR-598 — khối Báo cáo thực hiện dùng chung YCBG + ĐMH.

- Thêm bảng ĐẦU `tab_exec_report(owner_entity, owner_id)`; dựng đầu cho mọi YCBG
  đang có dữ liệu báo cáo với `id = id phiếu` — nhờ vậy bốn bảng con chỉ ĐỔI TÊN
  cột khóa (`survey_request_id` → `report_id`), không chép dòng nào.
- Đổi tên bốn bảng con `tab_survey_request_report_*` → `tab_exec_report_*`.
- Nút dòng hàng thêm `line_id` (id dòng chứng từ, 0 = nút đặt tay).
- Hồ sơ thêm `result` (cột «Kết quả» của bảng kế hoạch Excel thu mua).

Revision ID: bcth01
Revises: pmem01
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "bcth01"
down_revision: Union[str, None] = "pmem01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

#  (tên cũ, tên mới) — thứ tự: doc trước để giữ cùng nếp với migration gốc.
_TABLES = (
    ("tab_survey_request_report_item", "tab_exec_report_item"),
    ("tab_survey_request_report_phase", "tab_exec_report_phase"),
    ("tab_survey_request_report_doc", "tab_exec_report_doc"),
    ("tab_survey_request_report_trash", "tab_exec_report_trash"),
)


def upgrade() -> None:
    op.create_table(
        "tab_exec_report",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("owner_entity", sa.String(length=32), nullable=False, server_default="survey_request"),
        sa.Column("owner_id", sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("owner_entity", "owner_id", name="uq_exec_report_owner"),
    )
    op.create_index(op.f("ix_tab_exec_report_owner_id"), "tab_exec_report", ["owner_id"], unique=False)

    #  Đầu báo cáo cho dữ liệu YCBG cũ: id = id phiếu, nên khóa ở bảng con giữ nguyên giá trị.
    union = " UNION ".join(
        f"SELECT survey_request_id AS sid FROM {old}" for old, _ in _TABLES)
    op.execute(
        "INSERT INTO tab_exec_report (id, owner_entity, owner_id, created_by, updated_by) "
        f"SELECT sid, 'survey_request', sid, 0, 0 FROM ({union}) AS src WHERE sid > 0")

    for old, new in _TABLES:
        op.drop_index(op.f(f"ix_{old}_survey_request_id"), table_name=old)
        op.alter_column(old, "survey_request_id", new_column_name="report_id",
                        existing_type=sa.BigInteger(), existing_nullable=False)
        op.rename_table(old, new)
        op.create_index(op.f(f"ix_{new}_report_id"), new, ["report_id"], unique=False)

    op.add_column("tab_exec_report_item",
                  sa.Column("line_id", sa.BigInteger(), nullable=False, server_default="0"))
    op.add_column("tab_exec_report_doc",
                  sa.Column("result", sa.String(length=1000), nullable=False, server_default=""))


def downgrade() -> None:
    op.drop_column("tab_exec_report_doc", "result")
    op.drop_column("tab_exec_report_item", "line_id")
    for old, new in reversed(_TABLES):
        op.drop_index(op.f(f"ix_{new}_report_id"), table_name=new)
        op.rename_table(new, old)
        op.alter_column(old, "report_id", new_column_name="survey_request_id",
                        existing_type=sa.BigInteger(), existing_nullable=False)
        op.create_index(op.f(f"ix_{old}_survey_request_id"), old, ["survey_request_id"], unique=False)
    #  Báo cáo của ĐMH (đầu không phải YCBG) mất đường về — hạ cấp là mất dữ liệu đó.
    op.drop_index(op.f("ix_tab_exec_report_owner_id"), table_name="tab_exec_report")
    op.drop_table("tab_exec_report")
