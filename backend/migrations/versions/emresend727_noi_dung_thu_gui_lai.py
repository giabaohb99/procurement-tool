"""nhat ky email: luu noi dung thu + dong gui lai (bao-CR-727)

Revision ID: emresend727
Revises: hqx718b

tab_email_log them hai cot:
- html_body MEDIUMTEXT NULL: nguyen than HTML cua thu, de nut "Gui lai" tren man Nhat ky email gui lai y nguyen.
  Thu cu truoc dot nay de NULL (khong bu duoc). Thu dat lai mat khau / cap tai khoan KHONG BAO GIO luu
  (chua lien ket dat mat khau), xem `EmailLog.keep_body`.
- resent_from_id BIGINT NULL co index: dong nay la ban gui lai cua dong nao.
Chi them khi thieu (chay lai duoc).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision: str = "emresend727"
down_revision: Union[str, None] = "hqx718b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "tab_email_log"
INDEX = "ix_tab_email_log_resent_from_id"


def _columns() -> set[str]:
    return {c["name"] for c in sa.inspect(op.get_bind()).get_columns(TABLE)}


def upgrade() -> None:
    cols = _columns()
    if "html_body" not in cols:
        op.add_column(TABLE, sa.Column("html_body", sa.Text().with_variant(mysql.MEDIUMTEXT(), "mysql"),
                                       nullable=True))
    if "resent_from_id" not in cols:
        op.add_column(TABLE, sa.Column("resent_from_id", sa.BigInteger(), nullable=True))
        op.create_index(INDEX, TABLE, ["resent_from_id"])


def downgrade() -> None:
    cols = _columns()
    if "resent_from_id" in cols:
        op.drop_index(INDEX, table_name=TABLE)
        op.drop_column(TABLE, "resent_from_id")
    if "html_body" in cols:
        op.drop_column(TABLE, "html_body")
