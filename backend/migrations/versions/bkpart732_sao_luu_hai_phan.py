"""sao luu CSDL tach hai phan: ban chinh + ban du lieu tra cuu thi truong (bao-CR-732)

Revision ID: bkpart732
Revises: emresend727

tab_db_backup them hai cot:
- part VARCHAR(20) NOT NULL DEFAULT 'main' co index: 'main' = ban chinh (2 lan/ngay), 'customs' = du lieu tra cuu
  thi truong (1 lan/ngay, bo qua neu khong doi). Dong cu la ban chinh nen mac dinh 'main'.
- fingerprint VARCHAR(120) NOT NULL DEFAULT '': dau van tay du lieu tra cuu thi truong luc sao luu
  ('<alembic>:<sha1>'), de lan sau biet co doi khong.
Chi them khi thieu (chay lai duoc).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "bkpart732"
down_revision: Union[str, None] = "emresend727"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "tab_db_backup"
INDEX = "ix_tab_db_backup_part"


def _columns() -> set[str]:
    return {c["name"] for c in sa.inspect(op.get_bind()).get_columns(TABLE)}


def upgrade() -> None:
    cols = _columns()
    if "part" not in cols:
        op.add_column(TABLE, sa.Column("part", sa.String(20), nullable=False, server_default="main"))
        op.create_index(INDEX, TABLE, ["part"])
    if "fingerprint" not in cols:
        op.add_column(TABLE, sa.Column("fingerprint", sa.String(120), nullable=False, server_default=""))


def downgrade() -> None:
    cols = _columns()
    if "fingerprint" in cols:
        op.drop_column(TABLE, "fingerprint")
    if "part" in cols:
        op.drop_index(INDEX, table_name=TABLE)
        op.drop_column(TABLE, "part")
