"""duoc-CR-784 — tab "Tổng hợp theo sản phẩm": mọi sản phẩm có định mức, chi phí bao bì / chai cũ so với mới và xu hướng.

Cùng công thức và luật giá với Tác động giá: báo giá tính là giá mới, dòng giá 0 bị bỏ qua, thiếu giá chai thì chi phí rỗng.
Kiểm: số đếm theo xu hướng (không phụ thuộc bộ lọc xu hướng, có theo `q`), lọc / xếp / phân trang, quyền, phạm vi pháp nhân,
xuất Excel và SỐ TRUY VẤN cố định bất kể số sản phẩm."""
from io import BytesIO

import openpyxl
import pytest

from app.core.packaging_price_codes import CostTrend
from app.modules.packaging_cost.impact_filters import ImpactFilters
from app.modules.packaging_cost.model import PackagingBom
from app.modules.packaging_cost.product_overview_service import OVERVIEW_SORT_GETTERS, build_product_overview
from app.modules.user.model import User
from hdld_factory import client_as  # noqa: F401  (fixture)
from lich_lam_viec_factory import count_queries
from so_gia_factory_cr784 import add_ledger, add_products, add_quote, build_bom, read_report_sheet

URL = "/api/packaging-cost/product-overview"


def _bom(db, fg: str, bottle: str, **over) -> PackagingBom:
    base = dict(fg_code=fg, fg_name=f"Sản phẩm {fg}", legal_name=f"Pháp lý {fg}", bottle_code=bottle, cap_code="NAP",
                label_code="", carton_label_code="", carton_code="", carton_qty=10, created_by=1, updated_by=1)
    base.update(over)
    row = build_bom(**base)
    db.add(row)
    return row


@pytest.fixture
def world(db):
    """Sáu sản phẩm. Nắp NAP giá 10 (một lần mua → cũ = mới = 10).
    HH01 chai B_UP: mua 100, báo giá 120 (báo giá là giá mới) -> tăng.   HH02 chai B_DOWN: mua 100, báo giá 80 -> giảm.
    HH03 chai B_FLAT: một lần mua 100 -> không đổi.                    HH04 chai B_NONE: chưa có giá -> chưa có giá.
    HH05 như HH01 nhưng thêm thùng C1 giá 600 (chia quy cách 12) -> tăng.
    HH06 chai B_ZERO: mua 100 rồi một dòng GIÁ 0 mới hơn (bị bỏ qua) -> không đổi, không phải giảm về 0."""
    add_products(db, *[(c, f"Chai {c}", "Cái") for c in ("B_UP", "B_DOWN", "B_FLAT", "B_NONE", "B_ZERO")],
                 ("NAP", "Nắp", "Cái"), ("C1", "Thùng", "Cái"))
    for code, price in (("B_UP", 100), ("B_DOWN", 100), ("B_FLAT", 100), ("B_ZERO", 100), ("NAP", 10), ("C1", 600)):
        add_ledger(db, code, price, "2026-01-01")
    add_ledger(db, "B_ZERO", 0, "2026-02-01")
    add_quote(db, "B_UP", 120, "2026-03-01")
    add_quote(db, "B_DOWN", 80, "2026-03-01")
    _bom(db, "HH01", "B_UP")
    _bom(db, "HH02", "B_DOWN")
    _bom(db, "HH03", "B_FLAT")
    _bom(db, "HH04", "B_NONE")
    _bom(db, "HH05", "B_UP", carton_code="C1", carton_qty=12)
    _bom(db, "HH06", "B_ZERO")
    db.commit()


def _rows(db, **kw):
    return build_product_overview(db, **kw)


def _codes(res):
    return [r["fg_code"] for r in res["items"]]


# ── Xu hướng + số đếm ───────────────────────────────────────────────────────────
def test_xu_huong_tung_san_pham_va_so_dem(db, world):
    res = _rows(db)
    trend = {r["fg_code"]: r["trend"] for r in res["items"]}
    assert trend == {"HH01": CostTrend.UP, "HH02": CostTrend.DOWN, "HH03": CostTrend.SAME, "HH04": CostTrend.NO_PRICE,
                     "HH05": CostTrend.UP, "HH06": CostTrend.SAME}
    assert res["counts"] == {"all": 6, "up": 2, "down": 1, "flat": 2, "missing": 1} and res["total"] == 6


def test_bao_gia_la_gia_moi_va_cong_thuc_chi_phi_chai_va_thung(db, world):
    by = {r["fg_code"]: r for r in _rows(db)["items"]}
    up = by["HH01"]                                       # chai 100 -> 120, nắp 10, không thùng
    assert (up["cost_old_bottle"], up["cost_new_bottle"], up["diff_bottle"]) == (110, 130, 20)
    assert up["pct"] == round(20 / 110, 6)
    assert (up["cost_old_carton"], up["cost_applied_carton"], up["diff_carton"]) == (1100, 1300, 200)
    assert [(p["code"], p["old"], p["new"]) for p in up["parts"] if p["code"]] == [("B_UP", 100, 120), ("NAP", 10, 10)]
    assert by["HH05"]["cost_old_bottle"] == 160 and by["HH05"]["cost_new_bottle"] == 180   # + thùng 600 / 12 = 50
    assert by["HH02"]["diff_bottle"] == -20


def test_chua_co_gia_chai_thi_chi_phi_rong_va_co_canh_bao(db, world):
    row = {r["fg_code"]: r for r in _rows(db)["items"]}["HH04"]
    assert row["cost_old_bottle"] is None and row["cost_new_bottle"] is None and row["diff_bottle"] is None
    assert row["trend"] == CostTrend.NO_PRICE and row["warnings"]


def test_dong_gia_0_bi_bo_qua_nen_khong_phai_giam(db, world):
    row = {r["fg_code"]: r for r in _rows(db)["items"]}["HH06"]
    assert (row["cost_old_bottle"], row["cost_new_bottle"], row["trend"]) == (110, 110, CostTrend.SAME)


def test_dinh_muc_rong_tra_rong_khong_loi(db):
    assert _rows(db) == {"items": [], "total": 0, "counts": {"all": 0, "up": 0, "down": 0, "flat": 0, "missing": 0}}


# ── Lọc / xếp / phân trang ──────────────────────────────────────────────────────
@pytest.mark.parametrize("trend,expected", [("all", 6), ("up", 2), ("down", 1), ("flat", 2), ("missing", 1), ("lạ", 6)])
def test_loc_xu_huong_va_so_dem_khong_doi(db, world, trend, expected):
    res = _rows(db, trend=trend)
    assert res["total"] == expected and len(res["items"]) == expected
    assert res["counts"]["all"] == 6 and res["counts"]["up"] == 2          # chip luôn thấy đủ số


def test_tim_kiem_doi_so_dem_nhung_loc_xu_huong_thi_khong(db, world):
    res = _rows(db, q="b_up", trend="down")                # B_UP có ở HH01 + HH05, cả hai đều tăng
    assert res["total"] == 0 and res["counts"] == {"all": 2, "up": 2, "down": 0, "flat": 0, "missing": 0}
    assert _codes(_rows(db, q="phap ly hh03")) == ["HH03"] and _rows(db, q="c1")["counts"]["all"] == 1   # tên pháp lý, mã thành phần
    assert _rows(db, q="khong co")["total"] == 0


def test_xep_o_trong_xuong_cuoi_hai_chieu_khoa_phu_ma_hh(db, world):
    for direction in ("asc", "desc"):
        codes = _codes(_rows(db, sort_by="diff_bottle", sort_dir=direction))
        assert codes[-1] == "HH04"                           # chưa có giá → ô trống → cuối
        diffs = [r["diff_bottle"] for r in _rows(db, sort_by="diff_bottle", sort_dir=direction)["items"][:-1]]
        assert diffs == sorted(diffs, reverse=direction == "desc")
    assert _codes(_rows(db, sort_by="diff_bottle", sort_dir="asc"))[1:3] == ["HH03", "HH06"]   # hòa 0 → mã tăng dần
    assert _codes(_rows(db, sort_by="cost_new_bottle", sort_dir="desc"))[:2] == ["HH05", "HH01"]
    assert _codes(_rows(db, sort_by="fg_name", sort_dir="desc"))[0] == "HH06"


def test_khoa_xep_la_ve_ma_hh_va_moi_khoa_cua_man_deu_co():
    assert set(OVERVIEW_SORT_GETTERS) == {"fg_code", "fg_name", "carton_qty", "cost_old_bottle", "cost_new_bottle",
                                          "diff_bottle", "pct", "diff_carton", "part_bottle", "part_cap", "part_label",
                                          "part_carton_label", "part_carton"}      # năm cột thành phần: xếp theo giá mới


def test_khoa_xep_la_khong_vo_loi(db, world):
    for hostile in ("'; drop table x; --", "", "__class__", "id desc"):
        assert _codes(_rows(db, sort_by=hostile)) == [f"HH0{i}" for i in range(1, 7)]


def test_phan_trang_cat_dung_con_tong_va_so_dem_la_cua_ca_tap(db, world):
    page = _rows(db, page=2, page_size=4)
    assert _codes(page) == ["HH05", "HH06"] and page["total"] == 6 and page["counts"]["all"] == 6
    far = _rows(db, page=9, page_size=4)
    assert far["items"] == [] and far["total"] == 6


# ── Số truy vấn cố định ─────────────────────────────────────────────────────────
def test_so_truy_van_khong_doi_theo_so_san_pham_trang_loc_xep(db, world):
    def run(**kw):
        return len(count_queries(db, lambda: _rows(db, **kw))[1])

    small = {run(), run(page=1, page_size=2, trend="up"), run(q="HH0", sort_by="fg_name", sort_dir="desc"), run(page=9)}
    for i in range(7, 207):                                  # thêm 200 sản phẩm, mỗi cái một chai riêng có giá
        add_products(db, (f"X{i}", f"Chai X{i}", "Cái"))
        add_ledger(db, f"X{i}", 100 + i, "2026-01-01")
        _bom(db, f"HH{i:03d}", f"X{i}")
    db.commit()
    big = {run(), run(page=1, page_size=2, trend="up"), run(q="HH0", sort_by="fg_name", sort_dir="desc"), run(page=9)}
    assert len(small) == 1 and small == big and small.pop() <= 5
    assert _rows(db)["counts"]["all"] == 206


# ── Lọc nâng cao (dùng lại ImpactFilters của Tác động giá) ───────────────────────
def _flt(**kw) -> ImpactFilters:
    return ImpactFilters(roles_by_presence=True, **kw)


def _rng(low, high):
    from decimal import Decimal as D
    return (None if low is None else D(low), None if high is None else D(high))


@pytest.mark.parametrize("flt,expected", [
    (_flt(part_roles=frozenset({5})), ["HH05"]),                                  # vai trò theo MÃ CÓ MẶT (không cần mã được chọn)
    (_flt(part_roles=frozenset({1, 5})), ["HH01", "HH02", "HH03", "HH04", "HH05", "HH06"]),   # một trong các vai trò
    (_flt(part_roles=frozenset({3})), []),                                        # không sản phẩm nào có nhãn
    (_flt(carton_qty=_rng(12, 12)), ["HH05"]),
    (_flt(cost_old_bottle=_rng(150, None)), ["HH05"]),                           # 110 < 150 <= 160; HH04 trống bị loại
    (_flt(cost_old_bottle=_rng(None, 110)), ["HH01", "HH02", "HH03", "HH06"]),
    (_flt(cost_new_bottle=_rng(100, 130)), ["HH01", "HH03", "HH06"]),
    (_flt(diff_bottle=_rng(-30, -1)), ["HH02"]),
    (_flt(diff_bottle=_rng(0, 0)), ["HH03", "HH06"]),
    (_flt(diff_carton=_rng(240, None)), ["HH05"]),                               # 20 * 12
    (_flt(pct=_rng(15, None)), ["HH01"]),                                        # HH01 +18,2% ; HH05 +12,5%
    (_flt(pct=_rng(None, -10)), ["HH02"]),
])
def test_loc_nang_cao_tung_bo_loc(db, world, flt, expected):
    res = _rows(db, filters=flt)
    assert _codes(res) == expected and res["total"] == len(expected)


def test_loc_chi_san_pham_co_canh_bao(db, world):
    warned = [r["fg_code"] for r in _rows(db)["items"] if r["warnings"]]
    assert "HH04" in warned and _codes(_rows(db, filters=_flt(warnings_only=True))) == warned
    #  Ghép với khoảng CP/chai cũ: chỉ HH05 vừa có cảnh báo vừa cũ >= 150.
    assert _codes(_rows(db, filters=_flt(warnings_only=True, cost_old_bottle=_rng(150, None)))) == [c for c in warned if c == "HH05"]


def test_loc_nang_cao_ghep_nhieu_bo_loc_la_va(db, world):
    assert _codes(_rows(db, filters=_flt(diff_bottle=_rng(1, None), part_roles=frozenset({5})))) == ["HH05"]
    assert _rows(db, filters=_flt(diff_bottle=_rng(1, None), carton_qty=_rng(99, None)))["total"] == 0


def test_so_dem_chip_theo_tim_kiem_va_loc_nang_cao_nhung_khong_theo_xu_huong(db, world):
    flt = _flt(cost_old_bottle=_rng(100, 120))                  # HH01 HH02 HH03 HH06 (110); HH05 160 và HH04 (trống) bị loại
    res = _rows(db, filters=flt, trend="up")
    assert _codes(res) == ["HH01"] and res["total"] == 1
    assert res["counts"] == {"all": 4, "up": 1, "down": 1, "flat": 2, "missing": 0}
    assert _rows(db, filters=flt, q="hh0")["counts"]["all"] == 4 and _rows(db, filters=flt, q="hh01")["counts"]["all"] == 1


def test_loc_nang_cao_bo_qua_xu_huong_trong_filters_va_khong_loc_thi_nguyen_tap(db, world):
    assert _rows(db, filters=ImpactFilters(trend="up"))["total"] == 6          # xu hướng chỉ đi bằng tham số `trend`
    assert _rows(db, filters=ImpactFilters())["total"] == 6 and _rows(db, filters=None)["total"] == 6


def test_phan_tram_so_voi_so_mot_chu_so_le_dang_hien(db, world):
    #  HH05: 20 / 160 = 12,5% đúng; HH01: 20 / 110 = 18,1818% hiện +18,2% → khoảng 18,2..18,2 trúng, 18,3.. thì không
    assert _codes(_rows(db, filters=_flt(pct=_rng("18.2", "18.2")))) == ["HH01"]
    assert _rows(db, filters=_flt(pct=_rng("18.3", None)))["total"] == 0
    assert _codes(_rows(db, filters=_flt(pct=_rng("12.5", "12.5")))) == ["HH05"]


def test_so_truy_van_khong_doi_khi_loc_nang_cao(db, world):
    flt = _flt(part_roles=frozenset({1}), diff_bottle=_rng(-50, 50), pct=_rng(-50, 50), warnings_only=False)
    plain = len(count_queries(db, lambda: _rows(db))[1])
    assert len(count_queries(db, lambda: _rows(db, filters=flt, trend="up", q="hh", page=1, page_size=2))[1]) == plain


# ── API: quyền, phạm vi, xuất Excel ─────────────────────────────────────────────
@pytest.fixture
def api(db, seed, cap_quyen, client_as, world):  # noqa: F811
    cap_quyen(seed.u_req_id, "packaging_cost", scope="all", read=True, export=True)
    return client_as(db.get(User, seed.u_req_id))


def test_api_tra_items_total_counts_va_loc_theo_tham_so(api):
    data = api.get(URL).json()["data"]
    assert data["total"] == 6 and data["counts"]["up"] == 2 and len(data["items"]) == 6
    data = api.get(URL, params={"trend": "up", "page": 1, "page_size": 1, "sort_by": "cost_new_bottle", "sort_dir": "desc"}).json()["data"]
    assert [r["fg_code"] for r in data["items"]] == ["HH05"] and data["total"] == 2 and data["counts"]["all"] == 6


@pytest.mark.parametrize("params", [{"trend": "bad"}, {"sort_dir": "up"}, {"page": 0}, {"page_size": 501}, {"page_size": 0},
                                    {"q": "x" * 101}, {"sort_by": "x" * 31}])
def test_api_tham_so_sai_la_422(api, params):
    assert api.get(URL, params=params).status_code == 422


def test_api_tran_page_size_500_hop_le(api):
    assert api.get(URL, params={"page_size": 500}).status_code == 200


def test_khong_co_quyen_la_403_va_chi_doc_khong_xuat_duoc(db, seed, cap_quyen, client_as, world):  # noqa: F811
    assert client_as(db.get(User, seed.u_req_id)).get(URL).status_code == 403
    cap_quyen(seed.u_req_id, "packaging_cost", scope="all", read=True)
    only_read = client_as(db.get(User, seed.u_req_id))
    assert only_read.get(URL).status_code == 200 and only_read.get(URL + "/export").status_code == 403


def test_pham_vi_cong_ty_khong_thay_gia_cua_phap_nhan_khac(db, seed, cap_quyen, client_as, world):  # noqa: F811
    from app.modules.product_price.model import ProductPriceLedger
    db.query(ProductPriceLedger).update({ProductPriceLedger.company_id: seed.company_id})
    add_ledger(db, "B_FLAT", 150, "2026-04-01", company_id=seed.company_id + 99)       # pháp nhân khác, mới hơn
    cap_quyen(seed.u_req_id, "packaging_cost", scope="company", read=True)
    mine = client_as(db.get(User, seed.u_req_id)).get(URL, params={"q": "HH03"}).json()["data"]
    assert mine["items"][0]["trend"] == CostTrend.SAME                                # không thấy dòng 150
    cap_quyen(seed.u_req_id, "packaging_cost", scope="all", read=True)
    full = client_as(db.get(User, seed.u_req_id)).get(URL, params={"q": "HH03"}).json()["data"]
    assert full["items"][0]["trend"] == CostTrend.UP and full["items"][0]["cost_new_bottle"] == 160


def test_xuat_excel_theo_bo_loc_va_thu_tu_bo_qua_phan_trang(api):
    res = api.get(URL + "/export", params={"trend": "up", "sort_by": "fg_code", "sort_dir": "desc", "page": 3, "page_size": 1})
    assert res.status_code == 200 and "tong-hop-theo-san-pham" in res.headers["content-disposition"]
    header, rows = read_report_sheet(openpyxl.load_workbook(BytesIO(res.content))["Tổng hợp theo sản phẩm"])
    assert [r[0].value for r in rows] == ["HH05", "HH01"]
    assert "CP bao bì/chai mới" in header and "Trạng thái" in header and "Giá chai mới" in header
    assert rows[0][header.index("Trạng thái")].value == "Tăng"
    assert rows[0][header.index("CP bao bì/chai mới")].value == 180
    _, none_rows = read_report_sheet(openpyxl.load_workbook(BytesIO(api.get(URL + "/export", params={"trend": "missing"}).content))["Tổng hợp theo sản phẩm"])
    assert none_rows[0][header.index("CP bao bì/chai mới")].value is None      # ô trống, không phải 0


# ── API: lọc nâng cao qua tham số truy vấn + xuất Excel cùng bộ lọc ─────────────────
def test_api_loc_nang_cao_qua_tham_so(api):
    def codes(**params):
        res = api.get(URL, params=params)
        assert res.status_code == 200, res.text
        return [r["fg_code"] for r in res.json()["data"]["items"]]
    assert codes(part_roles="5") == ["HH05"] and codes(part_roles="1,5") == [f"HH0{i}" for i in range(1, 7)]
    assert codes(diff_bottle_min=-30, diff_bottle_max=-1) == ["HH02"] and codes(carton_qty_min=12) == ["HH05"]
    assert codes(pct_min=15) == ["HH01"] and codes(cost_old_bottle_min=150, trend="up") == ["HH05"]
    data = api.get(URL, params={"cost_old_bottle_max": 110, "trend": "flat"}).json()["data"]
    assert data["counts"] == {"all": 4, "up": 1, "down": 1, "flat": 2, "missing": 0} and data["total"] == 2
    assert api.get(URL, params={"warnings_only": "true"}).status_code == 200


@pytest.mark.parametrize("params", [{"part_roles": "0"}, {"part_roles": "6"}, {"part_roles": "1,,2"}, {"part_roles": "1,2,3,4,5,1"},
                                    {"part_roles": "a"}, {"carton_qty_min": -1}, {"carton_qty_max": 1_000_001},
                                    {"carton_qty_min": "x"}, {"diff_bottle_min": "nan"}, {"pct_max": "inf"},
                                    {"cost_old_bottle_min": 1e13}, {"pct_min": -1e13}, {"warnings_only": "maybe"},
                                    {"carton_qty_min": 30, "carton_qty_max": 10}, {"pct_min": 5, "pct_max": 1},
                                    {"cost_old_bottle_min": 2, "cost_old_bottle_max": 1}])
def test_api_loc_nang_cao_sai_la_422(api, params):
    assert api.get(URL, params=params).status_code == 422


def test_api_khoang_am_bang_nhau_va_du_nam_vai_tro_hop_le(api):
    assert api.get(URL, params={"diff_bottle_min": -100, "diff_bottle_max": -1}).status_code == 200
    assert api.get(URL, params={"pct_min": 18.2, "pct_max": 18.2, "part_roles": "1,2,3,4,5"}).status_code == 200


def test_xuat_excel_theo_loc_nang_cao(api):
    res = api.get(URL + "/export", params={"diff_bottle_min": 1, "part_roles": "5", "page": 2, "page_size": 1})
    assert res.status_code == 200
    _, rows = read_report_sheet(openpyxl.load_workbook(BytesIO(res.content))["Tổng hợp theo sản phẩm"])
    assert [r[0].value for r in rows] == ["HH05"]
    assert api.get(URL + "/export", params={"pct_min": 5, "pct_max": 1}).status_code == 422
