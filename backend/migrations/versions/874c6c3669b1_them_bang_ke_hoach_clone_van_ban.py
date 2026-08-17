"""them bang ke hoach clone van ban

Kế hoạch clone khai từ lúc TẠO văn bản, chạy lúc BAN HÀNH — xem
`app/modules/document/clone_plan_model.py`.

⚠️ Đã bỏ tay phần `alter_column` trên `tab_comment_*` / `tab_ticket*` mà
autogenerate kéo vào. Đó là độ lệch có sẵn giữa mô hình và cơ sở dữ liệu, không
liên quan gì tới bảng này; để lẫn vào đây thì một lần `downgrade` sẽ sửa cả
những bảng mình không hề đụng tới.

Revision ID: 874c6c3669b1
Revises: 2e99081b52d3
Create Date: 2026-08-17 07:09:39.851500
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '874c6c3669b1'
down_revision: Union[str, None] = '2e99081b52d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'tab_document_clone_plan',
        sa.Column('document_id', sa.BigInteger(), nullable=False),
        sa.Column('company_id', sa.BigInteger(), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('note', sa.String(length=500), nullable=False, server_default=''),
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_by', sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        #  Một pháp nhân đứng đúng một lần trong kế hoạch của một văn bản.
        sa.UniqueConstraint('document_id', 'company_id', name='uq_document_clone_plan'),
    )
    op.create_index(op.f('ix_tab_document_clone_plan_document_id'),
                    'tab_document_clone_plan', ['document_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_tab_document_clone_plan_document_id'),
                  table_name='tab_document_clone_plan')
    op.drop_table('tab_document_clone_plan')
