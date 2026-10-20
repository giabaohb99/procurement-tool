"""quyen mac dinh theo chuc vu: bang tab_job_position_role + cot tab_user_role.granted_by_position_id -- duoc-CR-653

Revision ID: jobposrole01
Revises: usgprof02
Create Date: 2026-10-20

VIET TAY (autogenerate repo nay troi ~650 dong moi lan; khong import ma ung dung).

upgrade
  - `tab_job_position_role` (job_position_id, role_id) UNIQUE -- goi vai tro mac dinh cua chuc vu.
  - `tab_user_role.granted_by_position_id` BIGINT NOT NULL DEFAULT 0 (+ index) -- 0 = quan tri gan tay,
    >0 = he thong tu cap theo chuc vu do. Dong cu giu 0 => khong dong nao bi he thong thu hoi.
  - UNIQUE (user_id, role_id) tren `tab_user_role` (review M2): DON TRUNG TRUOC -- giu dong GAN TAY
    (granted_by_position_id = 0) truoc, roi toi id thap nhat; in so dong da xoa. SQL dung cua so ROW_NUMBER (MySQL 8).
downgrade: bo chi muc unique + bo cot + bang. Dong tu cap van o lai trong tab_user_role (thanh dong "gan tay") -- chu y:
  sau khi ha cap, quyen da tu cap se KHONG con tu thu hoi khi doi chuc vu.
Moi buoc tu gac (inspect) nen chay lai sau su co (MySQL DDL tu commit) la an toan.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "jobposrole01"
down_revision: Union[str, None] = "usgprof02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_COL = "granted_by_position_id"
_IX = "ix_tab_user_role_granted_by_position_id"
_UQ = "uq_user_role_user_role"


def _insp():
    return inspect(op.get_bind())


def _dedupe_user_role() -> None:
    """Xoa dong trung (user_id, role_id): giu dong tay (marker 0) truoc, roi id thap nhat."""
    bind = op.get_bind()
    dup = bind.execute(sa.text(
        "SELECT COUNT(*) FROM (SELECT 1 FROM tab_user_role GROUP BY user_id, role_id HAVING COUNT(*) > 1) t"
    )).scalar() or 0
    if not dup:
        print("[jobposrole01] tab_user_role: khong co dong trung")
        return
    res = bind.execute(sa.text(
        "DELETE ur FROM tab_user_role ur JOIN ("
        " SELECT id FROM ("
        "  SELECT id, ROW_NUMBER() OVER (PARTITION BY user_id, role_id"
        "   ORDER BY (CASE WHEN granted_by_position_id > 0 THEN 1 ELSE 0 END), id) AS rn"
        "  FROM tab_user_role) ranked WHERE ranked.rn > 1"
        ") d ON d.id = ur.id"))
    print(f"[jobposrole01] tab_user_role: {dup} cap (user, role) trung, da xoa {res.rowcount} dong thua")


def upgrade() -> None:
    if not _insp().has_table("tab_job_position_role"):
        op.create_table(
            "tab_job_position_role",
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("created_by", sa.BigInteger(), nullable=False, server_default=sa.text("0")),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_by", sa.BigInteger(), nullable=False, server_default=sa.text("0")),
            sa.Column("job_position_id", sa.BigInteger(), nullable=False),
            sa.Column("role_id", sa.BigInteger(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("job_position_id", "role_id", name="uq_job_position_role"),
        )
        op.create_index("ix_tab_job_position_role_job_position_id", "tab_job_position_role", ["job_position_id"])
        op.create_index("ix_tab_job_position_role_role_id", "tab_job_position_role", ["role_id"])

    if _COL not in {c["name"] for c in _insp().get_columns("tab_user_role")}:
        op.add_column("tab_user_role", sa.Column(
            _COL, sa.BigInteger(), nullable=False, server_default=sa.text("0")))
    if _IX not in {i["name"] for i in _insp().get_indexes("tab_user_role")}:
        op.create_index(_IX, "tab_user_role", [_COL])
    if _UQ not in {i["name"] for i in _insp().get_indexes("tab_user_role")}:
        _dedupe_user_role()
        op.create_index(_UQ, "tab_user_role", ["user_id", "role_id"], unique=True)


def downgrade() -> None:
    if _UQ in {i["name"] for i in _insp().get_indexes("tab_user_role")}:
        op.drop_index(_UQ, table_name="tab_user_role")
    if _IX in {i["name"] for i in _insp().get_indexes("tab_user_role")}:
        op.drop_index(_IX, table_name="tab_user_role")
    if _COL in {c["name"] for c in _insp().get_columns("tab_user_role")}:
        op.drop_column("tab_user_role", _COL)
    if _insp().has_table("tab_job_position_role"):
        op.drop_table("tab_job_position_role")
