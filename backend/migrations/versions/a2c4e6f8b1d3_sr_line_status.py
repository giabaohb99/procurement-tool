"""them cot line_status cho tab_survey_request_line

Revision ID: a2c4e6f8b1d3
Revises: 8b6f0d4c2e51
Create Date: 2026-07-22

Task 2 (CR-007): trạng thái theo dòng khảo sát do người YC / phòng ban YC cập nhật.
Giá trị: "" chưa xác định · "can_khao_sat_lai" cần khảo sát lại · "hoan_thanh" hoàn thành.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a2c4e6f8b1d3"
down_revision: Union[str, None] = "8b6f0d4c2e51"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tab_survey_request_line",
                  sa.Column("line_status", sa.String(length=30), nullable=False, server_default=""))
    op.create_index("ix_tab_survey_request_line_line_status",
                    "tab_survey_request_line", ["line_status"])


def downgrade() -> None:
    op.drop_index("ix_tab_survey_request_line_line_status",
                  table_name="tab_survey_request_line")
    op.drop_column("tab_survey_request_line", "line_status")
