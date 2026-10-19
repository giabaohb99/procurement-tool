"""HĐLĐ -> bản lưu trữ ở phân hệ Văn bản: tab_labor_contract.document_id (duoc-CR-629)

Revision ID: lbrct02
Revises: mcpkey02

Chỉ thêm 1 cột + 1 index. KHÔNG backfill (script chạy tay `scripts/backfill_hdld_van_ban_luu_tru.py`),
KHÔNG chèn `tab_doc_type` (seed lo, insert-only). Không đụng FULLTEXT nên không cần
`innodb_ft_enable_stopword`. Viết tay vì autogenerate repo này trôi ~650 dòng.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "lbrct02"
down_revision: Union[str, None] = "mcpkey02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "tab_labor_contract"
INDEX = "ix_labor_contract_document"


def upgrade() -> None:
    insp = sa.inspect(op.get_bind())
    if "document_id" not in {c["name"] for c in insp.get_columns(TABLE)}:
        op.add_column(TABLE, sa.Column("document_id", sa.BigInteger(), nullable=False, server_default="0"))
    if INDEX not in {i["name"] for i in insp.get_indexes(TABLE)}:
        op.create_index(INDEX, TABLE, ["document_id"])


def downgrade() -> None:
    insp = sa.inspect(op.get_bind())
    if INDEX in {i["name"] for i in insp.get_indexes(TABLE)}:
        op.drop_index(INDEX, table_name=TABLE)
    if "document_id" in {c["name"] for c in insp.get_columns(TABLE)}:
        op.drop_column(TABLE, "document_id")
