"""bao-CR-800 — khoa quyen rieng cho Bang gia nguyen lieu (`packaging_material_price`).

Revision ID: matprice800
Revises: permsplit792
Create Date: 2026-11-27

Vi sao: gia nguyen lieu (san pham nhom NL) truoc day lo ra o cac man VTBB khi chon *Moi ma co gia*, nen ai co khoa Bang gia VTBB
cung xem duoc. Tu ban nay cac man VTBB khong con ma nguyen lieu va man Bang gia nguyen lieu gac bang khoa rieng.

upgrade (CHI DU LIEU, khong doi cau truc): vai tro dang co `packaging_price_list` voi Xem / Xuat thi nhan dung Xem / Xuat do tren
`packaging_material_price`, giu nguyen pham vi — khong ai mat thu dang xem duoc. Hanh dong ghi (tao / sua / xoa) KHONG chuyen: man
nguyen lieu chi doc. Quan tri bo tick cho bo phan khong duoc xem gia nguyen lieu tren man Vai tro & quyen.

Chay lai duoc: (vai tro, khoa moi) da co dong thi bo qua.

downgrade: xoa moi dong `packaging_material_price`.

VIET TAY, KHONG autogenerate. Chay duoc tren MySQL 8 va SQLite (bai kiem `test_quyen_rieng_gia_nguyen_lieu_cr800.py`).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "matprice800"
down_revision: Union[str, None] = "permsplit792"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SOURCE_KEY = "packaging_price_list"
NEW_KEY = "packaging_material_price"
COPIED_ACTIONS = ("read", "export")

_PERMISSION = sa.table(
    "tab_permission", sa.column("id", sa.BigInteger), sa.column("role_id", sa.BigInteger), sa.column("entity", sa.String),
    sa.column("scope", sa.String), sa.column("created_by", sa.BigInteger), sa.column("updated_by", sa.BigInteger),
    sa.column("can_read", sa.Boolean), sa.column("can_export", sa.Boolean))


def upgrade() -> None:
    conn = op.get_bind()
    p = _PERMISSION
    sources = conn.execute(
        sa.select(p.c.role_id, p.c.scope, p.c.created_by, p.c.updated_by, p.c.can_read, p.c.can_export)
        .where(p.c.entity == SOURCE_KEY).order_by(p.c.id)).mappings().all()
    existing = {row[0] for row in conn.execute(sa.select(p.c.role_id).where(p.c.entity == NEW_KEY)).all()}
    inserted = 0
    for row in sources:
        if row["role_id"] in existing or not (row["can_read"] or row["can_export"]):
            continue
        #  `created_by` / `updated_by` NOT NULL, khong co mac dinh o tang CSDL -> chep cua dong nguon. Bon co khong co
        #  `server_default` (create / write / delete / approve / cancel / print) dat tuong minh 0.
        conn.execute(sa.text(
            "INSERT INTO tab_permission (role_id, entity, scope, can_read, can_create, can_write, can_delete, can_export, "
            "can_approve, can_cancel, can_print, created_by, updated_by) VALUES (:role_id, :entity, :scope, :can_read, :zero, "
            ":zero, :zero, :can_export, :zero, :zero, :zero, :created_by, :updated_by)"),
            {"role_id": row["role_id"], "entity": NEW_KEY, "scope": row["scope"], "zero": False,
             "can_read": bool(row["can_read"]), "can_export": bool(row["can_export"]),
             "created_by": row["created_by"] or 0, "updated_by": row["updated_by"] or 0})
        existing.add(row["role_id"])
        inserted += 1
    print(f"[matprice800] {len(sources)} vai tro co {SOURCE_KEY} -> chen {inserted} dong {NEW_KEY}")


def downgrade() -> None:
    op.get_bind().execute(sa.delete(_PERMISSION).where(_PERMISSION.c.entity == NEW_KEY))
