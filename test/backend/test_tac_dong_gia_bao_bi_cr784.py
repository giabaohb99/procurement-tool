"""duoc-CR-784 phase 04 — Tác động giá bao bì: công thức chi phí, KPI, API (quyền / 422 / phạm vi pháp nhân), Bảng giá VTBB,
xuất Excel, và SỐ TRUY VẤN cố định bất kể số mã / số dòng định mức."""
from decimal import Decimal
from io import BytesIO
from types import SimpleNamespace

import openpyxl
import pytest

from app.core.packaging_price_codes import CostTrend, CostWarning, PackagingRole
from app.modules.packaging_cost.cost_service import compute_product_cost, fold_text, price_warnings
from app.modules.packaging_cost.impact_service import compute_impact
from app.modules.packaging_cost.model import PackagingBom
from app.modules.packaging_cost.price_list_service import build_price_list
from app.modules.user.model import User
from hdld_factory import client_as  # noqa: F401  (fixture)
from lich_lam_viec_factory import count_queries
from so_gia_factory_cr784 import add_ledger, add_limit, add_products, add_quote, read_report_sheet

D = Decimal
IMPACT, PRICE_LIST, OPTIONS = "/api/packaging-cost/impact", "/api/packaging-cost/price-list", "/api/packaging-cost/code-options"


def _bom(db, hh="HH0417.1", **over) -> PackagingBom:
    base = dict(hh_code=hh, hh_name=f"Sản phẩm {hh}", bottle_code="CPT0105", cap_code="NAP0085", label_code="NHG0001",
                carton_label_code="NDT0001", carton_code="THU0001", carton_qty=40, created_by=1, updated_by=1)
    base.update(over)
    row = PackagingBom(**base)
    db.add(row)
    db.commit()
    return row


@pytest.fixture
def world(db):
    """Chai 1000 → 1100 · nắp 200 · nhãn 300 · nhãn thùng 400 · thùng 8000; một sản phẩm, quy cách 40."""
    add_products(db, ("CPT0105", "Chai 450ml", "Cái"), ("NAP0085", "Nắp", "Cái"), ("NHG0001", "Nhãn", "Cái"),
                 ("NDT0001", "Nhãn thùng", "Cái"), ("THU0001", "Thùng", "Cái"))
    add_ledger(db, "CPT0105", 1000, "2026-01-01")
    add_ledger(db, "CPT0105", 1100, "2026-06-01")
    for code, price in (("NAP0085", 200), ("NHG0001", 300), ("NDT0001", 400), ("THU0001", 8000)):
        add_ledger(db, code, price, "2026-02-01")
    return _bom(db)


@pytest.fixture
def api(db, seed, cap_quyen, client_as, world):  # noqa: F811
    cap_quyen(seed.u_req_id, "packaging_cost", scope="all", read=True, export=True)
    return client_as(db.get(User, seed.u_req_id))


# ── Công thức (hàm thuần) ───────────────────────────────────────────────────────
def _price(old, new=None, unit="Cái", floor=None, ceiling=None):
    return SimpleNamespace(old=None if old is None else D(old), new=None if (new if new is not None else old) is None
                           else D(new if new is not None else old), unit=unit, floor=floor, ceiling=ceiling)


def _bom_ns(**over):
    base = dict(bottle_code="C", cap_code="N", label_code="L", carton_label_code="NT", carton_code="T", carton_qty=40)
    base.update(over)
    return SimpleNamespace(**base)


PRICES = {"C": _price(1000, 1100), "N": _price(200), "L": _price(300), "NT": _price(400), "T": _price(8000)}


def test_cong_thuc_chi_phi_chai_va_thung_dung_ban_mau():
    cost = compute_product_cost(_bom_ns(), PRICES, {"C": None})
    assert cost.cost_old_bottle == D("1710.0000")            # 1000+200+300+(400+8000)/40
    assert cost.cost_new_bottle == cost.cost_applied_bottle == D("1810.0000")
    assert (cost.diff_bottle, cost.diff_carton, cost.trend) == (D("100.0000"), D("4000.0000"), CostTrend.UP)
    assert cost.cost_old_carton == D("68400.0000") and cost.pct == D("0.058480")
    assert [p.selected for p in cost.parts] == [True, False, False, False, False]


def test_gia_gia_dinh_doi_gia_ap_dung_nhung_khong_doi_gia_cu_hay_gia_moi():
    cost = compute_product_cost(_bom_ns(), PRICES, {"C": D(1500)})
    assert (cost.cost_old_bottle, cost.cost_new_bottle, cost.cost_applied_bottle) == (D("1710.0000"), D("1810.0000"), D("2210.0000"))
    assert (cost.diff_bottle, cost.diff_carton) == (D("500.0000"), D("20000.0000"))
    chai = cost.parts[0]
    assert (chai.old, chai.new, chai.applied) == (D(1000), D(1100), D(1500))


def test_gia_gia_dinh_ma_khong_chon_thi_bo_qua_gia_ma_chon_khac_giu_gia_moi():
    cost = compute_product_cost(_bom_ns(), PRICES, {"N": D(250)})
    assert cost.cost_applied_bottle == D("1100") + D(250) + D(300) + D(210)        # chai không chọn → giá mới 1100


def test_thieu_gia_chai_thi_chi_phi_rong_xu_huong_chua_co_gia():
    cost = compute_product_cost(_bom_ns(), {**PRICES, "C": _price(None)}, {})
    assert cost.cost_old_bottle is None and cost.cost_applied_bottle is None and cost.diff_carton is None
    assert cost.trend == CostTrend.NO_PRICE
    assert (CostWarning.MISSING_BOTTLE_PRICE, PackagingRole.BOTTLE) in cost.warnings


def test_thanh_phan_khac_thieu_gia_tinh_0_va_canh_bao_nap_nhan_khong_ma_thi_canh_bao_thung_nhan_thung_khong_ma_thi_im():
    cost = compute_product_cost(_bom_ns(cap_code="", label_code="", carton_label_code="", carton_code=""), PRICES, {})
    assert cost.cost_old_bottle == D("1000.0000")
    kinds = {(w, r) for w, r in cost.warnings}
    assert (CostWarning.MISSING_COMPONENT_CODE, PackagingRole.CAP) in kinds
    assert (CostWarning.MISSING_COMPONENT_CODE, PackagingRole.LABEL) in kinds
    assert not any(r in (PackagingRole.CARTON, PackagingRole.CARTON_LABEL) for _, r in kinds)
    missing_price = compute_product_cost(_bom_ns(), {**PRICES, "N": _price(None)}, {})
    assert (CostWarning.MISSING_COMPONENT_PRICE, PackagingRole.CAP) in missing_price.warnings
    assert missing_price.cost_old_bottle == D("1000") + D(300) + D(210)


def test_thieu_quy_cach_thung_thi_phan_thung_tinh_0_va_canh_bao():
    cost = compute_product_cost(_bom_ns(carton_qty=0), PRICES, {})
    assert cost.cost_old_bottle == D("1500.0000")
    assert cost.cost_old_carton is None and cost.diff_carton is None
    assert (CostWarning.MISSING_CARTON_QTY, None) in cost.warnings
    no_carton = compute_product_cost(_bom_ns(carton_qty=0, carton_label_code="", carton_code=""), PRICES, {})
    assert (CostWarning.MISSING_CARTON_QTY, None) not in no_carton.warnings


def test_xu_huong_giam_va_khong_doi():
    down = compute_product_cost(_bom_ns(), PRICES, {"C": D(900)})
    assert down.trend == CostTrend.DOWN
    same = compute_product_cost(_bom_ns(), {**PRICES, "C": _price(1000)}, {"C": None})
    assert same.trend == CostTrend.SAME and same.diff_bottle == D(0)


def test_canh_bao_nguong_va_lech_dvt():
    p = _price(100, floor=D(120), ceiling=D(150), unit="Cái")
    assert price_warnings(p, D(100), "Cái") == [CostWarning.BELOW_FLOOR]
    assert price_warnings(p, D(200), "Kg") == [CostWarning.UNIT_MISMATCH, CostWarning.ABOVE_CEILING]
    assert price_warnings(p, D(130), "CÁI ") == []          # không phân biệt hoa thường / khoảng trắng
    assert price_warnings(None, D(1), "x") == []


# ── Dịch vụ + KPI ───────────────────────────────────────────────────────────────
def test_compute_impact_so_lieu_san_pham_va_kpi(db, world):
    _bom(db, "HH0417.2", cap_code="", label_code="", carton_label_code="", carton_code="", carton_qty=0)
    out = compute_impact(db, ["CPT0105", "NAP0085"], {"CPT0105": D(1500)})
    assert [p["hh_code"] for p in out["products"]] == ["HH0417.1", "HH0417.2"]
    first = out["products"][0]
    assert (first["cost_old_bottle"], first["cost_applied_bottle"], first["diff_bottle"], first["diff_carton"]) == \
        (1710, 2210, 500, 20000)
    assert first["trend"] == int(CostTrend.UP) and first["pct"] == pytest.approx(0.292398, abs=1e-6)
    second = out["products"][1]
    assert (second["cost_old_bottle"], second["diff_carton"]) == (1000, None)   # không có quy cách → không có /thùng
    k = out["kpis"]
    assert (k["selected_count"], k["assumed_count"], k["affected_products"], k["increased"], k["decreased"]) == (2, 1, 2, 2, 0)
    assert k["selected_by_group"] == {"Chai": 2}
    assert (k["max_increase_carton"], k["max_increase_bottle"]) == (20000, 500)
    sel = {r["code"]: r for r in out["selected"]}
    assert (sel["CPT0105"]["old"], sel["CPT0105"]["new"], sel["CPT0105"]["assumed"], sel["CPT0105"]["applied"],
            sel["CPT0105"]["diff"], sel["CPT0105"]["usage"]) == (1000, 1100, 1500, 1500, 500, 2)
    assert (sel["NAP0085"]["usage"], sel["NAP0085"]["assumed"], sel["NAP0085"]["diff"]) == (1, None, 0)


def test_kpi_giam_va_ma_khong_co_trong_dinh_muc_van_200(db, world):
    out = compute_impact(db, ["CPT0105"], {"CPT0105": D(500)})
    assert out["kpis"]["decreased"] == 1 and out["kpis"]["increased"] == 0
    stray = compute_impact(db, ["KHONG_CO"], {})
    assert stray["products"] == [] and stray["selected"][0]["usage"] == 0 and stray["selected"][0]["old"] is None
    assert stray["kpis"]["max_increase_carton"] is None


def test_ma_chua_co_gia_nao_canh_bao_thieu_gia(db, world):
    add_products(db, ("NAP0099", "Nắp mới", "Cái"))
    db.query(PackagingBom).update({PackagingBom.cap_code: "NAP0099"})
    db.commit()
    sel = compute_impact(db, ["NAP0099"], {})["selected"][0]
    assert sel["warnings"] == [int(CostWarning.MISSING_COMPONENT_PRICE)] and sel["applied"] is None


def test_min_max_nguong_trong_selected(db, world):
    add_limit(db, "CPT0105", floor=1200, ceiling=1300)
    sel = compute_impact(db, ["CPT0105"], {})["selected"][0]
    assert (sel["min"], sel["max"], sel["floor"], sel["ceiling"]) == (1000, 1100, 1200, 1300)
    assert sel["warnings"] == [int(CostWarning.BELOW_FLOOR)]     # giá áp dụng 1100 < sàn 1200


# ── Số truy vấn ─────────────────────────────────────────────────────────────────
def test_so_truy_van_khong_phu_thuoc_so_ma_va_so_dong_dinh_muc(db, world):
    _, small = count_queries(db, lambda: compute_impact(db, ["CPT0105"], {}))
    for i in range(300):
        _bom(db, f"HH{i:04d}", bottle_code=f"C{i % 30}")
    codes = [f"C{i}" for i in range(30)]
    _, big = count_queries(db, lambda: compute_impact(db, codes, {c: D(1) for c in codes}))
    assert len(small) == len(big) <= 6


def test_bang_gia_toi_da_7_truy_van(db, world):
    for i in range(50):
        _bom(db, f"HH{i:04d}", bottle_code=f"C{i}")
        add_quote(db, f"C{i}", 10 + i, "2026-07-01")
    for scope in ("bom", "all"):
        _, sqls = count_queries(db, lambda: build_price_list(db, scope=scope))
        assert len(sqls) <= 6


# ── API ─────────────────────────────────────────────────────────────────────────
def test_api_impact_tra_selected_kpis_products(api):
    res = api.post(IMPACT, json={"codes": ["CPT0105"], "assumed_prices": {"CPT0105": 1500}})
    assert res.status_code == 200, res.text
    data = res.json()["data"]
    assert set(data) == {"selected", "kpis", "products", "products_total"} and data["products_total"] == 1
    p = data["products"][0]
    assert p["hh_code"] == "HH0417.1" and p["diff_carton"] == 20000
    assert p["parts"][0] == {"role": 1, "code": "CPT0105", "name": "Chai 450ml", "old": 1000, "new": 1100,
                             "applied": 1500, "selected": True}
    assert "message" not in p and all(isinstance(w["kind"], int) for w in p["warnings"])


@pytest.mark.parametrize("body", [
    {"codes": []}, {"codes": ["   "]}, {"codes": [f"C{i}" for i in range(501)]},
    {"codes": ["A"], "assumed_prices": {"A": -1}}, {"codes": ["A"], "assumed_prices": {"B": 1}},
    {"codes": ["A"], "date_from": "2026-05-01", "date_to": "2026-01-01"}, {"codes": ["A" * 51]},
    {"codes": ["A"], "date_from": "0001-01-01"}, {},
])
def test_api_impact_422_cac_ca_bien(api, body):
    assert api.post(IMPACT, json=body).status_code == 422


def test_api_impact_tran_500_ma_hop_le(api):
    assert api.post(IMPACT, json={"codes": [f"C{i}" for i in range(500)]}).status_code == 200


def test_api_thieu_quyen_la_403_ke_ca_xuat(db, seed, cap_quyen, client_as, world):  # noqa: F811
    none = client_as(db.get(User, seed.u_req_id))
    assert none.post(IMPACT, json={"codes": ["CPT0105"]}).status_code == 403
    assert none.get(PRICE_LIST).status_code == 403 and none.get(OPTIONS).status_code == 403
    cap_quyen(seed.u_req_id, "packaging_cost", scope="all", read=True)       # có đọc, không có xuất
    only_read = client_as(db.get(User, seed.u_req_id))
    assert only_read.post(IMPACT, json={"codes": ["CPT0105"]}).status_code == 200
    assert only_read.post(IMPACT + "/export", json={"codes": ["CPT0105"]}).status_code == 403
    assert only_read.get(PRICE_LIST + "/export").status_code == 403


def test_pham_vi_cong_ty_nguoi_xem_chi_thay_gia_cua_phap_nhan_minh(db, seed, cap_quyen, client_as, world):  # noqa: F811
    from app.modules.product_price.model import ProductPriceLedger
    db.query(ProductPriceLedger).update({ProductPriceLedger.company_id: seed.company_id})   # sổ của `world` = pháp nhân của người xem
    add_ledger(db, "CPT0105", 5000, "2026-09-01", company_id=seed.company_id + 99)           # pháp nhân khác, mới nhất
    cap_quyen(seed.u_req_id, "packaging_cost", scope="company", read=True)
    mine = client_as(db.get(User, seed.u_req_id)).post(IMPACT, json={"codes": ["CPT0105"]}).json()["data"]
    assert (mine["selected"][0]["new"], mine["selected"][0]["old"]) == (1100, 1000)         # 5000 của pháp nhân khác bị ẩn
    assert mine["selected"][0]["max"] == 1100
    cap_quyen(seed.u_req_id, "packaging_cost", scope="all", read=True)                       # grant thứ hai: HỢP hai phạm vi
    full = client_as(db.get(User, seed.u_req_id)).post(IMPACT, json={"codes": ["CPT0105"]}).json()["data"]
    assert full["selected"][0]["new"] == 5000


# ── Bảng giá VTBB ───────────────────────────────────────────────────────────────
def test_bang_gia_dong_gia_cu_moi_chenh_so_sp_dung(api):
    res = api.get(PRICE_LIST)
    assert res.status_code == 200
    items = {r["code"]: r for r in res.json()["data"]["items"]}
    assert set(items) == {"CPT0105", "NAP0085", "NHG0001", "NDT0001", "THU0001"}
    chai = items["CPT0105"]
    assert (chai["old"], chai["new"], chai["diff"], chai["usage"], chai["purchase_count"]) == (1000, 1100, 100, 1, 2)
    assert chai["pct"] == pytest.approx(0.1) and chai["last_date"] == "2026-06-01" and chai["quote"] is None
    assert (chai["last_purchase_price"], chai["last_purchase_date"], chai["prev_purchase_price"]) == (1100, "2026-06-01", 1000)
    nap = items["NAP0085"]       # chỉ một lần mua → không có lần trước
    assert (nap["last_purchase_price"], nap["last_purchase_date"], nap["prev_purchase_price"]) == (200, "2026-02-01", None)
    assert res.json()["data"]["total"] == 5


def test_bang_gia_co_bao_gia_loc_xep_phan_trang(api, db):
    add_quote(db, "NAP0085", 260, "2026-07-01")
    add_limit(db, "NAP0085", floor=100, ceiling=250)
    rows = api.get(PRICE_LIST, params={"sort_by": "diff", "sort_dir": "desc"}).json()["data"]["items"]
    assert [r["code"] for r in rows[:2]] == ["CPT0105", "NAP0085"]                 # chênh 100 rồi 60; còn lại chênh 0
    nap = rows[1]
    assert nap["quote"]["price"] == 260 and nap["diff"] == 60 and nap["warnings"] == [int(CostWarning.ABOVE_CEILING)]
    assert [r["code"] for r in api.get(PRICE_LIST, params={"breach_only": True}).json()["data"]["items"]] == ["NAP0085"]
    assert api.get(PRICE_LIST, params={"q": "thung"}).json()["data"]["total"] == 2           # bỏ dấu: Thùng + Nhãn thùng
    assert api.get(PRICE_LIST, params={"group": "chai"}).json()["data"]["total"] == 5
    page = api.get(PRICE_LIST, params={"page": 2, "page_size": 2}).json()["data"]
    assert len(page["items"]) == 2 and page["total"] == 5


def test_sap_xep_theo_gia_mua_gan_nhat_o_trong_xuong_cuoi(api, db):
    add_ledger(db, "KHAC001", 10, "2026-03-01")          # ngoài định mức, chỉ hiện ở scope=all
    for direction in ("asc", "desc"):
        rows = api.get(PRICE_LIST, params={"scope": "all", "sort_by": "prev_purchase_price", "sort_dir": direction}
                       ).json()["data"]["items"]
        prev = [r["prev_purchase_price"] for r in rows]
        assert prev[0] == 1000 and all(v is None for v in prev[1:])        # chỉ chai có lần mua trước; còn lại xuống cuối


@pytest.mark.parametrize("direction", ["asc", "desc"])
def test_o_trong_luon_xuong_cuoi_ca_hai_chieu_khoa_phu_la_ma(api, db, direction):
    add_quote(db, "NAP0085", 260, "2026-07-01")
    rows = api.get(PRICE_LIST, params={"sort_by": "quote_price", "sort_dir": direction}).json()["data"]["items"]
    assert rows[0]["code"] == "NAP0085"
    assert [r["code"] for r in rows[1:]] == sorted(r["code"] for r in rows[1:])
    by_name = api.get(PRICE_LIST, params={"sort_by": "name", "sort_dir": direction}).json()["data"]["items"]
    names = [r["name"] for r in by_name]
    assert names == sorted(names, key=fold_text, reverse=(direction == "desc"))      # xếp theo tên ĐANG HIỆN, bỏ dấu


def test_phan_tham_so_sai_422_khoa_sort_la_roi_ve_ma(api):
    assert api.get(PRICE_LIST, params={"sort_dir": "up"}).status_code == 422
    assert api.get(PRICE_LIST, params={"scope": "x"}).status_code == 422
    assert api.get(PRICE_LIST, params={"date_from": "2026-05-01", "date_to": "2026-01-01"}).status_code == 422
    items = api.get(PRICE_LIST, params={"sort_by": "'; drop table"}).json()["data"]["items"]
    assert [r["code"] for r in items] == sorted(r["code"] for r in items)


def test_scope_all_them_ma_chi_co_trong_so_gia(api, db):
    add_ledger(db, "KHAC001", 10, "2026-03-01")
    assert api.get(PRICE_LIST).json()["data"]["total"] == 5
    assert api.get(PRICE_LIST, params={"scope": "all"}).json()["data"]["total"] == 6


def test_code_options_chi_ma_dang_dung_trong_dinh_muc(api, db):
    add_ledger(db, "KHAC001", 10, "2026-03-01")
    add_quote(db, "NAP0085", 260, "2026-07-01")
    items = api.get(OPTIONS).json()["data"]["items"]
    assert {r["code"] for r in items} == {"CPT0105", "NAP0085", "NHG0001", "NDT0001", "THU0001"}
    assert set(items[0]) == {"code", "name", "group", "usage", "new"}
    assert api.get(OPTIONS, params={"q": "nap"}).json()["data"]["items"][0]["code"] == "NAP0085"


# ── Xuất Excel ──────────────────────────────────────────────────────────────────
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def test_xuat_excel_tac_dong_hai_sheet_mo_duoc_va_chan_cong_thuc(api, db):
    db.query(PackagingBom).update({PackagingBom.hh_name: "=HYPERLINK(\"http://x\")"})
    db.commit()
    res = api.post(IMPACT + "/export", json={"codes": ["CPT0105"], "assumed_prices": {"CPT0105": 1500}})
    assert res.status_code == 200 and res.headers["content-type"] == XLSX
    wb = openpyxl.load_workbook(BytesIO(res.content))
    assert wb.sheetnames == ["Sản phẩm bị ảnh hưởng", "Mã đã chọn"]          # sheet chính đứng đầu như bản mẫu
    head, rows = read_report_sheet(wb["Sản phẩm bị ảnh hưởng"])
    assert head[:4] == ["Mã HH", "Tên hàng hoá", "Tên pháp lý", "Quy cách thùng"] and "Trạng thái" in head
    row = {h: c.value for h, c in zip(head, rows[0])}
    assert row["Mã HH"] == "HH0417.1" and row["Tăng/giảm /thùng"] == 20000 and row["Trạng thái"] == "Tăng"
    name_cell = rows[0][head.index("Tên hàng hoá")]
    assert name_cell.data_type == "s" and name_cell.value.startswith("=")            # không bị Excel chạy như công thức
    sel_head, sel_rows = read_report_sheet(wb["Mã đã chọn"])
    assert sel_rows[0][0].value == "CPT0105" and sel_rows[0][sel_head.index("Giá giả định")].value == 1500


def test_xuat_excel_bang_gia_theo_bo_loc_va_o_trong_khong_bi_thanh_0(api, db):
    add_ledger(db, "KHAC001", 10, "2026-03-01")
    res = api.get(PRICE_LIST + "/export", params={"scope": "all", "q": "KHAC"})
    assert res.status_code == 200
    head, rows = read_report_sheet(openpyxl.load_workbook(BytesIO(res.content)).active)
    assert len(rows) == 1 and rows[0][0].value == "KHAC001"
    row = {h: c.value for h, c in zip(head, rows[0])}
    assert row["Báo giá mới"] is None                                 # chưa có báo giá → ô trống, không phải 0
    assert row["Giá mua gần nhất"] == 10 and row["Giá mua lần trước"] is None
    assert row["Mua gần nhất"].date().isoformat() == "2026-03-01"


def test_chenh_lech_thung_nhan_so_tho_roi_moi_lam_tron():
    """Quy cách 7, thùng đổi 1 → 2: chênh /chai = 1/7 = 0,142857… Nhân số ĐÃ làm tròn (0,1429) ra 1,0003; nhân số thô ra 1,0000."""
    bom = _bom_ns(cap_code="", label_code="", carton_label_code="", carton_code="T", carton_qty=7)
    cost = compute_product_cost(bom, {"C": _price(1000), "T": _price(1)}, {"T": D(2)})
    assert cost.diff_bottle == D("0.1429")
    assert cost.diff_carton == D("1.0000")
    assert cost.cost_old_carton == D("7001.0000") and cost.cost_applied_carton == D("7002.0000")   # (1000 + 1/7) x 7, (1000 + 2/7) x 7
