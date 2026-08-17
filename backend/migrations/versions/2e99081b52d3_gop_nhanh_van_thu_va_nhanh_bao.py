"""gop nhanh van thu va nhanh bao

Hai nhánh migration chạy song song rồi gặp nhau ở đây:

  * `a87414ed3f08` — phân hệ Văn thư (quan hệ cha–con, phạm vi áp dụng, chữ ký);
  * `bafb164ba2ec` — nhánh `bao` (CR-074…CR-078: trạng thái dòng YCMH, slug
    tiếng Anh cho `line_status`, ngày trả kết quả thực tế của YCBG).

**Migration này KHÔNG đổi gì trong cơ sở dữ liệu** — nó chỉ nối hai đầu lại làm
một. Không có nó thì `alembic upgrade head` báo *"Multiple head revisions are
present"* và **`start.sh` chết ngay ở bước đó**, tức là api không khởi động
được. Đúng lỗi đã xảy ra sáng 17/08.

Revision ID: 2e99081b52d3
Revises: a87414ed3f08, bafb164ba2ec
Create Date: 2026-08-17 06:34:48.643356
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2e99081b52d3'
down_revision: Union[str, None] = ('a87414ed3f08', 'bafb164ba2ec')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
