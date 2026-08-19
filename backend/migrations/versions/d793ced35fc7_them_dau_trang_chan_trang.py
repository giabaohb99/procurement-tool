"""Thêm ĐẦU TRANG / CHÂN TRANG cho phiên bản văn bản.

Bốn ô: đầu trang trái–phải, chân trang trái–phải; mỗi ô là một chuỗi ngắn lặp
lại ở MỌI tờ giấy. Không nhận HTML — đây là dòng chạy trên mọi trang, cho định
dạng tự do thì mỗi trang một kiểu và bản in vỡ bố cục.

Nhận mấy thẻ được thay lúc vẽ: {{trang}}, {{tong_trang}}, {{so_hieu}},
{{ten_van_ban}}, {{ngay}} — danh sách gốc ở `version_model.THE_DAU_CHAN_TRANG`.

Theo PHIÊN BẢN như lề và cách đánh số mục: đổi chân trang ở bản 2.0 không được
kéo bản 1.0 đã ký đổi theo.

⚠️ Autogenerate còn dò ra lệch `nullable` ở các bảng bình luận / ticket — lệch
có sẵn, KHÔNG thuộc việc này nên đã bỏ khỏi bản vá.

Revision ID: d793ced35fc7
Revises: 9effe7ec20cb
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'd793ced35fc7'
down_revision: Union[str, None] = '9effe7ec20cb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_COT = ("header_left", "header_right", "footer_left", "footer_right")


def upgrade() -> None:
    for ten in _COT:
        op.add_column('tab_document_version',
                      sa.Column(ten, sa.String(length=200),
                                nullable=False, server_default=''))


def downgrade() -> None:
    for ten in reversed(_COT):
        op.drop_column('tab_document_version', ten)
