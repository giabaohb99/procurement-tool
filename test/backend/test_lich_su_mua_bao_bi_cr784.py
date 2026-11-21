"""duoc-CR-784 — tab "Lịch sử mua hàng" của cụm Giá bao bì: từng lần mua theo mã VTBB / theo sản phẩm (mở rộng qua định mức),
số gộp (giá bình quân gia quyền, min / max, số NCC, khoảng ngày), dòng giá 0 chỉ hiện chứ không tính, chênh so lần có giá liền
trước, lọc / xếp / phân trang, biểu đồ cho đúng một mã, phạm vi pháp nhân, quyền, xuất Excel và SỐ TRUY VẤN cố định."""
from io import BytesIO

import openpyxl
import pytest

from app.core.packaging_price_codes import PackagingRole, PriceSourceType
from app.modules.packaging_cost.history_service import SORT_KEYS, build_history
from app.modules.packaging_cost.model import PackagingBom
from app.modules.supplier.model import Supplier
from app.modules.user.model import User
from hdld_factory import client_as  # noqa: F401  (fixture)
from lich_lam_viec_factory import count_queries
from so_gia_factory_cr784 import add_ledger, add_products, add_quote, make_item, make_po

URL = "/api/packaging-cost/history"
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _bom(db, hh="HH0001", **over) -> PackagingBom:
    base = dict(hh_code=hh, hh_name=f"Sản phẩm {hh}", bottle_code="CPT0105", cap_code="NAP0085", label_code="NHG0001",
                carton_label_code="", carton_code="", carton_qty=40, created_by=1, updated_by=1)
    base.update(over)
    row = PackagingBom(**base)
    db.add(row)
    db.commit()
    return row


@pytest.fixture
def world(db):
    """Chai CPT0105: 5 lần có giá + 1 dòng giá 0 + 1 dòng ĐMH đang mở; nắp NAP0085: 1 lần; mã SP0001 NGOÀI định mức."""
    add_products(db, ("CPT0105", "Chai 450ml", "Cái"), ("NAP0085", "Nắp vặn", "Cái"), ("NHG0001", "Nhãn", "Cái"),
                 ("SP0001", "Sản phẩm ngoài định mức", "Cái"))
    db.add_all([Supplier(code="NCC01", name="Nhựa Á Châu - VTBB"), Supplier(code="NCC02", name="Nhựa Việt")])
    db.commit()
    for price, day, ncc, qty in ((100, "2026-01-01", "NCC01", 1000), (110, "2026-02-01", "NCC01", 500),
                                 (105, "2026-03-01", "NCC02", 1500), (120, "2026-04-01", "NCC02", 1000)):
        add_ledger(db, "CPT0105", price, day, supplier=ncc, qty=qty)
    add_ledger(db, "CPT0105", 0, "2026-04-15", supplier="NCC01", qty=50)          # giá 0: hiện nhưng không tính
    add_ledger(db, "CPT0105", 130, "2026-05-01", supplier="NCC01", qty=2000, source_type=PriceSourceType.PO_LINE,
               doc_id=77)
    add_ledger(db, "NAP0085", 200, "2026-02-01", supplier="NCC_LA", qty=10)       # nhà cung cấp không có trong danh mục
    add_ledger(db, "SP0001", 5000, "2026-02-01", qty=1)
    _bom(db)
    _bom(db, "HH0002", cap_code="CPT0105")          # chai CPT0105 làm NẮP ở sản phẩm 2: một mã hai vai trò
    return None


@pytest.fixture
def api(db, seed, cap_quyen, client_as, world):  # noqa: F811
    cap_quyen(seed.u_req_id, "packaging_cost", scope="all", read=True, export=True)
    return client_as(db.get(User, seed.u_req_id))


def _get(api, **params):
    res = api.get(URL, params=params)
    assert res.status_code == 200, res.text
    return res.json()["data"]


# ── Dòng + chênh + thứ tự ───────────────────────────────────────────────────────
def test_mot_ma_moi_nhat_truoc_kem_lan_mua_va_chenh_so_voi_lan_co_gia_truoc(api):
    data = _get(api, codes=["CPT0105"])
    rows = data["items"]
    assert [r["date"] for r in rows] == ["2026-05-01", "2026-04-15", "2026-04-01", "2026-03-01", "2026-02-01", "2026-01-01"]
    assert [r["seq"] for r in rows] == [6, 5, 4, 3, 2, 1]
    by_date = {r["date"]: r for r in rows}
    assert by_date["2026-05-01"]["prev_price"] == 120 and by_date["2026-05-01"]["diff"] == 10      # bỏ qua dòng giá 0 ngày 15/4
    assert by_date["2026-05-01"]["pct"] == pytest.approx(10 / 120, abs=1e-6)
    assert by_date["2026-03-01"]["diff"] == -5
    assert by_date["2026-01-01"]["prev_price"] is None and by_date["2026-01-01"]["diff"] is None
    zero = by_date["2026-04-15"]
    assert (zero["price"], zero["diff"], zero["pct"], zero["amount"]) == (0, None, None, 0)
    assert by_date["2026-04-01"]["prev_price"] == 105       # lần liền trước của 1/4 là 1/3, không phải dòng giá 0 (sau nó)


def test_dong_dmh_dang_mo_mang_nguon_va_so_dmh_dong_cu_khong_co(db, api):
    po = make_po(db, code="PO-HIST-1")
    from app.modules.product_price.model import ProductPriceLedger
    db.query(ProductPriceLedger).filter_by(doc_id=77).update({"doc_id": po.id})
    db.commit()
    rows = {r["date"]: r for r in _get(api, codes=["CPT0105"])["items"]}
    assert rows["2026-05-01"]["source_type"] == int(PriceSourceType.PO_LINE) and rows["2026-05-01"]["po_code"] == "PO-HIST-1"
    assert rows["2026-05-01"]["doc_id"] == po.id
    assert rows["2026-02-01"]["source_type"] == int(PriceSourceType.PURCHASE_HISTORY)
    assert rows["2026-02-01"]["doc_id"] == 0 and rows["2026-02-01"]["po_code"] == ""


def test_chenh_khong_phu_thuoc_bo_loc_ngay_va_ten_nha_cung_cap_bo_duoi_vtbb(api):
    rows = _get(api, codes=["CPT0105"], date_from="2026-03-01", date_to="2026-03-31")["items"]
    assert len(rows) == 1 and rows[0]["prev_price"] == 110 and rows[0]["diff"] == -5       # lần trước nằm NGOÀI khoảng lọc
    assert rows[0]["supplier"] == "Nhựa Việt" and rows[0]["name"] == "Chai 450ml" and rows[0]["group"] == "Chai"
    first = _get(api, codes=["CPT0105"], supplier=["NCC01"])["items"][-1]
    assert first["supplier"] == "Nhựa Á Châu"
    assert _get(api, codes=["NAP0085"])["items"][0]["supplier"] == "NCC_LA"        # không có trong danh mục -> lấy mã


# ── Số gộp ──────────────────────────────────────────────────────────────────────
def test_so_gop_gia_binh_quan_gia_quyen_chi_tinh_dong_co_gia(api):
    stats = _get(api, codes=["CPT0105"])["stats"]
    amount = 100 * 1000 + 110 * 500 + 105 * 1500 + 120 * 1000 + 130 * 2000
    qty_priced = 1000 + 500 + 1500 + 1000 + 2000
    assert stats["weighted_avg"] == pytest.approx(amount / qty_priced, abs=1e-3)
    assert (stats["purchase_count"], stats["priced_count"]) == (6, 5)
    assert stats["qty_total"] == qty_priced + 50                 # tổng SL của mọi dòng đang hiện, kể cả dòng giá 0
    assert (stats["min"], stats["max"]) == (100, 130)            # dòng giá 0 không kéo min xuống 0
    assert stats["supplier_count"] == 2
    assert (stats["first_date"], stats["last_date"]) == ("2026-01-01", "2026-05-01")


def test_so_gop_theo_bo_loc_va_khong_co_so_luong_thi_khong_co_gia_binh_quan(db, api):
    assert _get(api, codes=["CPT0105"], supplier=["NCC02"])["stats"]["weighted_avg"] == pytest.approx(
        (105 * 1500 + 120 * 1000) / 2500, abs=1e-3)
    add_ledger(db, "NHG0001", 80, "2026-03-01", qty=0)
    st = _get(api, codes=["NHG0001"])["stats"]
    assert (st["weighted_avg"], st["min"], st["max"], st["purchase_count"]) == (None, 80, 80, 1)
    only_zero = _get(api, codes=["CPT0105"], date_from="2026-04-10", date_to="2026-04-20")["stats"]
    assert (only_zero["priced_count"], only_zero["weighted_avg"], only_zero["min"], only_zero["max"]) == (0, None, None, None)
    assert only_zero["purchase_count"] == 1


# ── Biểu đồ ─────────────────────────────────────────────────────────────────────
def test_chuoi_bieu_do_chi_khi_dung_mot_ma_cu_toi_moi_va_bo_gia_0(api):
    series = _get(api, codes=["CPT0105"])["series"]
    assert [p["price"] for p in series] == [100, 110, 105, 120, 130]
    assert series[0] == {"date": "2026-01-01", "price": 100, "supplier_code": "NCC01", "supplier": "Nhựa Á Châu", "qty": 1000}
    assert _get(api, codes=["CPT0105", "NAP0085"])["series"] is None
    assert _get(api)["series"] is None
    assert _get(api, codes=["CPT0105"], supplier=["NCC02"])["series"] == [
        {"date": "2026-03-01", "price": 105, "supplier_code": "NCC02", "supplier": "Nhựa Việt", "qty": 1500},
        {"date": "2026-04-01", "price": 120, "supplier_code": "NCC02", "supplier": "Nhựa Việt", "qty": 1000}]


def test_chuoi_bieu_do_cat_o_1000_diem_gan_nhat(db, api):
    from app.modules.packaging_cost import history_service as hs
    for i in range(12):
        add_ledger(db, "NHG0001", 100 + i, f"2025-{1 + i % 12:02d}-10", qty=1)
    old = hs.SERIES_CAP
    hs.SERIES_CAP = 5
    try:
        series = _get(api, codes=["NHG0001"])["series"]
    finally:
        hs.SERIES_CAP = old
    assert len(series) == 5 and [p["date"] for p in series] == sorted(p["date"] for p in series)
    assert series[-1]["date"] == "2025-12-10"


# ── Lọc ─────────────────────────────────────────────────────────────────────────
def test_khong_chon_ma_nao_la_moi_ma_vtbb_cua_cum_gia_khong_gom_ma_ngoai_dinh_muc(db, api):
    codes = {r["code"] for r in _get(api, page_size=500)["items"]}
    assert codes == {"CPT0105", "NAP0085"}              # SP0001 không thuộc định mức / báo giá; NHG0001 chưa có lần mua
    add_quote(db, "SP0001", 4900, "2026-03-01")
    assert "SP0001" in {r["code"] for r in _get(api, page_size=500)["items"]}      # có báo giá = thuộc cụm giá


def test_loc_nha_cung_cap_khoang_ngay_va_chu_tim(api):
    assert {r["supplier_code"] for r in _get(api, codes=["CPT0105"], supplier=["NCC02"])["items"]} == {"NCC02"}
    assert len(_get(api, codes=["CPT0105"], supplier=["NCC01", "NCC02"])["items"]) == 6
    assert len(_get(api, codes=["CPT0105"], date_from="2026-02-01", date_to="2026-04-01")["items"]) == 3
    assert len(_get(api, q="nắp")["items"]) == 1                                  # theo tên sản phẩm
    assert len(_get(api, q="npp")["items"]) == 0
    assert {r["code"] for r in _get(api, q="NCC_LA")["items"]} == {"NAP0085"}     # theo mã nhà cung cấp
    assert len(_get(api, q="Việt", codes=["CPT0105"])["items"]) == 2              # theo tên nhà cung cấp
    assert _get(api, q="%")["total"] == 0                                         # ký tự đặc biệt bị thoát, không khớp tất cả


def test_o_chon_nha_cung_cap_chi_theo_pham_vi_ma_khong_theo_q_hay_nha_cung_cap(api):
    data = _get(api, codes=["CPT0105"], supplier=["NCC02"], q="Việt")
    assert data["suppliers"] == [{"code": "NCC01", "name": "Nhựa Á Châu"}, {"code": "NCC02", "name": "Nhựa Việt"}]
    assert [s["code"] for s in _get(api, codes=["NAP0085"])["suppliers"]] == ["NCC_LA"]


# ── Chế độ sản phẩm ─────────────────────────────────────────────────────────────
def test_che_do_san_pham_mo_rong_thanh_phan_dinh_muc_kem_vai_tro(api):
    data = _get(api, mode="product", hh_codes=["HH0001"], page_size=500)
    assert {r["code"] for r in data["items"]} == {"CPT0105", "NAP0085"}            # NHG0001 chưa có lần mua
    roles = {r["code"]: r["roles"] for r in data["items"]}
    assert roles["CPT0105"] == [int(PackagingRole.BOTTLE)] and roles["NAP0085"] == [int(PackagingRole.CAP)]
    assert data["series"] is None


def test_che_do_san_pham_mot_ma_hai_vai_tro_va_khong_co_dinh_muc_thi_rong(api):
    both = _get(api, mode="product", hh_codes=["HH0001", "HH0002"])["items"]
    assert {r["code"]: r["roles"] for r in both}["CPT0105"] == [int(PackagingRole.BOTTLE), int(PackagingRole.CAP)]
    none = _get(api, mode="product", hh_codes=["HH9999"])
    assert none["items"] == [] and none["total"] == 0 and none["stats"]["purchase_count"] == 0 and none["suppliers"] == []
    all_products = _get(api, mode="product", page_size=500)
    assert {r["code"] for r in all_products["items"]} == {"CPT0105", "NAP0085"}


def test_che_do_ma_bo_qua_hh_codes_va_nguoc_lai(api):
    assert {r["code"] for r in _get(api, mode="code", codes=["NAP0085"], hh_codes=["HH0001"])["items"]} == {"NAP0085"}
    assert all(r["roles"] == [] for r in _get(api, mode="code", codes=["CPT0105"])["items"])


# ── Xếp + phân trang ────────────────────────────────────────────────────────────
@pytest.mark.parametrize("key", SORT_KEYS)
@pytest.mark.parametrize("direction", ["asc", "desc"])
def test_moi_khoa_cot_deu_xep_duoc_va_khong_mat_dong_giua_cac_trang(api, key, direction):
    seen = []
    for page in (1, 2, 3):
        seen += [r["id"] for r in _get(api, codes=["CPT0105", "NAP0085"], sort_by=key, sort_dir=direction,
                                       page=page, page_size=3)["items"]]
    assert len(seen) == len(set(seen)) == 7


def test_xep_theo_gia_o_trong_xuong_cuoi_hai_chieu_va_khoa_la_bi_bo_qua(db, api):
    add_ledger(db, "NHG0001", 90, "2026-03-05", supplier="", qty=1)           # nhà cung cấp trống
    for direction in ("asc", "desc"):
        rows = _get(api, codes=["NHG0001", "NAP0085"], sort_by="supplier", sort_dir=direction)["items"]
        assert rows[-1]["supplier_code"] == ""
    prices = [r["price"] for r in _get(api, codes=["CPT0105"], sort_by="price", sort_dir="desc")["items"]]
    assert prices == sorted(prices, reverse=True)
    weird = _get(api, codes=["CPT0105"], sort_by="drop table", sort_dir="asc")["items"]
    assert [r["date"] for r in weird] == sorted((r["date"] for r in weird), reverse=True)      # rơi về ngày giảm dần


def test_phan_trang_tong_la_so_dong_sau_loc_khong_phai_so_dong_cua_trang(api):
    data = _get(api, codes=["CPT0105"], page=2, page_size=4)
    assert data["total"] == 6 and len(data["items"]) == 2 and data["stats"]["purchase_count"] == 6
    assert _get(api, codes=["CPT0105"], page=9, page_size=4)["items"] == []


# ── Đầu vào ─────────────────────────────────────────────────────────────────────
def test_dau_vao_sai_tra_422(api):
    assert api.get(URL, params={"date_from": "2026-05-01", "date_to": "2026-01-01"}).status_code == 422
    assert api.get(URL, params={"mode": "lạ"}).status_code == 422
    assert api.get(URL, params={"sort_dir": "up"}).status_code == 422
    assert api.get(URL, params={"page_size": 501}).status_code == 422
    assert api.get(URL, params={"codes": [f"C{i}" for i in range(201)]}).status_code == 422
    assert api.get(URL, params={"hh_codes": [f"H{i}" for i in range(201)], "mode": "product"}).status_code == 422
    assert api.get(URL, params={"q": "x" * 101}).status_code == 422


# ── Quyền + phạm vi ─────────────────────────────────────────────────────────────
def test_khong_co_quyen_la_403_va_chi_doc_khong_xuat_duoc(db, seed, cap_quyen, client_as, world):  # noqa: F811
    assert client_as(db.get(User, seed.u_req_id)).get(URL).status_code == 403
    assert client_as(db.get(User, seed.u_req_id)).get("/api/packaging-cost/hh-options").status_code == 403
    cap_quyen(seed.u_req_id, "packaging_cost", scope="all", read=True)
    only_read = client_as(db.get(User, seed.u_req_id))
    assert only_read.get(URL).status_code == 200 and only_read.get(URL + "/export").status_code == 403


def test_pham_vi_cong_ty_khong_thay_lan_mua_cua_phap_nhan_khac_ke_ca_trong_chenh_va_lan_mua(  # noqa: F811
        db, seed, cap_quyen, client_as, world):
    from app.modules.product_price.model import ProductPriceLedger
    db.query(ProductPriceLedger).update({ProductPriceLedger.company_id: seed.company_id})
    add_ledger(db, "CPT0105", 999, "2026-03-15", company_id=seed.company_id + 99)      # pháp nhân khác, chen giữa 1/3 và 1/4
    cap_quyen(seed.u_req_id, "packaging_cost", scope="company", read=True)
    data = client_as(db.get(User, seed.u_req_id)).get(URL, params={"codes": ["CPT0105"]}).json()["data"]
    assert data["total"] == 6 and data["stats"]["max"] == 130 and len(data["series"]) == 5
    by_date = {r["date"]: r for r in data["items"]}
    assert by_date["2026-04-01"]["prev_price"] == 105 and by_date["2026-04-01"]["seq"] == 4      # không nhìn thấy dòng 999
    cap_quyen(seed.u_req_id, "packaging_cost", scope="all", read=True)
    full = client_as(db.get(User, seed.u_req_id)).get(URL, params={"codes": ["CPT0105"]}).json()["data"]
    assert full["total"] == 7 and full["stats"]["max"] == 999


# ── Danh mục sản phẩm cho ô chọn ────────────────────────────────────────────────
def test_hh_options_tra_ma_va_ten_san_pham_theo_ma(api):
    items = api.get("/api/packaging-cost/hh-options").json()["data"]["items"]
    assert items == [{"code": "HH0001", "name": "Sản phẩm HH0001"}, {"code": "HH0002", "name": "Sản phẩm HH0002"}]


# ── Xuất Excel ──────────────────────────────────────────────────────────────────
def test_xuat_excel_dung_bo_loc_thu_tu_va_cot_vai_tro_cua_che_do_san_pham(api):
    res = api.get(URL + "/export", params={"codes": ["CPT0105"], "sort_by": "price", "sort_dir": "asc"})
    assert res.status_code == 200 and res.headers["content-type"] == XLSX
    ws = openpyxl.load_workbook(BytesIO(res.content)).active
    head = [c.value for c in ws[1]]
    assert head[:3] == ["Ngày mua", "Mã VTBB", "Tên vật tư"] and "Vai trò" not in head
    assert ws.max_row == 7                                                     # tiêu đề + 6 lần mua
    prices = [ws.cell(row=r, column=head.index("Đơn giá") + 1).value for r in range(2, 8)]
    assert prices == sorted(prices) and prices[0] == 0
    sources = {ws.cell(row=r, column=head.index("Nguồn") + 1).value for r in range(2, 8)}
    assert sources == {"Lịch sử mua hàng", "Dòng đơn mua hàng"}
    product = openpyxl.load_workbook(BytesIO(api.get(URL + "/export", params={"mode": "product", "hh_codes": ["HH0001"]}).content)).active
    head2 = [c.value for c in product[1]]
    assert "Vai trò" in head2 and {product.cell(row=r, column=head2.index("Vai trò") + 1).value for r in range(2, product.max_row + 1)} == {"Chai", "Nắp"}


def test_xuat_excel_chan_o_tran_so_dong(db, api, monkeypatch):
    monkeypatch.setattr("app.modules.packaging_cost.history_service.MAX_ROWS", 3)
    monkeypatch.setattr("app.core.export_xlsx.MAX_ROWS", 3)
    assert api.get(URL + "/export", params={"codes": ["CPT0105"]}).status_code == 400


# ── Số truy vấn ─────────────────────────────────────────────────────────────────
def test_so_truy_van_co_dinh_khong_phu_thuoc_so_ma_so_dong_hay_bo_loc(db, world):
    from datetime import date
    busy = dict(q="chai", suppliers=["NCC01"], date_from=date(2026, 1, 1), date_to=date(2026, 12, 31), sort_by="name",
                sort_dir="desc", page=2, page_size=10)
    _, small = count_queries(db, lambda: build_history(db, codes=["CPT0105"]))
    _, small_all = count_queries(db, lambda: build_history(db))
    for i in range(80):
        code = f"C{i:04d}"
        _bom(db, f"HH1{i:04d}", bottle_code=code)
        add_products(db, (code, f"Chai {i}", "Cái"))
        for k in range(10):
            add_ledger(db, code, 100 + k, f"2026-0{1 + k % 9}-01", supplier="NCC01" if k % 2 else "NCC02", qty=10 + k)
    res, big_all = count_queries(db, lambda: build_history(db, page_size=500))
    assert res["total"] > 800 and len(res["items"]) == 500
    _, big_one = count_queries(db, lambda: build_history(db, codes=["CPT0105"]))
    _, big_busy = count_queries(db, lambda: build_history(db, codes=["CPT0105", "NAP0085"], **busy))
    _, big_prod = count_queries(db, lambda: build_history(db, mode="product", hh_codes=["HH0001"] + [f"HH1{i:04d}" for i in range(80)]))
    assert len(small_all) == len(big_all) == 3                    # số gộp + ô chọn nhà cung cấp + trang dòng
    assert len(small) == len(big_one) == 4                        # + truy vấn biểu đồ của đúng một mã
    assert len(big_busy) == 3 and len(big_prod) == 4              # nhiều mã = không biểu đồ; chế độ sản phẩm + truy vấn định mức
