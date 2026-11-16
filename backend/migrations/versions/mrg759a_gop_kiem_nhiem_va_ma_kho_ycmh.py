"""bao-CR-759: migration GỘP hai nhánh — kiêm nhiệm (kn755a -> kn756a) và mã kho dòng YCMH (prwh759a)

Revision ID: mrg759a
Revises: kn756a, prwh759a
Create Date: 2026-11-16

Vì sao có tệp này: `prwh759a` (bao-CR-759) được nối thẳng sau `stix723` — head đang chạy trên prod — để cherry-pick
riêng CR-759 lên main mà không kéo theo duoc-CR-755/756 (chưa duyệt lên prod). Trên erp-v2 hai migration kiêm nhiệm
cũng nối sau `stix723`, nên erp-v2 có hai head; tệp này gộp chúng lại thành MỘT head.

Thân trống: hai nhánh đụng hai bảng khác nhau (`tab_employee_concurrent` và `tab_purchase_request_item`), không có gì
phải làm khi gặp nhau. Lúc CR-755/756 lên prod thì main nhận luôn tệp gộp này, chuỗi khớp với erp-v2.
"""
from typing import Sequence, Union

revision: str = "mrg759a"
down_revision: Union[str, Sequence[str], None] = ("kn756a", "prwh759a")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
