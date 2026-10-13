"""so thay doi do bot ghi + hoan tac 24 gio (ai-CR-182, phase 15.1)

Revision ID: grp14
Revises: grp13

Bang `tab_assistant_change` (DB ERP, KHONG phai bang cua dich vu AI): moi lan nguoi dung xac nhan
cho bot ghi phieu thi them mot dong — anh truoc / sau (JSON), dau trang thai phieu sau khi ghi,
kenh, trang thai hoan tac. Model: `app/modules/assistant/change_model.py`.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "grp14"
down_revision: Union[str, None] = "grp13"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "tab_assistant_change"


def upgrade() -> None:
    op.create_table(
        TABLE,
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("entity", sa.String(50), nullable=False, server_default=""),
        sa.Column("entity_id", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("doc_code", sa.String(50), nullable=False, server_default=""),
        # ChangeAction: 1 tao · 2 sua · 3 xoa · 4 gui duyet · 5 dung lai nhap · 6 lap bo tai khoan.
        sa.Column("action", sa.SmallInteger(), nullable=False, server_default="2"),
        sa.Column("summary", sa.String(300), nullable=False, server_default=""),
        sa.Column("before", sa.JSON(), nullable=True),
        sa.Column("after", sa.JSON(), nullable=True),
        sa.Column("after_sig", sa.String(64), nullable=False, server_default=""),
        # ChangeSource: 0 khong ro · 1 telegram · 2 web · 3 zalo.
        sa.Column("source", sa.SmallInteger(), nullable=False, server_default="0"),
        # UndoStatus: 0 chua · 1 da hoan tac · 2 bi chan.
        sa.Column("undo_status", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("undone_at", sa.DateTime(), nullable=True),
        sa.Column("undone_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("undo_of", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_assistant_change_user_created", TABLE, ["user_id", "created_at"])
    op.create_index("ix_assistant_change_entity", TABLE, ["entity", "entity_id"])


def downgrade() -> None:
    op.drop_index("ix_assistant_change_entity", table_name=TABLE)
    op.drop_index("ix_assistant_change_user_created", table_name=TABLE)
    op.drop_table(TABLE)
