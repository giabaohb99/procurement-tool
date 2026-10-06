"""hoa_chat_stt_cong_thuc: tab_customs_regulation them seq_no, sort_order, formula, mixture_pct

Revision ID: nd24reg01
Revises: wsched01
Create Date: 2026-10-06

duoc-CR-598 muc 3 -- du lieu hoa chat NĐ 24/2026 cap nhat tu tep «03. KHAI BAO HOA CHAT.xlsx»:
them STT trong phu luc, thu tu dong theo van ban, cong thuc hoa hoc, va NGUONG HAM LUONG HON HOP (%)
cua phu luc II (> 5%) va III (nhom 1 > 1%; nhom 2: tien chat cong nghiep > 5%, con lai > 1%).
Dong TT 01/2026 truoc nay muon cot `category` de giu cong thuc -> doi sang `formula`.

VIET TAY (khong autogenerate) -- repo autogenerate troi ~650 dong.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "nd24reg01"
down_revision: Union[str, None] = "wsched01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLE = "tab_customs_regulation"
_PUBLISH_TT01 = 11   # RegulationList.PUBLISH_TT01


def upgrade() -> None:
    op.add_column(_TABLE, sa.Column("seq_no", sa.String(20), nullable=False, server_default=""))
    op.add_column(_TABLE, sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"))
    op.add_column(_TABLE, sa.Column("formula", sa.String(100), nullable=False, server_default=""))
    op.add_column(_TABLE, sa.Column("mixture_pct", sa.Numeric(5, 2), nullable=True))
    op.execute(sa.text(
        f"UPDATE {_TABLE} SET formula = category, category = '' "
        f"WHERE list_code = {_PUBLISH_TT01} AND category <> ''"))


def downgrade() -> None:
    op.execute(sa.text(
        f"UPDATE {_TABLE} SET category = formula "
        f"WHERE list_code = {_PUBLISH_TT01} AND formula <> '' AND category = ''"))
    op.drop_column(_TABLE, "mixture_pct")
    op.drop_column(_TABLE, "formula")
    op.drop_column(_TABLE, "sort_order")
    op.drop_column(_TABLE, "seq_no")
