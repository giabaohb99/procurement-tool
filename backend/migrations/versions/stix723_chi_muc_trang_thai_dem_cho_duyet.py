"""chi muc cot status cho dem phieu cho duyet tren menu trai (duoc-CR-723)

Revision ID: stix723
Revises: mrg719x732

Duong /api/dashboard/menu-badges dem `status = 'submitted'` tren bon bang moi lan nguoi dung doi trang
va moi 60 giay. tab_survey_request da co chi muc status; ba bang con lai thi khong (YCMH / DMH chi co
chi muc GHEP voi nguoi duyet / NSPT dung truoc, phieu khao sat khong co gi) nen phai quet ca bang.
Them chi muc rieng cho cot status. Chi tao khi thieu (chay lai duoc).
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import inspect

revision: str = "stix723"
down_revision: Union[str, None] = "mrg719x732"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

#  Ten theo quy uoc mac dinh cua SQLAlchemy (`ix_<bang>_<cot>`) — khop `index=True` tren model, de
#  `alembic --autogenerate` lan sau khong doi tao lai.
INDEXES = [
    ("ix_tab_survey_status", "tab_survey"),
    ("ix_tab_purchase_request_status", "tab_purchase_request"),
    ("ix_tab_purchase_order_status", "tab_purchase_order"),
]


def _index_names(table: str) -> set[str]:
    return {ix["name"] for ix in inspect(op.get_bind()).get_indexes(table)}


def upgrade() -> None:
    for name, table in INDEXES:
        if name not in _index_names(table):
            op.create_index(name, table, ["status"])


def downgrade() -> None:
    for name, table in INDEXES:
        if name in _index_names(table):
            op.drop_index(name, table_name=table)
