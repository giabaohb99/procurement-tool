"""CRUD báo giá + ngưỡng giá của màn Giá bao bì (duoc-CR-784, phase 03).

Cả hai gác khóa `packaging_cost` bằng quyền HÀNH ĐỘNG (read / create / write / delete). Hai bảng là danh mục dùng chung —
không có cột pháp nhân — nên dựng bằng `make_crud_router(scoped=False)`; phạm vi theo pháp nhân của khóa này đo trên SỔ
GIÁ (`ProductPriceLedger.company_id`), áp ở `packaging_cost/impact_controller.py`.
"""
from app.core.crud import make_crud_router

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
def _quote_before_create(db, data) -> None:
    chk.ensure_products_exist(db, [data.product_code])
    chk.ensure_supplier_ok(db, data.supplier_code)


def _quote_before_update(db, obj, values) -> None:
    chk.reject_null(values, ("product_code", "supplier_code", "price", "vat", "valid_from", "note"))
    if "product_code" in values:
        chk.ensure_products_exist(db, [values["product_code"]])
    if "supplier_code" in values:
        chk.ensure_supplier_ok(db, values["supplier_code"])


def _quote_enrich(db, rows: list[dict]) -> None:
    """Gắn tên + ĐVT sản phẩm và tên NCC — hai truy vấn cho cả trang."""
    from app.modules.supplier.model import Supplier
    info = chk.product_info(db, [r["product_code"] for r in rows])
    sup_codes = {r["supplier_code"] for r in rows if r["supplier_code"]}
    sup_names = dict(db.query(Supplier.code, Supplier.name).filter(Supplier.code.in_(sup_codes)).all()) if sup_codes else {}
    for r in rows:
        r["product_name"], r["product_unit"] = info.get(r["product_code"], ("", ""))
        r["supplier_name"] = sup_names.get(r["supplier_code"], "")


quote_router = _retag(make_crud_router(
    "/api/product-price-quotes", ENTITY, ProductPriceQuote, QuoteCreate, QuoteUpdate, QuoteOut,
    filterable=["product_code", "supplier_code", "note"], unique_field=None,
    before_create=_quote_before_create, before_update=_quote_before_update,
    scoped=False, enrich_out=_quote_enrich, audit_entity="packaging_cost_quote"))


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
