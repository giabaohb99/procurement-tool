"""them document_delivery_date (po_item) + document_status (purchase_order)

Revision ID: b4d6f8a0c2e5
Revises: a2c4e6f8b1d3
Create Date: 2026-07-22

Task 8 (CR-007): ngày giao chứng từ cho KT — tách bước "Chưa gửi ĐMH cho KT" -> "Đã gửi ĐMH cho KT".
Task 10b (CR-007): trạng thái hồ sơ chứng từ (cập nhật tay) hiển thị ở list ĐMH.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b4d6f8a0c2e5"
down_revision: Union[str, None] = "a2c4e6f8b1d3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tab_po_item",
                  sa.Column("document_delivery_date", sa.String(length=10), nullable=False, server_default=""))
    op.add_column("tab_purchase_order",
                  sa.Column("document_status", sa.String(length=30), nullable=False,
                            server_default="chưa có chứng từ"))
    op.create_index("ix_tab_purchase_order_document_status",
                    "tab_purchase_order", ["document_status"])


def downgrade() -> None:
    op.drop_index("ix_tab_purchase_order_document_status", table_name="tab_purchase_order")
    op.drop_column("tab_purchase_order", "document_status")
    op.drop_column("tab_po_item", "document_delivery_date")
