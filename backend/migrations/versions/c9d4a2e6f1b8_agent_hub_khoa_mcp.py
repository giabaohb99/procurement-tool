"""agent hub: bang tab_agent_mcp_key — khoa ket noi MCP ca nhan (ai-CR-063, M-02)

Revision ID: c9d4a2e6f1b8
Revises: c490e1f2a3b4
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c9d4a2e6f1b8'
down_revision: Union[str, None] = 'c490e1f2a3b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('tab_agent_mcp_key',
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.Column('name', sa.String(length=80), nullable=False),
    sa.Column('token_hash', sa.String(length=64), nullable=False),
    sa.Column('key_hint', sa.String(length=8), nullable=False),
    sa.Column('scope', sa.SmallInteger(), nullable=False),
    sa.Column('expires_at', sa.DateTime(), nullable=True),
    sa.Column('last_used_at', sa.DateTime(), nullable=True),
    sa.Column('revoked_at', sa.DateTime(), nullable=True),
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('created_by', sa.BigInteger(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_by', sa.BigInteger(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tab_agent_mcp_key_user_id'), 'tab_agent_mcp_key', ['user_id'], unique=False)
    op.create_index(op.f('ix_tab_agent_mcp_key_token_hash'), 'tab_agent_mcp_key', ['token_hash'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_tab_agent_mcp_key_token_hash'), table_name='tab_agent_mcp_key')
    op.drop_index(op.f('ix_tab_agent_mcp_key_user_id'), table_name='tab_agent_mcp_key')
    op.drop_table('tab_agent_mcp_key')
