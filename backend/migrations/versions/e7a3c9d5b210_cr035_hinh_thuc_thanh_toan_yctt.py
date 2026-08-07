"""CR-035 - them cot hinh thuc thanh toan cho phieu yeu cau thanh toan

Nguoi lap phieu chon Chuyen khoan (transfer) hay Tien mat (cash). Ban in chi in cum
"Thong tin chuyen khoan" khi la chuyen khoan.

Phieu cu mac dinh 'transfer' -> ban in giu nguyen nhu truoc, khong phai sua tay.

Revision ID: e7a3c9d5b210
Revises: e3c5afa61ac0
Create Date: 2026-08-07
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e7a3c9d5b210"
down_revision: Union[str, None] = "e3c5afa61ac0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tab_payment_request",
                  sa.Column("payment_method", sa.String(length=20),
                            nullable=False, server_default="transfer"))


def downgrade() -> None:
    op.drop_column("tab_payment_request", "payment_method")
