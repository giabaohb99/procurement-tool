"""ai-CR-173 / ai-CR-174 (phase 23.4 + 23.5) — tìm giá + link trên web và chấm điểm NCC.

Chỉ kiểm phần vừa làm: hai handler ở `tools/market_tool.py`, nhóm ở `tool_router`, nhãn con ở sổ ý định.
Tìm web bị chặn hoàn toàn (monkeypatch `web_search.search` / `fetch`; `requests` ném lỗi nếu lỡ gọi) — bài kiểm không ra mạng.
"""
from datetime import date, timedelta

import pytest

from app.modules.agent_hub import web_search
from app.modules.assistant import tool_router as tr
from app.modules.assistant import tools as T
from app.modules.assistant.tools import market_tool as mt
from app.modules.contract.model import Contract
from app.modules.product.model import Product
from app.modules.purchase_history.model import PurchaseHistory
from app.modules.purchase_order.model import PODelivery, PurchaseOrder
from app.modules.supplier.model import Supplier
from app.modules.user.model import User

TODAY = date.today()


def _d(days_ago: int) -> str:
    return (TODAY - timedelta(days=days_ago)).isoformat()


@pytest.fixture(autouse=True)
def _chan_mang(monkeypatch):
    """Lỡ gọi mạng là đỏ ngay — không có bài nào ở đây được phép ra Internet."""
    def boom(*a, **k):
        raise AssertionError("bài kiểm không được ra mạng")

    monkeypatch.setattr(web_search.requests, "get", boom)
    monkeypatch.setattr(web_search.requests, "post", boom)


def _hoi(db, seed, name, args):
    return T.run_tool(db, db.get(User, seed.u_req_id), name, args)


@pytest.fixture
def web_gia(monkeypatch):
    """Máy tìm giả: lượt «giá …» ra 2 trang (một trang Shopee), lượt «báo giá …» ra thêm 1 trang; đọc trang trả chữ có giá."""
    asked: list[str] = []

    def fake_search(q, limit=8):
        asked.append(q)
        if q.startswith("giá "):
            return [{"title": "Thép phi 10 Hòa Phát - Thép Mạnh Hà", "url": "https://thepmanhha.vn/thep-phi-10",
                     "snippet": "Giá thép phi 10 Hòa Phát 15.200đ/kg"},
                    {"title": "Thép phi 10 | Shopee", "url": "https://shopee.vn/thep-phi-10-i.123",
                     "snippet": "Thép cây phi 10"}]
        return [{"title": "Báo giá thép xây dựng", "url": "https://thepviet.vn/bao-gia",
                 "snippet": "Bảng báo giá"},
                {"title": "Thép phi 10 Hòa Phát - Thép Mạnh Hà", "url": "https://thepmanhha.vn/thep-phi-10/",
                 "snippet": "trùng"}]

    def fake_fetch(url):
        if "thepmanhha" in url:
            return ("Thép Mạnh Hà chuyên thép xây dựng. " * 10
                    + "Thép phi 10 Hòa Phát CB300 giá 15.250 đ/kg, cập nhật 09/10/2026. "
                    + "Giao hàng toàn quốc. " * 20)
        if "shopee" in url:
            return "Thép cây phi 10 dài 11,7m. ₫ 185.000 Đã bán 12"
        return ""

    monkeypatch.setattr(web_search, "search", fake_search)
    monkeypatch.setattr(web_search, "fetch", fake_fetch)
    return asked


@pytest.fixture
def hang(db, seed):
    """Mã GA4 + 3 NCC (NX của seed, NCCB, NCCC) với lịch sử mua, ĐMH + lần giao, hợp đồng — đủ bốn cột điểm."""
    db.add(Product(code="GA4", name="Giấy A4 Double A 80gsm", unit="ram", item_group="VPP"))
    db.add_all([Supplier(code="NCCB", name="NCC B", is_active=True), Supplier(code="NCCC", name="NCC C", is_active=True)])
    rows = [
        # NX: rẻ nhất 100, mua 3 lần
        ("NX", "Nhà Xuất NX", 100, 10, _d(20)), ("NX", "Nhà Xuất NX", 100, 10, _d(60)), ("NX", "Nhà Xuất NX", 100, 10, _d(90)),
        # NCCB: 125, mua 1 lần
        ("NCCB", "NCC B", 125, 10, _d(40)),
        # NCCC: 200, mua 2 lần
        ("NCCC", "NCC C", 200, 10, _d(30)), ("NCCC", "NCC C", 200, 10, _d(70)),
        # dòng CŨ ngoài kỳ 12 tháng: không được tính
        ("NCCB", "NCC B", 50, 10, _d(400)),
    ]
    for code, name, price, qty, day in rows:
        db.add(PurchaseHistory(product_code="GA4", product_name="Giấy A4 Double A 80gsm", supplier_code=code,
                               supplier_name=name, price=price, qty_order=qty, amount=price * qty, unit="ram",
                               order_date=day, company_id=seed.company_id))
    db.flush()
    # ĐMH + lần giao: NX 2/2 đúng hạn; NCCC 1 lần trễ 5 ngày; NCCB không có lần giao nào.
    po_nx = PurchaseOrder(code="PO-NX", supplier_code="NX", supplier_name="Nhà Xuất NX", order_date=_d(30),
                          company_id=seed.company_id, status="received", created_by=seed.u_req_id)
    po_c = PurchaseOrder(code="PO-C", supplier_code="NCCC", supplier_name="NCC C", order_date=_d(30),
                         company_id=seed.company_id, status="received", created_by=seed.u_req_id)
    db.add_all([po_nx, po_c])
    db.flush()
    db.add_all([
        PODelivery(po_id=po_nx.id, po_item_id=1, promised_date=_d(20), received_date=_d(21)),
        PODelivery(po_id=po_nx.id, po_item_id=2, promised_date=_d(10), received_date=_d(10)),
        PODelivery(po_id=po_c.id, po_item_id=3, promised_date=_d(15), received_date=_d(10)),
        PODelivery(po_id=po_c.id, po_item_id=4, promised_date="", received_date=_d(5)),     # thiếu ngày cam kết: bỏ
    ])
    # Hợp đồng: NX còn hạn, NCCB hết hạn, NCCC không có.
    db.add_all([
        Contract(code="HD-NX", party_type="supplier", party_code="NX", party_name="Nhà Xuất NX", end_date=_d(-200),
                 status="active", company_id=seed.company_id),
        Contract(code="HD-B", party_type="supplier", party_code="NCCB", party_name="NCC B", end_date=_d(30),
                 status="active", company_id=seed.company_id),
    ])
    db.commit()


def _cap_du(seed, cap_quyen):
    cap_quyen(seed.u_req_id, "product", scope="all", read=True)
    cap_quyen(seed.u_req_id, "supplier", scope="all", read=True)
    cap_quyen(seed.u_req_id, "purchase_order", scope="all", read=True)
    cap_quyen(seed.u_req_id, "contract", scope="all", read=True)


# ── market_price_search ──────────────────────────────────────────────────────────────────
def test_tim_gia_web_thieu_quyen_thi_denied(db, seed, web_gia):
    out = _hoi(db, seed, "market_price_search", {"product": "thép phi 10"})
    assert out.get("denied") is True
    assert web_gia == [], "chưa có quyền thì không được tốn một lượt tìm web nào"


def test_tim_gia_web_tra_nguon_co_doan_trich_va_gia_erp_theo_ma(db, seed, cap_quyen, hang, web_gia):
    _cap_du(seed, cap_quyen)
    out = _hoi(db, seed, "market_price_search", {"product": "thép phi 10 Hòa Phát", "product_code": "GA4", "limit": 3})

    assert out["count"] == 3 and len(out["sources"]) == 3
    assert web_gia == ["giá thép phi 10 Hòa Phát", "báo giá thép phi 10 Hòa Phát"]   # hai lượt vì lượt một chưa đủ 3
    urls = [s["url"] for s in out["sources"]]
    assert urls == ["https://thepmanhha.vn/thep-phi-10", "https://shopee.vn/thep-phi-10-i.123", "https://thepviet.vn/bao-gia"]
    first, shopee = out["sources"][0], out["sources"][1]
    assert first["seller"] == "thepmanhha.vn" and shopee["seller"] == "Shopee"
    assert "15.250 đ/kg" in first["excerpt"] and len(first["excerpt"]) <= mt.EXCERPT_CHARS
    assert "185.000" in shopee["excerpt"]
    assert all(s["seen_on"] == TODAY.isoformat() for s in out["sources"])
    assert "name" in out["columns"] and "seen_on" in out["columns"]
    assert "tham khảo" in out["note"].lower() or "THAM KHẢO" in out["note"]

    erp = out["erp"]
    assert erp["product_code"] == "GA4" and erp["product_name"] == "Giấy A4 Double A 80gsm"
    assert erp["latest_price"]["price"] == 100.0 and erp["latest_price"]["order_date"] == _d(20)
    #  Giá tốt nhất xét TOÀN lịch sử (hàm `product_best_price`): dòng cũ 400 ngày của NCCB giá 50 đứng đầu.
    assert erp["best_price_suppliers"][0]["supplier_code"] == "NCCB"
    assert erp["best_price_suppliers"][0]["price"] == 50.0
    assert "customs" not in out    # không có dữ liệu hải quan thì không bịa khối này


def test_tim_gia_web_tu_do_ma_hang_theo_ten_khi_dung_mot_ket_qua(db, seed, cap_quyen, hang, web_gia):
    cap_quyen(seed.u_req_id, "product", scope="all", read=True)     # KHÔNG có supplier.read
    out = _hoi(db, seed, "market_price_search", {"product": "Giấy A4 Double A"})
    assert out["erp"]["product_code"] == "GA4"
    assert out["erp"]["latest_price"]["price"] == 100.0
    assert "best_price_suppliers" not in out["erp"]          # thiếu supplier.read thì không lộ tên NCC
    assert "supplier_code" not in out["erp"]["recent_purchases"][0]


def test_tim_gia_web_khong_ra_gi_van_tra_cau_giai_thich(db, seed, cap_quyen, monkeypatch):
    cap_quyen(seed.u_req_id, "product", scope="all", read=True)
    monkeypatch.setattr(web_search, "search", lambda q, limit=8: [])
    out = _hoi(db, seed, "market_price_search", {"product": "máy đào hầm lượng tử"})
    assert out["count"] == 0 and out["sources"] == []
    assert "Không tìm được" in out["note"]
    assert out["erp_note"].startswith("Chưa đối chiếu")


def test_doan_trich_lay_quanh_cho_co_gia():
    text = "mo ta dai " * 50 + "Giá bán: 1.250.000đ / thùng" + " chu khac " * 50 + "Khuyến mãi còn 990.000 VNĐ" + " x" * 300
    ex = mt._excerpt(text)
    assert "1.250.000đ" in ex and "990.000 VNĐ" in ex and " ... " in ex
    assert len(ex) <= mt.EXCERPT_CHARS
    assert mt._excerpt("không có số nào ở đây") == "không có số nào ở đây"
    assert mt._seller_of("https://www.lazada.vn/products/x") == "Lazada"
    assert mt._seller_of("https://www.hoaphat.com.vn/gia") == "hoaphat.com.vn"


# ── supplier_scorecard ───────────────────────────────────────────────────────────────────
def test_cham_diem_ncc_thieu_quyen_thi_denied(db, seed, cap_quyen, hang):
    assert _hoi(db, seed, "supplier_scorecard", {"product_code": "GA4"}).get("denied") is True
    cap_quyen(seed.u_req_id, "product", scope="all", read=True)      # chỉ product, thiếu supplier
    assert _hoi(db, seed, "supplier_scorecard", {"product_code": "GA4"}).get("denied") is True


def test_cham_diem_ncc_dung_cong_thuc_va_sap_theo_diem(db, seed, cap_quyen, hang):
    _cap_du(seed, cap_quyen)
    out = _hoi(db, seed, "supplier_scorecard", {"product_code": "GA4"})

    assert out["weights"] == {"gia": 40, "on_dinh": 20, "giao_hang": 20, "phap_ly": 20}
    assert out["count"] == 3 and [i["supplier_code"] for i in out["items"]] == ["NX", "NCCB", "NCCC"]
    nx, b, c = out["items"]

    assert nx["parts"] == {"gia": 40.0, "on_dinh": 20.0, "giao_hang": 20.0, "phap_ly": 20.0} and nx["score"] == 100.0
    assert nx["name"] == "Nhà Xuất NX" and nx["url"].startswith("/production/suppliers/")
    assert nx["metrics"]["deliveries"] == {"total": 2, "on_time": 2} and nx["data_gaps"] == []

    #  B: giá 125 → 40 × 100/125 = 32; mua 1/3 lần → 6.7; không lần giao → 0 + thiếu; hợp đồng hết hạn → 5.
    assert b["parts"] == {"gia": 32.0, "on_dinh": 6.7, "giao_hang": 0.0, "phap_ly": 5.0} and b["score"] == 43.7
    assert b["metrics"]["times"] == 1, "dòng mua 400 ngày trước phải nằm ngoài kỳ 12 tháng"
    assert any("giao hàng" in g for g in b["data_gaps"])
    assert any("hết hạn" in r for r in b["reasons"])

    #  C: giá 200 → 20; mua 2/3 lần → 13.3; 1 lần giao trễ → 0/1; không hợp đồng → 0.
    assert c["parts"] == {"gia": 20.0, "on_dinh": 13.3, "giao_hang": 0.0, "phap_ly": 0.0} and c["score"] == 33.3
    assert c["metrics"]["deliveries"] == {"total": 1, "on_time": 0}
    assert any("trễ nhất 5 ngày" in r for r in c["reasons"])
    assert any("hợp đồng" in g for g in c["data_gaps"])

    assert "không tự chọn ncc" in out["note"].lower() and "market_price_search" in out["note"]
    assert out["data_gaps"] == []      # có dữ liệu giao hàng ít nhất một NCC, đơn vị đồng nhất


def test_cham_diem_ncc_khong_co_du_lieu_giao_hang_thi_ghi_thieu(db, seed, cap_quyen, hang):
    _cap_du(seed, cap_quyen)
    db.query(PODelivery).delete()
    db.commit()
    out = _hoi(db, seed, "supplier_scorecard", {"product": "Giấy A4"})
    assert out["count"] == 3 and out["products"] == ["GA4"]
    assert all(i["parts"]["giao_hang"] == 0.0 for i in out["items"])
    assert all(any("chưa có dữ liệu giao hàng" in g for g in i["data_gaps"]) for i in out["items"])
    assert any("Chưa có dữ liệu giao hàng" in g for g in out["data_gaps"])


def test_cham_diem_ncc_thieu_quyen_dmh_hop_dong_thi_chi_bo_trong_cot_do(db, seed, cap_quyen, hang):
    cap_quyen(seed.u_req_id, "product", scope="all", read=True)
    cap_quyen(seed.u_req_id, "supplier", scope="all", read=True)
    out = _hoi(db, seed, "supplier_scorecard", {"product_code": "GA4", "months": 6})
    assert out["count"] == 3
    nx = out["items"][0]
    assert nx["parts"]["gia"] == 40.0 and nx["parts"]["giao_hang"] == 0.0 and nx["parts"]["phap_ly"] == 0.0
    assert any("quyền xem ĐMH" in g for g in nx["data_gaps"]) and any("quyền xem hợp đồng" in g for g in nx["data_gaps"])
    assert any("đơn mua hàng" in g for g in out["data_gaps"]) and any("hợp đồng" in g for g in out["data_gaps"])


def test_cham_diem_ncc_theo_danh_sach_ma_ncc_ke_ca_ncc_chua_ban(db, seed, cap_quyen, hang):
    _cap_du(seed, cap_quyen)
    out = _hoi(db, seed, "supplier_scorecard", {"product_code": "GA4", "supplier_codes": ["NCCB", "NCCX"]})
    codes = [i["supplier_code"] for i in out["items"]]
    assert codes == ["NCCB", "NCCX"]
    b, x = out["items"]
    assert b["parts"]["gia"] == 40.0, "chỉ còn một NCC có giá thì NCC đó rẻ nhất"
    assert any("chưa so được" in r for r in b["reasons"])
    assert x["score"] == 0.0 and any("không có trong danh mục" in g for g in x["data_gaps"])


def test_cham_diem_ncc_khong_ai_ban_thi_goi_y_tim_web(db, seed, cap_quyen, hang):
    _cap_du(seed, cap_quyen)
    out = _hoi(db, seed, "supplier_scorecard", {"product": "máy đào hầm lượng tử"})
    assert out["count"] == 0 and any("market_price_search" in g for g in out["data_gaps"])
    assert "error" in _hoi(db, seed, "supplier_scorecard", {})


# ── Nhóm công cụ + nhãn con ──────────────────────────────────────────────────────────────
@pytest.mark.parametrize("q", ["giá thị trường thép phi 10 hiện nay", "NCC nào tốt nhất cho giấy A4",
                               "nên mua thép của ai", "tìm link mua máy in HP"])
def test_router_chon_nhom_mua_hang_cho_cau_gia_web_va_ncc_tot_nhat(q):
    picked = tr.select(q)
    assert picked is not None and {"market_price_search", "supplier_scorecard"} <= picked


def test_nhan_con_so_y_dinh():
    from app.modules.agent_hub import intent_ledger as il

    assert il.TOOL_SUB["market_price_search"] == il.Sub.LOOKUP_MARKET
    assert il.TOOL_SUB["supplier_scorecard"] == il.Sub.LOOKUP_SUPPLIER
    assert il.SUB_CODES[il.Sub.LOOKUP_MARKET][0] == "tra_cuu.gia_thi_truong"
