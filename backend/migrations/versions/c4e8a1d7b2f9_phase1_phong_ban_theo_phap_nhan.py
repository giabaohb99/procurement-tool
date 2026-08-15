"""phase1 phong ban theo phap nhan

Revision ID: c4e8a1d7b2f9
Revises: a1c7f4d92e63, b62f3c8d1a04
Create Date: 2026-08-15 16:10:00.000000

Gộp hai head hiện có và tạo bảng A06. Dòng pháp nhân gốc của từng phòng được
backfill từ hai cột legacy để sau migration giao diện có dữ liệu ngay.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c4e8a1d7b2f9"
down_revision: Union[str, Sequence[str], None] = (
    "a1c7f4d92e63",
    "b62f3c8d1a04",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tab_department_company",
        sa.Column("department_id", sa.BigInteger(), nullable=False),
        sa.Column("company_id", sa.BigInteger(), nullable=False),
        sa.Column("manager_employee_id", sa.BigInteger(), nullable=True),
        sa.Column("issue_code_override", sa.String(length=20), nullable=False,
                  server_default=""),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("created_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(
            ["company_id"], ["tab_company.id"],
            name="fk_department_company_company", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["department_id"], ["tab_department.id"],
            name="fk_department_company_department", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["manager_employee_id"], ["tab_employee.id"],
            name="fk_department_company_manager", ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("department_id", "company_id", name="uq_department_company"),
    )
    op.create_index(
        "ix_tab_department_company_department_id",
        "tab_department_company",
        ["department_id"],
    )
    op.create_index(
        "ix_tab_department_company_company_id",
        "tab_department_company",
        ["company_id"],
    )

    # Không có chữ tiếng Việt trong DML; dữ liệu tên/mã được nạp bằng seed
    # Python/SQLAlchemy theo quy định của repository.
    op.execute(sa.text("""
        INSERT INTO tab_department_company
            (department_id, company_id, manager_employee_id,
             issue_code_override, is_active, created_by, updated_by)
        SELECT d.id, d.company_id, NULLIF(d.manager_id, 0), '', d.is_active, 0, 0
        FROM tab_department AS d
        WHERE d.company_id > 0
    """))


def downgrade() -> None:
    op.drop_table("tab_department_company")
