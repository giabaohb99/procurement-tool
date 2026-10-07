"""hop_dong_lao_dong: tab_labor_contract_template + tab_labor_contract

Revision ID: lbrct01
Revises: aikey01
Create Date: 2026-10-05

HDLD cua nhan su + mau .docx theo phap nhan. Thiet ke: plan
`frontend-v2/plans/261005-1537-hop-dong-lao-dong-mau-theo-phap-nhan/phase-01-*.md`.

VIET TAY (cat tu autogenerate), chi dung 2 bang nay -- repo autogenerate troi ~650 dong.
Cac cot *_id la FK MEM (khong ForeignKey thuc), don o tang service.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "lbrct01"
down_revision: Union[str, None] = "aikey01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _audit_cols() -> list[sa.Column]:
    """Cot chuan AuditMixin (id + created/updated)."""
    return [
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
    ]


def upgrade() -> None:
    op.create_table(
        "tab_labor_contract_template",
        sa.Column("company_id", sa.BigInteger(), nullable=False),
        # LaborContractType (app/core/labor_contract_codes.py)
        sa.Column("contract_type", sa.SmallInteger(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("note", sa.String(500), nullable=False, server_default=""),
        sa.Column("file_id", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("original_filename", sa.String(255), nullable=False, server_default=""),
        sa.Column("placeholders", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        *_audit_cols(),
        sa.UniqueConstraint("company_id", "name", name="uq_labor_contract_template_company_name"),
    )
    op.create_index("ix_tab_labor_contract_template_company_id", "tab_labor_contract_template", ["company_id"])
    op.create_index("ix_labor_contract_template_pick", "tab_labor_contract_template",
                    ["company_id", "contract_type", "is_active"])

    op.create_table(
        "tab_labor_contract",
        sa.Column("code", sa.String(25), nullable=False),
        sa.Column("contract_no", sa.String(50), nullable=False, server_default=""),
        sa.Column("employee_id", sa.BigInteger(), nullable=False),
        sa.Column("company_id", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("department_id", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("template_id", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("contract_type", sa.SmallInteger(), nullable=False),
        # LaborContractStatus; EXPIRED (3) suy ra, khong ghi DB.
        sa.Column("status", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("sign_date", sa.Date(), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("job_title", sa.String(100), nullable=False, server_default=""),
        sa.Column("work_location", sa.String(255), nullable=False, server_default=""),
        sa.Column("base_salary", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("insurance_salary", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("allowance", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("allowance_note", sa.String(500), nullable=False, server_default=""),
        sa.Column("note", sa.String(500), nullable=False, server_default=""),
        sa.Column("generated_file_id", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("generated_at", sa.DateTime(), nullable=True),
        sa.Column("generated_by", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("signed_file_id", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("terminated_date", sa.Date(), nullable=True),
        sa.Column("terminate_reason", sa.String(500), nullable=False, server_default=""),
        *_audit_cols(),
        sa.UniqueConstraint("code", name="uq_tab_labor_contract_code"),
    )
    op.create_index("ix_labor_contract_emp_start", "tab_labor_contract", ["employee_id", "start_date"])
    op.create_index("ix_labor_contract_company_status", "tab_labor_contract", ["company_id", "status"])


def downgrade() -> None:
    op.drop_table("tab_labor_contract")
    op.drop_table("tab_labor_contract_template")
