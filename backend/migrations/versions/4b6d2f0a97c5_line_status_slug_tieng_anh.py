"""Doi line_status cua dong khao sat sang slug tieng Anh

Truoc: "" | "can_khao_sat_lai" | "hoan_thanh"  (tieng Viet khong dau)
Sau:   "" | "resurvey"         | "completed"   (khop cot `status` cung bang)

Revision ID: 4b6d2f0a97c5
Revises: 21aa1787c80f
"""
from alembic import op
import sqlalchemy as sa

revision = "4b6d2f0a97c5"
down_revision = "21aa1787c80f"
branch_labels = None
depends_on = None

MAP = [("can_khao_sat_lai", "resurvey"), ("hoan_thanh", "completed")]


def upgrade() -> None:
    for cu, moi in MAP:
        op.execute(sa.text(
            "UPDATE tab_survey_request_line SET line_status = :moi WHERE line_status = :cu"
        ).bindparams(cu=cu, moi=moi))


def downgrade() -> None:
    for cu, moi in MAP:
        op.execute(sa.text(
            "UPDATE tab_survey_request_line SET line_status = :cu WHERE line_status = :moi"
        ).bindparams(cu=cu, moi=moi))
