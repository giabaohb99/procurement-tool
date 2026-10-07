"""agent hub: phien bien ban hop tu ghi am / video (ai-CR-104, phase 10 buoc 10.1)

Bang moi tab_agent_meeting; khong dung bang cu. Ban chep loi dai nen dung MEDIUMTEXT.

Revision ID: meet01
Revises: pitem01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = "meet01"
down_revision: Union[str, None] = "pitem01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tab_agent_meeting",
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("chat_id", sa.String(length=50), nullable=False, server_default=""),
        sa.Column("source_kind", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("source_ref", sa.String(length=300), nullable=False, server_default=""),
        sa.Column("title", sa.String(length=200), nullable=False, server_default=""),
        sa.Column("mime", sa.String(length=80), nullable=False, server_default=""),
        sa.Column("status", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("template", sa.String(length=40), nullable=False, server_default=""),
        sa.Column("duration_sec", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("transcript", sa.Text().with_variant(mysql.MEDIUMTEXT(), "mysql"), nullable=False),
        sa.Column("recap", sa.Text(), nullable=False),
        sa.Column("note_id", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("drive_file_id", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("error", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tab_agent_meeting_user_id", "tab_agent_meeting", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_tab_agent_meeting_user_id", table_name="tab_agent_meeting")
    op.drop_table("tab_agent_meeting")
