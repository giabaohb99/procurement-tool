"""Don gia cho phep 4 so thap phan (Numeric(18,2) -> Numeric(18,4))

Đơn giá nhập vào bị làm tròn còn 2 số lẻ khi lưu: người dùng gõ 1.668,182 thì lưu xuống
thành 1.668,18, kéo theo thành tiền lệch (4.759.999,2 thay vì 4.760.000,08). Nguyên nhân là
các cột ĐƠN GIÁ khai Numeric(18, 2) — MySQL tự làm tròn theo scale của cột.

Nới scale các cột ĐƠN GIÁ (giá 1 đơn vị) lên 4 số lẻ, chạy suốt luồng
YCKS -> YCBG -> khảo sát -> YCMH -> ĐMH -> tồn kho:

  tab_survey_request_line.proposed_price
  tab_survey.proposed_rate
  tab_survey_product_line.price_by_volume
  tab_survey_request_option.snap_price_by_volume
  tab_purchase_request_item.price
  tab_po_item.price
  tab_po_delivery.shipping_unit_price
  tab_inventory_move.unit_price
  tab_inventory.avg_cost

KHÔNG đụng các cột TIỀN (amount / total / value / paid...) — tiền vẫn ghi nhận tới đồng,
giữ Numeric(18, 2). Nới scale không mất dữ liệu (18,2 là tập con của 18,4).

Revision ID: d4b9e7c1a305
Revises: c8d1f6b3a92e
Create Date: 2026-08-07 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4b9e7c1a305'
down_revision: Union[str, None] = 'c8d1f6b3a92e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (bảng, cột) — chỉ các cột ĐƠN GIÁ
PRICE_COLS = [
    ("tab_survey_request_line", "proposed_price"),
    ("tab_survey", "proposed_rate"),
    ("tab_survey_product_line", "price_by_volume"),
    ("tab_survey_request_option", "snap_price_by_volume"),
    ("tab_purchase_request_item", "price"),
    ("tab_po_item", "price"),
    ("tab_po_delivery", "shipping_unit_price"),
    ("tab_inventory_move", "unit_price"),
    ("tab_inventory", "avg_cost"),
]


def _alter(from_scale: int, to_scale: int) -> None:
    # MySQL viết lại NGUYÊN định nghĩa cột khi ALTER, nên nullability phải lấy đúng thứ DB
    # đang có (model và DB thật lệch nhau ở nhiều cột) — đoán bừa là đổi luôn cả NULL/NOT NULL.
    insp = sa.inspect(op.get_bind())
    existing = set(insp.get_table_names())
    for table, col in PRICE_COLS:
        if table not in existing:
            continue
        info = next((c for c in insp.get_columns(table) if c["name"] == col), None)
        if info is None:
            continue
        op.alter_column(table, col,
                        existing_type=sa.Numeric(18, from_scale),
                        type_=sa.Numeric(18, to_scale),
                        existing_nullable=bool(info["nullable"]))


def upgrade() -> None:
    _alter(2, 4)


def downgrade() -> None:
    # Quay về 2 số lẻ SẼ LÀM TRÒN đơn giá đang lưu — chấp nhận, đây là chiều đi lùi.
    _alter(4, 2)
