"""gop head bao-CR-316 (main: tach cot received_date YCMH) voi head erp-v2

Merge revision rong: nhanh main mang a7c3e91f5b28 (them cot
tab_purchase_request.received_date + backfill) vao erp-v2. Ban dau gop voi
6835fb9cfecd; sau khi keo code dong nghiep ve (08/09/2026) head erp-v2 da la
4f5033c40f3c (HRM chuc vu chu thuong) nen doi lai cho chi con MOT head.
Khong doi schema - chi gop 2 head ve 1.

Revision ID: b1e4d7a03c58
Revises: 4f5033c40f3c, a7c3e91f5b28
Create Date: 2026-09-08
"""
from typing import Sequence, Union

revision: str = "b1e4d7a03c58"
down_revision: Union[str, Sequence[str], None] = ("4f5033c40f3c", "a7c3e91f5b28")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
