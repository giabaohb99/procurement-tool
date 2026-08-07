"""CR-034: YCMH them trang thai 'dispatched' (Da dieu phoi)

Revision ID: c5b1d0a7e934
Revises: bd465aae44d0
Create Date: 2026-08-07

KHONG doi cau truc bang — cot `status` da la String(30), chi them mot GIA TRI moi.

Chuyen du lieu cu: truoc CR-034, phieu vao 'approved' la da duoc phan bo NSTM tu dong ngay
luc truong phong duyet, tuc la da di qua khau dieu phoi. Sau CR-034 'approved' mang nghia
MOI = "da duyet, DANG CHO dieu phoi" (chua co nhan su, chua tao duoc DMH). Neu giu nguyen,
toan bo phieu dang chay se bi keo nguoc ve hang doi cho dieu phoi va khong tao duoc DMH.
=> Doi 'approved' cu thanh 'dispatched'.
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'c5b1d0a7e934'
down_revision: Union[str, None] = 'bd465aae44d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("UPDATE tab_purchase_request SET status = 'dispatched' WHERE status = 'approved'")


def downgrade() -> None:
    op.execute("UPDATE tab_purchase_request SET status = 'approved' WHERE status = 'dispatched'")
