"""bao_cr310_p3b_chot_hoan_thanh_phuong_an_dong_ycmh

Hai cột trên DÒNG Yêu cầu mua hàng cho bước "chốt hoàn thành xử lý phương án"
(khuôn complete_sr của Yêu cầu báo giá): `options_done` — NSTM tuyên bố đã xử lý
xong dòng, khóa sửa phương án và mở cho người yêu cầu chọn; `no_option` — chốt
rỗng, xử lý rồi nhưng không có NCC phù hợp. Chỉ THÊM CỘT, không đụng bảng khác
(autogenerate vẫn đòi alter loạt bảng lệch từ trước — bỏ, ngoài phạm vi).

Revision ID: a3e8c1f6d924
Revises: d5f7a9c1b3e2
Create Date: 2026-09-14 17:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a3e8c1f6d924'
down_revision: Union[str, None] = 'd5f7a9c1b3e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = 'tab_purchase_request_item'


def upgrade() -> None:
    op.add_column(TABLE, sa.Column('options_done', sa.Boolean(), nullable=False,
                                   server_default=sa.false()))
    op.add_column(TABLE, sa.Column('no_option', sa.Boolean(), nullable=False,
                                   server_default=sa.false()))


def downgrade() -> None:
    op.drop_column(TABLE, 'no_option')
    op.drop_column(TABLE, 'options_done')
