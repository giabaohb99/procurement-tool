"""CR-149 - cho sua cau chu ban in phieu yeu cau thanh toan (ticket #14)

Nguoi dung muon tu sua 3 cau tren ban in: Noi dung thanh toan, Dien giai bang,
Noi dung chuyen khoan (truoc gio ca 3 deu in chung 1 cau tu dong theo prepay/CR-146).

Them 1 cot Text `print_texts` luu JSON {"content","line_desc","transfer"}; khoa nao
rong thi ban in van dung cau tu dong nhu cu -> phieu cu KHONG can backfill.

Revision ID: e2f8a5c7d310
Revises: d9c4b7a2e510
Create Date: 2026-08-27
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e2f8a5c7d310"
down_revision: Union[str, None] = "d9c4b7a2e510"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # nullable=True theo dung mau reject_reason tren cung bang (997591492479):
    # MySQL khong cho DEFAULT literal tren TEXT; hang cu de NULL, parse phia app lo.
    op.add_column("tab_payment_request",
                  sa.Column("print_texts", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("tab_payment_request", "print_texts")
