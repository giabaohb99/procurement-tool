"""them_head_of_dept_id_vao_ycmh

Revision ID: a1c7f4d92e63
Revises: 29639909b354
Create Date: 2026-08-15 09:10:00.000000

CR-071 — Trưởng bộ phận trên YCMH trở thành NGƯỜI DUYỆT CÓ CHỈ ĐỊNH, nên phải neo bằng
id nhân sự (`head_of_dept_id`) chứ không bằng tên. Cột chuỗi `head_of_dept` GIỮ NGUYÊN
làm bản chụp tên lúc lập phiếu (phiếu cũ không có id, và bản in vẫn in cái tên đó).

Phiếu cũ để `head_of_dept_id = 0` = KHÔNG chỉ định ai → rơi về luật cũ (ai có quyền duyệt
trong phạm vi thì duyệt được). Cố ý không backfill từ tên: tên trùng nhau giữa các phòng
là chuyện có thật, đoán id theo chuỗi thì sai âm thầm, mà cái sai đó lại nằm ở quyền duyệt.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a1c7f4d92e63'
down_revision: Union[str, None] = '29639909b354'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tab_purchase_request',
                  sa.Column('head_of_dept_id', sa.BigInteger(), nullable=False,
                            server_default='0'))


def downgrade() -> None:
    op.drop_column('tab_purchase_request', 'head_of_dept_id')
