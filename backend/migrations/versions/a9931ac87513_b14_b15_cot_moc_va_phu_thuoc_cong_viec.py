"""B-14 cột mốc + B-15 phụ thuộc công việc (cụm Gantt mở rộng)

Hai thay đổi, đều cho khung nhìn Gantt:

- `tab_work_task.kind` — việc thường (1) hay CỘT MỐC (2). `server_default='1'`
  là bắt buộc: cột NOT NULL thêm vào bảng đã có dữ liệu mà không có mặc định thì
  MySQL từ chối cả lượt nâng cấp.
- `tab_work_task_link` — mũi tên việc trước → việc sau (FS/SS/FF/SF). Unique
  `(predecessor_id, successor_id)` để một cặp việc chỉ có một mũi tên; luật
  KHÔNG-VÒNG-LẶP thì DB không giữ nổi, nằm ở `link_service.creates_cycle`.

Revision ID: a9931ac87513
Revises: c8a1d4f60b72
Create Date: 2026-08-29 08:15:39.076842
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a9931ac87513'
down_revision: Union[str, None] = 'c8a1d4f60b72'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'tab_work_task',
        sa.Column('kind', sa.SmallInteger(), nullable=False, server_default='1'),
    )

    op.create_table(
        'tab_work_task_link',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('company_id', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('list_id', sa.BigInteger(), nullable=False),
        sa.Column('predecessor_id', sa.BigInteger(), nullable=False),
        sa.Column('successor_id', sa.BigInteger(), nullable=False),
        sa.Column('link_type', sa.SmallInteger(), nullable=False, server_default='1'),
        sa.Column('lag_days', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_by', sa.BigInteger(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['list_id'], ['tab_work_list.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['predecessor_id'], ['tab_work_task.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['successor_id'], ['tab_work_task.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_tab_work_task_link_company_id'), 'tab_work_task_link',
                    ['company_id'], unique=False)
    op.create_index(op.f('ix_tab_work_task_link_list_id'), 'tab_work_task_link',
                    ['list_id'], unique=False)
    op.create_index(op.f('ix_tab_work_task_link_predecessor_id'), 'tab_work_task_link',
                    ['predecessor_id'], unique=False)
    op.create_index(op.f('ix_tab_work_task_link_successor_id'), 'tab_work_task_link',
                    ['successor_id'], unique=False)
    op.create_index('uq_work_task_link', 'tab_work_task_link',
                    ['predecessor_id', 'successor_id'], unique=True)


def downgrade() -> None:
    op.drop_index('uq_work_task_link', table_name='tab_work_task_link')
    op.drop_index(op.f('ix_tab_work_task_link_successor_id'), table_name='tab_work_task_link')
    op.drop_index(op.f('ix_tab_work_task_link_predecessor_id'), table_name='tab_work_task_link')
    op.drop_index(op.f('ix_tab_work_task_link_list_id'), table_name='tab_work_task_link')
    op.drop_index(op.f('ix_tab_work_task_link_company_id'), table_name='tab_work_task_link')
    op.drop_table('tab_work_task_link')
    op.drop_column('tab_work_task', 'kind')
