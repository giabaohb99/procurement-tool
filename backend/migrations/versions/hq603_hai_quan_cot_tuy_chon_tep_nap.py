"""bao-CR-603: Tra cứu thị trường — bốn cột lấy từ tệp nạp (tùy chọn)

Tệp GTT02 nạp vào màn «Tra cứu thị trường» nay nhận thêm các cột tùy chọn: Hoạt chất,
Hàm lượng / dạng, Đơn giá quy đổi VND (thuế NK 7%), Đơn giá quy đổi VND (theo thuế suất XNK)
(và «Nước nhận hàng» thành không bắt buộc, không cần cột mới). Thêm vào `tab_customs_line`:

- `active_ingredient_from_file`, `formulation_from_file` TINYINT(1) NOT NULL DEFAULT 0: 1 = giá trị
  lấy từ tệp, `retag_all` không được ghi đè; 0 = suy ra từ tên hàng như cũ.
- `price_vnd_flat`, `price_vnd_line_tax` DECIMAL(18,2) NULL: giá VND lấy từ tệp; NULL = tính lúc đọc
  như trước (bao-CR-493). Không vào mã băm chống trùng (bao-CR-541) nên dòng cũ giữ nguyên mã.

Bảng chia phân vùng theo năm `reg_date`; ADD COLUMN không đụng khóa phân vùng nên chạy bình thường.

Revision ID: hq603
Revises: bcth01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "hq603"
down_revision: Union[str, None] = "bcth01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tab_customs_line",
                  sa.Column("active_ingredient_from_file", sa.Boolean(), nullable=False, server_default="0"))
    op.add_column("tab_customs_line",
                  sa.Column("formulation_from_file", sa.Boolean(), nullable=False, server_default="0"))
    op.add_column("tab_customs_line", sa.Column("price_vnd_flat", sa.Numeric(18, 2), nullable=True))
    op.add_column("tab_customs_line", sa.Column("price_vnd_line_tax", sa.Numeric(18, 2), nullable=True))


def downgrade() -> None:
    op.drop_column("tab_customs_line", "price_vnd_line_tax")
    op.drop_column("tab_customs_line", "price_vnd_flat")
    op.drop_column("tab_customs_line", "formulation_from_file")
    op.drop_column("tab_customs_line", "active_ingredient_from_file")
