"""duoc-CR-784 phase 03 — CRUD báo giá: schema (trần độ dài, giá âm, ngày), chốt danh mục, quyền 403/422/400. Phase 04 BỎ phần ngưỡng
sàn / trần (đường `/api/product-price-limits` phải là 404)."""
from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.main import app
from app.modules.product_price.model import ProductPriceQuote
from app.modules.product_price.schema import QuoteCreate, QuoteUpdate
from app.modules.supplier.model import Supplier
from app.modules.user.model import User
from hdld_factory import client_as  # noqa: F401  (fixture)
from so_gia_factory_cr784 import add_products, add_quote

QUOTES, LIMITS = "/api/product-price-quotes", "/api/product-price-limits"     # LIMITS: đã bỏ, chỉ để khẳng định 404


@pytest.fixture
def api(db, seed, cap_quyen, client_as):  # noqa: F811
    cap_quyen(seed.u_req_id, "packaging_cost", scope="all", read=True, create=True, write=True, delete=True)
    add_products(db, ("CPT0075", "Chai 1L", "Cái"), ("NAP0085", "Nắp", "Cái"))
    return client_as(db.get(User, seed.u_req_id))


# ── Schema ──────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("field,size", [("product_code", 51), ("supplier_code", 51), ("note", 501)])
def test_schema_bao_gia_chan_chuoi_dai_hon_cot(field, size):
    data = {"product_code": "CPT0075", "price": 100, "valid_from": "2026-11-01", field: "x" * size}
    with pytest.raises(ValidationError) as exc:
        QuoteCreate(**data)
    assert any(e["type"] == "string_too_long" for e in exc.value.errors())


@pytest.mark.parametrize("bad", [{"price": -1}, {"price": "1e13"}, {"vat": 100}, {"vat": -1},
                                 {"valid_from": "0001-01-01"}, {"valid_from": "9999-12-31"}, {"product_code": "  "}])
def test_schema_bao_gia_chan_gia_tri_vo_ly(bad):
    with pytest.raises(ValidationError):
        QuoteCreate(**{"product_code": "CPT0075", "price": 100, "valid_from": "2026-11-01", **bad})


def test_schema_bao_gia_cap_nhat_rong_khong_ghi_gi():
    assert QuoteUpdate().model_dump(exclude_unset=True) == {}


# ── Quyền ───────────────────────────────────────────────────────────────────────
def test_khong_co_quyen_la_403(db, seed, client_as):  # noqa: F811
    client = client_as(db.get(User, seed.u_req_id))
    assert client.get(QUOTES).status_code == 403
    assert client.post(QUOTES, json={"product_code": "CPT0075"}).status_code == 403


def test_chi_co_quyen_xem_thi_khong_tao_khong_xoa(db, seed, cap_quyen, client_as):  # noqa: F811
    cap_quyen(seed.u_req_id, "packaging_cost", scope="all", read=True)
    client = client_as(db.get(User, seed.u_req_id))
    assert client.get(QUOTES).status_code == 200
    assert client.post(QUOTES, json={}).status_code == 403
    assert client.delete(f"{QUOTES}/1").status_code == 403


# ── Báo giá ─────────────────────────────────────────────────────────────────────
def test_tao_bao_gia_ghi_ca_gia_tri_va_tra_ten_san_pham(api, db, seed):
    db.add(Supplier(code="NCC01", name="NCC Một", supplier_type="goods", is_active=True))
    db.commit()
    res = api.post(QUOTES, json={"product_code": "CPT0075", "supplier_code": "NCC01", "price": 1250.5,
                                 "vat": 8, "valid_from": "2026-12-01", "note": "báo tăng"})
    assert res.status_code == 201, res.text
    data = res.json()["data"]
    assert (data["product_name"], data["supplier_name"], data["product_unit"]) == ("Chai 1L", "NCC Một", "Cái")
    row = db.query(ProductPriceQuote).one()
    assert (row.price, row.valid_from, row.created_by) == (Decimal("1250.5"), date(2026, 12, 1), seed.u_req_id)


def test_nhieu_bao_gia_cung_ma_khong_bi_chan_trung(api, db):
    for day in ("2026-11-01", "2026-12-01"):
        assert api.post(QUOTES, json={"product_code": "CPT0075", "price": 100, "valid_from": day}).status_code == 201
    assert db.query(ProductPriceQuote).count() == 2


@pytest.mark.parametrize("body,needle", [
    ({"product_code": "KHONG_CO", "price": 1, "valid_from": "2026-11-01"}, "không có trong danh mục sản phẩm"),
    ({"product_code": "CPT0075", "supplier_code": "XX", "price": 1, "valid_from": "2026-11-01"}, "nhà cung cấp"),
])
def test_bao_gia_ma_khong_co_trong_danh_muc_la_422_tieng_viet(api, body, needle):
    res = api.post(QUOTES, json=body)
    assert res.status_code == 422 and needle in res.text


def test_bao_gia_gia_am_hoac_ngay_nam_0_la_422(api):
    assert api.post(QUOTES, json={"product_code": "CPT0075", "price": -5, "valid_from": "2026-11-01"}).status_code == 422
    assert api.post(QUOTES, json={"product_code": "CPT0075", "price": 5, "valid_from": "0001-01-01"}).status_code == 422


def test_sua_bao_gia_chi_ghi_o_gui_len_va_chan_null_cot_bat_buoc(api, db):
    q = add_quote(db, "CPT0075", 100, "2026-11-01")
    ok = api.patch(f"{QUOTES}/{q.id}", json={"price": 150})
    assert ok.status_code == 200 and db.get(ProductPriceQuote, q.id).price == Decimal("150")
    assert api.patch(f"{QUOTES}/{q.id}", json={"price": None}).status_code == 422
    assert api.patch(f"{QUOTES}/{q.id}", json={"product_code": "KHONG_CO"}).status_code == 422


def test_xoa_bao_gia_va_404(api, db):
    q = add_quote(db, "CPT0075", 100, "2026-11-01")
    assert api.delete(f"{QUOTES}/{q.id}").status_code == 200
    assert api.delete(f"{QUOTES}/{q.id}").status_code == 404


# ── Ngưỡng giá đã bỏ (phase 04, C6) ─────────────────────────────────────────────
def test_duong_nguong_gia_khong_con_la_404_ca_khi_co_du_quyen(api):
    """Router `/api/product-price-limits` đã gỡ: mọi phương thức, kể cả đường chi tiết, phải 404 (không phải 403 / 405)."""
    assert api.get(LIMITS).status_code == 404
    assert api.post(LIMITS, json={"product_code": "CPT0075", "floor_price": 1}).status_code == 404
    assert api.get(f"{LIMITS}/1").status_code == 404
    assert api.patch(f"{LIMITS}/1", json={"floor_price": 1}).status_code == 404
    assert api.delete(f"{LIMITS}/1").status_code == 404
    assert not [r.path for r in app.routes if "price-limit" in getattr(r, "path", "")]


def test_model_va_schema_nguong_khong_con():
    import app.modules.product_price.model as model
    import app.modules.product_price.schema as schema
    assert not hasattr(model, "ProductPriceLimit")
    assert not any(n.startswith("Limit") for n in dir(schema))


def test_danh_sach_loc_theo_ma(api, db):
    add_quote(db, "CPT0075", 100, "2026-11-01")
    add_quote(db, "NAP0085", 50, "2026-11-01")
    res = api.get(QUOTES, params={"product_code": "NAP"})
    assert [r["product_code"] for r in res.json()["data"]["items"]] == ["NAP0085"]


def test_impact_request_cat_khoang_trang_khoa_gia_gia_dinh_va_chan_khoa_la_va_qua_500():
    from app.modules.packaging_cost.impact_schema import ImpactRequest
    ok = ImpactRequest(codes=["A", "B"], assumed_prices={" A ": 10, "B\t": 20})
    assert ok.assumed_prices == {"A": Decimal(10), "B": Decimal(20)}
    with pytest.raises(ValidationError, match="chưa chọn"):
        ImpactRequest(codes=["A"], assumed_prices={" B ": 1})
    with pytest.raises(ValidationError):
        ImpactRequest(codes=[f"C{i}" for i in range(500)], assumed_prices={f"C{i}": 1 for i in range(501)})


def test_ten_entity_nhat_ky_cua_hai_danh_muc_quy_ve_khoa_packaging_cost():
    """`audit_entity` của hai CRUD (định mức, báo giá) phải có trong PERMISSION_KEY_ALIAS, kẻo màn Nhật ký hỏi quyền theo tên không có trong bảng quyền."""
    from app.modules.audit.controller import PERMISSION_KEY_ALIAS
    from app.modules.packaging_cost.bom_controller import router as bom_router
    from app.modules.product_price.quote_limit_controller import quote_router
    for name in ("packaging_bom", "packaging_cost_quote"):
        assert PERMISSION_KEY_ALIAS[name] == "packaging_cost"
    assert "packaging_cost_limit" not in PERMISSION_KEY_ALIAS
    assert bom_router and quote_router
