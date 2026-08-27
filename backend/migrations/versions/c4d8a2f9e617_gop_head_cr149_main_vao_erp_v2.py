"""gop head CR-149 (main: print_texts YCTT) voi head erp-v2

Merge revision rong: nhanh main mang e2f8a5c7d310 (them cot
tab_payment_request.print_texts) vao erp-v2 dang dung o b2d9f1c47a30.
Khong doi schema — chi gop 2 head ve 1.

Revision ID: c4d8a2f9e617
Revises: b2d9f1c47a30, e2f8a5c7d310
Create Date: 2026-08-27
"""
from typing import Sequence, Union

revision: str = "c4d8a2f9e617"
down_revision: Union[str, Sequence[str], None] = ("b2d9f1c47a30", "e2f8a5c7d310")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
