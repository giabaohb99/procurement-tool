"""them bang tab_comment (CR-029)

Bang binh luan dung chung cho moi chung tu theo cap (entity, entity_id) —
cung khuon voi tab_file_link cua dinh kem.

Autogenerate co sinh kem hang tram lenh alter_column NOT NULL cho cac bang cu
(lech san co giua model va DB doi truoc, khong lien quan CR nay). Da BO HET,
chi giu lai phan tao bang moi.

Revision ID: 4fbb4f65df99
Revises: c8d1f6b3a92e
Create Date: 2026-08-06 02:26:14.279634
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '4fbb4f65df99'
down_revision: Union[str, None] = 'c8d1f6b3a92e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'tab_comment',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('entity', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.BigInteger(), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.BigInteger(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_by', sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_tab_comment_entity'), 'tab_comment', ['entity'], unique=False)
    op.create_index(op.f('ix_tab_comment_entity_id'), 'tab_comment', ['entity_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_tab_comment_entity_id'), table_name='tab_comment')
    op.drop_index(op.f('ix_tab_comment_entity'), table_name='tab_comment')
    op.drop_table('tab_comment')
