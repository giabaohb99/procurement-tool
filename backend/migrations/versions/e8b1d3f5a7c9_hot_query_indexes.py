"""them index cho cac cot query nong (apply_scope + man Tien do mua hang)

Revision ID: e8b1d3f5a7c9
Revises: d7f9b1c3e5a8
Create Date: 2026-07-22

CR-007: ra soat cac duong query nong roi danh index. apply_scope loc theo
company_id/created_by o MOI request list PYC/DMH; pr_code la cross-ref nong
(sync / man Tien do / list DMH theo PYC); progress_status bi loc o man Tien do
mua hang; assignee (PYC item) dung o scope "duoc giao". Cac cot join (po_id,
po_item_id) va order_date/received_date da co index tu truoc.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "e8b1d3f5a7c9"
down_revision: Union[str, None] = "d7f9b1c3e5a8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (ten_index, ten_bang, cot) — ten khop voi model: cot index=True dung quy uoc
# mac dinh ix_<table>_<col>; created_by dat ten tuong minh trong __table_args__.
_INDEXES = [
    ("ix_tab_purchase_order_pr_code", "tab_purchase_order", "pr_code"),
    ("ix_tab_purchase_order_company_id", "tab_purchase_order", "company_id"),
    ("ix_tab_purchase_order_department", "tab_purchase_order", "department"),
    ("ix_po_created_by", "tab_purchase_order", "created_by"),
    ("ix_tab_po_item_progress_status", "tab_po_item", "progress_status"),
    ("ix_tab_purchase_request_company_id", "tab_purchase_request", "company_id"),
    ("ix_pr_created_by", "tab_purchase_request", "created_by"),
    ("ix_tab_purchase_request_item_assignee", "tab_purchase_request_item", "assignee"),
]


def upgrade() -> None:
    for name, table, col in _INDEXES:
        op.create_index(name, table, [col])


def downgrade() -> None:
    for name, table, _col in reversed(_INDEXES):
        op.drop_index(name, table_name=table)
