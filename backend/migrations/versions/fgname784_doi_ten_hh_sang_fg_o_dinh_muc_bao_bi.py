"""doi_ten_hh_sang_fg_o_dinh_muc_bao_bi: `tab_packaging_bom.hh_code / hh_name` -> `fg_code / fg_name` (duoc-CR-784, phase 06)

Revision ID: fgname784
Revises: cleanup784
Create Date: 2026-11-25

Chu du an chot C8 (25/11/2026): dinh danh tieng Viet khong dau `hh` (hang hoa) doi sang tieng Anh `fg` (finished good), cung nghia voi
`tab_po_item.fg_code / fg_name`. Nhan nguoi dung thay (Ma HH, Ten hang hoa) giu nguyen.

upgrade:  doi ten hai cot (giu kieu, NOT NULL, mac dinh '' cua `fg_name`); rang buoc duy nhat doi ten theo
          (`uq_tab_packaging_bom_hh_code` -> `uq_tab_packaging_bom_fg_code`, chi MySQL - SQLite khong doi ten duoc rang buoc).
downgrade: dung nguoc.
Khong dung du lieu: chi doi ten cot / chi muc. VIET TAY, KHONG autogenerate. Chay duoc tren MySQL 8 va SQLite (bai kiem).
`tab_product.hh_code / hh_name` (danh muc san pham, da len prod) KHONG doi.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "fgname784"
down_revision: Union[str, None] = "cleanup784"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "tab_packaging_bom"
OLD_UNIQUE = "uq_tab_packaging_bom_hh_code"
NEW_UNIQUE = "uq_tab_packaging_bom_fg_code"


def _rename_columns(old_code: str, new_code: str, old_name: str, new_name: str) -> None:
    """Doi ten hai cot. `existing_*` bat buoc voi MySQL (CHANGE COLUMN phai khai lai day du kieu)."""
    with op.batch_alter_table(TABLE) as batch:     # batch: SQLite dung lai bang, MySQL chay ALTER thuong
        batch.alter_column(old_code, new_column_name=new_code, existing_type=sa.String(50), existing_nullable=False)
        batch.alter_column(old_name, new_column_name=new_name, existing_type=sa.String(255), existing_nullable=False,
                           existing_server_default=sa.text("''"))


def _rename_unique(old: str, new: str) -> None:
    """MySQL: `RENAME INDEX` neu rang buoc ten cu con ton tai (DB dung tu `pkgcost784`). Dialect khac: bo qua."""
    conn = op.get_bind()
    if conn.dialect.name != "mysql":
        return
    names = {ix["name"] for ix in sa.inspect(conn).get_indexes(TABLE)}
    if old in names:
        op.execute(f"ALTER TABLE {TABLE} RENAME INDEX {old} TO {new}")


def upgrade() -> None:
    _rename_columns("hh_code", "fg_code", "hh_name", "fg_name")
    _rename_unique(OLD_UNIQUE, NEW_UNIQUE)


def downgrade() -> None:
    _rename_columns("fg_code", "hh_code", "fg_name", "hh_name")
    _rename_unique(NEW_UNIQUE, OLD_UNIQUE)
