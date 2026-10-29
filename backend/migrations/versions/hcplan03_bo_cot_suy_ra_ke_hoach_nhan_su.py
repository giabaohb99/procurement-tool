"""bo_cot_suy_ra_ke_hoach_nhan_su: DROP planned_headcount / planned_payroll_monthly

Revision ID: hcplan03
Revises: hcplan02
Create Date: 2026-10-28

duoc-CR-690 (phase 24). Bao cao A4 / A5 doc ke hoach co hieu luc theo thang (`headcount_plan.effective`) nen hai cot suy ra
cua dot 4 khong con ai doc / ghi. Downgrade dung lai hai cot (mac dinh 0; khong con suy lai tu dong ke hoach tu duoc-CR-692).

VIET TAY (tuong duong autogenerate da got): repo nay autogenerate troi ~650 dong moi lan.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "hcplan03"
down_revision: Union[str, None] = "hcplan02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("tab_headcount_plan", "planned_payroll_monthly")
    op.drop_column("tab_headcount_plan", "planned_headcount")


def downgrade() -> None:
    op.add_column("tab_headcount_plan", sa.Column("planned_headcount", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("tab_headcount_plan", sa.Column("planned_payroll_monthly", sa.BigInteger(), nullable=False,
                                                  server_default="0"))
    #  duoc-CR-692: khong suy lai gia tri nua (module `headcount_plan`/`costing` da xoa). Khi ha cap tu hcplan05, cac bang ke
    #  hoach duoc dung lai RONG nen khong co hang nao can suy; hai cot giu mac dinh 0.
