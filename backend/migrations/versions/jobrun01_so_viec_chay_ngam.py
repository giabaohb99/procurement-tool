"""so viec chay ngam: tab_job_run (bao-CR-703)

Revision ID: jobrun01
Revises: mcplog03

Mỗi lần một task Celery của ERP chạy là một dòng (ghi bằng tín hiệu task_prerun / task_postrun / task_failure).
Chỉ tạo khi thiếu. Không có bản cặp ở migrations_agent: tiến trình dịch vụ AI tách riêng không ghi sổ này.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "jobrun01"
down_revision: Union[str, None] = "mcplog03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "tab_job_run"


def upgrade() -> None:
    if TABLE in sa.inspect(op.get_bind()).get_table_names():
        return
    op.create_table(
        TABLE,
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("task_name", sa.String(120), nullable=False, server_default=""),
        sa.Column("task_id", sa.String(64), nullable=False, server_default=""),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("status", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("result_summary", sa.Text(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("worker", sa.String(120), nullable=False, server_default=""),
    )
    op.create_index("ix_job_run_task_started", TABLE, ["task_name", "started_at"])
    op.create_index("ix_tab_job_run_task_id", TABLE, ["task_id"])
    op.create_index("ix_tab_job_run_started_at", TABLE, ["started_at"])


def downgrade() -> None:
    if TABLE in sa.inspect(op.get_bind()).get_table_names():
        op.drop_table(TABLE)
