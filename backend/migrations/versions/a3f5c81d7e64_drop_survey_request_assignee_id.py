"""drop cot tab_survey_request.assignee_id (CR-018 / N-001)

Revision ID: a3f5c81d7e64
Revises: e1c7b40d5a92
Create Date: 2026-08-05

NSTM khao sat thuoc ve DONG (`tab_survey_request_line.assignee`), khong thuoc ve phieu.
Cot header nay chi duoc ghi 1 lan luc duyet va khong dong bo khi doi NSTM dong.
Code da go het (model/auto_assign/scoping) o CR-018 -> gio drop cot.

Cot khong co index, khong co FK, kieu BIGINT NOT NULL DEFAULT 0.
KHONG dung toi `tab_purchase_request.assignee_id` (trung ten nhung van dang dung).
"""
from alembic import op
import sqlalchemy as sa


revision = 'a3f5c81d7e64'
down_revision = 'e1c7b40d5a92'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column('tab_survey_request', 'assignee_id')


def downgrade() -> None:
    # Khoi phuc cau truc cot (gia tri cu KHONG khoi phuc duoc — da bo di).
    op.add_column('tab_survey_request',
                  sa.Column('assignee_id', sa.BigInteger(), nullable=False, server_default='0'))
