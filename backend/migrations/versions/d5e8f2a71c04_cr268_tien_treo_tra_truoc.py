"""CR-268 — Tiền treo (thanh toán trước): hai cột theo dõi đối trừ trên dòng YCTT.

Phiếu thanh toán TRƯỚC (prepay=1) được chi khi CHƯA có công nợ, nên số tiền đã
chi "treo" ở đó chờ đối trừ. Trên mỗi dòng phiếu:

- `allocated_amount` = phần đã ĐỐI TRỪ vào công nợ (tự động lúc nhận hàng với
  phiếu gắn đơn, hoặc kế toán bấm tay với phiếu treo cấp NCC).
- `refunded_amount`  = phần NCC đã HOÀN TIỀN lại (đường B: trả full đơn sau,
  NCC trả cọc — kế toán ghi nhận tay).

Tiền treo còn lại của một dòng = amount - allocated_amount - refunded_amount.
Hai cột tách riêng vì hai nghiệp vụ khác bản chất: đối trừ là tiền ở lại với
NCC (thành tiền hàng), hoàn tiền là tiền quay về công ty — gộp một cột là mất
dấu vết khi đối chiếu.

Revision ID: d5e8f2a71c04
Revises: 7e93b1977593
"""
from alembic import op
import sqlalchemy as sa

revision = "d5e8f2a71c04"
down_revision = "7e93b1977593"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tab_payment_request_line",
                  sa.Column("allocated_amount", sa.Numeric(18, 2), nullable=False,
                            server_default="0"))
    op.add_column("tab_payment_request_line",
                  sa.Column("refunded_amount", sa.Numeric(18, 2), nullable=False,
                            server_default="0"))


def downgrade() -> None:
    op.drop_column("tab_payment_request_line", "refunded_amount")
    op.drop_column("tab_payment_request_line", "allocated_amount")
