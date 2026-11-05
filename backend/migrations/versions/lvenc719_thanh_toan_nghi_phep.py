"""thanh toan nghi phep (duoc-CR-719): cot loai nghi + quy, cot YCTT nguon, bang tab_leave_encashment

Revision ID: lvenc719
Revises: hqx718b

Them (chi khi thieu, chay lai duoc):
  tab_leave_type      allow_encashment · max_encashable_days · non_encashable_days
  tab_leave_balance   encashed_days (khoan TRU vao cong thuc con lai) · encashed_carried_days (phan mang sang da thanh toan)
  tab_payment_request payee_employee_id · source_ref_id + INDEX ix_payment_request_source_ref (source_type, source_ref_id)
  tab_leave_encashment (bang moi) + INDEX (employee_id, balance_year) + UNIQUE uq_leave_encash_active_key
Viet tay (autogenerate tren repo nay troi ~650 dong). Downgrade bo dung nhung gi da them.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "lvenc719"
down_revision: Union[str, None] = "hqx718b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ENC = "tab_leave_encashment"
PAY_INDEX = "ix_payment_request_source_ref"

#  (bang, cot, kieu) — them neu thieu.
NEW_COLUMNS = (
    ("tab_leave_type", "allow_encashment", sa.Boolean(), "0"),
    ("tab_leave_type", "max_encashable_days", sa.Float(), "0"),
    ("tab_leave_type", "non_encashable_days", sa.Float(), "0"),
    ("tab_leave_balance", "encashed_days", sa.Float(), "0"),
    ("tab_leave_balance", "encashed_carried_days", sa.Float(), "0"),
    ("tab_payment_request", "payee_employee_id", sa.BigInteger(), "0"),
    ("tab_payment_request", "source_ref_id", sa.BigInteger(), "0"),
)


def _columns(inspector, table: str) -> set[str]:
    return {c["name"] for c in inspector.get_columns(table)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    for table, column, col_type, default in NEW_COLUMNS:
        if table in tables and column not in _columns(inspector, table):
            op.add_column(table, sa.Column(column, col_type, nullable=False, server_default=default))

    if "tab_payment_request" in tables and PAY_INDEX not in {
            i["name"] for i in inspector.get_indexes("tab_payment_request")}:
        op.create_index(PAY_INDEX, "tab_payment_request", ["source_type", "source_ref_id"])

    if ENC not in tables:
        op.create_table(
            ENC,
            sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("created_by", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_by", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("code", sa.String(30), nullable=False),
            sa.Column("company_id", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("department_id", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("employee_id", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("leave_type_id", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("balance_year", sa.SmallInteger(), nullable=False, server_default="0"),
            sa.Column("reason_kind", sa.SmallInteger(), nullable=False, server_default="1"),
            sa.Column("encashment_date", sa.Date(), nullable=True),
            sa.Column("days", sa.Float(), nullable=False, server_default="0"),
            sa.Column("carried_paid_days", sa.Float(), nullable=False, server_default="0"),
            sa.Column("balance_snapshot", sa.Float(), nullable=False, server_default="0"),
            sa.Column("encashable_snapshot", sa.Float(), nullable=False, server_default="0"),
            sa.Column("note", sa.String(1000), nullable=False, server_default=""),
            sa.Column("status", sa.SmallInteger(), nullable=False, server_default="1"),
            sa.Column("approval_instance_id", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("decided_at", sa.DateTime(), nullable=True),
            sa.Column("decision_note", sa.String(500), nullable=False, server_default=""),
            sa.Column("payment_request_id", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("active_key", sa.String(60), nullable=True),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.UniqueConstraint("code", name="uq_leave_encashment_code"),
            mysql_charset="utf8mb4",
        )
        op.create_index("ix_leave_encash_emp_year", ENC, ["employee_id", "balance_year"])
        op.create_index("uq_leave_encash_active_key", ENC, ["active_key"], unique=True)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if ENC in tables:
        op.drop_table(ENC)
    if "tab_payment_request" in tables and PAY_INDEX in {
            i["name"] for i in inspector.get_indexes("tab_payment_request")}:
        op.drop_index(PAY_INDEX, table_name="tab_payment_request")
    for table, column, _type, _default in reversed(NEW_COLUMNS):
        if table in tables and column in _columns(inspector, table):
            op.drop_column(table, column)
