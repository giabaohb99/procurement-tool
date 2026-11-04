"""phieu nghi bu: chot loai nhan + nam quy + khoa «mot ngay mot phieu» (duoc-CR-715 C, sua theo review)

Revision ID: lvcmp716
Revises: lvcmp715

Them 3 cot cho tab_leave_comp_request: comp_leave_type_id, balance_year, active_key (UNIQUE, NULL khi phieu het hieu luc).
Chi them khi thieu (chay lai duoc). Phieu da co: dien loai nhan = loai bu dau tien, nam = nam di lam, va cap active_key
cho phieu con hieu luc (neu trung ngay thi chi phieu id nho nhat giu khoa).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "lvcmp716"
down_revision: Union[str, None] = "lvcmp715"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "tab_leave_comp_request"
INDEX = "uq_leave_comp_active_key"
#  LeaveCompStatus.REJECTED = 4, CANCELLED = 6 — hai trang thai het hieu luc.
INACTIVE = (4, 6)


def _has_column(inspector, column: str) -> bool:
    return column in {c["name"] for c in inspector.get_columns(TABLE)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if TABLE not in inspector.get_table_names():
        return
    if not _has_column(inspector, "comp_leave_type_id"):
        op.add_column(TABLE, sa.Column("comp_leave_type_id", sa.BigInteger(), nullable=False, server_default="0"))
    if not _has_column(inspector, "balance_year"):
        op.add_column(TABLE, sa.Column("balance_year", sa.SmallInteger(), nullable=False, server_default="0"))
    if not _has_column(inspector, "active_key"):
        op.add_column(TABLE, sa.Column("active_key", sa.String(40), nullable=True))

    comp_type = bind.execute(sa.text(
        "SELECT id FROM tab_leave_type WHERE is_active = :on AND is_compensatory = :on AND counts_balance = :on "
        "ORDER BY sort_order, id LIMIT 1"), {"on": True}).scalar()
    if comp_type:
        bind.execute(sa.text(f"UPDATE {TABLE} SET comp_leave_type_id = :t WHERE comp_leave_type_id = 0 "
                             "AND status IN (2, 3)"), {"t": comp_type})
    #  EXTRACT(YEAR FROM ...) chay duoc ca MySQL lan SQLite-test (Postgres).
    bind.execute(sa.text(f"UPDATE {TABLE} SET balance_year = EXTRACT(YEAR FROM work_date) "
                         "WHERE balance_year = 0 AND status = 3"))

    seen: set[str] = set()
    rows = bind.execute(sa.text(
        f"SELECT id, employee_id, work_date, status, is_deleted FROM {TABLE} WHERE active_key IS NULL "
        "ORDER BY id")).fetchall()
    for row_id, employee_id, work_date, status, is_deleted in rows:
        if status in INACTIVE or is_deleted:
            continue
        key = f"{employee_id}:{work_date}"
        if key in seen:
            continue
        seen.add(key)
        bind.execute(sa.text(f"UPDATE {TABLE} SET active_key = :k WHERE id = :i"), {"k": key, "i": row_id})

    inspector = sa.inspect(bind)
    if INDEX not in {i["name"] for i in inspector.get_indexes(TABLE)}:
        op.create_index(INDEX, TABLE, ["active_key"], unique=True)


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if TABLE not in inspector.get_table_names():
        return
    if INDEX in {i["name"] for i in inspector.get_indexes(TABLE)}:
        op.drop_index(INDEX, table_name=TABLE)
    for column in ("active_key", "balance_year", "comp_leave_type_id"):
        if _has_column(inspector, column):
            op.drop_column(TABLE, column)
