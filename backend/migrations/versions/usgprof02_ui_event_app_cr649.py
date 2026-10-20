"""tab_ui_event.app: ung dung gui su kien (1 ERP v2, 2 thumua) -- bao-CR-649

Revision ID: usgprof02
Revises: usgprof01
Create Date: 2026-10-20

VIET TAY (autogenerate repo nay troi ~650 dong moi lan; khong import ma ung dung).

upgrade
  - `tab_ui_event.app` SMALLINT NOT NULL DEFAULT 1 -- dong cu (toan bo tu ERP v2) nhan 1 qua server_default,
    khong UPDATE rieng. Khong them chi muc: bao cao theo app loc tren `occurred_at` (da co chi muc) roi gom.
downgrade: drop cot. Khong dung du lieu khac.
Tu gac (inspect) nen chay lai sau su co (MySQL DDL tu commit) la an toan.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "usgprof02"
down_revision: Union[str, None] = "usgprof01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLE = "tab_ui_event"
_COL = "app"


def _has_column() -> bool:
    insp = inspect(op.get_bind())
    return insp.has_table(_TABLE) and any(c["name"] == _COL for c in insp.get_columns(_TABLE))


def upgrade() -> None:
    if not _has_column():
        op.add_column(_TABLE, sa.Column(_COL, sa.SmallInteger(), nullable=False, server_default="1"))


def downgrade() -> None:
    if _has_column():
        op.drop_column(_TABLE, _COL)
