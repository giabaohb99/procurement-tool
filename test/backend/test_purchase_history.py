"""Lịch sử mua hàng — snapshot ghi ĐÚNG 1 LẦN khi dòng ĐMH vào "Hoàn thành".

Bảng tab_purchase_history là dữ liệu trùng lặp có chủ đích của ĐMH, nên thứ dễ hỏng nhất là
điểm ghi: ghi sót (dòng hoàn thành mà không có lịch sử), ghi trùng (1 dòng ra 2 record), hoặc
ghi nhầm dòng chưa hoàn thành. Test khóa đúng 3 rủi ro đó + không lẫn dữ liệu giữa các SP/NCC.
"""
import json

from app.modules.company.model import Company
from app.modules.purchase_history.model import PurchaseHistory
from app.modules.purchase_history.service import list_history, snapshot_line
from app.modules.purchase_order.model import POItem, PurchaseOrder
from app.modules.purchase_order.service import (PROG_COMPLETED, PROG_DOC_SENT, PROG_ORDERED,
                                                auto_advance_line)

PG = {"offset": 0, "limit": 50}


def _po(db, **doi):
    base = dict(code="PO0001", pr_code="PYC001", misa_code="MISA1", company_id=0,
                supplier_code="NCC01", supplier_name="NCC Một", order_date="2026-08-06",
                nspt="Nguyễn Thanh Tiên", payment_terms="Công nợ 30 ngày", is_urgent=True,
                note="ghi chú đơn", department="Mua hàng", status="approved")
    base.update(doi)
    po = PurchaseOrder(**base)
    db.add(po)
    db.commit()
    db.refresh(po)
    return po


def _item(db, po, **doi):
    base = dict(po_id=po.id, product_code="SP001", product_name="Hàng A", unit="Cái",
                qty_order=2000, price=156, vat=8, amount=336960, qty_received=2000,
                invoice_no="HD001", progress_status=PROG_DOC_SENT)
    base.update(doi)
    it = POItem(**base)
    db.add(it)
    db.commit()
    db.refresh(it)
    return it


# ── Nội dung snapshot ──────────────────────────────────────────────────────────
def test_snapshot_luu_du_thong_tin_chung_va_dong_hang(db):
    db.add(Company(id=7, code="DEGO", name="CÔNG TY TNHH DEGO HOLDING"))
    db.commit()
    po = _po(db, company_id=7)
    it = _item(db, po)

    snapshot_line(db, po, it)
    db.commit()

    h = db.query(PurchaseHistory).one()
    # Cột phẳng — thứ hiển thị/lọc/sort trên bảng
    assert (h.po_code, h.product_code, h.supplier_code) == ("PO0001", "SP001", "NCC01")
    assert h.order_date == "2026-08-06"
    assert h.company_name == "CÔNG TY TNHH DEGO HOLDING"   # denormalize từ tab_company
    assert (float(h.qty_order), float(h.price), float(h.amount)) == (2000, 156, 336960)
    assert h.completed_at                                   # có ngày chốt
    # Phần "Thông tin chung" còn lại nằm trong JSON
    extra = json.loads(h.extra)
    assert extra["pr_code"] == "PYC001"
    assert extra["misa_code"] == "MISA1"
    assert extra["nspt"] == "Nguyễn Thanh Tiên"
    assert extra["payment_terms"] == "Công nợ 30 ngày"
    assert extra["is_urgent"] is True
    assert extra["po_note"] == "ghi chú đơn"
    assert extra["invoice_no"] == "HD001"


def test_don_2_dong_thi_ra_2_record(db):
    po = _po(db)
    a = _item(db, po, product_code="SP001", product_name="Hàng A")
    b = _item(db, po, product_code="SP002", product_name="Hàng B", price=200)

    snapshot_line(db, po, a)
    snapshot_line(db, po, b)
    db.commit()

    assert db.query(PurchaseHistory).count() == 2
    assert {h.product_code for h in db.query(PurchaseHistory)} == {"SP001", "SP002"}


def test_goi_lai_khong_ghi_trung(db):
    po = _po(db)
    it = _item(db, po)
    snapshot_line(db, po, it)
    db.commit()

    assert snapshot_line(db, po, it) is None      # idempotent
    db.commit()
    assert db.query(PurchaseHistory).count() == 1


# ── Điểm ghi: auto_advance_line ────────────────────────────────────────────────
def test_dong_vao_hoan_thanh_thi_tu_ghi_lich_su(db, monkeypatch):
    """auto_advance_line là chỗ duy nhất dòng vào "Hoàn thành" → phải tự chốt lịch sử."""
    import app.modules.purchase_order.service as po_service
    monkeypatch.setattr(po_service, "highest_satisfied_step", lambda *a, **k: 5)  # → "Hoàn thành"

    po = _po(db)
    it = _item(db, po)
    assert auto_advance_line(db, po, it) is True
    db.commit()

    assert it.progress_status == PROG_COMPLETED
    assert db.query(PurchaseHistory).count() == 1


def test_dong_chua_hoan_thanh_thi_khong_ghi(db, monkeypatch):
    import app.modules.purchase_order.service as po_service
    monkeypatch.setattr(po_service, "highest_satisfied_step", lambda *a, **k: 2)  # "Đã nhận hàng"

    po = _po(db)
    it = _item(db, po, progress_status=PROG_ORDERED)
    auto_advance_line(db, po, it)
    db.commit()

    assert db.query(PurchaseHistory).count() == 0


def test_dong_da_hoan_thanh_chay_lai_khong_ghi_them(db, monkeypatch):
    """Sau reopen ĐMH, auto_advance_line vẫn chạy lại — dòng đã ở điểm cuối phải bị bỏ qua."""
    import app.modules.purchase_order.service as po_service
    monkeypatch.setattr(po_service, "highest_satisfied_step", lambda *a, **k: 5)

    po = _po(db)
    it = _item(db, po)
    auto_advance_line(db, po, it)
    db.commit()

    assert auto_advance_line(db, po, it) is False   # điểm cuối → bỏ qua
    db.commit()
    assert db.query(PurchaseHistory).count() == 1


# ── Truy vấn ───────────────────────────────────────────────────────────────────
def test_loc_theo_ma_sp_va_ma_ncc_khong_lan_nhau(db):
    po1 = _po(db, code="PO0001", supplier_code="NCC01", order_date="2026-01-01")
    po2 = _po(db, code="PO0002", supplier_code="NCC02", order_date="2026-05-05")
    snapshot_line(db, po1, _item(db, po1, product_code="SP001"))
    snapshot_line(db, po2, _item(db, po2, product_code="SP001"))
    snapshot_line(db, po2, _item(db, po2, product_code="SP002"))
    db.commit()

    total, items = list_history(db, PG, product_code="SP001")
    assert total == 2
    assert {i.supplier_code for i in items} == {"NCC01", "NCC02"}

    total, items = list_history(db, PG, supplier_code="NCC02")
    assert total == 2
    assert {i.product_code for i in items} == {"SP001", "SP002"}


def test_search_tim_theo_ma_po_va_ten_ncc(db):
    """Ô tìm kiếm của popup chọn giá — lọc trong phạm vi mã SP, không thoát ra ngoài."""
    po1 = _po(db, code="PO_ALPHA", supplier_code="NCC01", supplier_name="NCC Một")
    po2 = _po(db, code="PO_BETA", supplier_code="NCC02", supplier_name="Bao bì Đông Tây")
    snapshot_line(db, po1, _item(db, po1, product_code="SP001"))
    snapshot_line(db, po2, _item(db, po2, product_code="SP001"))
    snapshot_line(db, po2, _item(db, po2, product_code="SP002"))
    db.commit()

    total, items = list_history(db, PG, product_code="SP001", search="ALPHA")
    assert (total, [i.po_code for i in items]) == (1, ["PO_ALPHA"])

    # Tìm theo tên NCC có dấu tiếng Việt
    total, items = list_history(db, PG, product_code="SP001", search="Đông Tây")
    assert (total, [i.po_code for i in items]) == (1, ["PO_BETA"])

    # Từ khóa khớp SP002 nhưng đang lọc SP001 → không được lọt ra
    total, _ = list_history(db, PG, product_code="SP001", search="KHONG_TON_TAI")
    assert total == 0


def test_sap_xep_moi_nhat_truoc(db):
    po_cu = _po(db, code="PO_CU", order_date="2025-01-01")
    po_moi = _po(db, code="PO_MOI", order_date="2026-08-06")
    snapshot_line(db, po_cu, _item(db, po_cu))
    snapshot_line(db, po_moi, _item(db, po_moi))
    db.commit()

    _, items = list_history(db, PG, product_code="SP001")
    assert [i.po_code for i in items] == ["PO_MOI", "PO_CU"]


# ── Che NCC với người không có quyền `supplier.read` ───────────────────────────
# Popup "Lịch sử mua hàng gần nhất" mở được từ YÊU CẦU MUA HÀNG, nơi người yêu cầu chỉ cần
# `product.read` — nhưng NCC là thông tin riêng của khối thu mua. Che ở giao diện là chưa đủ:
# gọi thẳng API vẫn đọc được, và ô tìm kiếm vẫn dò ra được ai bán mã hàng đó.
def test_khong_co_quyen_ncc_thi_khong_tim_duoc_theo_ten_ncc(db):
    po1 = _po(db, code="PO_ALPHA", supplier_code="NCC01", supplier_name="NCC Một")
    po2 = _po(db, code="PO_BETA", supplier_code="NCC02", supplier_name="Bao bì Đông Tây")
    snapshot_line(db, po1, _item(db, po1, product_code="SP001"))
    snapshot_line(db, po2, _item(db, po2, product_code="SP001"))
    db.commit()

    # Có quyền: gõ tên NCC ra đúng 1 dòng (mốc để so sánh)
    total, _ = list_history(db, PG, product_code="SP001", search="Đông Tây")
    assert total == 1

    # Không quyền: tên NCC không còn là vế tìm kiếm -> không suy ngược ra được NCC nào
    total, _ = list_history(db, PG, product_code="SP001", search="Đông Tây", search_by_supplier=False)
    assert total == 0

    # Các vế còn lại (mã PO / tên SP / công ty) vẫn tìm bình thường
    total, items = list_history(db, PG, product_code="SP001", search="ALPHA", search_by_supplier=False)
    assert (total, [i.po_code for i in items]) == (1, ["PO_ALPHA"])


def test_payload_xoa_ten_va_ma_ncc_khi_khong_co_quyen(db):
    from app.modules.purchase_history.controller import _payload

    po = _po(db, supplier_code="NCC01", supplier_name="NCC Một")
    snapshot_line(db, po, _item(db, po))
    db.commit()
    items = db.query(PurchaseHistory).all()

    co = _payload(1, items)["items"][0]
    assert (co["supplier_code"], co["supplier_name"]) == ("NCC01", "NCC Một")

    khong = _payload(1, items, show_supplier=False)["items"][0]
    assert (khong["supplier_code"], khong["supplier_name"]) == ("", "")
    # Chỉ che NCC — phần giá/số lượng vẫn phải còn để người yêu cầu tham chiếu
    assert khong["po_code"] == "PO0001" and khong["price"]
