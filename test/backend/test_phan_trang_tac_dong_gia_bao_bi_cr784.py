"""duoc-CR-784 — bảng SẢN PHẨM BỊ ẢNH HƯỞNG phân trang / tìm / xếp tại MÁY CHỦ (KPI vẫn tính trên toàn bộ tập), đường nhanh của
Bảng giá (lọc + xếp + cắt trang trước, tính giá sau) phải cho đúng kết quả của đường đầy đủ, và số truy vấn không đổi theo trang."""
from decimal import Decimal
from io import BytesIO

import openpyxl
import pytest

from app.modules.packaging_cost.impact_service import SORT_GETTERS, compute_impact
from app.modules.packaging_cost.model import PackagingBom
from app.modules.packaging_cost.price_list_service import STATIC_SORT_KEYS, build_price_list, build_price_list_page
from app.modules.user.model import User
from hdld_factory import client_as  # noqa: F401  (fixture)
from lich_lam_viec_factory import count_queries
from so_gia_factory_cr784 import add_ledger, add_products, add_quote, build_bom, column_values

D = Decimal
IMPACT = "/api/packaging-cost/impact"
PRICE_LIST = "/api/packaging-cost/price-list"
N = 30
BOTTLES = [f"B{i:02d}" for i in range(N)]


def _bom(db, i: int, **over) -> PackagingBom:
    base = {"fg_code": f"HH{i:03d}", "fg_name": f"Sản phẩm số {i}", "legal_name": f"Tên pháp lý {i}", "bottle_code": BOTTLES[i],
            "cap_code": "NAP1", "label_code": "", "carton_label_code": "", "carton_code": "", "carton_qty": 10 + i,
            "created_by": 1, "updated_by": 1}
    base.update(over)
    row = build_bom(**base)
    db.add(row)
    return row


@pytest.fixture
def world(db):
    """30 sản phẩm, mỗi sản phẩm một chai riêng (giá chai i: 1000 + 10 i); nắp chung NAP1 giá 100; quy cách thùng 10 + i
    (sản phẩm 5 và 6 KHÔNG có quy cách thùng → chênh /thùng trống)."""
    add_products(db, *[(c, f"Chai {c}", "Cái") for c in BOTTLES], ("NAP1", "Nắp một", "Cái"))
    for i, code in enumerate(BOTTLES):
        add_ledger(db, code, 1000 + 10 * i, "2026-01-01")
    add_ledger(db, "NAP1", 100, "2026-01-01")
    for i in range(N):
        _bom(db, i, **({"carton_qty": 0} if i in (5, 6) else {}))
    db.commit()


ASSUMED = {code: D(2000 + 7 * i) for i, code in enumerate(BOTTLES)}   # chênh /chai = 1000 - 3 i  (giảm dần theo i)


def _impact(db, **kw):
    return compute_impact(db, BOTTLES, ASSUMED, **kw)


# ── Phân trang ──────────────────────────────────────────────────────────────────
def test_trang_cat_dung_va_kpi_tinh_tren_toan_bo_tap(db, world):
    full = _impact(db)
    page = _impact(db, page=2, page_size=10)
    assert [p["fg_code"] for p in page["products"]] == [f"HH{i:03d}" for i in range(10, 20)]
    assert page["products_total"] == N and len(full["products"]) == N
    assert page["kpis"] == full["kpis"] and page["kpis"]["affected_products"] == N and page["kpis"]["increased"] == N
    assert page["selected"] == full["selected"]


def test_trang_cuoi_le_trang_qua_ban_va_trang_xa_deu_rong_nhung_van_co_tong(db, world):
    assert len(_impact(db, page=3, page_size=12)["products"]) == 6
    far = _impact(db, page=99, page_size=10)
    assert far["products"] == [] and far["products_total"] == N and far["kpis"]["affected_products"] == N


def test_xep_ho_tro_hai_chieu_o_trong_xuong_cuoi_khoa_phu_la_ma_hh(db, world):
    for direction in ("asc", "desc"):
        rows = _impact(db, sort_by="diff_carton", sort_dir=direction)["products"]
        assert [r["fg_code"] for r in rows[-2:]] == ["HH005", "HH006"]            # không có quy cách → trống → cuối, mã tăng dần
        filled = [r["diff_carton"] for r in rows[:-2]]
        assert filled == sorted(filled, reverse=(direction == "desc"))
    rows = _impact(db, sort_by="trend", sort_dir="desc")["products"]               # mọi sản phẩm cùng xu hướng → hòa → mã tăng dần
    assert [r["fg_code"] for r in rows] == [f"HH{i:03d}" for i in range(N)]


def test_xep_theo_ten_bo_dau_va_khoa_la_roi_ve_ma_hh(db, world):
    names = [p["fg_name"] for p in _impact(db, sort_by="fg_name", sort_dir="desc")["products"]]
    assert names == sorted(names, reverse=True)
    for hostile in ("'; drop table tab_packaging_bom; --", "", "diff_bottle desc, id", "__class__"):
        rows = _impact(db, sort_by=hostile)["products"]
        assert [r["fg_code"] for r in rows] == [f"HH{i:03d}" for i in range(N)]


def test_moi_khoa_xep_deu_chay_duoc():
    assert set(SORT_GETTERS) >= {"fg_code", "fg_name", "carton_qty", "cost_old_bottle", "cost_applied_bottle", "diff_bottle",
                                 "diff_carton", "pct", "trend"}


# ── Tìm kiếm ────────────────────────────────────────────────────────────────────
def test_tim_khong_phan_biet_dau_theo_ten_ma_hh_ma_thanh_phan_va_ten_phap_ly(db, world):
    assert [p["fg_code"] for p in _impact(db, q="san pham so 7")["products"]] == ["HH007", "HH017", "HH027"]   # bỏ dấu, khớp chuỗi con
    assert _impact(db, q="HH01")["products_total"] == 10                              # HH010..HH019
    assert [p["fg_code"] for p in _impact(db, q="b07")["products"]] == ["HH007"]      # mã thành phần
    assert _impact(db, q="phap ly 12")["products_total"] == 1                          # tên pháp lý
    assert _impact(db, q="nap1")["products_total"] == N                                # mã nắp chung
    assert _impact(db, q="so 7 nap1")["products_total"] == 3                           # nhiều từ khóa: tất cả đều phải khớp
    assert _impact(db, q="so 7 b07")["products_total"] == 1
    out = _impact(db, q="khong co gi ca", page=1, page_size=5)
    assert out["products"] == [] and out["products_total"] == 0
    assert out["kpis"]["affected_products"] == N                                       # tìm KHÔNG đổi KPI


def test_tim_voi_ky_tu_la_khong_vo_loi(db, world):
    for hostile in ("%", "_", "' OR '1'='1", "\\", "   ", "đ", "ǅ" * 50):
        assert _impact(db, q=hostile)["products_total"] in (0, N)


def test_tim_trong_ket_hop_xep_va_trang(db, world):
    out = _impact(db, q="HH01", sort_by="diff_bottle", sort_dir="asc", page=2, page_size=4)
    assert out["products_total"] == 10 and len(out["products"]) == 4
    diffs = [p["diff_bottle"] for p in _impact(db, q="HH01", sort_by="diff_bottle", sort_dir="asc")["products"]]
    assert diffs == sorted(diffs) and [p["diff_bottle"] for p in out["products"]] == diffs[4:8]


# ── Số truy vấn ─────────────────────────────────────────────────────────────────
def test_so_truy_van_khong_doi_theo_trang_tim_xep(db, world):
    counts = set()
    for kw in ({}, {"page": 1, "page_size": 5}, {"page": 4, "page_size": 5, "q": "HH01", "sort_by": "diff_bottle"},
               {"page": 99, "page_size": 500, "sort_by": "fg_name", "sort_dir": "desc"}):
        _, sqls = count_queries(db, lambda kw=kw: _impact(db, **kw))
        counts.add(len(sqls))
    assert len(counts) == 1 and counts.pop() <= 6


# ── API ─────────────────────────────────────────────────────────────────────────
@pytest.fixture
def api(db, seed, cap_quyen, client_as, world):  # noqa: F811
    for key in ("packaging_impact", "packaging_price_list"):       # bao-CR-792: mỗi màn một khóa
        cap_quyen(seed.u_req_id, key, scope="all", read=True, export=True)
    return client_as(db.get(User, seed.u_req_id))


def _body(**over):
    body = {"codes": BOTTLES, "assumed_prices": {c: float(v) for c, v in ASSUMED.items()}}
    body.update(over)
    return body


def test_api_mac_dinh_trang_1_50_dong_va_tra_products_total(api):
    data = api.post(IMPACT, json=_body()).json()["data"]
    assert len(data["products"]) == N and data["products_total"] == N               # 30 < 50
    data = api.post(IMPACT, json=_body(page_size=7, page=2, sort_by="fg_code", sort_dir="desc")).json()["data"]
    assert [p["fg_code"] for p in data["products"]] == [f"HH{i:03d}" for i in range(22, 15, -1)]
    assert data["kpis"]["affected_products"] == N


@pytest.mark.parametrize("over", [{"page": 0}, {"page": -1}, {"page": 100001}, {"page_size": 0}, {"page_size": 501},
                                  {"page_size": -5}, {"sort_dir": "up"}, {"sort_dir": ""}, {"sort_by": "x" * 31},
                                  {"q": "x" * 101}, {"page": "abc"}, {"page_size": 1.5}])
def test_api_tham_so_phan_trang_sai_la_422(api, over):
    assert api.post(IMPACT, json=_body(**over)).status_code == 422


def test_api_tran_page_size_500_hop_le(api):
    assert api.post(IMPACT, json=_body(page_size=500)).status_code == 200


def test_xuat_excel_bo_qua_phan_trang_nhung_theo_tim_va_xep(api):
    res = api.post(IMPACT + "/export", json=_body(page=3, page_size=1, q="HH01", sort_by="fg_code", sort_dir="desc"))
    assert res.status_code == 200
    ws = openpyxl.load_workbook(BytesIO(res.content))["Sản phẩm bị ảnh hưởng"]
    assert column_values(ws, "Mã HH") == [f"HH{i:03d}" for i in range(19, 9, -1)]
    full = api.post(IMPACT + "/export", json=_body(page_size=1))
    assert len(column_values(openpyxl.load_workbook(BytesIO(full.content))["Sản phẩm bị ảnh hưởng"], "Mã HH")) == N


# ── Bảng giá: đường nhanh == đường đầy đủ ───────────────────────────────────────
@pytest.fixture
def price_world(db):
    """Danh mục lẫn lộn: có / không có nhóm, ĐVT trống, tên có dấu, mã chỉ có báo giá, mã định mức chưa có trong danh mục."""
    for code, name, unit, group in (("C1", "Chai Đỏ", "Cái", "Chai"), ("C2", "chai xanh", "", "Chai"), ("N1", "Nắp ơ", "Cái", "Nắp"),
                                    ("L1", "Nhãn A", "Tờ", ""), ("T1", "Thùng 5 lớp", "Cái", "Thùng")):
        add_products(db, (code, name, unit))
    from app.modules.product.model import Product
    for code, group in (("C1", "Chai"), ("C2", "Chai"), ("N1", "Nắp"), ("L1", ""), ("T1", "Thùng")):
        db.query(Product).filter(Product.code == code).update({Product.item_group: group})
    for i, (code, price) in enumerate((("C1", 100), ("C1", 120), ("C2", 90), ("N1", 30), ("T1", 700), ("T1", 650))):
        add_ledger(db, code, price, f"2026-0{1 + i}-01")
    add_quote(db, "N1", 35, "2026-08-01")
    add_quote(db, "ONLYQ", 5, "2026-08-01")        # có báo giá nhưng không có trong danh mục
    for i, (bottle, cap, label) in enumerate((("C1", "N1", "L1"), ("C2", "N1", ""), ("C1", "", "L1"), ("GHOST", "N1", "L1"))):
        db.add(build_bom(fg_code=f"HH{i}", fg_name=f"SP {i}", bottle_code=bottle, cap_code=cap, label_code=label,
                            carton_code="T1" if i == 0 else "", carton_qty=12, created_by=1, updated_by=1))
    db.commit()


@pytest.mark.parametrize("sort_by", sorted(STATIC_SORT_KEYS))
@pytest.mark.parametrize("sort_dir", ["asc", "desc"])
@pytest.mark.parametrize("filters", [{}, {"q": "chai"}, {"q": "đỏ"}, {"q": "c1"}, {"group": "chai"}, {"group": "Khác"},
                                     {"q": "zzz"}, {"q": "n", "group": "nắp"}])
def test_duong_nhanh_cho_cung_ket_qua_voi_duong_day_du(db, price_world, sort_by, sort_dir, filters):
    full = build_price_list(db, sort_by=sort_by, sort_dir=sort_dir, **filters)
    for page_size in (1, 2, 50):
        got, seen = [], 0
        for page in range(1, len(full) // page_size + 3):
            items, total = build_price_list_page(db, page=page, page_size=page_size, sort_by=sort_by, sort_dir=sort_dir, **filters)
            assert total == len(full)
            got += items
            seen += 1
        assert got == full, (sort_by, sort_dir, filters, page_size)


def test_duong_nhanh_chi_tinh_gia_cho_ma_cua_trang_va_khong_doi_so_truy_van(db, price_world):
    _, sqls = count_queries(db, lambda: build_price_list_page(db, page=1, page_size=2))
    assert len(sqls) <= 7
    states_sql = [s for s in sqls if "tab_product_price_ledger" in s]
    assert states_sql, "đường nhanh vẫn phải đọc sổ giá cho các mã của trang"
    # đường đầy đủ (xếp theo số / scope=all) vẫn đúng và vẫn <= 7 truy vấn
    for kw in ({"sort_by": "diff"}, {"scope": "all"}):
        _, sqls = count_queries(db, lambda kw=kw: build_price_list_page(db, page=1, page_size=2, **kw))
        assert len(sqls) <= 7


def test_bang_gia_dvt_danh_muc_trong_lay_dvt_lan_mua_va_xep_theo_dvt_dang_hien(db, price_world):
    """C2 có ĐVT danh mục trống: cột ĐVT hiện ĐVT của lần mua ("Cái") ở cả đường nhanh lẫn đường đầy đủ, xếp theo giá trị đang hiện,
    và số truy vấn vẫn trong trần 7."""
    items, _ = build_price_list_page(db, page=1, page_size=50)
    assert {r["code"]: r["unit"] for r in items}["C2"] == "Cái"
    assert "unit" not in STATIC_SORT_KEYS
    asc = [r["unit"] for r in build_price_list(db, sort_by="unit", sort_dir="asc") if r["unit"]]
    assert asc == sorted(asc, key=str.casefold) and "Cái" in asc
    _, sqls = count_queries(db, lambda: build_price_list_page(db, page=1, page_size=2))
    _, sqls_unit = count_queries(db, lambda: build_price_list_page(db, page=1, page_size=2, sort_by="unit"))
    assert len(sqls) <= 7 and len(sqls_unit) <= 7
