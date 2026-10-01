"""bao-CR-541: ma bam chong trung dong hang hai quan (Tra cuu thi truong)

- tab_customs_line.row_hash VARCHAR(40) NOT NULL DEFAULT '': SHA-1 cua du cac cot du lieu
  sau chuan hoa (app.modules.customs.dedupe). Nap tep moi: dong co ma da co thi bo qua,
  khong con thay theo khoang ngay.
- Chi muc (row_hash, reg_date): kem reg_date vi bang chia phan vung theo nam cua no.

KHONG tinh ma trong migration: ham bam nam o ma nguon ung dung, migration goi ma ung dung la
dong cung phien ban. Dong cu de rong; lan nap sau cham khoang ngay cua no thi tu tinh, hoac
chay `python scripts/customs_row_hash.py --backfill` mot lan.

Revision ID: c540a7d3e9f1
Revises: b4d81f2c6e37
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c540a7d3e9f1'
down_revision: Union[str, None] = 'b4d81f2c6e37'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tab_customs_line',
                  sa.Column('row_hash', sa.String(40), nullable=False, server_default=''))
    op.create_index('ix_customs_line_hash_date', 'tab_customs_line', ['row_hash', 'reg_date'])


def downgrade() -> None:
    op.drop_index('ix_customs_line_hash_date', table_name='tab_customs_line')
    op.drop_column('tab_customs_line', 'row_hash')
