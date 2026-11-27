"""duoc-CR-784 (26/11/2026) — Lịch sử mua hàng chế độ "Theo mã sản phẩm" khi chọn ĐÚNG MỘT sản phẩm: `series_by_code` = mỗi mã thành
phần của định mức có lần mua có giá một đường giá cũ -> mới. Hợp đồng: `[{code, name, role, points: [{date, price}]}]`, xếp theo vai trò
rồi mã, tối đa SERIES_CAP điểm gần nhất mỗi mã; ngược lại `null`. Cùng bộ lọc + phạm vi pháp nhân với bảng; thêm đúng một truy vấn."""
from datetime import date

import pytest

from app.core.packaging_price_codes import PackagingRole
from app.modules.packaging_cost import history_service
from app.modules.packaging_cost.history_service import build_history
from app.modules.supplier.model import Supplier
from app.modules.user.model import User
from hdld_factory import client_as  # noqa: F401  (fixture)
from lich_lam_viec_factory import count_queries
from so_gia_factory_cr784 import add_ledger, add_products, build_bom

URL = "/api/packaging-cost/history"


def _bom(db, fg, **over):
    base = dict(fg_code=fg, fg_name=f"Sản phẩm {fg}", bottle_code="CPT0105", cap_code="", label_code="", carton_label_code="",
                carton_code="", carton_qty=40, created_by=1, updated_by=1)
    base.update(over)
    db.add(build_bom(**base))
    db.commit()


@pytest.fixture
def world(db):
    """HH0001 = chai CPT0105 (3 lần mua) + nắp NAP0085 (1) + nhãn NHG0001 (1) + thùng THG0001 (chỉ giá 0); HH0002 = chai và nắp cùng một mã."""
    add_products(db, ("CPT0105", "Chai 450ml", "Cái"), ("NAP0085", "Nắp vặn", "Cái"), ("NHG0001", "Nhãn", "Cái"),
                 ("THG0001", "Thùng", "Cái"))
    db.add_all([Supplier(code="NCC01", name="Nhựa Á Châu"), Supplier(code="NCC02", name="Nhựa Việt")])
    db.commit()
    add_ledger(db, "CPT0105", 100, "2026-01-01", supplier="NCC01")
    add_ledger(db, "CPT0105", 110, "2026-02-01", supplier="NCC02")
    add_ledger(db, "CPT0105", 120, "2026-02-01", supplier="NCC01", doc_id=5)       # cùng ngày: hơn doc_id nên đứng sau
    add_ledger(db, "NAP0085", 200, "2026-02-01", supplier="NCC01")
    add_ledger(db, "NHG0001", 50, "2026-03-01", supplier="NCC02")
    add_ledger(db, "THG0001", 0, "2026-03-01", supplier="NCC02")                   # giá 0: không có điểm
    _bom(db, "HH0001", cap_code="NAP0085", label_code="NHG0001", carton_code="THG0001")
    _bom(db, "HH0002", cap_code="CPT0105")
    _bom(db, "HH0003", bottle_code="THG0001")                                       # chỉ mã giá 0
    return None


@pytest.fixture
def api(db, seed, cap_quyen, client_as, world):  # noqa: F811
    cap_quyen(seed.u_req_id, "packaging_history", scope="all", read=True)
    return client_as(db.get(User, seed.u_req_id))


def _get(api, **params):
    res = api.get(URL, params=params)
    assert res.status_code == 200, res.text
    return res.json()["data"]


def test_mot_san_pham_moi_thanh_phan_co_gia_mot_duong_xep_theo_vai_tro(api):
    data = _get(api, mode="product", fg_codes=["HH0001"])
    assert data["series"] is None
    assert data["series_by_code"] == [
        {"code": "CPT0105", "name": "Chai 450ml", "role": int(PackagingRole.BOTTLE),
         "points": [{"date": "2026-01-01", "price": 100}, {"date": "2026-02-01", "price": 110},
                    {"date": "2026-02-01", "price": 120}]},
        {"code": "NAP0085", "name": "Nắp vặn", "role": int(PackagingRole.CAP), "points": [{"date": "2026-02-01", "price": 200}]},
        {"code": "NHG0001", "name": "Nhãn", "role": int(PackagingRole.LABEL), "points": [{"date": "2026-03-01", "price": 50}]},
    ]                                                                                # THG0001 chỉ giá 0 -> không có đường


def test_ma_hai_vai_tro_chi_mot_duong_vai_tro_nho_nhat(api):
    lines = _get(api, mode="product", fg_codes=["HH0002"])["series_by_code"]
    assert [(line["code"], line["role"], len(line["points"])) for line in lines] == [("CPT0105", int(PackagingRole.BOTTLE), 3)]


def test_khong_phai_dung_mot_san_pham_hoac_khong_co_gia_thi_null(api):
    assert _get(api, mode="product", fg_codes=["HH0001", "HH0002"])["series_by_code"] is None
    assert _get(api, mode="product")["series_by_code"] is None                       # rỗng = mọi sản phẩm
    assert _get(api, mode="product", fg_codes=["HH0003"])["series_by_code"] is None  # chỉ lần mua giá 0
    assert _get(api, mode="product", fg_codes=["HH9999"])["series_by_code"] is None  # không có định mức
    assert _get(api, mode="code", codes=["CPT0105"])["series_by_code"] is None      # chế độ mã dùng `series`


def test_bo_loc_nha_cung_cap_khoang_ngay_va_chu_tim_ap_cho_bieu_do(api):
    by_supplier = _get(api, mode="product", fg_codes=["HH0001"], supplier=["NCC02"])["series_by_code"]
    assert [(line["code"], [p["price"] for p in line["points"]]) for line in by_supplier] == [("CPT0105", [110]), ("NHG0001", [50])]
    by_date = _get(api, mode="product", fg_codes=["HH0001"], date_from="2026-02-01", date_to="2026-02-28")["series_by_code"]
    assert [(line["code"], [p["price"] for p in line["points"]]) for line in by_date] == [("CPT0105", [110, 120]), ("NAP0085", [200])]
    by_text = _get(api, mode="product", fg_codes=["HH0001"], q="nắp")["series_by_code"]
    assert [line["code"] for line in by_text] == ["NAP0085"]


def test_tran_so_diem_moi_ma_la_cac_diem_gan_nhat_cu_den_moi(db, world, monkeypatch):
    monkeypatch.setattr(history_service, "SERIES_CAP", 2)
    lines = build_history(db, mode="product", fg_codes=["HH0001"])["series_by_code"]
    chai = next(line for line in lines if line["code"] == "CPT0105")
    assert [p["price"] for p in chai["points"]] == [110, 120]                        # hai điểm mới nhất, vẫn cũ -> mới


def test_pham_vi_cong_ty_khong_lo_diem_cua_phap_nhan_khac(db, seed, cap_quyen, client_as, world):  # noqa: F811
    from app.modules.product_price.model import ProductPriceLedger
    db.query(ProductPriceLedger).update({ProductPriceLedger.company_id: seed.company_id})
    add_ledger(db, "CPT0105", 999, "2026-03-15", company_id=seed.company_id + 99)
    cap_quyen(seed.u_req_id, "packaging_history", scope="company", read=True)
    res = client_as(db.get(User, seed.u_req_id)).get(URL, params={"mode": "product", "fg_codes": ["HH0001"]})
    chai = next(line for line in res.json()["data"]["series_by_code"] if line["code"] == "CPT0105")
    assert [p["price"] for p in chai["points"]] == [100, 110, 120]


def test_dung_mot_truy_van_them_cho_moi_ma_thanh_phan(db, world):
    _, one_product = count_queries(db, lambda: build_history(db, mode="product", fg_codes=["HH0001"]))
    for i in range(30):                                                             # thêm nhiều mã thành phần: số truy vấn đứng yên
        add_products(db, (f"X{i:03d}", f"Vật tư {i}", "Cái"))
        add_ledger(db, f"X{i:03d}", 10 + i, "2026-03-02")
    _bom(db, "HH5000", bottle_code="X000", cap_code="X001", label_code="X002", carton_label_code="X003", carton_code="X004")
    res, five_parts = count_queries(db, lambda: build_history(db, mode="product", fg_codes=["HH5000"]))
    _, two_products = count_queries(db, lambda: build_history(db, mode="product", fg_codes=["HH0001", "HH5000"]))
    assert len(res["series_by_code"]) == 5
    assert len(one_product) == len(five_parts) == 5 and len(two_products) == 4        # +1 truy vấn biểu đồ chỉ khi đúng một sản phẩm
