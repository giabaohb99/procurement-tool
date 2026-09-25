"""bao-CR-490: cot truong phong phe duyet tren YCMH, YCBG, DMH

`approver_employee_id` = nhan su thuc bam Duyet o chang truong phong. Ban in noi bo cho chon o ky
hien nguoi duyet hay truong phong theo ho so phong ban. Phieu cu de 0 (ban in lui ve nhat ky).

Revision ID: a490b1c2d3e4
Revises: e6b1d4f8a2c7
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a490b1c2d3e4'
down_revision: Union[str, None] = 'e6b1d4f8a2c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLES = ("tab_purchase_request", "tab_survey_request", "tab_purchase_order")


def upgrade() -> None:
    for table in TABLES:
        op.add_column(table, sa.Column("approver_employee_id", sa.BigInteger(), nullable=False,
                                       server_default="0"))


def downgrade() -> None:
    for table in TABLES:
        op.drop_column(table, "approver_employee_id")
