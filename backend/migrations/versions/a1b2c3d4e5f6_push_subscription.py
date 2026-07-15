"""push_subscription table

Revision ID: a1b2c3d4e5f6
Revises: 997591492479
Create Date: 2026-07-15
"""
from alembic import op
import sqlalchemy as sa

revision = "a1b2c3d4e5f6"
down_revision = "997591492479"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "tab_push_subscription",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), nullable=True, index=True),
        sa.Column("endpoint", sa.Text(), nullable=True),
        sa.Column("p256dh", sa.String(length=255), nullable=True),
        sa.Column("auth", sa.String(length=255), nullable=True),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.Column("updated_by", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )


def downgrade():
    op.drop_table("tab_push_subscription")
