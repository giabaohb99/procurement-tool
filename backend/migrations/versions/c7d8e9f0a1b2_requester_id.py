"""them requester_id cho survey_request + purchase_request (so scope theo nguoi yeu cau)

Revision ID: c7d8e9f0a1b2
Revises: a1b2c3d4e5f6
Create Date: 2026-07-16
"""
from alembic import op
import sqlalchemy as sa

revision = "c7d8e9f0a1b2"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def _has_col(insp, table, col):
    return col in [c["name"] for c in insp.get_columns(table)]


def upgrade():
    insp = sa.inspect(op.get_bind())
    for table in ("tab_survey_request", "tab_purchase_request"):
        if not _has_col(insp, table, "requester_id"):
            op.add_column(table, sa.Column("requester_id", sa.BigInteger(), nullable=False, server_default="0"))
            op.create_index(f"ix_{table}_requester_id", table, ["requester_id"])


def downgrade():
    for table in ("tab_survey_request", "tab_purchase_request"):
        op.drop_index(f"ix_{table}_requester_id", table_name=table)
        op.drop_column(table, "requester_id")
