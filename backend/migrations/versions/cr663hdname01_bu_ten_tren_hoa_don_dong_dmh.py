"""duoc-CR-663 (kh-NT1-4a) — bù «Tên trên hóa đơn» cho dòng ĐMH cũ còn trống

Từ CR-663 backend GHI tên này vào cột `tab_po_item.invoice_name` lúc lưu dòng (lấy từ sản phẩm
master theo mã hàng). Dòng cũ để trống vì trước đó tên chỉ được suy lúc TRẢ API. Migration này
chỉ chép đúng giá trị mà màn hình vẫn đang hiện: dòng trống + mã hàng có tên hóa đơn ở master.

Không đổi cấu trúc bảng; không ghi đè dòng đã có tên; dòng không có mã hàng / master trống để nguyên.
Chạy lại nhiều lần vẫn an toàn (lần sau không còn dòng trống khớp). Downgrade không hoàn tác được
(không phân biệt được tên người gõ với tên bù) nên là no-op.

Revision ID: cr663hdname01
Revises: d01merge01
"""
from typing import Sequence, Union

from alembic import op

revision: str = "cr663hdname01"
down_revision: Union[str, Sequence[str], None] = "d01merge01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# MIN() phòng khi master có hai dòng cùng mã (subquery vô hướng của MySQL sẽ báo lỗi nếu trả >1 dòng).
_TEN_MASTER = ("SELECT MIN(TRIM(p.invoice_name)) FROM tab_product p "
               "WHERE p.code = tab_po_item.product_code "
               "AND p.invoice_name IS NOT NULL AND TRIM(p.invoice_name) <> ''")


def upgrade() -> None:
    op.execute(
        f"UPDATE tab_po_item SET invoice_name = ({_TEN_MASTER}) "
        "WHERE (invoice_name IS NULL OR TRIM(invoice_name) = '') "
        f"AND product_code IS NOT NULL AND TRIM(product_code) <> '' AND ({_TEN_MASTER}) IS NOT NULL"
    )


def downgrade() -> None:
    pass
