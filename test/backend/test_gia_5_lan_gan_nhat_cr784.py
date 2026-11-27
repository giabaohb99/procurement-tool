"""duoc-CR-784 — tab "Giá mua gần nhất" (3 / 5 / 10 lần): lần 1 = lần mua CÓ GIÁ gần nhất, biến động, giá trung bình, tên nhà cung cấp,
lọc (nhóm, nhà cung cấp, khoảng ngày, biến động, ngưỡng, trong định mức) / xếp / phân trang, phạm vi pháp nhân, quyền, xuất Excel, và SỐ TRUY VẤN cố định bất kể số mã."""
from datetime import date
from io import BytesIO

import openpyxl
import pytest

from app.modules.packaging_cost.last_prices_service import build_last_prices, supplier_label
from app.modules.packaging_cost.model import PackagingBom
from app.modules.product.model import Product
from app.modules.supplier.model import Supplier
from app.modules.user.model import User
from hdld_factory import client_as  # noqa: F401  (fixture)
from lich_lam_viec_factory import count_queries
from so_gia_factory_cr784 import add_ledger, add_products, add_quote, build_bom, read_report_sheet

URL = "/api/packaging-cost/last-prices"
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _bom(db, fg="HH0001", **over) -> PackagingBom:
    base = dict(fg_code=fg, fg_name=f"Sản phẩm {fg}", bottle_code="CPT0105", cap_code="NAP0085", label_code="NHG0001",
                carton_label_code="", carton_code="", carton_qty=40, created_by=1, updated_by=1)
    base.update(over)
    row = build_bom(**base)
    db.add(row)
    db.commit()
    return row


@pytest.fixture
def world(db):
    """Chai CPT0105: 6 lần mua có giá + 1 dòng giá 0; nắp NAP0085: 1 lần; nhãn NHG0001: chưa có lần nào."""
    add_products(db, ("CPT0105", "Chai 450ml", "Cái"), ("NAP0085", "Nắp", "Cái"), ("NHG0001", "Nhãn", "Cái"))
    db.add_all([Supplier(code="NCC01", name="Nhựa Á Châu - VTBB"), Supplier(code="NCC02", name="Nhựa Việt")])
    db.commit()
    for price, day, ncc in ((100, "2026-01-01", "NCC01"), (110, "2026-02-01", "NCC01"), (105, "2026-03-01", "NCC02"),
                            (120, "2026-04-01", "NCC02"), (130, "2026-05-01", "NCC01"), (150, "2026-06-01", "NCC02")):
        add_ledger(db, "CPT0105", price, day, supplier=ncc)
    add_ledger(db, "CPT0105", 0, "2026-07-01", supplier="NCC01")        # giá 0: bị bỏ, không làm thành lần 1
    add_ledger(db, "NAP0085", 200, "2026-02-01", supplier="NCC_LA")      # nhà cung cấp không có trong danh mục
    return _bom(db)


@pytest.fixture
def api(db, seed, cap_quyen, client_as, world):  # noqa: F811
    cap_quyen(seed.u_req_id, "packaging_last_price", scope="all", read=True, export=True)
    return client_as(db.get(User, seed.u_req_id))


def _items(api, **params):
    res = api.get(URL, params=params)
    assert res.status_code == 200, res.text
    return res.json()["data"]


# ── Dữ liệu từng dòng ───────────────────────────────────────────────────────────
def test_lan_1_la_lan_mua_co_gia_gan_nhat_bo_dong_gia_0_va_chi_lay_5_lan(api):
    row = {r["code"]: r for r in _items(api)["items"]}["CPT0105"]
    assert row["purchase_count"] == 6                       # 6 lần có giá, dòng giá 0 không đếm
    assert [p["price"] for p in row["purchases"]] == [150, 130, 120, 105, 110]
    assert [p["date"] for p in row["purchases"]][:2] == ["2026-06-01", "2026-05-01"]
    assert (row["last_price"], row["last_date"]) == (150, "2026-06-01")


def test_bien_dong_lan_1_so_lan_2_lan_1_so_lan_5_va_gia_tb(api):
    row = {r["code"]: r for r in _items(api)["items"]}["CPT0105"]
    assert row["v12"] == pytest.approx(150 / 130 - 1, abs=1e-6)
    assert row["v1n"] == pytest.approx(150 / 110 - 1, abs=1e-6)
    assert row["avg"] == pytest.approx((150 + 130 + 120 + 105 + 110) / 5)


def test_mot_lan_mua_thi_khong_co_bien_dong_nhung_van_co_gia_tb(api):
    row = {r["code"]: r for r in _items(api)["items"]}["NAP0085"]
    assert (row["v12"], row["v1n"], row["avg"], row["purchase_count"]) == (None, None, 200, 1)


def test_chi_4_lan_thi_lan_1_so_lan_5_trong(db, api):
    add_ledger(db, "NAP0085", 220, "2026-03-01")
    add_ledger(db, "NAP0085", 240, "2026-04-01")
    add_ledger(db, "NAP0085", 260, "2026-05-01")
    row = {r["code"]: r for r in _items(api)["items"]}["NAP0085"]
    assert len(row["purchases"]) == 4 and row["v1n"] is None and row["v12"] == pytest.approx(260 / 240 - 1, abs=1e-6)


def test_cung_ngay_id_lon_hon_la_gan_hon(db, api):
    add_ledger(db, "NAP0085", 300, "2026-09-01")
    add_ledger(db, "NAP0085", 310, "2026-09-01")
    row = {r["code"]: r for r in _items(api)["items"]}["NAP0085"]
    assert [p["price"] for p in row["purchases"]][:2] == [310, 300]


def test_ten_nha_cung_cap_bo_duoi_vtbb_khong_co_trong_danh_muc_thi_lay_ma(api):
    rows = {r["code"]: r for r in _items(api)["items"]}
    assert [p["supplier"] for p in rows["CPT0105"]["purchases"]][:2] == ["Nhựa Việt", "Nhựa Á Châu"]
    assert rows["NAP0085"]["purchases"][0]["supplier"] == "NCC_LA"
    assert supplier_label("Công ty ABC - vtbb ", "X") == "Công ty ABC" and supplier_label(None, "X") == "X"


def test_tab_product_mo_ta_ten_nhom_dvt_va_ma_chua_co_gia_chi_hien_khi_tat_chi_ma_co_gia(api):
    on = {r["code"] for r in _items(api)["items"]}
    assert on == {"CPT0105", "NAP0085"}                                # NHG0001 chưa có lần mua nào
    off = {r["code"]: r for r in _items(api, only_priced=False)["items"]}
    assert set(off) == {"CPT0105", "NAP0085", "NHG0001"}
    assert off["NHG0001"]["purchases"] == [] and off["NHG0001"]["avg"] is None and off["NHG0001"]["purchase_count"] == 0
    assert (off["CPT0105"]["name"], off["CPT0105"]["group"], off["CPT0105"]["unit"]) == ("Chai 450ml", "Chai", "Cái")


def test_ma_co_bao_gia_nhung_ngoai_dinh_muc_van_nam_trong_tap_ma_vtbb(db, api):
    add_ledger(db, "KHAC001", 10, "2026-03-01")
    assert "KHAC001" not in {r["code"] for r in _items(api)["items"]}
    add_quote(db, "KHAC001", 12, "2026-04-01")
    assert "KHAC001" in {r["code"] for r in _items(api)["items"]}
    assert "KHAC001" in {r["code"] for r in _items(api, scope="all")["items"]}


# ── Lọc / xếp / phân trang ──────────────────────────────────────────────────────
def test_chip_nhom_dem_truoc_khi_tim_va_loc_theo_nhom(db, api):
    db.query(Product).filter_by(code="NAP0085").update({"item_group": "Nắp"})
    db.commit()
    data = _items(api)
    assert data["groups"] == [{"group": "Chai", "count": 1}, {"group": "Nắp", "count": 1}]    # chai → nắp đúng thứ tự cột
    only = _items(api, group="nap")                                                          # so không dấu, không phân biệt hoa thường
    assert [r["code"] for r in only["items"]] == ["NAP0085"] and only["groups"] == data["groups"]


def test_tim_theo_ma_ten_nhom_va_ten_nha_cung_cap_khong_dau(api):
    assert [r["code"] for r in _items(api, q="chai 450")["items"]] == ["CPT0105"]
    assert [r["code"] for r in _items(api, q="nhua viet")["items"]] == ["CPT0105"]       # NCC của lần 1
    assert [r["code"] for r in _items(api, q="ncc_la")["items"]] == ["NAP0085"]
    assert _items(api, q="khong-co-gi")["items"] == []


def test_xep_theo_gia_lan_1_o_trong_xuong_cuoi_ca_hai_chieu_va_khoa_phu_la_ma(api):
    for direction in ("asc", "desc"):
        codes = [r["code"] for r in _items(api, only_priced=False, sort_by="last_price", sort_dir=direction)["items"]]
        assert codes[-1] == "NHG0001"                                  # chưa có giá luôn cuối
    assert [r["code"] for r in _items(api, sort_by="last_price", sort_dir="desc")["items"]] == ["NAP0085", "CPT0105"]
    assert [r["code"] for r in _items(api, sort_by="v12", sort_dir="asc")["items"]] == ["CPT0105", "NAP0085"]  # v12 trống của NAP → cuối
    assert [r["code"] for r in _items(api, sort_by="v12", sort_dir="desc")["items"]] == ["CPT0105", "NAP0085"]


@pytest.mark.parametrize("key", ["code", "name", "group", "unit", "purchase_count", "last_price", "last_date", "v12", "v1n", "avg"])
def test_moi_khoa_xep_deu_duoc_nhan(api, key):
    assert api.get(URL, params={"sort_by": key, "sort_dir": "desc"}).status_code == 200


def test_phan_trang_va_tham_so_sai(api):
    page = _items(api, page=2, page_size=1)
    assert page["total"] == 2 and len(page["items"]) == 1
    assert api.get(URL, params={"sort_dir": "up"}).status_code == 422
    assert api.get(URL, params={"scope": "x"}).status_code == 422
    assert api.get(URL, params={"page_size": 501}).status_code == 422
    assert [r["code"] for r in _items(api, sort_by="khong_co")["items"]] == ["CPT0105", "NAP0085"]    # khóa lạ → xếp theo mã


# ── Quyền + phạm vi ─────────────────────────────────────────────────────────────
def test_thieu_quyen_la_403_ke_ca_xuat(db, seed, cap_quyen, client_as, world):  # noqa: F811
    assert client_as(db.get(User, seed.u_req_id)).get(URL).status_code == 403
    cap_quyen(seed.u_req_id, "packaging_last_price", scope="all", read=True)
    only_read = client_as(db.get(User, seed.u_req_id))
    assert only_read.get(URL).status_code == 200 and only_read.get(URL + "/export").status_code == 403


def test_pham_vi_cong_ty_chi_thay_lan_mua_cua_phap_nhan_minh(db, seed, cap_quyen, client_as, world):  # noqa: F811
    from app.modules.product_price.model import ProductPriceLedger
    db.query(ProductPriceLedger).update({ProductPriceLedger.company_id: seed.company_id})
    add_ledger(db, "CPT0105", 999, "2026-09-01", company_id=seed.company_id + 99)      # pháp nhân khác, mới nhất
    cap_quyen(seed.u_req_id, "packaging_last_price", scope="company", read=True)
    rows = {r["code"]: r for r in client_as(db.get(User, seed.u_req_id)).get(URL).json()["data"]["items"]}
    assert rows["CPT0105"]["last_price"] == 150 and rows["CPT0105"]["purchase_count"] == 6
    cap_quyen(seed.u_req_id, "packaging_last_price", scope="all", read=True)
    full = {r["code"]: r for r in client_as(db.get(User, seed.u_req_id)).get(URL).json()["data"]["items"]}
    assert full["CPT0105"]["last_price"] == 999


# ── Số truy vấn ─────────────────────────────────────────────────────────────────
#  bao-CR-800 (27/11/2026): thêm MỘT truy vấn cố định lấy mã nhóm nguyên liệu (màn VTBB không mang mã nguyên liệu) nên
#  5 -> 6. Vẫn là hằng số: không theo số mã, số lần hay bộ lọc. Tên bài giữ nguyên để khỏi đổi lịch sử.
QUERY_COUNT = 6


def test_so_truy_van_la_5_va_khong_phu_thuoc_so_ma_so_lan_hay_bo_loc(db, world):
    busy = dict(q="chai", groups=["Chai", "Nắp"], suppliers=["NCC01"], date_from=date(2026, 1, 1), date_to=date(2026, 12, 31),
                trend="up", min_pct=1.0, bom_only=True, sort_by="p2_price", sort_dir="desc")
    _, small = count_queries(db, lambda: build_last_prices(db))
    for i in range(120):
        code = f"C{i:04d}"
        _bom(db, f"HH1{i:04d}", bottle_code=code)
        add_products(db, (code, f"Chai {i}", "Cái"))
        for k in range(12):
            add_ledger(db, code, 100 + k, f"2026-0{1 + k % 9}-01", supplier="NCC01" if k % 2 else "NCC02")
    res, big = count_queries(db, lambda: build_last_prices(db))
    assert len(res["rows"]) > 100
    assert len(small) == len(big) == QUERY_COUNT
    for n in (3, 10):
        _, plain = count_queries(db, lambda: build_last_prices(db, n=n))
        _, filtered = count_queries(db, lambda: build_last_prices(db, n=n, **busy))
        assert len(plain) == len(filtered) == QUERY_COUNT
    _, wide = count_queries(db, lambda: build_last_prices(db, scope="all", only_priced=False))
    assert len(wide) == QUERY_COUNT


# ── Xuất Excel ──────────────────────────────────────────────────────────────────
def test_xuat_excel_dung_cot_loc_va_o_trong_khong_thanh_0(api, db):
    res = api.get(URL + "/export", params={"only_priced": False, "sort_by": "code"})
    assert res.status_code == 200 and res.headers["content-type"] == XLSX
    ws = openpyxl.load_workbook(BytesIO(res.content)).active
    head, rows = read_report_sheet(ws)
    #  Hàng nhóm như bản mẫu: THÔNG TIN VTBB · LẦN k · BIẾN ĐỘNG · GIÁ TB (ô gộp), dưới là tên cột ngắn.
    assert head[:6] == ["THÔNG TIN VTBB - Mã VTBB", "THÔNG TIN VTBB - Tên vật tư", "THÔNG TIN VTBB - Nhóm",
                        "THÔNG TIN VTBB - ĐVT", "THÔNG TIN VTBB - Số lần có giá", "LẦN 1 (gần nhất) - Ngày mua"]
    assert head[-3:] == ["BIẾN ĐỘNG - Lần 1 so lần 2", "BIẾN ĐỘNG - Lần 1 so lần 5", "GIÁ TB - Giá TB 5 lần"]
    assert len(head) == 5 + 15 + 3
    assert "A4:E4" in {str(m) for m in ws.merged_cells.ranges}
    by_code = {r[0].value: {h: c.value for h, c in zip(head, r)} for r in rows}
    assert list(by_code) == ["CPT0105", "NAP0085", "NHG0001"]
    chai = by_code["CPT0105"]
    assert chai["LẦN 1 (gần nhất) - Đơn giá"] == 150 and chai["LẦN 5 - Đơn giá"] == 110
    assert chai["LẦN 1 (gần nhất) - Nhà cung cấp"] == "Nhựa Việt"
    #  Phần trăm ghi TỶ SỐ, định dạng 0.0% để Excel tự hiện "15,4%".
    v12 = rows[0][head.index("BIẾN ĐỘNG - Lần 1 so lần 2")]
    assert v12.value == pytest.approx(150 / 130 - 1, abs=1e-6) and v12.number_format.startswith("0.0%")
    nhan = by_code["NHG0001"]
    assert nhan["LẦN 1 (gần nhất) - Đơn giá"] is None and nhan["GIÁ TB - Giá TB 5 lần"] is None
    _, only_q = read_report_sheet(openpyxl.load_workbook(BytesIO(api.get(URL + "/export", params={"q": "nap"}).content)).active)
    assert len(only_q) == 1 and only_q[0][0].value == "NAP0085"


# ── Số lần hiển thị n ───────────────────────────────────────────────────────────
def test_n_3_chi_lay_3_lan_va_lan_1_so_lan_n_theo_n(api):
    row = {r["code"]: r for r in _items(api, n=3)["items"]}["CPT0105"]
    assert [p["price"] for p in row["purchases"]] == [150, 130, 120]
    assert row["v1n"] == pytest.approx(150 / 120 - 1, abs=1e-6)
    assert row["avg"] == pytest.approx((150 + 130 + 120) / 3) and row["purchase_count"] == 6


def test_n_10_co_6_lan_thi_lan_1_so_lan_10_trong(api):
    row = {r["code"]: r for r in _items(api, n=10)["items"]}["CPT0105"]
    assert len(row["purchases"]) == 6 and row["v1n"] is None
    assert row["avg"] == pytest.approx((150 + 130 + 120 + 105 + 110 + 100) / 6)


@pytest.mark.parametrize("params", [{"n": 1}, {"n": 11}, {"trend": "sideways"}, {"min_pct": -1},
                                    {"date_from": "2026-05-01", "date_to": "2026-01-01"},
                                    {"group": "x" * 51}, {"group": ["Chai", "x" * 51]}, {"group": [f"G{i}" for i in range(201)]}])
def test_tham_so_sai_la_422(api, params):
    assert api.get(URL, params=params).status_code == 422


# ── Bộ lọc mới ──────────────────────────────────────────────────────────────────
def test_o_chon_ma_chi_giu_dung_cac_ma_da_chon(api):
    """Ô chọn mã (27/11/2026): `code` lặp chỉ giữ đúng các mã đó; mã không có dòng thì bỏ qua, không lỗi."""
    got = {r["code"] for r in _items(api, code=["NAP0085", "KHONGCO01"])["items"]}
    assert got == {"NAP0085"}
    both = {r["code"] for r in _items(api, code=["NAP0085", "CPT0105"])["items"]}
    assert both == {"NAP0085", "CPT0105"}
    assert api.get(URL, params={"code": [f"M{i}" for i in range(501)]}).status_code == 422


def test_khoang_ngay_loc_truoc_khi_xep_hang_va_dem_so_lan(api):
    row = {r["code"]: r for r in _items(api, date_from="2026-02-01", date_to="2026-05-31")["items"]}["CPT0105"]
    assert [p["price"] for p in row["purchases"]] == [130, 120, 105, 110]      # 150 (tháng 6) nằm ngoài khoảng
    assert row["purchase_count"] == 4 and row["last_date"] == "2026-05-01"
    only = _items(api, date_from="2026-06-01")["items"]
    assert [r["code"] for r in only] == ["CPT0105"]                             # NAP (tháng 2) hết lần mua trong khoảng


def test_loc_nha_cung_cap_giu_ma_co_ncc_do_trong_n_lan_dang_hien(api):
    assert [r["code"] for r in _items(api, supplier=["NCC_LA"])["items"]] == ["NAP0085"]
    assert [r["code"] for r in _items(api, supplier=["NCC02"], n=2)["items"]] == ["CPT0105"]       # 150 của NCC02 ở lần 1
    assert _items(api, supplier=["NCC01"], date_from="2026-06-01")["items"] == []                  # NCC01 ngoài khoảng → không còn lần nào
    both = {r["code"] for r in _items(api, supplier=["NCC_LA", "NCC02"])["items"]}
    assert both == {"CPT0105", "NAP0085"}


def test_danh_sach_nha_cung_cap_chua_ap_bo_loc_nha_cung_cap(api):
    data = _items(api, supplier=["NCC_LA"])
    assert {s["code"]: s["name"] for s in data["suppliers"]} == {
        "NCC01": "Nhựa Á Châu", "NCC02": "Nhựa Việt", "NCC_LA": "NCC_LA"}


@pytest.fixture
def moves(db, world):
    """Thêm mã tăng (CPT0105 15,4%), giảm (DWN01 -25%), không đổi (FLT01), một lần (NAP0085) — đều trong định mức."""
    add_products(db, ("DWN01", "Chai giảm", "Cái"), ("FLT01", "Nắp phẳng", "Cái"))
    add_ledger(db, "DWN01", 200, "2026-01-01")
    add_ledger(db, "DWN01", 150, "2026-02-01")
    add_ledger(db, "FLT01", 100, "2026-01-01")
    add_ledger(db, "FLT01", 100, "2026-02-01")
    _bom(db, "HH2", bottle_code="DWN01", cap_code="FLT01", label_code="")


def test_loc_bien_dong_lan_1_so_lan_2(api, moves):
    codes = lambda **kw: sorted(r["code"] for r in _items(api, **kw)["items"])  # noqa: E731
    assert codes(trend="up") == ["CPT0105"]
    assert codes(trend="down") == ["DWN01"]
    assert codes(trend="flat") == ["FLT01"]                       # mã một lần mua (NAP) không có chiều đổi giá
    assert codes(trend="all") == ["CPT0105", "DWN01", "FLT01", "NAP0085"]


def test_nguong_bien_dong_tuyet_doi_lan_1_so_lan_2(api, moves):
    codes = lambda **kw: sorted(r["code"] for r in _items(api, **kw)["items"])  # noqa: E731
    assert codes(min_pct=20) == ["DWN01"]                         # |-25%| >= 20, 15,4% thì không
    assert codes(min_pct=15) == ["CPT0105", "DWN01"]
    assert codes(min_pct=0) == ["CPT0105", "DWN01", "FLT01", "NAP0085"]
    assert codes(min_pct=15, trend="up") == ["CPT0105"]


def test_chi_ma_trong_dinh_muc_bo_ma_chi_co_bao_gia(db, api):
    add_ledger(db, "QUOTED1", 10, "2026-03-01")
    add_quote(db, "QUOTED1", 12, "2026-04-01")
    assert "QUOTED1" in {r["code"] for r in _items(api)["items"]}
    assert "QUOTED1" not in {r["code"] for r in _items(api, bom_only=True)["items"]}
    assert "QUOTED1" not in {r["code"] for r in _items(api, scope="all", bom_only=True)["items"]}


def test_so_luong_tung_lan_mua_co_trong_du_lieu(db, api):
    add_ledger(db, "NAP0085", 210, "2026-08-01", qty=1234.5)
    row = {r["code"]: r for r in _items(api)["items"]}["NAP0085"]
    assert row["purchases"][0]["qty"] == 1234.5


def test_xep_theo_gia_va_ngay_cua_lan_thu_k(api, moves):
    desc = [r["code"] for r in _items(api, sort_by="p2_price", sort_dir="desc")["items"]]
    assert desc == ["DWN01", "CPT0105", "FLT01", "NAP0085"]       # lần 2: 200 > 130 > 100, NAP chưa có lần 2 → cuối
    asc = [r["code"] for r in _items(api, sort_by="p2_price", sort_dir="asc")["items"]]
    assert asc == ["FLT01", "CPT0105", "DWN01", "NAP0085"]
    by_date = [r["code"] for r in _items(api, sort_by="p1_date", sort_dir="desc")["items"]]
    assert by_date[0] == "CPT0105" and by_date[-1] in ("DWN01", "FLT01", "NAP0085")
    assert api.get(URL, params={"sort_by": "p99_price"}).status_code == 200      # lần ngoài giới hạn → rơi về mã


def test_xuat_excel_theo_n_va_them_cot_so_luong_va_loc(api, moves):
    head, _ = read_report_sheet(openpyxl.load_workbook(BytesIO(api.get(URL + "/export", params={"n": 3, "show_qty": True}).content)).active)
    assert len(head) == 5 + 3 * 4 + 3
    assert "LẦN 3 - Số lượng" in head and "BIẾN ĐỘNG - Lần 1 so lần 3" in head and "GIÁ TB - Giá TB 3 lần" in head
    ws10 = openpyxl.load_workbook(BytesIO(api.get(URL + "/export", params={"n": 10}).content)).active
    assert ws10.max_column == 5 + 10 * 3 + 3
    _, filtered = read_report_sheet(openpyxl.load_workbook(BytesIO(api.get(URL + "/export", params={"trend": "down"}).content)).active)
    assert len(filtered) == 1 and filtered[0][0].value == "DWN01"


def test_dvt_danh_muc_trong_thi_lay_dvt_cua_lan_mua_gan_nhat_co_ghi_dvt(db, api):
    db.query(Product).filter_by(code="CPT0105").update({"unit": ""})
    db.query(Product).filter_by(code="NAP0085").update({"unit": "Bộ"})          # danh mục có ĐVT → giữ nguyên
    add_ledger(db, "CPT0105", 160, "2026-08-01", unit="")                         # lần mới nhất không ghi ĐVT → bỏ qua
    db.commit()
    rows = {r["code"]: r for r in _items(api)["items"]}
    assert rows["CPT0105"]["unit"] == "Cái"      # từ lần mua gần nhất có ĐVT (add_ledger mặc định "Cái")
    assert rows["NAP0085"]["unit"] == "Bộ"


def test_chip_nhom_dem_theo_moi_bo_loc_tru_bo_loc_nhom(db, api):
    """Lọc nhà cung cấp / tìm / ngày / xu hướng thì số trên chip nhóm co theo; chọn nhóm thì chip các nhóm khác vẫn giữ."""
    db.query(Product).filter_by(code="NAP0085").update({"item_group": "Nắp"})
    db.commit()
    both = [{"group": "Chai", "count": 1}, {"group": "Nắp", "count": 1}]
    assert _items(api)["groups"] == both
    assert _items(api, supplier=["NCC_LA"])["groups"] == [{"group": "Nắp", "count": 1}]       # chỉ nắp có NCC_LA
    assert _items(api, supplier=["NCC02"], n=2)["groups"] == [{"group": "Chai", "count": 1}]
    assert _items(api, q="chai")["groups"] == [{"group": "Chai", "count": 1}]
    assert _items(api, date_from="2026-06-01")["groups"] == [{"group": "Chai", "count": 1}]
    assert _items(api, supplier=["NCC_LA"], group="Chai")["groups"] == [{"group": "Nắp", "count": 1}]   # nhóm không tự co chính nó
    assert _items(api, supplier=["NCC_LA"], group="Chai")["items"] == []


# ── Chip nhóm bật / tắt, chọn nhiều nhóm cùng lúc (HOẶC) ────────────────────────────
@pytest.fixture
def grouped(db, moves):
    """CPT0105 + DWN01 = Chai, NAP0085 = Nắp, FLT01 = Nhãn."""
    for code, grp in (("CPT0105", "Chai"), ("DWN01", "Chai"), ("NAP0085", "Nắp"), ("FLT01", "Nhãn")):
        db.query(Product).filter_by(code=code).update({"item_group": grp})
    db.commit()


def test_nhieu_nhom_la_hoac_mot_nhom_va_ten_nhom_cu_van_nhan(api, grouped):
    codes = lambda **kw: sorted(r["code"] for r in _items(api, **kw)["items"])  # noqa: E731
    assert codes() == ["CPT0105", "DWN01", "FLT01", "NAP0085"]                       # không chọn nhóm nào = không lọc
    assert codes(group="Chai") == ["CPT0105", "DWN01"]                               # một giá trị (cách gọi cũ)
    assert codes(group=["Chai", "Nắp"]) == ["CPT0105", "DWN01", "NAP0085"]           # HOẶC
    assert codes(group=["nap", "NHAN"]) == ["FLT01", "NAP0085"]                      # không dấu, không phân biệt hoa thường
    assert codes(group=["", "Nắp"]) == ["NAP0085"]                                   # giá trị rỗng bị bỏ
    assert codes(group=[""]) == ["CPT0105", "DWN01", "FLT01", "NAP0085"]
    assert codes(group=["Chai", "Nắp"], trend="up") == ["CPT0105"]                   # cộng với bộ lọc khác theo VÀ


def test_chip_nhom_khong_doi_khi_chon_nhom_va_xuat_excel_theo_nhieu_nhom(api, grouped):
    base = _items(api)["groups"]
    assert base == [{"group": "Chai", "count": 2}, {"group": "Nắp", "count": 1}, {"group": "Nhãn", "count": 1}]
    for picked in (["Chai"], ["Chai", "Nắp"], ["Nhãn", "Nắp", "Chai"]):
        assert _items(api, group=picked)["groups"] == base                           # chip không tự co theo nhóm đang bật
    assert _items(api, group=["Nắp"], trend="down")["groups"] == [{"group": "Chai", "count": 1}]   # nhưng co theo bộ lọc khác
    res = api.get(URL + "/export", params={"group": ["Chai", "Nắp"]})
    _, rows = read_report_sheet(openpyxl.load_workbook(BytesIO(res.content)).active)
    assert sorted(r[0].value for r in rows) == ["CPT0105", "DWN01", "NAP0085"]
