"""agent hub: bang tab_agent_google_link — noi Google ca nhan tung nguoi (ai-CR-064, M-06)

Revision ID: d2f7b4a9c6e1
Revises: c9d4a2e6f1b8
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'd2f7b4a9c6e1'
down_revision: Union[str, None] = 'c9d4a2e6f1b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('tab_agent_google_link',
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('scopes', sa.String(length=500), nullable=False),
    sa.Column('refresh_token_enc', sa.Text(), nullable=False),
    sa.Column('access_token_enc', sa.Text(), nullable=False),
    sa.Column('access_expires_at', sa.DateTime(), nullable=True),
    sa.Column('revoked_at', sa.DateTime(), nullable=True),
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.BigInteger(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_by', sa.BigInteger(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tab_agent_google_link_user_id'), 'tab_agent_google_link', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_tab_agent_google_link_user_id'), table_name='tab_agent_google_link')
    op.drop_table('tab_agent_google_link')
