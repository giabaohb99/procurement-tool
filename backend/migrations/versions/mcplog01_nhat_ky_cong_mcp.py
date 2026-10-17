"""nhat ky luot goi cong MCP + bang dem theo ngay (ai-CR-209, K3 doc/erp/21 §4.3 + §5.4)

Revision ID: mcplog01
Revises: grp14

Hai bảng của DỊCH VỤ AI (tiền tố `tab_agent_`): ở chế độ nhúng nằm chung DB ERP (migration này), ở chế độ tách nằm ở DB
`agent_hub` (cặp với `migrations_agent/versions/agent0011_nhat_ky_cong_mcp.py`). `status` = mcp_log.CallStatus
(1 thành công · 2 bị từ chối · 3 lỗi).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "mcplog01"
down_revision: Union[str, None] = "grp14"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CALL = "tab_agent_mcp_call"
DAILY = "tab_agent_mcp_call_daily"


def _tables() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def upgrade() -> None:
    have = _tables()
    if CALL not in have:
        op.create_table(
            CALL,
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column("key_id", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("user_id", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("employee_id", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("department_id", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("company_id", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("client_name", sa.String(100), nullable=False, server_default=""),
            sa.Column("method", sa.String(40), nullable=False, server_default=""),
            sa.Column("tool", sa.String(80), nullable=False, server_default=""),
            sa.Column("skill_id", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("status", sa.SmallInteger(), nullable=False, server_default="1"),
            sa.Column("deny_reason", sa.String(200), nullable=False, server_default=""),
            sa.Column("duration_ms", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("ip", sa.String(45), nullable=False, server_default=""),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_tab_agent_mcp_call_created_at", CALL, ["created_at"])
        op.create_index("ix_agent_mcp_call_user_created", CALL, ["user_id", "created_at"])
        op.create_index("ix_agent_mcp_call_key_created", CALL, ["key_id", "created_at"])
    if DAILY not in have:
        op.create_table(
            DAILY,
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column("day", sa.Date(), nullable=False),
            sa.Column("user_id", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("key_id", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("method", sa.String(40), nullable=False, server_default=""),
            sa.Column("tool", sa.String(80), nullable=False, server_default=""),
            sa.Column("status", sa.SmallInteger(), nullable=False, server_default="1"),
            sa.Column("calls", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("total_ms", sa.BigInteger(), nullable=False, server_default="0"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_tab_agent_mcp_call_daily_day", DAILY, ["day"])
        op.create_index("ux_agent_mcp_call_daily", DAILY, ["day", "user_id", "key_id", "method", "tool", "status"],
                        unique=True)


def downgrade() -> None:
    have = _tables()
    if DAILY in have:
        op.drop_table(DAILY)
    if CALL in have:
        op.drop_table(CALL)
