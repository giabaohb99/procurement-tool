"""agent hub: OAuth cho cong MCP: ung dung tu dang ky + ma cap quyen + cot ket noi OAuth tren khoa (ai-CR-218, K14 doc/erp/21 §7.2)

Revision ID: agent0013
Revises: agent0012

Bảng của DỊCH VỤ AI (tiền tố `tab_agent_`): ở chế độ nhúng nằm chung DB ERP (migration này), ở chế độ tách nằm ở DB
`agent_hub` (cặp với `migrations/versions/mcpoauth01_oauth_cong_mcp.py`). Chỉ tạo / thêm khi thiếu.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "agent0013"
down_revision: Union[str, None] = "agent0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

KEY = "tab_agent_mcp_key"
CLIENT = "tab_agent_oauth_client"
CODE = "tab_agent_oauth_code"
KEY_COLUMNS = (
    ("kind", lambda: sa.Column("kind", sa.SmallInteger(), nullable=False, server_default="1")),
    ("oauth_client_id", lambda: sa.Column("oauth_client_id", sa.BigInteger(), nullable=False, server_default="0")),
    ("access_expires_at", lambda: sa.Column("access_expires_at", sa.DateTime(), nullable=True)),
    ("refresh_hash", lambda: sa.Column("refresh_hash", sa.String(64), nullable=False, server_default="")),
)


def _insp():
    return sa.inspect(op.get_bind())


def upgrade() -> None:
    insp = _insp()
    have = {c["name"] for c in insp.get_columns(KEY)}
    for name, col in KEY_COLUMNS:
        if name not in have:
            op.add_column(KEY, col())
    if "ix_tab_agent_mcp_key_refresh_hash" not in {i["name"] for i in insp.get_indexes(KEY)}:
        op.create_index("ix_tab_agent_mcp_key_refresh_hash", KEY, ["refresh_hash"])
    tables = set(insp.get_table_names())
    if CLIENT not in tables:
        op.create_table(
            CLIENT,
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column("client_id", sa.String(64), nullable=False, server_default=""),
            sa.Column("client_name", sa.String(200), nullable=False, server_default=""),
            sa.Column("redirect_uris", sa.JSON(), nullable=True),
            sa.Column("token_endpoint_auth_method", sa.String(30), nullable=False, server_default="none"),
            sa.Column("client_secret_hash", sa.String(64), nullable=False, server_default=""),
            sa.Column("ip", sa.String(45), nullable=False, server_default=""),
            sa.Column("last_used_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("created_by", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_by", sa.BigInteger(), nullable=False, server_default="0"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_tab_agent_oauth_client_client_id", CLIENT, ["client_id"])
    if CODE not in tables:
        op.create_table(
            CODE,
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column("code_hash", sa.String(64), nullable=False, server_default=""),
            sa.Column("client_pk", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("user_id", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("redirect_uri", sa.String(500), nullable=False, server_default=""),
            sa.Column("code_challenge", sa.String(128), nullable=False, server_default=""),
            sa.Column("scope", sa.SmallInteger(), nullable=False, server_default="0"),
            sa.Column("resource", sa.String(500), nullable=False, server_default=""),
            sa.Column("expires_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("used_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_tab_agent_oauth_code_code_hash", CODE, ["code_hash"])


def downgrade() -> None:
    insp = _insp()
    tables = set(insp.get_table_names())
    for t in (CODE, CLIENT):
        if t in tables:
            op.drop_table(t)
    if "ix_tab_agent_mcp_key_refresh_hash" in {i["name"] for i in insp.get_indexes(KEY)}:
        op.drop_index("ix_tab_agent_mcp_key_refresh_hash", table_name=KEY)
    have = {c["name"] for c in insp.get_columns(KEY)}
    for name, _col in reversed(KEY_COLUMNS):
        if name in have:
            op.drop_column(KEY, name)
