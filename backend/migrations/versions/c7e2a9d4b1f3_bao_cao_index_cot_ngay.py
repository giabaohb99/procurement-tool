"""bao cao: index cot ngay cho 5 bao cao Hanh chinh (Dat xe, Dong dau, Van ban, Phe duyet)

Các đường `/summary` mới lọc kỳ theo cột ngày — thiếu index thì mỗi lần mở trang Tổng
quan báo cáo là quét cả bảng. Viết tay (không autogenerate, repo trôi dạt ~650 dòng).

Revision ID: c7e2a9d4b1f3
Revises: 5f39bbc564db (01/10: noi sau chi muc bao cao Thu mua khi rebase)
Create Date: 2026-10-01
"""
from alembic import op

revision = "c7e2a9d4b1f3"
down_revision = "5f39bbc564db"
branch_labels = None
depends_on = None

_INDEXES = [
    ("ix_vbooking_start_time", "tab_vehicle_booking", ["start_time"]),
    ("ix_seal_created_at", "tab_seal_request", ["created_at"]),
    ("ix_document_created_at", "tab_document", ["created_at"]),
    ("ix_document_issued_at", "tab_document", ["issued_at"]),
    ("ix_approval_instance_started_at", "tab_approval_instance", ["started_at"]),
]


def upgrade() -> None:
    for name, table, cols in _INDEXES:
        op.create_index(name, table, cols)


def downgrade() -> None:
    for name, table, _cols in reversed(_INDEXES):
        op.drop_index(name, table_name=table)
