"""tra cuu thi truong: bang lo xuat toan bo chay nen (bao-CR-718 phan 2)

Revision ID: hqx718b
Revises: invuq717

tab_customs_export_batch: moi lo xuat toan bo (hoac theo bo loc) chia nhieu tep .xlsx, moi tep mot task Celery.
active_user_id UNIQUE (NULL khi lo da ket thuc) = moi nguoi mot lo dang chay. Chi tao khi thieu (chay lai duoc).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "hqx718b"
down_revision: Union[str, None] = "invuq717"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "tab_customs_export_batch"


def upgrade() -> None:
    if TABLE in sa.inspect(op.get_bind()).get_table_names():
        return
    op.create_table(
        TABLE,
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        # CustomsExportStatus: 1 cho, 2 dang xuat, 3 xong, 4 loi, 5 da dung, 6 het han.
        sa.Column("status", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("active_user_id", sa.BigInteger(), nullable=True),
        sa.Column("filters", sa.JSON(), nullable=True),
        sa.Column("filter_summary", sa.String(500), nullable=False, server_default=""),
        sa.Column("total_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rows_per_file", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("file_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("files_done", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rows_done", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_id", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("last_id", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("files", sa.JSON(), nullable=True),
        sa.Column("error", sa.String(500), nullable=False, server_default=""),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column("updated_by", sa.BigInteger(), nullable=True),
        sa.UniqueConstraint("active_user_id", name="uq_customs_export_active_user"),
    )
    op.create_index("ix_customs_export_batch_creator", TABLE, ["created_by", "id"])
    op.create_index("ix_customs_export_batch_status", TABLE, ["status"])


def downgrade() -> None:
    if TABLE in sa.inspect(op.get_bind()).get_table_names():
        op.drop_table(TABLE)
