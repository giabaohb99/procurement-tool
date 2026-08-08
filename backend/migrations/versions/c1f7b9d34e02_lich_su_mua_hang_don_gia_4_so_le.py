"""Lich su mua hang: don gia len 4 so thap phan (Numeric(18,2) -> Numeric(18,4))

Migration `d4b9e7c1a305` đã nới 9 cột ĐƠN GIÁ lên 4 số lẻ nhưng BỎ SÓT
`tab_purchase_history.price` (bảng lịch sử ra đời ở nhánh khác, merge sau tại
`b8a33f9d2bd3` nên không nằm trong danh sách lúc đó).

Hậu quả: dòng ĐMH có đơn giá 4 số lẻ (vd 1.668,1823) khi chốt "Hoàn thành" được
chụp vào lịch sử thì MySQL tự làm tròn còn 1.668,18 — mất số lẻ NGAY LÚC GHI, nên
việc hiển thị đủ 4 số lẻ ở bảng lịch sử (CR-039) không cứu được. Lịch sử mua hàng
là bản chụp bất biến, sai ở đây là sai vĩnh viễn.

Nới scale không mất dữ liệu (18,2 là tập con của 18,4). Các bản ghi CŨ đã bị làm
tròn thì không khôi phục được từ bảng này — nếu cần chính xác phải chụp lại từ
`tab_po_item.price`, không nằm trong phạm vi migration.

KHÔNG đụng `amount` (tiền, vẫn 2 số lẻ tới đồng) và `qty_order` (18,3).

Revision ID: c1f7b9d34e02
Revises: b8a33f9d2bd3
Create Date: 2026-08-08 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1f7b9d34e02'
down_revision: Union[str, None] = 'b8a33f9d2bd3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TABLE = "tab_purchase_history"
COL = "price"


def _alter(from_scale: int, to_scale: int) -> None:
    # MySQL viết lại NGUYÊN định nghĩa cột khi ALTER, nên nullability phải lấy đúng thứ DB
    # đang có (model và DB thật lệch nhau ở nhiều cột) — đoán bừa là đổi luôn cả NULL/NOT NULL.
    insp = sa.inspect(op.get_bind())
    if TABLE not in set(insp.get_table_names()):
        return
    info = next((c for c in insp.get_columns(TABLE) if c["name"] == COL), None)
    if info is None:
        return
    op.alter_column(TABLE, COL,
                    existing_type=sa.Numeric(18, from_scale),
                    type_=sa.Numeric(18, to_scale),
                    existing_nullable=bool(info["nullable"]))


def upgrade() -> None:
    _alter(2, 4)


def downgrade() -> None:
    # Hạ scale sẽ LÀM TRÒN dữ liệu đang có — chấp nhận, đây là chiều lùi.
    _alter(4, 2)
