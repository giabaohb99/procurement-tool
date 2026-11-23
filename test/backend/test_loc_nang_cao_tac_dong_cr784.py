"""duoc-CR-784 — LỌC NÂNG CAO + XẾP THEO CỘT THÀNH PHẦN của bảng sản phẩm bị ảnh hưởng (`POST /impact`) và Tổng hợp theo sản
phẩm: từng bộ lọc, ghép nhiều bộ lọc, ô trống bị loại khi khoảng bật, xếp năm cột thành phần hai chiều (ô trống cuối, hòa theo
mã thành phần rồi mã HH), xuất Excel theo cùng bộ lọc, KPI không đổi theo lọc, số truy vấn không đổi, và các giá trị sai là 422."""
import json
from decimal import Decimal
from io import BytesIO

import openpyxl
import pytest

from app.modules.packaging_cost.impact_filters import ImpactFilters
from app.modules.packaging_cost.impact_service import PART_SORT_ROLES, compute_impact
from app.modules.packaging_cost.model import PackagingBom
from app.modules.user.model import User
from hdld_factory import client_as  # noqa: F401  (fixture)
from lich_lam_viec_factory import count_queries
from so_gia_factory_cr784 import add_ledger, add_products

D = Decimal
IMPACT = "/api/packaging-cost/impact"
OVERVIEW = "/api/packaging-cost/product-overview"
CODES = ["BA", "BB", "CA", "T1"]
ASSUMED = {"BA": D(130), "BB": D(150), "T1": D(180)}


def _bom(db, hh, bottle, cap, label, carton_label, carton, qty):
    db.add(PackagingBom(hh_code=hh, hh_name=f"Sản phẩm {hh}", legal_name="", bottle_code=bottle, cap_code=cap, label_code=label,
                        carton_label_code=carton_label, carton_code=carton, carton_qty=qty, created_by=1, updated_by=1))


@pytest.fixture
def world(db):
    """Năm sản phẩm (đã tính tay):
    HH1 chai BA, nắp CA, nhãn LA, thùng T1, 12/thùng   → CP cũ 125, mới 160, +35/chai, +420/thùng, TĂNG
    HH2 chai BB, nắp CA, KHÔNG nhãn, thùng T1, 24      → CP cũ 215, mới 167,5, -47,5/chai, -1140/thùng, GIẢM, cảnh báo thiếu mã nhãn
    HH3 chai BC, nắp CA, nhãn LA, không thùng, 0       → CP 315, KHÔNG ĐỔI, không có quy cách thùng
    HH4 chai BD (chưa có giá), nắp CA, nhãn LA, 6      → CHƯA CÓ GIÁ, cảnh báo thiếu giá chai
    HH5 chai BA, nắp CA, nhãn LA, nhãn thùng TL1, thùng T1, 12 → CP cũ 128, mới 163, +35/chai, +420/thùng, TĂNG
    Chọn BA, BB, CA, T1; giá giả định BA 130, BB 150, T1 180 (CA chọn không kèm giá)."""
    add_products(db, *[(c, f"Vật tư {c}", "Cái") for c in ("BA", "BB", "BC", "BD", "CA", "LA", "TL1", "T1")])
    for code, price in (("BA", 100), ("BB", 200), ("BC", 300), ("CA", 10), ("LA", 5), ("TL1", 36), ("T1", 120)):
        add_ledger(db, code, price, "2026-01-01")
    _bom(db, "HH1", "BA", "CA", "LA", "", "T1", 12)
    _bom(db, "HH2", "BB", "CA", "", "", "T1", 24)
    _bom(db, "HH3", "BC", "CA", "LA", "", "", 0)
    _bom(db, "HH4", "BD", "CA", "LA", "", "", 6)
    _bom(db, "HH5", "BA", "CA", "LA", "TL1", "T1", 12)
    db.commit()


def _hh(db, **kw):
    return [p["hh_code"] for p in compute_impact(db, CODES, ASSUMED, **kw)["products"]]


def _flt(**kw) -> ImpactFilters:
    return ImpactFilters(**kw)


def _range(low, high):
    return (None if low is None else D(low), None if high is None else D(high))


# ── Công thức đúng như đã tính tay (nền cho mọi bài dưới) ────────────────────────
def test_nen_so_lieu(db, world):
    rows = {p["hh_code"]: p for p in compute_impact(db, CODES, ASSUMED)["products"]}
    assert rows["HH1"]["cost_applied_bottle"] == 160 and rows["HH1"]["diff_carton"] == 420 and rows["HH1"]["trend"] == 1
    assert rows["HH2"]["cost_applied_bottle"] == 167.5 and rows["HH2"]["diff_bottle"] == -47.5 and rows["HH2"]["trend"] == 2
    assert rows["HH3"]["trend"] == 3 and rows["HH3"]["diff_carton"] is None
    assert rows["HH4"]["trend"] == 4 and rows["HH4"]["cost_applied_bottle"] is None


# ── Từng bộ lọc ─────────────────────────────────────────────────────────────────
def test_khong_loc_thi_khong_doi(db, world):
    assert _hh(db, filters=_flt()) == _hh(db) == ["HH1", "HH2", "HH3", "HH4", "HH5"]
    assert not _flt().active and _flt(trend="up").active and _flt(warnings_only=True).active


@pytest.mark.parametrize("trend,expected", [("all", ["HH1", "HH2", "HH3", "HH4", "HH5"]), ("up", ["HH1", "HH5"]),
                                            ("down", ["HH2"]), ("flat", ["HH3"]), ("missing", ["HH4"])])
def test_loc_xu_huong(db, world, trend, expected):
    assert _hh(db, filters=_flt(trend=trend)) == expected


@pytest.mark.parametrize("roles,expected", [
    ({5}, ["HH1", "HH2", "HH5"]),                       # T1 đã chọn ở vai trò thùng
    ({1}, ["HH1", "HH2", "HH5"]),                       # BA / BB đã chọn ở vai trò chai
    ({2}, ["HH1", "HH2", "HH3", "HH4", "HH5"]),         # CA đã chọn ở vai trò nắp — mọi sản phẩm
    ({3}, []), ({4}, []),                               # nhãn LA / nhãn thùng TL1 KHÔNG được chọn → không sản phẩm nào
    ({1, 5}, ["HH1", "HH2", "HH5"]), ({3, 4}, []),      # nhiều vai trò = HOẶC
])
def test_loc_ma_da_chon_o_vai_tro(db, world, roles, expected):
    assert _hh(db, filters=_flt(part_roles=frozenset(roles))) == expected


def test_loc_vai_tro_phan_biet_chai_va_thung_khi_chon_khac(db, world):
    """Chỉ chọn CA + T1: chai không còn là mã đã chọn nên vai trò Chai không giữ sản phẩm nào."""
    out = compute_impact(db, ["CA", "T1"], {}, filters=_flt(part_roles=frozenset({1})))
    assert out["products"] == [] and out["kpis"]["affected_products"] == 5


@pytest.mark.parametrize("low,high,expected", [(12, 12, ["HH1", "HH5"]), (13, None, ["HH2"]), (None, 12, ["HH1", "HH4", "HH5"]),
                                               (1, 24, ["HH1", "HH2", "HH4", "HH5"]), (100, None, [])])
def test_loc_quy_cach_thung_va_o_trong_bi_loai(db, world, low, high, expected):
    assert _hh(db, filters=_flt(carton_qty=_range(low, high))) == expected     # HH3 (không có quy cách) luôn bị loại


@pytest.mark.parametrize("name,low,high,expected", [
    ("diff_bottle", 0, None, ["HH1", "HH3", "HH5"]), ("diff_bottle", None, -1, ["HH2"]), ("diff_bottle", 35, 35, ["HH1", "HH5"]),
    ("diff_bottle", -100, 100, ["HH1", "HH2", "HH3", "HH5"]),                       # HH4 chưa có giá → trống → loại
    ("diff_carton", 400, None, ["HH1", "HH5"]), ("diff_carton", None, 0, ["HH2"]),  # HH3 / HH4 không có chênh /thùng → loại
    ("cost_new_bottle", 161, 200, ["HH2", "HH5"]), ("cost_new_bottle", 300, None, ["HH3"]),
    ("cost_new_bottle", 160, 160, ["HH1"]),                                          # biên đóng
])
def test_loc_khoang_so(db, world, name, low, high, expected):
    assert _hh(db, filters=_flt(**{name: _range(low, high)})) == expected


def test_loc_chi_co_canh_bao(db, world):
    assert _hh(db, filters=_flt(warnings_only=True)) == ["HH2", "HH4"]      # thiếu mã nhãn · thiếu giá chai


def test_ket_hop_nhieu_bo_loc_la_va(db, world):
    assert _hh(db, filters=_flt(trend="up", carton_qty=_range(12, 12))) == ["HH1", "HH5"]
    assert _hh(db, filters=_flt(trend="up", part_roles=frozenset({5}), warnings_only=True)) == []
    assert _hh(db, filters=_flt(trend="down", warnings_only=True, diff_bottle=_range(None, 0))) == ["HH2"]
    assert _hh(db, q="HH5", filters=_flt(trend="up")) == ["HH5"]            # cùng ô tìm
    assert _hh(db, q="HH2", filters=_flt(trend="up")) == []
    assert _hh(db, filters=_flt(trend="up", diff_bottle=_range(30, None)), sort_by="hh_code", sort_dir="desc") == ["HH5", "HH1"]


def test_loc_khong_doi_kpi_va_tong_so_dong_la_sau_loc(db, world):
    full = compute_impact(db, CODES, ASSUMED)
    out = compute_impact(db, CODES, ASSUMED, filters=_flt(trend="up"), page=1, page_size=1)
    assert out["kpis"] == full["kpis"] and out["kpis"]["affected_products"] == 5
    assert out["selected"] == full["selected"]
    assert out["products_total"] == 2 and [p["hh_code"] for p in out["products"]] == ["HH1"]     # cắt trang SAU lọc


# ── Xếp theo năm cột thành phần ─────────────────────────────────────────────────
def test_xep_cot_chai_theo_gia_dang_ap_o_trong_cuoi_hai_chieu(db, world):
    #  Giá chai đang áp: HH1 130 · HH2 150 · HH3 300 · HH4 chưa có giá · HH5 130 (BA hòa nhau → mã HH tăng dần)
    assert _hh(db, sort_by="part_bottle", sort_dir="asc") == ["HH1", "HH5", "HH2", "HH3", "HH4"]
    assert _hh(db, sort_by="part_bottle", sort_dir="desc") == ["HH3", "HH2", "HH1", "HH5", "HH4"]


def test_xep_cot_nhan_va_thung_o_trong_la_san_pham_khong_co_ma(db, world):
    for direction in ("asc", "desc"):
        assert _hh(db, sort_by="part_label", sort_dir=direction)[-1] == "HH2"                   # HH2 không có nhãn → cuối
        assert _hh(db, sort_by="part_carton_label", sort_dir=direction)[0] == "HH5"             # chỉ HH5 có nhãn thùng
        assert _hh(db, sort_by="part_carton_label", sort_dir=direction)[1:] == ["HH1", "HH2", "HH3", "HH4"]
        assert _hh(db, sort_by="part_carton", sort_dir=direction)[:3] == ["HH1", "HH2", "HH5"]  # T1 (180) hòa → mã HH tăng
        assert _hh(db, sort_by="part_carton", sort_dir=direction)[3:] == ["HH3", "HH4"]
        assert _hh(db, sort_by="part_cap", sort_dir=direction) == ["HH1", "HH2", "HH3", "HH4", "HH5"]  # CA 10 hòa hết


def test_xep_thanh_phan_hoa_gia_theo_ma_thanh_phan_roi_ma_hh(db):
    """Hai mã nắp khác nhau cùng giá: hòa → mã thành phần tăng dần, rồi mã HH tăng dần (cả hai chiều)."""
    add_products(db, *[(c, f"Vật tư {c}", "Cái") for c in ("B1", "NZ", "NA")])
    for code, price in (("B1", 100), ("NZ", 10), ("NA", 10)):
        add_ledger(db, code, price, "2026-01-01")
    for hh, cap in (("HHA", "NZ"), ("HHB", "NA"), ("HHC", "NZ"), ("HHD", "NA")):
        _bom(db, hh, "B1", cap, "", "", "", 10)
    db.commit()
    for direction in ("asc", "desc"):
        rows = compute_impact(db, ["B1"], {}, sort_by="part_cap", sort_dir=direction)["products"]
        assert [p["hh_code"] for p in rows] == ["HHB", "HHD", "HHA", "HHC"]


def test_xep_theo_gia_giang_dinh_khong_phai_gia_cu(db, world):
    """Đổi giả định BA từ 130 lên 500 thì HH1 / HH5 (dùng BA) nhảy xuống cuối cột chai: xếp theo giá ĐANG ÁP, không theo giá cũ 100."""
    assert _hh(db, sort_by="part_bottle")[:2] == ["HH1", "HH5"]
    out = compute_impact(db, CODES, {**ASSUMED, "BA": D(500)}, sort_by="part_bottle")["products"]
    assert [p["hh_code"] for p in out] == ["HH2", "HH3", "HH1", "HH5", "HH4"]


def test_moi_khoa_xep_thanh_phan_deu_co_va_khoa_la_van_ve_ma_hh(db, world):
    assert set(PART_SORT_ROLES) == {"part_bottle", "part_cap", "part_label", "part_carton_label", "part_carton"}
    assert _hh(db, sort_by="part_hacker") == ["HH1", "HH2", "HH3", "HH4", "HH5"]


def test_xep_thanh_phan_ket_hop_loc_va_trang(db, world):
    out = compute_impact(db, CODES, ASSUMED, filters=_flt(carton_qty=_range(1, None)), sort_by="part_bottle", sort_dir="desc",
                         page=2, page_size=2)
    #  Sau lọc quy cách >= 1: HH1 HH2 HH4 HH5; xếp chai giảm: HH2 (150), HH1, HH5 (130), HH4 (trống) → trang 2 = HH5, HH4
    assert out["products_total"] == 4 and [p["hh_code"] for p in out["products"]] == ["HH5", "HH4"]


def test_so_truy_van_khong_doi_theo_loc_va_xep(db, world):
    counts = set()
    for kw in ({}, {"filters": _flt(trend="up")}, {"filters": _flt(warnings_only=True, carton_qty=_range(1, 50)), "sort_by": "part_bottle"},
               {"filters": _flt(part_roles=frozenset({1, 2, 3, 4, 5})), "sort_by": "part_carton", "sort_dir": "desc", "page": 2}):
        _, sqls = count_queries(db, lambda kw=kw: compute_impact(db, CODES, ASSUMED, **kw))
        counts.add(len(sqls))
    assert len(counts) == 1 and counts.pop() <= 6


# ── API ─────────────────────────────────────────────────────────────────────────
@pytest.fixture
def api(db, seed, cap_quyen, client_as, world):  # noqa: F811
    cap_quyen(seed.u_req_id, "packaging_cost", scope="all", read=True, export=True)
    return client_as(db.get(User, seed.u_req_id))


def _body(**over):
    body = {"codes": CODES, "assumed_prices": {c: float(v) for c, v in ASSUMED.items()}}
    body.update(over)
    return body


def _api_hh(api, **over):
    res = api.post(IMPACT, json=_body(**over))
    assert res.status_code == 200, res.text
    return res.json()["data"]


def test_api_loc_xu_huong_va_vai_tro_va_khoang(api):
    data = _api_hh(api, trend="up")
    assert [p["hh_code"] for p in data["products"]] == ["HH1", "HH5"] and data["products_total"] == 2
    assert data["kpis"]["affected_products"] == 5 and data["kpis"]["increased"] == 2
    assert _api_hh(api, part_roles=[3, 4])["products_total"] == 0
    assert [p["hh_code"] for p in _api_hh(api, part_roles=[5, 5])["products"]] == ["HH1", "HH2", "HH5"]
    assert [p["hh_code"] for p in _api_hh(api, cost_new_bottle_min=161, cost_new_bottle_max=200)["products"]] == ["HH2", "HH5"]
    assert [p["hh_code"] for p in _api_hh(api, diff_carton_max=0)["products"]] == ["HH2"]
    assert [p["hh_code"] for p in _api_hh(api, carton_qty_min=12, carton_qty_max=12)["products"]] == ["HH1", "HH5"]
    assert [p["hh_code"] for p in _api_hh(api, warnings_only=True)["products"]] == ["HH2", "HH4"]
    assert [p["hh_code"] for p in _api_hh(api, sort_by="part_bottle", sort_dir="desc")["products"]] == ["HH3", "HH2", "HH1", "HH5", "HH4"]


@pytest.mark.parametrize("over", [
    {"trend": "sideways"}, {"trend": ""}, {"part_roles": [0]}, {"part_roles": [6]}, {"part_roles": [1, 2, 3, 4, 5, 1]},
    {"part_roles": ["a"]}, {"carton_qty_min": -1}, {"carton_qty_max": 1_000_001}, {"carton_qty_min": 1.5},
    {"carton_qty_min": 10, "carton_qty_max": 5}, {"diff_bottle_min": 5, "diff_bottle_max": 1},
    {"diff_carton_min": 1e13}, {"diff_carton_max": -1e13}, {"cost_new_bottle_min": "abc"},
    {"cost_new_bottle_min": 9, "cost_new_bottle_max": 8}, {"warnings_only": "maybe"},
])
def test_api_loc_nang_cao_sai_la_422(api, over):
    assert api.post(IMPACT, content=json.dumps(_body(**over)), headers={"Content-Type": "application/json"}).status_code == 422


def test_api_khoang_am_va_bang_nhau_hop_le(api):
    assert api.post(IMPACT, json=_body(diff_bottle_min=-100, diff_bottle_max=-1)).status_code == 200
    assert api.post(IMPACT, json=_body(diff_bottle_min=35, diff_bottle_max=35)).status_code == 200
    assert api.post(IMPACT, json=_body(part_roles=[1, 2, 3, 4, 5])).status_code == 200


def test_xuat_excel_theo_bo_loc_va_xep(api):
    res = api.post(IMPACT + "/export", json=_body(trend="up", sort_by="part_bottle", sort_dir="desc", page=2, page_size=1))
    assert res.status_code == 200
    ws = openpyxl.load_workbook(BytesIO(res.content))["Sản phẩm bị ảnh hưởng"]
    assert [ws.cell(row=r, column=1).value for r in range(2, ws.max_row + 1)] == ["HH1", "HH5"]
    allrows = api.post(IMPACT + "/export", json=_body(warnings_only=True, part_roles=[1]))
    ws = openpyxl.load_workbook(BytesIO(allrows.content))["Sản phẩm bị ảnh hưởng"]
    assert [ws.cell(row=r, column=1).value for r in range(2, ws.max_row + 1)] == ["HH2"]


def test_tong_hop_theo_san_pham_xep_cot_thanh_phan(api):
    """Tổng hợp không có giá giả định: chai BA 100, BB 200, BC 300, BD chưa có giá."""
    def order(**q):
        res = api.get(OVERVIEW, params={"page_size": 50, **q})
        assert res.status_code == 200, res.text
        return [p["hh_code"] for p in res.json()["data"]["items"]]
    assert order(sort_by="part_bottle", sort_dir="asc") == ["HH1", "HH5", "HH2", "HH3", "HH4"]
    assert order(sort_by="part_bottle", sort_dir="desc") == ["HH3", "HH2", "HH1", "HH5", "HH4"]
    assert order(sort_by="part_carton_label", sort_dir="desc")[0] == "HH5"
    assert order(sort_by="part_label", sort_dir="asc")[-1] == "HH2"
    assert order(sort_by="part_nope") == ["HH1", "HH2", "HH3", "HH4", "HH5"]
    assert api.get(OVERVIEW, params={"sort_by": "x" * 31}).status_code == 422
