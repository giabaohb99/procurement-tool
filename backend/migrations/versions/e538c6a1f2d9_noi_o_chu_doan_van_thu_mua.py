"""noi o chu doan van thu mua

bao-CR-538 (01/10/2026): nới các ô chữ đoạn văn của khảo sát / YCBG / YCMH / ĐMH sau sự cố
D30D24DF («Data too long» ở nspt_note, đã vá riêng ở bao-CR-537). Đại ca chốt cách nới: KHÔNG
lên TEXT mà CỘNG THÊM 100 vào trần hiện tại («255 thêm 100 là 355, vừa nhất»); «Chính sách
công nợ» là chuỗi mặc định nên 50 → 100 là đủ. Nới VARCHAR không mất dữ liệu.

Giữ đúng NOT NULL và mặc định `''` ở cấp DB của từng cột như trên prod (đọc information_schema
01/10): thiếu `existing_server_default` thì MySQL MODIFY xóa mất mặc định đó.

Thứ tự: nối sau e537b2c4d6f8 (head prod). Trên erp-v2 cụm thuốc BVTV (5f39bbc564db …) được dời
ra SAU migration này, cùng cách làm với c531a7e4d2f9 / e537b2c4d6f8.

Revision ID: e538c6a1f2d9
Revises: e537b2c4d6f8
Create Date: 2026-10-01 09:00:00
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'e538c6a1f2d9'
down_revision: Union[str, None] = 'e537b2c4d6f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

#  (bảng, cột, trần cũ, trần mới, có mặc định '' ở cấp DB)
_COLUMNS = [
    ("tab_survey_supplier_line", "debt_policy", 50, 100, False),
    ("tab_survey_product_line", "debt_policy", 50, 100, True),
    ("tab_survey_product_line", "active_ingredient", 255, 355, True),
    ("tab_survey_product_line", "shipping_policy", 255, 355, True),
    ("tab_survey_supplier_line", "delivery_policy", 255, 355, False),
    ("tab_survey_supplier_line", "reliability", 255, 355, False),
    ("tab_survey_supplier_line", "production_tech", 255, 355, False),
    ("tab_survey_supplier_line", "invoice_policy", 255, 355, False),
    ("tab_survey_supplier_line", "defect_return", 255, 355, False),
    ("tab_survey_supplier_line", "source_of_information", 255, 355, False),
    ("tab_survey_request", "purpose", 255, 355, True),
    ("tab_purchase_request", "purpose", 255, 355, False),
    ("tab_purchase_request_item", "note", 255, 355, False),
    ("tab_po_item", "note", 255, 355, False),
    ("tab_po_cost", "description", 255, 355, True),
    ("tab_survey", "main_content", 500, 600, True),
    ("tab_po_cost_type", "note", 500, 600, True),
]


def _alter(widen: bool) -> None:
    for table, column, before, after, has_default in _COLUMNS:
        src, dst = (before, after) if widen else (after, before)
        op.alter_column(table, column, existing_type=sa.String(src), type_=sa.String(dst),
                        existing_nullable=False,
                        existing_server_default=sa.text("''") if has_default else None)


def upgrade() -> None:
    _alter(widen=True)


def downgrade() -> None:
    #  Hạ trần sẽ HỎNG dòng đã dài hơn trần cũ — chỉ chạy khi chắc không còn dòng nào vượt.
    _alter(widen=False)
