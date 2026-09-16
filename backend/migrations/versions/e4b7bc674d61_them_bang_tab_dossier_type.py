"""them bang tab_dossier_type

Revision ID: e4b7bc674d61
Revises: a3e8c1f6d924
Create Date: 2026-09-16 08:03:18.795402

⚠️ Bản autogenerate đầu tiên dài 639 dòng: ngoài bảng mới, nó còn gom hàng trăm
`alter_column ... nullable=False` của ~40 bảng khác — đó là DRIFT có sẵn giữa
model và DB thật, không phải việc của migration này. Đã cắt sạch, chỉ giữ bảng
`tab_dossier_type`. Muốn dọn drift thì làm một migration riêng, có rà từng bảng.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'e4b7bc674d61'
down_revision: Union[str, None] = 'a3e8c1f6d924'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'tab_dossier_type',
        sa.Column('code', sa.String(length=30), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=False),
        sa.Column('default_valid_months', sa.SmallInteger(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_by', sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
    )


def downgrade() -> None:
    op.drop_table('tab_dossier_type')
