"""cr470_chi_muc_doi_tac — chỉ mục (partner_id, reg_date) cho tab_customs_line (bao-CR-470).

Lọc «các lần nhập khác của đối tác này» đi theo `partner_id`; không có chỉ mục thì MySQL quét
cả bảng qua mọi phân vùng rồi sắp xếp (đo 1,8 giây trên dev ngày 23/09/2026). Tách migration
riêng vì `c4d8e2a6f470` đã chạy trên dev.

Revision ID: d7a3f9c2b481
Revises: c4d8e2a6f470
Create Date: 2026-09-23
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'd7a3f9c2b481'
down_revision: Union[str, None] = 'c4d8e2a6f470'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLE = 'tab_customs_line'
_INDEX = 'ix_customs_line_partner_date'


def _has_index() -> bool:
    return any(ix['name'] == _INDEX for ix in sa.inspect(op.get_bind()).get_indexes(_TABLE))


def upgrade() -> None:
    if not _has_index():
        op.create_index(_INDEX, _TABLE, ['partner_id', 'reg_date'])


def downgrade() -> None:
    if _has_index():
        op.drop_index(_INDEX, table_name=_TABLE)
