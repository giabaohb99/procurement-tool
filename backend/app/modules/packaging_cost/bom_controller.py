"""CRUD định mức bao bì theo mã hàng hóa (duoc-CR-784, phase 03).

Gác khóa `packaging_cost` bằng quyền HÀNH ĐỘNG; danh mục dùng chung nên `scoped=False` (xem `product_price/
quote_limit_controller.py`). Đầu ra mỗi dòng kèm `parts` — năm thành phần với tên + ĐVT lấy từ `tab_product`, gom MỘT
truy vấn cho cả trang (không N+1).
"""
from app.core.crud import make_crud_router
from app.core.packaging_price_codes import PackagingRole
from app.modules.product_price import catalog_checks as chk
from app.modules.product_price.quote_limit_controller import ENTITY, _retag

from .model import PackagingBom
from .schema import BomCreate, BomOut, BomUpdate

#  (vai trò, tên cột mã thành phần) — thứ tự hiển thị của một dòng định mức.
PART_COLUMNS = (
    (PackagingRole.BOTTLE, "bottle_code"), (PackagingRole.CAP, "cap_code"), (PackagingRole.LABEL, "label_code"),
    (PackagingRole.CARTON_LABEL, "carton_label_code"), (PackagingRole.CARTON, "carton_code"),
)
NOT_NULL_COLUMNS = ("hh_code", "hh_name", "legal_name", "bottle_code", "cap_code", "label_code",
                    "carton_label_code", "carton_code", "carton_qty")


def _before_create(db, data) -> None:
    chk.ensure_products_exist(db, [getattr(data, col) for _, col in PART_COLUMNS], "Mã thành phần")


def _before_update(db, obj, values) -> None:
    chk.reject_null(values, NOT_NULL_COLUMNS)
    chk.ensure_products_exist(db, [values[col] for _, col in PART_COLUMNS if col in values], "Mã thành phần")


def _enrich(db, rows: list[dict]) -> None:
    """`parts = [{role, code, name, unit, in_catalog}]` cho từng dòng — một truy vấn `tab_product` cho cả trang."""
    info = chk.product_info(db, [r[col] for r in rows for _, col in PART_COLUMNS])
    for r in rows:
        r["parts"] = [{"role": int(role), "code": r[col], "name": info.get(r[col], ("", ""))[0],
                       "unit": info.get(r[col], ("", ""))[1], "in_catalog": r[col] in info}
                      for role, col in PART_COLUMNS]


router = _retag(make_crud_router(
    "/api/packaging-boms", ENTITY, PackagingBom, BomCreate, BomUpdate, BomOut,
    filterable=["hh_code", "hh_name", "legal_name", "bottle_code", "cap_code", "label_code",
                "carton_label_code", "carton_code"],
    unique_field="hh_code", before_create=_before_create, before_update=_before_update,
    scoped=False, enrich_out=_enrich, audit_entity="packaging_bom"))
