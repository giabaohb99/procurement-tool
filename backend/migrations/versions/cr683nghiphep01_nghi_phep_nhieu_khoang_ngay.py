"""nghi phep: nhieu khoang ngay trong mot don (duoc-CR-683)

Bảng `tab_leave_request_period` — mỗi dòng là MỘT khoảng ngày liền của tờ đơn.
Đầu đơn (`from_date/to_date/from_session/to_session`) trở thành bao ngoài dẫn xuất.

⚠️ Backfill là bắt buộc: mọi đơn (kể cả nháp, đã xóa, nghỉ theo giờ) thành đúng MỘT
khoảng, để SQL JOIN thẳng bảng khoảng không sót đơn cũ. Viết tay, không autogenerate
(repo này autogenerate ra ~650 dòng trôi dạt không liên quan).

Revision ID: cr683nghiphep01
Revises: cr684fmcode01
Create Date: 2026-10-26
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'cr683nghiphep01'
down_revision: Union[str, None] = 'cr684fmcode01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'tab_leave_request_period',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('request_id', sa.BigInteger(), nullable=False),
        sa.Column('from_date', sa.Date(), nullable=False),
        sa.Column('from_session', sa.SmallInteger(), nullable=False),
        sa.Column('to_date', sa.Date(), nullable=False),
        sa.Column('to_session', sa.SmallInteger(), nullable=False),
        sa.Column('days', sa.Float(), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'),
                  nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'),
                  nullable=False),
        sa.Column('updated_by', sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_leave_request_period_request', 'tab_leave_request_period',
                    ['request_id'], unique=False)

    op.execute(sa.text("""
        INSERT INTO tab_leave_request_period
            (request_id, from_date, from_session, to_date, to_session, days, sort_order,
             created_at, created_by, updated_at, updated_by)
        SELECT r.id, r.from_date, r.from_session, r.to_date, r.to_session, r.total_days, 0,
               NOW(), r.created_by, NOW(), r.updated_by
        FROM tab_leave_request r
    """))


def downgrade() -> None:
    op.drop_index('ix_leave_request_period_request', table_name='tab_leave_request_period')
    op.drop_table('tab_leave_request_period')
