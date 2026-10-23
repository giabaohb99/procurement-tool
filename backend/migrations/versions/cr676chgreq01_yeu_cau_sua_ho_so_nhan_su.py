"""duoc-CR-676 (HR2-2 / C6) — bảng yêu cầu sửa hồ sơ nhân sự do nhân viên tự khai, nhân sự duyệt

Chỉ THÊM bảng `tab_employee_change_request` (FK mềm `employee_id`, không CASCADE — dọn ở tầng
service khi xóa hồ sơ). Không đụng bảng nào khác, không dữ liệu mồi.

Revision ID: cr676chgreq01
Revises: cr660imp01
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "cr676chgreq01"
down_revision: Union[str, Sequence[str], None] = "cr660imp01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tab_employee_change_request",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("employee_id", sa.BigInteger(), nullable=False),
        #  = employee_id khi đang chờ duyệt, NULL khi đã xử lý/rút — UNIQUE giữ «tối đa một yêu cầu chờ» mỗi nhân sự.
        sa.Column("pending_employee_id", sa.BigInteger(), nullable=True),
        sa.Column("status", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("changes", sa.JSON(), nullable=False),
        sa.Column("families", sa.JSON(), nullable=True),
        sa.Column("note", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("reject_reason", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("decided_at", sa.DateTime(), nullable=True),
        sa.Column("decided_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("pending_employee_id", name="uq_employee_change_request_pending"),
    )
    op.create_index("ix_tab_employee_change_request_employee_id", "tab_employee_change_request",
                    ["employee_id"])
    op.create_index("ix_employee_change_request_status", "tab_employee_change_request", ["status"])


def downgrade() -> None:
    op.drop_index("ix_employee_change_request_status", table_name="tab_employee_change_request")
    op.drop_index("ix_tab_employee_change_request_employee_id", table_name="tab_employee_change_request")
    op.drop_table("tab_employee_change_request")
