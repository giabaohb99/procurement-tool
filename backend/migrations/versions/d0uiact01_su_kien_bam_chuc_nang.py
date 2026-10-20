"""tab_ui_event.action_key: ma nut duoc bam (UiAction) -- duoc-CR-654

Revision ID: d0uiact01
Revises: jobposrole01
Create Date: 2026-10-20

VIET TAY (autogenerate repo nay troi ~650 dong moi lan; khong import ma ung dung).

upgrade
  - `tab_ui_event.action_key` SMALLINT NOT NULL DEFAULT 0 -- dong cu nhan 0 qua server_default.
    Khong them chi muc: gom ngay quet theo `occurred_at` (da co chi muc).
downgrade: drop cot. Tu gac (inspect) nen chay lai sau su co la an toan.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "d0uiact01"
down_revision: Union[str, None] = "jobposrole01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLE = "tab_ui_event"
_COL = "action_key"


def _has_column() -> bool:
    insp = inspect(op.get_bind())
    return insp.has_table(_TABLE) and any(c["name"] == _COL for c in insp.get_columns(_TABLE))


def upgrade() -> None:
    if not _has_column():
        op.add_column(_TABLE, sa.Column(_COL, sa.SmallInteger(), nullable=False, server_default="0"))


def downgrade() -> None:
    if _has_column():
        op.drop_column(_TABLE, _COL)
