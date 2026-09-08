"""gop head bao-CR-316 (main: tach cot received_date YCMH) voi head erp-v2

Merge revision rong: nhanh main mang a7c3e91f5b28 (them cot
tab_purchase_request.received_date + backfill) vao erp-v2 dang dung o 6835fb9cfecd.
Khong doi schema - chi gop 2 head ve 1.

Revision ID: b1e4d7a03c58
Revises: 6835fb9cfecd, a7c3e91f5b28
Create Date: 2026-09-08
"""
from typing import Sequence, Union

revision: str = "b1e4d7a03c58"
down_revision: Union[str, Sequence[str], None] = ("6835fb9cfecd", "a7c3e91f5b28")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
