"""duoc-CR-761: migration GỘP hai đầu — xếp ca theo ngày (wshift758) và nhánh mrg759a (kiêm nhiệm + mã kho YCMH)

Revision ID: mrg761a
Revises: mrg759a, wshift758
Create Date: 2026-11-16

Vì sao có tệp này: `wshift758` (duoc-CR-761, tên revision giữ số cũ lúc đặt chỗ) nối sau `kn756a`; cùng lúc bao-CR-759
thêm `mrg759a` cũng gộp sau `kn756a`, nên erp-v2 có hai head. Tệp này gộp lại thành MỘT head.

Thân trống: hai nhánh đụng các bảng khác nhau (`tab_work_shift_*` với `tab_employee_concurrent` / `tab_purchase_request_item`).
"""
from typing import Sequence, Union

revision: str = "mrg761a"
down_revision: Union[str, Sequence[str], None] = ("mrg759a", "wshift758")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
