"""Bang phan cong NSTM theo phan loai co them cot phong ban (bao-CR-414 giai doan 2)

Revision ID: b8e5f2a1c7d3
Revises: a7d414c0b1e2
Create Date: 2026-09-17

Phong ban tu mua hang — giai doan 2. Truoc day moi phan loai chi co MOT cap NSTM
(chinh + du phong) dung chung ca cong ty. Nay nha may tu mua hang nen phai co bo
phan cong rieng: cot `department_id` (0 = thu mua chung, dung cho moi phong khong
co bo rieng), khoa duy nhat doi tu (item_group_id) sang (department_id, item_group_id).

Du lieu cu giu nguyen voi department_id = 0, tuc van la bo phan cong chung.
"""

from alembic import op
import sqlalchemy as sa

revision = "b8e5f2a1c7d3"
down_revision = "a7d414c0b1e2"
branch_labels = None
depends_on = None

_TABLE = "tab_category_assignee"
_OLD_UNIQUE = "ix_tab_category_assignee_item_group_id"
_NEW_UNIQUE = "uq_category_assignee_dept_group"
_DEPT_INDEX = "ix_tab_category_assignee_department_id"


def upgrade() -> None:
    op.add_column(_TABLE, sa.Column("department_id", sa.BigInteger(), nullable=False,
                                    server_default="0"))
    op.create_index(_DEPT_INDEX, _TABLE, ["department_id"])
    op.drop_index(_OLD_UNIQUE, table_name=_TABLE)
    op.create_index(_OLD_UNIQUE, _TABLE, ["item_group_id"])
    op.create_unique_constraint(_NEW_UNIQUE, _TABLE, ["department_id", "item_group_id"])


def downgrade() -> None:
    op.drop_constraint(_NEW_UNIQUE, _TABLE, type_="unique")
    op.drop_index(_OLD_UNIQUE, table_name=_TABLE)
    op.create_index(_OLD_UNIQUE, _TABLE, ["item_group_id"], unique=True)
    op.drop_index(_DEPT_INDEX, table_name=_TABLE)
    op.drop_column(_TABLE, "department_id")
