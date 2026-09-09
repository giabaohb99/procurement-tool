"""gop head main (bao-CR-319/320/321) voi head erp-v2

Merge revision rong: nhanh main mang chuoi c5a81b3f6d24 -> ed610675320b ->
b7e2c4d9a1f3 -> c9d3e7a1f5b6 (don hang nhap khau + dieu khoan in theo NCC)
vao erp-v2 (head b1e4d7a03c58, 09/09/2026). Khong doi schema - chi gop
2 head ve 1.

Revision ID: d7f2a9c4e1b8
Revises: b1e4d7a03c58, c9d3e7a1f5b6
Create Date: 2026-09-09
"""
from typing import Sequence, Union

revision: str = "d7f2a9c4e1b8"
down_revision: Union[str, Sequence[str], None] = ("b1e4d7a03c58", "c9d3e7a1f5b6")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
