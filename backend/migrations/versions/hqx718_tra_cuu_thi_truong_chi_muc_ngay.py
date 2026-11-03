"""tra cuu thi truong: chi muc theo ngay cho danh sach (bao-CR-718)

Revision ID: hqx718
Revises: lvpol717

ix_customs_line_date (reg_date): man danh sach sap "ngay dang ky giam dan, id giam dan" + LIMIT. Thieu chi muc nay MySQL
quet ca bang roi sap xep (do tren bang thu 328 nghin dong: 352 ms trang 1 khong loc, 739 ms khi co tu khoa). Co chi muc
thi di nguoc chi muc va dung som (0,1 ms / 9 ms). Bang chia phan vung theo nam cua reg_date nen chi muc nay hop le.
Chi them khi thieu (chay lai duoc).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "hqx718"
down_revision: Union[str, None] = "lvpol717"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

LINE = "tab_customs_line"
DATE_INDEX = "ix_customs_line_date"


def upgrade() -> None:
    insp = sa.inspect(op.get_bind())
    if DATE_INDEX not in {i["name"] for i in insp.get_indexes(LINE)}:
        op.create_index(DATE_INDEX, LINE, ["reg_date"])


def downgrade() -> None:
    insp = sa.inspect(op.get_bind())
    if DATE_INDEX in {i["name"] for i in insp.get_indexes(LINE)}:
        op.drop_index(DATE_INDEX, table_name=LINE)
