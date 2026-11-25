"""CRUD báo giá + ngưỡng giá của màn Giá bao bì (duoc-CR-784, phase 03).

Cả hai gác khóa `packaging_cost` bằng quyền HÀNH ĐỘNG (read / create / write / delete). Hai bảng là danh mục dùng chung —
không có cột pháp nhân — nên dựng bằng `make_crud_router(scoped=False)`; phạm vi theo pháp nhân của khóa này đo trên SỔ
GIÁ (`ProductPriceLedger.company_id`), áp ở `packaging_cost/impact_controller.py`.
"""
from fastapi import HTTPException

from app.core.crud import make_crud_router
from app.core.packaging_price_codes import QUOTE_SOURCE_TYPE_LABELS, QuoteSourceType

from . import catalog_checks as chk
from .model import ProductPriceLimit, ProductPriceQuote
from .schema import LimitCreate, LimitOut, LimitUpdate, QuoteCreate, QuoteOut, QuoteUpdate

ENTITY = "packaging_cost"
TAG = "packaging-cost"


def _retag(router):
    """Đổi tag Swagger của các đường do bộ sinh dựng (bộ sinh mặc định gắn tag = tên khóa quyền)."""
    for route in router.routes:
        route.tags = [TAG]
    return router


# ── Báo giá ─────────────────────────────────────────────────────────────────────
QUOTE_DUPLICATE_MESSAGE = "Đã có báo giá cùng mã, NCC và ngày hiệu lực"
#  Cột làm đổi NGHĨA của một báo giá: đổi một trong số này ở form thì dòng không còn là dòng đã nhập từ Excel nữa.
QUOTE_VALUE_FIELDS = ("price", "vat", "product_code", "supplier_code", "valid_from")


def _ensure_quote_key_free(db, product_code: str, supplier_code: str, valid_from, exclude_id: int | None = None) -> None:
    """Khóa (mã, NCC, ngày hiệu lực) chưa có báo giá nào khác dùng — có rồi thì 409 (ràng buộc `uq_ppq_key` là chốt cuối khi hai
    người gửi sát nhau; chốt này cho câu trả lời rõ trong trường hợp thường)."""
    q = db.query(ProductPriceQuote.id).filter(
        ProductPriceQuote.product_code == product_code, ProductPriceQuote.supplier_code == (supplier_code or ""),
        ProductPriceQuote.valid_from == valid_from)
    if exclude_id is not None:
        q = q.filter(ProductPriceQuote.id != exclude_id)
    if q.first() is not None:
        raise HTTPException(409, QUOTE_DUPLICATE_MESSAGE)


def _quote_before_create(db, data) -> None:
    chk.ensure_products_exist(db, [data.product_code])
    chk.ensure_supplier_ok(db, data.supplier_code)
    _ensure_quote_key_free(db, data.product_code, data.supplier_code, data.valid_from)


def _quote_before_update(db, obj, values) -> None:
    chk.reject_null(values, ("product_code", "supplier_code", "price", "vat", "valid_from", "note"))
    if "product_code" in values:
        chk.ensure_products_exist(db, [values["product_code"]])
    if "supplier_code" in values:
        chk.ensure_supplier_ok(db, values["supplier_code"])
    changed = {k: values[k] for k in QUOTE_VALUE_FIELDS if k in values and values[k] != getattr(obj, k)}
    if {"product_code", "supplier_code", "valid_from"} & changed.keys():
        _ensure_quote_key_free(db, values.get("product_code", obj.product_code), values.get("supplier_code", obj.supplier_code),
                               values.get("valid_from", obj.valid_from), exclude_id=obj.id)
    if changed:
        #  Người sửa tay giá / VAT / khóa thì giá hiện hành là do TAY ghi, kể cả dòng vốn nhập từ Excel (chủ dự án chốt C4).
        #  Chỉ đổi ghi chú thì nguồn giữ nguyên. `values` đi thẳng vào `setattr` của bộ CRUD.
        values["source_type"], values["source_id"] = int(QuoteSourceType.MANUAL), 0


def _quote_enrich(db, rows: list[dict]) -> None:
    """Gắn tên + ĐVT sản phẩm và tên NCC — hai truy vấn cho cả trang."""
    from app.modules.supplier.model import Supplier
    info = chk.product_info(db, [r["product_code"] for r in rows])
    sup_codes = {r["supplier_code"] for r in rows if r["supplier_code"]}
    sup_names = dict(db.query(Supplier.code, Supplier.name).filter(Supplier.code.in_(sup_codes)).all()) if sup_codes else {}
    for r in rows:
        r["product_name"], r["product_unit"] = info.get(r["product_code"], ("", ""))
        r["supplier_name"] = sup_names.get(r["supplier_code"], "")
        #  Nhãn của bộ mã `quote_source_type`; chữ "(lô #N)" + liên kết sang đợt nhập do giao diện ghép từ `source_id`.
        r["source_label"] = QUOTE_SOURCE_TYPE_LABELS.get(r["source_type"], "")


quote_router = _retag(make_crud_router(
    "/api/product-price-quotes", ENTITY, ProductPriceQuote, QuoteCreate, QuoteUpdate, QuoteOut,
    filterable=["product_code", "supplier_code", "note"], unique_field=None,
    before_create=_quote_before_create, before_update=_quote_before_update,
    scoped=False, enrich_out=_quote_enrich, audit_entity="packaging_cost_quote",
    conflict_message=QUOTE_DUPLICATE_MESSAGE, conflict_status=409))


# ── Ngưỡng giá ──────────────────────────────────────────────────────────────────
def _limit_before_create(db, data) -> None:
    chk.ensure_products_exist(db, [data.product_code])


def _limit_before_update(db, obj, values) -> None:
    chk.reject_null(values, ("product_code", "note"))
    if "product_code" in values:
        chk.ensure_products_exist(db, [values["product_code"]])
    floor = values.get("floor_price", obj.floor_price)
    ceiling = values.get("ceiling_price", obj.ceiling_price)
    if floor is not None and ceiling is not None and floor > ceiling:
        from fastapi import HTTPException
        raise HTTPException(422, "Ngưỡng sàn không được lớn hơn ngưỡng trần")


def _limit_enrich(db, rows: list[dict]) -> None:
    info = chk.product_info(db, [r["product_code"] for r in rows])
    for r in rows:
        r["product_name"], r["product_unit"] = info.get(r["product_code"], ("", ""))


limit_router = _retag(make_crud_router(
    "/api/product-price-limits", ENTITY, ProductPriceLimit, LimitCreate, LimitUpdate, LimitOut,
    filterable=["product_code", "note"], unique_field="product_code",
    before_create=_limit_before_create, before_update=_limit_before_update,
    scoped=False, enrich_out=_limit_enrich, audit_entity="packaging_cost_limit"))
