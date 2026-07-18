"""them import_key vao tab_survey (khoa idempotent khi import)

Revision ID: 3c1d9e2f8a7b
Revises: 2bad028f037a
Create Date: 2026-07-18
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "3c1d9e2f8a7b"
down_revision: Union[str, None] = "2bad028f037a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tab_survey", sa.Column("import_key", sa.String(length=160), nullable=False, server_default=""))
    op.create_index(op.f("ix_tab_survey_import_key"), "tab_survey", ["import_key"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_tab_survey_import_key"), table_name="tab_survey")
    op.drop_column("tab_survey", "import_key")
