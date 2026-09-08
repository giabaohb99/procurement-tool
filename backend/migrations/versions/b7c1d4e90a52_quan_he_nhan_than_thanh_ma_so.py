"""quan_he_nhan_than_thanh_ma_so — `relation` của hai bảng con: VARCHAR → SMALLINT

Khách chốt 08/09/2026: ô «Quan hệ» phải là Ô CHỌN, không nhập tay. Thành danh
sách cố định thì R2/QĐ-11 áp dụng — lưu `SMALLINT` + `IntEnum`, không lưu chữ.
Bộ mã ở `app/modules/employee/constants.py` (`RELATION_LABELS`).

Vì sao đổi NGAY: hai bảng con ra đời cùng ngày (`a3f8e9d62714`) và **chưa lên
prod**, nên chưa có dữ liệu thật để dịch. Để tới lúc có thì phải viết một
migration đọc từng chuỗi rồi đoán ý người gõ («vợ» · «Vợ» · «v/c» · «vo») —
đúng thứ luật R2 sinh ra để tránh.

⚠️ `DROP` rồi `ADD` chứ không `ALTER TYPE`: MySQL không đổi được `VARCHAR` sang
`SMALLINT` khi cột có dữ liệu chữ, mà ở đây dữ liệu duy nhất là mấy dòng thử
trên máy lập trình viên. Nói thẳng ra để không ai nhầm là mất dữ liệu thật.

Revision ID: b7c1d4e90a52
Revises: a3f8e9d62714
Create Date: 2026-09-08 10:30:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'b7c1d4e90a52'
down_revision: Union[str, None] = 'a3f8e9d62714'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLES = ("tab_employee_contact", "tab_employee_family")


def upgrade() -> None:
    for table in _TABLES:
        op.drop_column(table, "relation")
        op.add_column(table, sa.Column("relation", sa.SmallInteger(),
                                       nullable=False, server_default="0"))


def downgrade() -> None:
    for table in _TABLES:
        op.drop_column(table, "relation")
        op.add_column(table, sa.Column("relation", sa.String(50),
                                       nullable=False, server_default=""))
