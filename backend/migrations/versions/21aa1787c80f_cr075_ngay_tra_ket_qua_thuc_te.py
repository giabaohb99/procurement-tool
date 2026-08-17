"""CR-075 — ngay tra ket qua thuc te cua dong yeu cau bao gia

Dong YCBG truoc day chi co `result_due_date` (han tra ket qua) nen khong do duoc tre han:
khong biet NSTM tra ket qua ngay nao. Them `result_date` — ghi tu dong luc bam "Chot khao sat"
(co phuong an hoac chot rong). Du lieu cu backfill bang scripts/backfill_result_date_cr075.py.

Revision ID: 21aa1787c80f
Revises: a1c7f4d92e63
Create Date: 2026-08-17 03:16:54.375549

Noi vao a1c7f4d92e63 (moc CHUNG cua ca hai nhanh) chu khong noi vao nhanh van thu:
nhanh `bao` (dang chay dev/prod) chua co van thu, noi nham la alembic gay khi deploy.
Nho vay tep nay giong het nhau o ca hai nhanh; ben erp-v2 co migration gop rieng.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '21aa1787c80f'
down_revision: Union[str, None] = 'a1c7f4d92e63'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tab_survey_request_line',
                  sa.Column('result_date', sa.String(length=10), nullable=False, server_default=''))


def downgrade() -> None:
    op.drop_column('tab_survey_request_line', 'result_date')
