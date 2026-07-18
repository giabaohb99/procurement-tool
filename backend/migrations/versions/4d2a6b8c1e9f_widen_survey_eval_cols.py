"""noi rong cac cot danh gia dong khao sat (String20 -> 255) de import khong bi cat

Revision ID: 4d2a6b8c1e9f
Revises: 3c1d9e2f8a7b
Create Date: 2026-07-18
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "4d2a6b8c1e9f"
down_revision: Union[str, None] = "3c1d9e2f8a7b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_SUP = [("tab_survey_supplier_line", "reliability"), ("tab_survey_supplier_line", "nspt_note"),
        ("tab_survey_supplier_line", "line_approve")]
_PROD = [("tab_survey_product_line", "lab_result"), ("tab_survey_product_line", "nspt_note"),
         ("tab_survey_product_line", "line_approve")]


def upgrade() -> None:
    for tbl, col in _SUP + _PROD:
        op.alter_column(tbl, col, type_=sa.String(length=255), existing_type=sa.String(length=20),
                        existing_nullable=False)


def downgrade() -> None:
    for tbl, col in _SUP + _PROD:
        op.alter_column(tbl, col, type_=sa.String(length=20), existing_type=sa.String(length=255),
                        existing_nullable=False)
