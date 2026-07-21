"""bang tab_survey_request_pr (lien ket YCKS-dong <-> YCMH, cho phep 1 dong tao nhieu YCMH)

Revision ID: 7a5e9c3b1f42
Revises: 6f4d2c8a1b30
Create Date: 2026-07-20
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "7a5e9c3b1f42"
down_revision: Union[str, None] = "6f4d2c8a1b30"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tab_survey_request_pr",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("survey_request_id", sa.BigInteger(), nullable=False),
        sa.Column("survey_request_line_id", sa.BigInteger(), nullable=False),
        sa.Column("option_id", sa.BigInteger(), server_default="0"),
        sa.Column("product_survey_line_id", sa.BigInteger(), server_default="0"),
        sa.Column("pr_id", sa.BigInteger(), nullable=False),
        sa.Column("pr_code", sa.String(length=50), server_default=""),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("created_by", sa.BigInteger(), server_default="0"),
        sa.Column("updated_by", sa.BigInteger(), server_default="0"),
    )
    op.create_index(op.f("ix_tab_survey_request_pr_survey_request_id"), "tab_survey_request_pr", ["survey_request_id"])
    op.create_index(op.f("ix_tab_survey_request_pr_survey_request_line_id"), "tab_survey_request_pr", ["survey_request_line_id"])
    op.create_index(op.f("ix_tab_survey_request_pr_option_id"), "tab_survey_request_pr", ["option_id"])
    op.create_index(op.f("ix_tab_survey_request_pr_pr_id"), "tab_survey_request_pr", ["pr_id"])

    # Backfill YCMH đã tạo trước đây (mỗi dòng completed = 1 YCMH) vào bảng liên kết.
    op.execute("""
        INSERT INTO tab_survey_request_pr
            (survey_request_id, survey_request_line_id, option_id, product_survey_line_id, pr_id, pr_code, created_by, updated_by)
        SELECT l.survey_request_id, l.id,
               COALESCE((SELECT o.id FROM tab_survey_request_option o
                         WHERE o.survey_request_line_id = l.id AND o.is_chosen = 1 LIMIT 1), 0),
               COALESCE((SELECT o.product_survey_line_id FROM tab_survey_request_option o
                         WHERE o.survey_request_line_id = l.id AND o.is_chosen = 1 LIMIT 1), 0),
               l.pr_id, COALESCE(l.pr_code, ''), 0, 0
        FROM tab_survey_request_line l
        WHERE l.pr_id IS NOT NULL AND l.pr_id <> 0
    """)

    # Mô hình mới: sau khi tạo YCMH thì tự bỏ chọn. Đồng bộ data cũ -> bỏ chọn option ở các
    # dòng đã tạo YCMH (tránh vô tình tạo YCMH trùng khi mở lại phiếu done cũ).
    op.execute("""
        UPDATE tab_survey_request_option o
        JOIN tab_survey_request_line l ON l.id = o.survey_request_line_id
        SET o.is_chosen = 0
        WHERE l.pr_id IS NOT NULL AND l.pr_id <> 0 AND o.is_chosen = 1
    """)


def downgrade() -> None:
    op.drop_table("tab_survey_request_pr")
