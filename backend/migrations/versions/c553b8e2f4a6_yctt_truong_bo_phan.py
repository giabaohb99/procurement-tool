"""yctt truong bo phan

bao-CR-553 (01/10/2026): phiếu yêu cầu thanh toán thêm ô «Trưởng bộ phận» như YCMH
(`head_of_dept_id` + `head_of_dept`), in ở dòng «Trưởng phòng ban/bộ phận» của bản in; rỗng thì
vẫn là trưởng phòng của người lập. Phiếu cũ mặc định 0 / rỗng nên hành vi không đổi.
(02/10: đại ca bỏ ô «Người duyệt» — «thêm 1 trường là trưởng phòng duyệt là oke rồi».)

Thứ tự: nối sau c540a7d3e9f1 (head prod). Trên erp-v2 chỉ mục báo cáo 5f39bbc564db được dời ra
SAU migration này, cùng cách làm với e537b2c4d6f8 / e538c6a1f2d9.

Revision ID: c553b8e2f4a6
Revises: c540a7d3e9f1
Create Date: 2026-10-01 18:00:00
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'c553b8e2f4a6'
down_revision: Union[str, None] = 'c540a7d3e9f1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tab_payment_request', sa.Column('head_of_dept_id', sa.BigInteger(), nullable=False,
                                                   server_default='0'))
    op.add_column('tab_payment_request', sa.Column('head_of_dept', sa.String(255), nullable=False,
                                                   server_default=''))


def downgrade() -> None:
    op.drop_column('tab_payment_request', 'head_of_dept')
    op.drop_column('tab_payment_request', 'head_of_dept_id')
