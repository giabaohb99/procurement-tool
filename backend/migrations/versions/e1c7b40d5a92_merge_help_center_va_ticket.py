"""merge 2 nhanh: help-center (bd92193a9cf7) + ticket (d8f1a3c5e7b9)

Revision ID: e1c7b40d5a92
Revises: bd92193a9cf7, d8f1a3c5e7b9
Create Date: 2026-08-05

Merge nhanh `main` (phieu ho tro / ticket) vao nhanh `bao` (Help Center).
Chi noi 2 head lai, KHONG doi schema.
"""
from alembic import op
import sqlalchemy as sa


revision = 'e1c7b40d5a92'
down_revision = ('bd92193a9cf7', 'd8f1a3c5e7b9')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
