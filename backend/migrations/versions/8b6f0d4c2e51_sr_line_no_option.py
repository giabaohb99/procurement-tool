"""them cot no_option cho dong YCKS (chot rong - khong co phuong an phu hop)

Revision ID: 8b6f0d4c2e51
Revises: 7a5e9c3b1f42
Create Date: 2026-07-21
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "8b6f0d4c2e51"
down_revision: Union[str, None] = "7a5e9c3b1f42"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tab_survey_request_line",
                  sa.Column("no_option", sa.Boolean(), nullable=False, server_default=sa.text("0")))


def downgrade() -> None:
    op.drop_column("tab_survey_request_line", "no_option")
