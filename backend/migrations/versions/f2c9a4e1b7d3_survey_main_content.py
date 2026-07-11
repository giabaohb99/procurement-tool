"""them cot main_content (noi dung chinh) cho tab_survey

Revision ID: f2c9a4e1b7d3
Revises: 5ad008ca924e
Create Date: 2026-07-11

"""
from alembic import op
import sqlalchemy as sa

revision = "f2c9a4e1b7d3"
down_revision = "5ad008ca924e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tab_survey", sa.Column("main_content", sa.String(length=500), nullable=False, server_default=""))


def downgrade() -> None:
    op.drop_column("tab_survey", "main_content")
