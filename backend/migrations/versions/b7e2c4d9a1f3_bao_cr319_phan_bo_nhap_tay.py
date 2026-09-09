"""bao_cr319_phan_bo_nhap_tay

Cách chia chi phí lô hàng số 5 "Nhập tay": cột JSON lưu số tiền người dùng gõ cho từng
dòng hàng. Bốn cách chia cũ vẫn tính lúc xem, không lưu; chỉ cách này bắt buộc lưu vì
con số do người gõ. Cột TEXT nên để nullable (MySQL không cho TEXT có DEFAULT), mã đọc
bằng `or ""`.

Revision ID: b7e2c4d9a1f3
Revises: ed610675320b
Create Date: 2026-09-09 10:40:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7e2c4d9a1f3'
down_revision: Union[str, None] = 'ed610675320b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tab_po_import_cost', sa.Column('manual_allocation', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('tab_po_import_cost', 'manual_allocation')
