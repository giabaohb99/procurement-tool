"""survey nspt_note text

bao-CR-537 (30/09/2026, hotfix prod): «Ghi chú NSPT» của dòng NCC và dòng sản phẩm phiếu khảo sát
từ VARCHAR(255) lên TEXT. Người dùng gõ ghi chú 263 ký tự thì MySQL báo «Data too long for column
'nspt_note'» → màn hình hiện «lỗi không lường trước» (mã sự cố D30D24DF) và mất công sửa tay.

Thứ tự: nối sau c531a7e4d2f9 (head prod 30/09). Trên erp-v2 cụm thuốc BVTV (5f39bbc564db …) được
dời ra SAU migration này, cùng cách làm với c531a7e4d2f9.

Revision ID: e537b2c4d6f8
Revises: c531a7e4d2f9
Create Date: 2026-09-30 17:00:00
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'e537b2c4d6f8'
down_revision: Union[str, None] = 'c531a7e4d2f9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLES = ("tab_survey_supplier_line", "tab_survey_product_line")


def upgrade() -> None:
    for table in _TABLES:
        op.alter_column(table, "nspt_note", existing_type=sa.String(255), type_=sa.Text(),
                        existing_nullable=False)


def downgrade() -> None:
    #  Hạ về 255 sẽ CẮT/HỎNG ghi chú dài đã nhập — chỉ chạy khi chắc không còn dòng nào quá 255.
    for table in _TABLES:
        op.alter_column(table, "nspt_note", existing_type=sa.Text(), type_=sa.String(255),
                        existing_nullable=False)
