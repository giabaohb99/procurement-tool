"""duoc-CR-803 — cot `tab_purchase_request.return_mode` (kieu tra ve YCMH).

Revision ID: prret803
Revises: matprice800
Create Date: 2026-11-28

Them mot cot SMALLINT mac dinh 0 (ma `PrReturnMode` o `app/core/pr_return_codes.py`). 1 = YCMH dang mua hang bi tra
ve CHI de sua Cong ty nhan hoa don; cac DMH lien quan bi khoa ghi toi khi duyet lai. Moi phieu cu nhan 0 (khong doi gi).

VIET TAY, KHONG autogenerate.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "prret803"
down_revision: Union[str, None] = "matprice800"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tab_purchase_request",
                  sa.Column("return_mode", sa.SmallInteger(), nullable=False, server_default="0"))


def downgrade() -> None:
    op.drop_column("tab_purchase_request", "return_mode")
