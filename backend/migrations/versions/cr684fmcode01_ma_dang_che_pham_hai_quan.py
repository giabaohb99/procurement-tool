"""duoc-CR-684 — danh mục tra cứu «Mã dạng chế phẩm» (EC, SC, WG…) của màn Tra cứu thị trường.

Bảng chỉ để tra cứu / cấu hình, nạp dữ liệu bằng scripts/load_customs_lookup_config_cr684.py.

Revision ID: cr684fmcode01
Revises: cr682erpact01
"""
import sqlalchemy as sa
from alembic import op

revision = "cr684fmcode01"
down_revision = "cr682erpact01"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "tab_customs_formulation_code",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("name_en", sa.String(100), nullable=False, server_default=""),
        sa.Column("name_vi", sa.String(100), nullable=False, server_default=""),
        sa.Column("description", sa.String(255), nullable=False, server_default=""),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("created_by", sa.BigInteger(), server_default="0"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_by", sa.BigInteger(), server_default="0"),
        sa.UniqueConstraint("code", name="uq_customs_formulation_code"),
    )


def downgrade():
    op.drop_table("tab_customs_formulation_code")
