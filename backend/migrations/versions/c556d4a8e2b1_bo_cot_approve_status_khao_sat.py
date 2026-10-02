"""bo cot approve_status khao sat

bao-CR-556 (02/10/2026): bỏ cột `tab_survey.approve_status` (B-04, «kết quả xét duyệt»
pending / approved / rejected). Không màn hình nào đọc cột này, và sau bao-CR-554 (trả về được cả
phiếu đã duyệt) nó chỉ còn là bản sao của `status`. Lý do trả về / từ chối vẫn ở `approve_note`.

Thứ tự: nối sau c553b8e2f4a6 (cùng đợt lên prod). Trên erp-v2 chỉ mục báo cáo 5f39bbc564db được
dời ra SAU migration này, cùng cách làm với e537b2c4d6f8 / e538c6a1f2d9 / c553b8e2f4a6.

Revision ID: c556d4a8e2b1
Revises: c553b8e2f4a6
Create Date: 2026-10-02 10:00:00
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'c556d4a8e2b1'
down_revision: Union[str, None] = 'c553b8e2f4a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('tab_survey', 'approve_status')


def downgrade() -> None:
    #  Dựng lại cột với mặc định `pending`; giá trị cũ không khôi phục được (suy từ `status`
    #  nếu cần: approved → approved, rejected → rejected, còn lại pending).
    op.add_column('tab_survey', sa.Column('approve_status', sa.String(20), nullable=False,
                                          server_default='pending'))
