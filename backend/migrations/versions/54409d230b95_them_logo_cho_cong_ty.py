"""them logo cho cong ty

Revision ID: 54409d230b95
Revises: dd3aa147c56f
Create Date: 2026-08-06 07:36:02.742007

Chỉ thêm cột tab_company.logo. Các thay đổi NOT NULL của tab_ticket/tab_ticket_message
mà autogenerate dò ra là DRIFT có sẵn từ trước, KHÔNG thuộc phạm vi thay đổi này nên đã bỏ.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '54409d230b95'
down_revision: Union[str, None] = 'dd3aa147c56f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # server_default='' để các bản ghi công ty đang có được điền sẵn chuỗi rỗng
    op.add_column(
        'tab_company',
        sa.Column('logo', sa.String(length=500), nullable=False, server_default=''),
    )


def downgrade() -> None:
    op.drop_column('tab_company', 'logo')
