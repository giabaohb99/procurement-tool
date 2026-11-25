"""duoc-CR-784 — Lịch sử mua hàng chế độ "Theo mã sản phẩm" y bản mẫu `renderHistBySP`: mỗi dòng = một lần mua x một cặp
(sản phẩm, mã thành phần của định mức) — một lần mua của mã dùng ở N sản phẩm cho N dòng; mã hai vai trò trong cùng sản phẩm chỉ tính
một lần; thứ tự mặc định ngày -> mã sản phẩm -> thành phần; thẻ số liệu (số dòng, mã liên quan, số sản phẩm, số NCC); lọc / xếp /
phân trang tại máy chủ với khóa phụ không làm mất / lặp dòng; xuất Excel đúng thứ tự cột của bản mẫu; phạm vi pháp nhân."""
from io import BytesIO

import openpyxl
import pytest

from app.core.packaging_price_codes import PackagingRole
from app.modules.packaging_cost.history_service import SORT_KEYS
from app.modules.packaging_cost.model import PackagingBom
from app.modules.supplier.model import Supplier
from app.modules.user.model import User
from hdld_factory import client_as  # noqa: F401  (fixture)
from so_gia_factory_cr784 import add_ledger, add_products, read_report_sheet

URL = "/api/packaging-cost/history"


def _bom(db, hh, **over):
    base = dict(hh_code=hh, hh_name=f"Sản phẩm {hh}", bottle_code="CPT0105", cap_code="", label_code="", carton_label_code="",
                carton_code="", carton_qty=40, created_by=1, updated_by=1)
    base.update(over)
    db.add(PackagingBom(**base))
    db.commit()


@pytest.fixture
def world(db):
    """Chai CPT0105 (3 lần mua) dùng ở 3 sản phẩm; nắp NAP0085 (1 lần) chỉ ở HH0001; HH0002 khai chai CPT0105 làm cả NẮP."""
    add_products(db, ("CPT0105", "Chai 450ml", "Cái"), ("NAP0085", "Nắp vặn", "Cái"), ("NHG0001", "Nhãn", "Cái"))
    db.add_all([Supplier(code="NCC01", name="Nhựa Á Châu"), Supplier(code="NCC02", name="Nhựa Việt")])
    db.commit()
    add_ledger(db, "CPT0105", 100, "2026-01-01", supplier="NCC01", qty=1000)
    add_ledger(db, "CPT0105", 110, "2026-02-01", supplier="NCC02", qty=500)
    add_ledger(db, "CPT0105", 120, "2026-02-01", supplier="NCC01", qty=700, doc_id=5)       # cùng ngày: hơn doc_id
    add_ledger(db, "NAP0085", 200, "2026-02-01", supplier="NCC01", qty=10)
    add_ledger(db, "NHG0001", 50, "2026-03-01", supplier="NCC02", qty=300)
    _bom(db, "HH0001", cap_code="NAP0085", label_code="NHG0001")
    _bom(db, "HH0002", cap_code="CPT0105", label_code="NHG0001")
    _bom(db, "HH0003")
    return None


@pytest.fixture
def api(db, seed, cap_quyen, client_as, world):  # noqa: F811
    cap_quyen(seed.u_req_id, "packaging_cost", scope="all", read=True, export=True)
    return client_as(db.get(User, seed.u_req_id))


def _get(api, **params):
    res = api.get(URL, params={"mode": "product", **params})
    assert res.status_code == 200, res.text
    return res.json()["data"]


def test_moi_lan_mua_ra_mot_dong_cho_moi_san_pham_dung_ma_do(api):
    data = _get(api, page_size=500)
    rows = data["items"]
    #  CPT0105: 3 lần mua x 3 sản phẩm = 9 dòng; NAP0085: 1 x HH0001; NHG0001: 1 x (HH0001 + HH0002)
    assert data["total"] == len(rows) == 9 + 1 + 2
    chai = [r for r in rows if r["code"] == "CPT0105"]
    assert {(r["hh_code"], r["id"]) for r in chai} == {(hh, i) for hh in ("HH0001", "HH0002", "HH0003")
                                                        for i in {c["id"] for c in chai}} and len(chai) == 9
    assert all(r["hh_name"] == f"Sản phẩm {r['hh_code']}" for r in rows)
    assert {r["seq"] for r in chai if r["date"] == "2026-02-01" and r["price"] == 120} == {1}        # Lần theo MÃ, không theo sản phẩm
    assert sorted({r["seq"] for r in chai}) == [1, 2, 3]


def test_ma_hai_vai_tro_trong_cung_san_pham_chi_mot_dong_vai_tro_nho_nhat(api):
    rows = [r for r in _get(api, hh_codes=["HH0002"], page_size=500)["items"] if r["code"] == "CPT0105"]
    assert len(rows) == 3 and {r["role"] for r in rows} == {int(PackagingRole.BOTTLE)}      # chai + nắp cùng mã: tính một lần, vai trò Chai


def test_thu_tu_mac_dinh_ngay_giam_dan_roi_ma_san_pham_roi_thanh_phan_roi_id_giam(api):
    rows = _get(api, page_size=500)["items"]
    keys = [(r["date"], r["hh_code"], r["role"], r["id"]) for r in rows]
    assert keys == sorted(keys, key=lambda k: (-int(k[0].replace("-", "")), k[1], k[2], -k[3]))
    assert [r["date"] for r in rows][:2] == ["2026-03-01", "2026-03-01"] and rows[0]["hh_code"] == "HH0001"
    asc = _get(api, sort_dir="asc", page_size=500)["items"]
    assert [r["date"] for r in asc] == sorted(r["date"] for r in asc)


def test_the_so_lieu_so_dong_ma_lien_quan_so_san_pham_va_so_nha_cung_cap(api):
    stats = _get(api)["stats"]
    assert (stats["purchase_count"], stats["code_count"], stats["product_count"], stats["supplier_count"]) == (12, 3, 3, 2)
    assert (stats["first_date"], stats["last_date"]) == ("2026-01-01", "2026-03-01")
    assert stats["first_price"] is None and stats["last_price"] is None      # trộn nhiều mã: giá đầu / cuối vô nghĩa
    one = _get(api, hh_codes=["HH0003"])["stats"]
    assert (one["purchase_count"], one["code_count"], one["product_count"]) == (3, 1, 1)
    assert _get(api, hh_codes=["HH0003", "HH9999"])["stats"]["product_count"] == 1        # mã không có định mức không tính
    empty = _get(api, hh_codes=["HH9999"])
    assert (empty["total"], empty["items"], empty["stats"]["product_count"], empty["suppliers"]) == (0, [], 0, [])


@pytest.mark.parametrize("params", [
    {}, {"hh_codes": ["HH0002"]}, {"hh_codes": ["HH0001", "HH0003"]}, {"q": "nap"}, {"q": "Việt"}, {"q": "HH0002"},
    {"q": "nhãn"}, {"q": "chai", "hh_codes": ["HH0001", "HH0002"]}, {"supplier": ["NCC01"]},
    {"date_from": "2026-02-01", "date_to": "2026-02-28", "q": "Sản phẩm"},
])
def test_so_gop_cong_co_trong_so_theo_cap_bang_dung_so_tu_cac_dong_da_nhan(db, api, params):
    """Số gộp không nối từng cặp mà nhân dòng sổ giá với số cặp của mã: phải trùng số cộng tay từ MỌI dòng đã nhân của danh sách."""
    add_products(db, ("TEM0009", "Tem dán", "Cái"))
    add_ledger(db, "TEM0009", 0, "2026-03-05", qty=4)                  # giá 0: có dòng, không tính vào số có giá
    _bom(db, "HH0004", label_code="TEM0009", cap_code="NAP0085")
    data = _get(api, page_size=500, **params)
    rows, stats = data["items"], data["stats"]
    priced = [r for r in rows if r["price"] and r["price"] > 0]
    assert len(rows) == data["total"] == stats["purchase_count"]
    assert stats["priced_count"] == len(priced)
    assert stats["code_count"] == len({r["code"] for r in rows})
    assert stats["supplier_count"] == len({r["supplier_code"] for r in rows if r["supplier_code"]})
    assert stats["qty_total"] == pytest.approx(sum(r["qty"] for r in rows))
    assert stats["amount_total"] == pytest.approx(sum(r["amount"] or 0 for r in priced))
    if priced:
        assert (stats["min"], stats["max"]) == (min(r["price"] for r in priced), max(r["price"] for r in priced))
        assert (stats["first_date"], stats["last_date"]) == (min(r["date"] for r in rows), max(r["date"] for r in rows))
    assert {r["supplier_code"] for r in rows} <= {o["code"] for o in data["suppliers"]} | {""}


def test_loc_chu_tim_ma_va_ten_san_pham_va_ten_thanh_phan(api):
    assert {r["hh_code"] for r in _get(api, q="HH0002")["items"]} == {"HH0002"}
    assert {r["hh_code"] for r in _get(api, q="Sản phẩm HH0003")["items"]} == {"HH0003"}
    assert {r["role"] for r in _get(api, q="nap")["items"]} == {int(PackagingRole.CAP)}       # khớp tên vật tư "Nắp vặn" không dấu
    assert len(_get(api, q="thùng")["items"]) == 0                  # chưa sản phẩm nào có thùng
    assert _get(api, q="Việt", hh_codes=["HH0003"])["total"] == 1   # nhà cung cấp vẫn tìm được
    assert _get(api, supplier=["NCC02"], date_from="2026-02-01", date_to="2026-02-28")["total"] == 3


def test_chu_tim_khop_ca_ten_thanh_phan_du_ten_vat_tu_khong_chua_chu_do(db, api):
    add_products(db, ("TEM0009", "Tem dán", "Cái"))
    add_ledger(db, "TEM0009", 15, "2026-03-05", qty=1)
    _bom(db, "HH0004", label_code="TEM0009")
    rows = _get(api, q="nhãn", page_size=500)["items"]
    assert ("TEM0009", int(PackagingRole.LABEL)) in {(r["code"], r["role"]) for r in rows}       # chỉ khớp qua cột Thành phần
    assert all(r["role"] == int(PackagingRole.LABEL) or "nhãn" in r["name"].lower() for r in rows)


@pytest.mark.parametrize("key", SORT_KEYS)
@pytest.mark.parametrize("direction", ["asc", "desc"])
def test_moi_khoa_cot_xep_duoc_o_che_do_san_pham_khong_mat_khong_lap_dong_giua_cac_trang(api, key, direction):
    seen = []
    for page in (1, 2, 3, 4, 5):
        seen += [(r["hh_code"], r["id"]) for r in _get(api, sort_by=key, sort_dir=direction, page=page, page_size=3)["items"]]
    assert len(seen) == len(set(seen)) == 12


def test_xep_theo_ma_san_pham_ten_san_pham_va_thanh_phan_dung_chieu(api):
    asc = _get(api, sort_by="hh_code", sort_dir="asc", page_size=500)["items"]
    assert [r["hh_code"] for r in asc] == sorted(r["hh_code"] for r in asc)
    desc = _get(api, sort_by="hh_name", sort_dir="desc", page_size=500)["items"]
    assert [r["hh_name"] for r in desc] == sorted((r["hh_name"] for r in desc), reverse=True)
    roles = [r["role"] for r in _get(api, sort_by="role", sort_dir="asc", page_size=500)["items"]]
    assert roles == sorted(roles)


def test_khoa_cot_san_pham_o_che_do_ma_roi_ve_ngay_giam_dan(api):
    res = api.get(URL, params={"mode": "code", "codes": ["CPT0105"], "sort_by": "hh_code", "sort_dir": "asc"})
    dates = [r["date"] for r in res.json()["data"]["items"]]
    assert res.status_code == 200 and dates == sorted(dates, reverse=True)


def test_phan_trang_may_chu_tong_la_so_dong_sau_loc(api):
    page2 = _get(api, page=2, page_size=5)
    assert page2["total"] == 12 and len(page2["items"]) == 5 and _get(api, page=3, page_size=5)["items"].__len__() == 2


def test_pham_vi_cong_ty_chi_thay_dong_cua_phap_nhan_minh_ke_ca_lan(db, seed, cap_quyen, client_as, world):  # noqa: F811
    from app.modules.product_price.model import ProductPriceLedger
    db.query(ProductPriceLedger).update({ProductPriceLedger.company_id: seed.company_id})
    add_ledger(db, "CPT0105", 999, "2026-03-15", company_id=seed.company_id + 99)         # pháp nhân khác, mới nhất
    cap_quyen(seed.u_req_id, "packaging_cost", scope="company", read=True)
    data = client_as(db.get(User, seed.u_req_id)).get(URL, params={"mode": "product", "page_size": 500}).json()["data"]
    assert data["total"] == 12 and max(r["price"] for r in data["items"]) == 200 and {r["seq"] for r in data["items"] if r["code"] == "CPT0105"} == {1, 2, 3}


def test_xuat_excel_che_do_san_pham_dung_thu_tu_cot_ban_mau_va_dung_so_dong(api):
    res = api.get(URL + "/export", params={"mode": "product", "hh_codes": ["HH0001", "HH0002"], "sort_by": "hh_code", "sort_dir": "asc"})
    assert res.status_code == 200
    ws = openpyxl.load_workbook(BytesIO(res.content)).active
    head, rows = read_report_sheet(ws)
    assert head[:8] == ["Mã SP", "Tên sản phẩm", "Thành phần", "Mã VTBB", "Tên vật tư", "Lần", "Ngày mua", "Mã NCC"]
    assert len(rows) == 5 + 4
    api_rows = _get(api, hh_codes=["HH0001", "HH0002"], sort_by="hh_code", sort_dir="asc", page_size=500)["items"]
    assert [r[0].value for r in rows] == [r["hh_code"] for r in api_rows]
    assert [r[head.index("Lần")].value for r in rows] == [r["seq"] for r in api_rows]
    assert {r[head.index("Thành phần")].value for r in rows} == {"Chai", "Nắp", "Nhãn"}
    assert "2 sản phẩm · 3 mã VTBB · 9 dòng lịch sử" in ws["A2"].value
