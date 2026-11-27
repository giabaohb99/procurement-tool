"""tach_khoa_quyen_gia_nvl_theo_man: khoa `packaging_cost` -> moi man mot khoa (bao-CR-792)

Revision ID: permsplit792
Revises: bombatch784
Create Date: 2026-11-27

Chu du an yeu cau 27/11/2026: cum Gia nguyen vat lieu san xuat (duoc-CR-784) dang gac MOT khoa `packaging_cost` cho ca sau man,
nay moi man mot khoa de cap tung man cho tung nhom nguoi:

    packaging_impact            Tac dong gia bao bi              read, export
    packaging_product_summary   Tong hop theo san pham           read, export
    packaging_price_list        Bang gia VTBB (kem Bao gia VTBB) read, export, create, write, delete
    packaging_last_price        Gia mua gan nhat                 read, export
    packaging_history           Lich su mua hang (kem So Misa)   read, export, write, delete
    packaging_bom               Dinh muc bao bi                  read, export, create, write, delete

Migration nay CHUYEN quyen, khong dat lai quyen: moi dong `tab_permission` cua `packaging_cost` sinh ra cac dong khoa moi cung vai
tro + cung pham vi (`scope`), co hanh dong theo bang tren (`split_flags`), roi XOA dong `packaging_cost` (khoa cu nghi han, khong con
trong `ENTITIES`). Khong chuyen thi deploy xong nguoi dang dung mat het sau man cho toi khi quan tri tick lai tay.

  - read / export  -> ca sau khoa
  - create         -> packaging_price_list, packaging_bom
  - write / delete -> packaging_price_list, packaging_bom, packaging_history
  - approve / cancel / print / import: khong man nao cua cum dung -> khong chuyen.

Chay lai duoc: (vai tro, khoa moi) da co dong thi BO QUA (giu chinh tay cua quan tri); lan hai khong con dong `packaging_cost` nen
khong lam gi. Khoa moi khong co hanh dong nao (vd vai tro chi co `create` thi `packaging_impact` rong) thi khong chen dong.

downgrade (tot nhat co the): gop nguoc sau khoa ve mot dong `packaging_cost` moi vai tro — co = HOP cac co, pham vi = pham vi RONG
nhat trong cac dong gop; vai tro da co dong `packaging_cost` thi giu nguyen dong do. Roi xoa dong cua sau khoa moi.

VIET TAY, KHONG autogenerate. Chay duoc tren MySQL 8 va SQLite (bai kiem `test_tach_quyen_gia_nvl_cr792.py`).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "permsplit792"
down_revision: Union[str, None] = "bombatch784"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

OLD_KEY = "packaging_cost"
#  Khoa moi -> cac hanh dong CO NGHIA tren man do. Chep tay (migration phai dung yen theo thoi gian, khong nhap tu `app`).
NEW_KEY_ACTIONS: dict[str, tuple[str, ...]] = {
    "packaging_impact": ("read", "export"),
    "packaging_product_summary": ("read", "export"),
    "packaging_price_list": ("read", "export", "create", "write", "delete"),
    "packaging_last_price": ("read", "export"),
    "packaging_history": ("read", "export", "write", "delete"),
    "packaging_bom": ("read", "export", "create", "write", "delete"),
}
ACTIONS = ("read", "create", "write", "delete", "export")       # nam hanh dong duoc chuyen
SCOPE_RANK = {"own": 0, "assigned": 1, "proc": 1, "dept_proc": 1, "dept": 2, "company": 3, "all": 4}

_PERMISSION = sa.table(
    "tab_permission", sa.column("id", sa.BigInteger), sa.column("role_id", sa.BigInteger), sa.column("entity", sa.String),
    sa.column("scope", sa.String), sa.column("created_by", sa.BigInteger), sa.column("updated_by", sa.BigInteger),
    *(sa.column(f"can_{action}", sa.Boolean) for action in ACTIONS))


def split_flags(old_flags: dict[str, bool]) -> dict[str, dict[str, bool]]:
    """Ham THUAN: co hanh dong cua mot dong `packaging_cost` -> `{khoa moi: {hanh dong: True}}`.

    Chi tra khoa moi co IT NHAT mot hanh dong; hanh dong ngoai `NEW_KEY_ACTIONS` cua khoa do bi bo.
    """
    out: dict[str, dict[str, bool]] = {}
    for key, allowed in NEW_KEY_ACTIONS.items():
        flags = {action: True for action in allowed if old_flags.get(action)}
        if flags:
            out[key] = flags
    return out


def merge_flags(rows: list[dict]) -> tuple[dict[str, bool], str]:
    """Ham THUAN (downgrade): cac dong khoa moi cua MOT vai tro (`{"scope": ..., hanh dong: bool}`) -> `(co hop, pham vi rong nhat)`."""
    flags = {action: True for action in ACTIONS if any(row.get(action) for row in rows)}
    scope = max((row.get("scope") or "own" for row in rows), key=lambda s: SCOPE_RANK.get(s, 0))
    return flags, scope


def _rows(conn, entities: list[str]) -> list[dict]:
    p = _PERMISSION
    found = conn.execute(
        sa.select(p.c.id, p.c.role_id, p.c.entity, p.c.scope, p.c.created_by, p.c.updated_by,
                  *(p.c[f"can_{action}"] for action in ACTIONS))
        .where(p.c.entity.in_(entities)).order_by(p.c.id)).mappings().all()
    return [{**{k: row[k] for k in ("id", "role_id", "entity", "scope", "created_by", "updated_by")},
             **{action: bool(row[f"can_{action}"]) for action in ACTIONS}} for row in found]


def _insert(conn, role_id: int, entity: str, scope: str, flags: dict[str, bool], source: dict) -> None:
    #  `created_by` / `updated_by` NOT NULL, khong co mac dinh o tang CSDL -> chep cua dong nguon (giu dau vet ai dung bo quyen).
    #  Cac co con lai (approve / cancel / print / import) de mac dinh: dat tuong minh 0 cho bon co khong co `server_default`.
    conn.execute(sa.text(
        "INSERT INTO tab_permission (role_id, entity, scope, can_read, can_create, can_write, can_delete, can_export, "
        "can_approve, can_cancel, can_print, created_by, updated_by) VALUES (:role_id, :entity, :scope, :can_read, :can_create, "
        ":can_write, :can_delete, :can_export, :zero, :zero, :zero, :created_by, :updated_by)"),
        {"role_id": role_id, "entity": entity, "scope": scope, "zero": False,
         "created_by": source["created_by"] or 0, "updated_by": source["updated_by"] or 0,
         **{f"can_{action}": bool(flags.get(action)) for action in ACTIONS}})


def _delete(conn, entities: list[str]) -> None:
    conn.execute(sa.delete(_PERMISSION).where(_PERMISSION.c.entity.in_(entities)))


def upgrade() -> None:
    conn = op.get_bind()
    old_rows = _rows(conn, [OLD_KEY])
    existing = {(row["role_id"], row["entity"]) for row in _rows(conn, list(NEW_KEY_ACTIONS))}
    inserted = skipped = 0
    for row in old_rows:
        for key, flags in split_flags(row).items():
            if (row["role_id"], key) in existing:
                skipped += 1
                continue
            _insert(conn, row["role_id"], key, row["scope"], flags, row)
            existing.add((row["role_id"], key))
            inserted += 1
    _delete(conn, [OLD_KEY])
    print(f"[permsplit792] {len(old_rows)} dong packaging_cost -> chen {inserted} dong khoa moi, bo qua {skipped} dong da co; "
          "da xoa dong packaging_cost")


def downgrade() -> None:
    conn = op.get_bind()
    by_role: dict[int, list[dict]] = {}
    for row in _rows(conn, list(NEW_KEY_ACTIONS)):
        by_role.setdefault(row["role_id"], []).append(row)
    has_old = {row["role_id"] for row in _rows(conn, [OLD_KEY])}
    for role_id, rows in by_role.items():
        if role_id in has_old:
            continue
        flags, scope = merge_flags(rows)
        if flags:
            _insert(conn, role_id, OLD_KEY, scope, flags, rows[0])
    _delete(conn, list(NEW_KEY_ACTIONS))
