"""tab_seal_request_company: bang noi 1 yeu cau dong dau -> nhieu cong ty

Revision ID: seal2multi01
Revises: seal1status01
Create Date: 2026-09-05

Duyet dau: mot phieu can dong dau cua NHIEU cong ty. `company_id` tren phieu giu lai
la cong ty chinh; danh sach day du o bang noi nay. Chua co du lieu cu can di doi.
"""
from alembic import op
import sqlalchemy as sa

revision = "seal2multi01"
down_revision = "seal1status01"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "tab_seal_request_company",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("seal_request_id", sa.BigInteger(), nullable=False),
        sa.Column("company_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("updated_by", sa.BigInteger(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_seal_req_company_req", "tab_seal_request_company", ["seal_request_id"])
    op.create_index("ix_seal_req_company_company", "tab_seal_request_company", ["company_id"])


def downgrade():
    op.drop_index("ix_seal_req_company_company", table_name="tab_seal_request_company")
    op.drop_index("ix_seal_req_company_req", table_name="tab_seal_request_company")
    op.drop_table("tab_seal_request_company")
