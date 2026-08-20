"""gop nhanh cr109 va dau trang chan trang

Hai nhánh migration chạy song song rồi gặp nhau ở đây:

  * `c9e4b1a7d260` — CR-109 trên nhánh `main`: dọn `lab_result` chữ tự do sang
    `lab_note` để ô kết luận LAB chỉ còn hai lựa chọn;
  * `d793ced35fc7` — nhánh `erp-v2`: đầu trang / chân trang của phân hệ Văn thư.

**Migration này KHÔNG đổi gì trong cơ sở dữ liệu** — nó chỉ nối hai đầu lại làm
một. Không có nó thì `alembic upgrade head` báo *"Multiple head revisions are
present"* và **`start.sh` chết ngay ở bước đó**, tức là api không khởi động
được. Đúng lỗi đã xảy ra chiều 20/08 lúc deploy dev.

Chỉ có trên `erp-v2`: nhánh `main` không có `d793ced35fc7` nên ở đó
`c9e4b1a7d260` vẫn là head duy nhất.

Revision ID: c66984bcd932
Revises: c9e4b1a7d260, d793ced35fc7
Create Date: 2026-08-20 08:35:24.926780
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c66984bcd932'
down_revision: Union[str, None] = ('c9e4b1a7d260', 'd793ced35fc7')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
