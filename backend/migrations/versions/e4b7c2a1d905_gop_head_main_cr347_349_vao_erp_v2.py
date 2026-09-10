"""gop head main (bao-CR-347/349) voi head erp-v2

Merge revision rong: nhanh main mang chuoi a1c6f80b2d47 -> d2f45a8c9e10
(gia von lo hang nhap khau + cot tab_user.notify_email) vao erp-v2
(head 94f0a2c4e43c - lop nhat ky P1b, 10/09/2026). Khong doi schema,
chi gop 2 head ve 1.

Revision ID: e4b7c2a1d905
Revises: 94f0a2c4e43c, d2f45a8c9e10
Create Date: 2026-09-10
"""
from typing import Sequence, Union

revision: str = "e4b7c2a1d905"
down_revision: Union[str, Sequence[str], None] = ("94f0a2c4e43c", "d2f45a8c9e10")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
