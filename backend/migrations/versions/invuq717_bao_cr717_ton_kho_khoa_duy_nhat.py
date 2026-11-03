"""bao-CR-717: rang buoc duy nhat (company_id, warehouse_code, product_code) cho tab_inventory

Revision ID: invuq717
Revises: hqx718 (nối lại sau hqx718 của bao-CR-718 — hai đầu alembic làm api dev không khởi động)
Create Date: 2026-11-03

Tai lieu phi chuc nang cua Kho (PCN-KHO-08) ghi mot dong ton cho moi bo (cong ty, kho, ma) nhung bang chi co ba chi muc
roi -- hai luot luu DMH / nhan hang cung luc co the sinh hai dong ton. Soat prod 03/11/2026: 381 dong, 0 nhom trung.

upgrade(): KIEM TRUNG TRUOC. Co nhom trung thi DUNG kem danh sach nhom, KHONG tu gop (gop la viec cua nguoi: dong nao
giu ten hang / don vi, so lieu dung lai tu so phat sinh bang `inventory.service._recompute`). Sach thi them rang buoc.
Ten rang buoc dung chung voi `Inventory.INVENTORY_KEY_CONSTRAINT` o model.

VIET TAY, khong autogenerate.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "invuq717"
down_revision: Union[str, None] = "hqx718"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CONSTRAINT = "uq_inventory_company_wh_product"
DUP_SQL = sa.text(
    "SELECT company_id, warehouse_code, product_code, COUNT(*) AS n FROM tab_inventory "
    "GROUP BY company_id, warehouse_code, product_code HAVING COUNT(*) > 1 ORDER BY n DESC, company_id, warehouse_code, "
    "product_code"
)


def duplicate_groups(conn) -> list[tuple]:
    """Nhóm (company_id, warehouse_code, product_code, số dòng) đang trùng — rỗng là sạch."""
    return [tuple(r) for r in conn.execute(DUP_SQL).fetchall()]


def upgrade() -> None:
    conn = op.get_bind()
    dups = duplicate_groups(conn)
    if dups:
        shown = "\n".join(f"  - công ty {c}, kho '{w}', mã '{p}': {n} dòng" for c, w, p, n in dups[:20])
        more = f"\n  ... và {len(dups) - 20} nhóm nữa" if len(dups) > 20 else ""
        raise RuntimeError(
            f"bao-CR-717: tab_inventory có {len(dups)} nhóm (công ty, kho, mã) bị trùng dòng tồn, không thêm được ràng "
            f"buộc duy nhất. Migration KHÔNG tự gộp. Gộp tay: giữ một dòng mỗi nhóm (tên hàng, đơn vị), xóa dòng còn lại, "
            f"rồi tính lại số liệu từ sổ phát sinh (inventory.service._recompute), sau đó chạy lại migration.\n{shown}{more}"
        )
    op.create_unique_constraint(CONSTRAINT, "tab_inventory", ["company_id", "warehouse_code", "product_code"])


def downgrade() -> None:
    op.drop_constraint(CONSTRAINT, "tab_inventory", type_="unique")
