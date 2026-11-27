"""CRUD định mức bao bì theo mã hàng hóa (duoc-CR-784, phase 03).

Gác khóa `packaging_bom` (bao-CR-792, 27/11/2026: mỗi màn một khóa; trước đó là khóa chung `packaging_cost`) bằng quyền HÀNH
ĐỘNG; danh mục dùng chung nên `scoped=False` (xem `product_price/quote_limit_controller.py`). Đầu ra mỗi dòng kèm `parts` — mỗi loại thành phần một mục với tên + ĐVT lấy từ `tab_product`, gom MỘT
truy vấn cho cả trang (không N+1).

Chuẩn hóa 25/11/2026: mã thành phần nằm ở bảng `tab_packaging_bom_part` (loại + mã, nối bằng `bom_id`). Hình dạng API KHÔNG đổi —
vẫn nhận / trả `bottle_code`, `cap_code`, `label_code`, `carton_label_code`, `carton_code`: đọc qua thuộc tính chỉ đọc của model
(lọc / xếp ở máy chủ như cũ), ghi qua `bom_parts_service.set_bom_codes` (khai ở `virtual_fields` của bộ sinh CRUD).
"""
from sqlalchemy import func

from app.core.crud import make_crud_router
from app.core.packaging_price_codes import PackagingRole
from app.modules.product_price import catalog_checks as chk
from app.modules.product_price.quote_limit_controller import _retag

from .bom_parts_service import codes_from_fields, set_bom_codes
from .model import PackagingBom, role_field
from .schema import BomCreate, BomOut, BomUpdate

ENTITY = "packaging_bom"

#  (loại, tên trường phẳng của API) — thứ tự hiển thị của một dòng định mức; dựng từ `PackagingRole`.
PART_COLUMNS = tuple((role, role_field(role)) for role in PackagingRole)
PART_FIELDS = tuple(field for _, field in PART_COLUMNS)
NOT_NULL_COLUMNS = ("fg_code", "fg_name", "legal_name", *PART_FIELDS, "carton_qty")


def _before_create(db, data) -> None:
    chk.ensure_products_exist(db, [getattr(data, field) for field in PART_FIELDS], "Mã thành phần")


def _after_create(db, obj, data) -> None:
    """Ghi các dòng thành phần cùng giao dịch với đầu phiếu (mã rỗng thì không tạo dòng)."""
    set_bom_codes(obj, codes_from_fields(data.model_dump()))


def _before_update(db, obj, values) -> None:
    chk.reject_null(values, NOT_NULL_COLUMNS)
    codes = codes_from_fields(values)
    chk.ensure_products_exist(db, list(codes.values()), "Mã thành phần")
    #  Đổi riêng mã thành phần không chạm cột nào của đầu phiếu nên `onupdate` không chạy — tự đẩy mốc "Cập nhật".
    if set_bom_codes(obj, codes):
        obj.updated_at = func.now()


def _enrich(db, rows: list[dict]) -> None:
    """`parts = [{role, code, name, unit, in_catalog}]` cho từng dòng — một truy vấn `tab_product` cho cả trang."""
    info = chk.product_info(db, [r[field] for r in rows for field in PART_FIELDS])
    for r in rows:
        r["parts"] = [{"role": int(role), "code": r[field], "name": info.get(r[field], ("", ""))[0],
                       "unit": info.get(r[field], ("", ""))[1], "in_catalog": r[field] in info}
                      for role, field in PART_COLUMNS]


router = _retag(make_crud_router(
    "/api/packaging-boms", ENTITY, PackagingBom, BomCreate, BomUpdate, BomOut,
    filterable=["fg_code", "fg_name", "legal_name", *PART_FIELDS],
    unique_field="fg_code", before_create=_before_create, before_update=_before_update,
    scoped=False, enrich_out=_enrich, audit_entity="packaging_bom",
    virtual_fields=PART_FIELDS, after_create=_after_create))
