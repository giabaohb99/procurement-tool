"""CR-146 - them co 'thanh toan truoc' cho phieu yeu cau thanh toan (ticket #12)

Don hang tra truoc nhung ban in mac dinh ghi "Thanh toan cong no ..." -> sai ban chat.
Nguoi lap phieu danh dau prepay = 1 thi noi dung in (Dien giai + Noi dung chuyen khoan)
doi thanh "Thanh toan truoc cho nha cung cap <ten NCC> <ky>".

Phieu cu mac dinh 0 (thanh toan cong no) -> ban in giu nguyen nhu truoc.

Revision ID: d9c4b7a2e510
Revises: b7c2f4e8a915
Create Date: 2026-08-26
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d9c4b7a2e510"
down_revision: Union[str, None] = "b7c2f4e8a915"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tab_payment_request",
                  sa.Column("prepay", sa.SmallInteger(),
                            nullable=False, server_default="0"))


def downgrade() -> None:
    op.drop_column("tab_payment_request", "prepay")
