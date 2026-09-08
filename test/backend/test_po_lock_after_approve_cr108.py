"""CR-108 (phiếu hỗ trợ TK19082604) — Đơn mua hàng ĐÃ DUYỆT thì khóa nội dung đã duyệt.

Sau khi duyệt, đơn chỉ còn sửa được vài ô phát sinh sau đó (tên trên hóa đơn, ngày dự
kiến có hàng, kho nhận, ghi chú, ngày giao chứng từ cho KT). Muốn đổi mã hàng, số lượng,
đơn giá, VAT hay bất kỳ ô nào của đơn thì phải "Hủy duyệt" để đơn về Nháp rồi gửi duyệt
lại. Chặn ở backend chứ không chỉ khóa ô trên màn hình — gọi thẳng API vẫn phải chặn.
"""
import pytest
from fastapi import HTTPException

from app.modules.payment_request.model import PaymentRequest, PaymentRequestLine
from app.modules.purchase_order.model import POItem, PurchaseOrder
from app.modules.purchase_order.schema import POItemIn, POUpdate
from app.modules.purchase_order.service import (PROG_COMPLETED, PROG_DOC_PENDING,
                                                PROG_NOT_ORDERED, PROG_ORDERED, PROG_PAUSED,
                                                block_clear_misa_in_use,
                                                block_edit_approved_order, unapprove_po)


def _don(db, status="approved", qty_received=0.0, progress_status=PROG_ORDERED,
         misa_code="", status_before_pause=""):
    po = PurchaseOrder(code="PO-CR108", status=status, supplier_code="NCC01",
                       supplier_name="NCC Một", department="Thu mua", vat_rate=0.08,
                       misa_code=misa_code)
    db.add(po)
    db.commit()
    db.refresh(po)
    it = POItem(po_id=po.id, product_code="SP001", product_name="Hàng A", unit="Cái",
                item_group="Nhóm A", qty_order=10, price=1000, vat=8,
                qty_received=qty_received, warehouse_code="KHO1",
                progress_status=progress_status, status_before_pause=status_before_pause)
    db.add(it)
    db.commit()
    db.refresh(it)
    return po, it


def _dong(it, **doi):
    """Dòng hàng gửi lên y như màn hình gửi: đủ các ô, chỉ đổi ô đang thử."""
    base = dict(id=it.id, product_code=it.product_code, product_name=it.product_name,
                unit=it.unit, item_group=it.item_group, qty_order=float(it.qty_order or 0),
                price=float(it.price or 0), vat=float(it.vat or 0),
                warehouse_code=it.warehouse_code or "", note=it.note or "")
    base.update(doi)
    return POItemIn(**base)


# ───────────────────────── Ô của ĐƠN ─────────────────────────
def test_da_duyet_khong_doi_duoc_ncc(db):
    po, it = _don(db)
    with pytest.raises(HTTPException) as e:
        block_edit_approved_order(db, po, POUpdate(supplier_name="NCC Hai", items=[_dong(it)]))
    assert e.value.status_code == 400
    assert "Tên NCC" in e.value.detail
    assert "Hủy duyệt" in e.value.detail


def test_da_duyet_khong_doi_duoc_vat_chung(db):
    po, it = _don(db)
    with pytest.raises(HTTPException) as e:
        block_edit_approved_order(db, po, POUpdate(vat_rate=0.1))
    assert "VAT chung" in e.value.detail


def test_da_duyet_van_cap_nhat_duoc_ho_so_chung_tu(db):
    """document_status có endpoint riêng, sửa được cả khi đơn Hoàn thành — không chặn."""
    po, it = _don(db)
    block_edit_approved_order(db, po, POUpdate(document_status="full", items=[_dong(it)]))


def test_da_duyet_van_sua_duoc_ma_don_misa(db):
    """Kế toán đối chiếu số MISA sau khi đơn đã duyệt — mã đơn MISA phải sửa được sau duyệt."""
    po, it = _don(db)
    block_edit_approved_order(db, po, POUpdate(misa_code="MISA-2026-001", items=[_dong(it)]))


# ───────────────────────── Xóa trắng Mã đơn MISA ─────────────────────────
# Bước 1 của tiến độ dòng đòi đơn có mã MISA, mà auto_advance_line chỉ TIẾN không lùi.
# Xóa trắng ô đó xong dòng kẹt lại ở bậc cao trong khi điều kiện đã hết đúng — trên màn
# hiện ra cảnh "chưa có mã MISA mà dòng đã Chưa gửi ĐMH cho KT" (gặp thật trên PO00358).
@pytest.mark.parametrize("progress_status", [PROG_ORDERED, PROG_DOC_PENDING, PROG_COMPLETED])
def test_khong_xoa_trang_ma_misa_khi_dong_da_tien(db, progress_status):
    po, it = _don(db, misa_code="MISA-001", progress_status=progress_status)
    with pytest.raises(HTTPException) as e:
        block_clear_misa_in_use(db, po, POUpdate(misa_code=""))
    assert e.value.status_code == 400
    assert "Mã đơn MISA" in e.value.detail
    assert "SP001" in e.value.detail            # gọi tên dòng đang kẹt


def test_khong_xoa_trang_ma_misa_khi_dong_tam_ngung_giu_bac_cu(db):
    """Tạm ngưng giữ bậc cũ ở status_before_pause và sẽ quay lại đó khi bấm Tiếp tục."""
    po, it = _don(db, misa_code="MISA-001", progress_status=PROG_PAUSED,
                  status_before_pause=PROG_DOC_PENDING)
    with pytest.raises(HTTPException) as e:
        block_clear_misa_in_use(db, po, POUpdate(misa_code=""))
    assert "Mã đơn MISA" in e.value.detail


def test_van_doi_duoc_ma_misa_sang_ma_khac(db):
    """Gõ nhầm phải sửa được — điều kiện 'có mã' vẫn thỏa nên không có dòng nào kẹt."""
    po, it = _don(db, misa_code="MISA-001", progress_status=PROG_DOC_PENDING)
    block_clear_misa_in_use(db, po, POUpdate(misa_code="MISA-002"))


def test_xoa_trang_ma_misa_khi_chua_dong_nao_tien(db):
    po, it = _don(db, misa_code="MISA-001", progress_status=PROG_NOT_ORDERED)
    block_clear_misa_in_use(db, po, POUpdate(misa_code=""))


def test_dong_da_huy_khong_chan_xoa_ma_misa(db):
    """Hủy đơn nằm ngoài luồng tuần tự, không có bậc để mà kẹt."""
    po, it = _don(db, misa_code="MISA-001", progress_status="cancelled")
    block_clear_misa_in_use(db, po, POUpdate(misa_code=""))


def test_khong_gui_o_misa_thi_khong_dung_toi(db):
    """Màn khác chỉ sửa ghi chú thì payload không có misa_code — đừng chặn oan."""
    po, it = _don(db, misa_code="MISA-001", progress_status=PROG_DOC_PENDING)
    block_clear_misa_in_use(db, po, POUpdate(note="x"))


def test_don_von_chua_co_ma_misa_thi_khong_chan(db):
    """Lưu lại y nguyên: màn gửi misa_code='' trong khi DB cũng rỗng — không phải xóa."""
    po, it = _don(db, misa_code="", progress_status=PROG_DOC_PENDING)
    block_clear_misa_in_use(db, po, POUpdate(misa_code=""))


def test_ma_misa_chi_toan_khoang_trang_coi_nhu_xoa(db):
    po, it = _don(db, misa_code="MISA-001", progress_status=PROG_DOC_PENDING)
    with pytest.raises(HTTPException):
        block_clear_misa_in_use(db, po, POUpdate(misa_code="   "))


# ───────────────────────── Ô của DÒNG HÀNG ─────────────────────────
@pytest.mark.parametrize("doi,label", [
    ({"product_code": "SP999"}, "Mã hàng"),
    ({"product_name": "Hàng B"}, "Tên hàng"),
    ({"unit": "Thùng"}, "ĐVT"),
    ({"qty_order": 20}, "SL đặt NCC"),
    ({"price": 1500}, "Đơn giá"),
    ({"vat": 10}, "VAT (%)"),
])
def test_da_duyet_khoa_o_dong_hang(db, doi, label):
    po, it = _don(db)
    with pytest.raises(HTTPException) as e:
        block_edit_approved_order(db, po, POUpdate(items=[_dong(it, **doi)]))
    assert e.value.status_code == 400
    assert label in e.value.detail
    assert "Hàng A" in e.value.detail          # gọi đúng tên dòng để biết sửa dòng nào


def test_da_duyet_van_sua_duoc_cac_o_phat_sinh_sau_duyet(db):
    """5 ô khách chốt cho sửa + ngày giao chứng từ cho KT (điều kiện của bước tiến độ)."""
    po, it = _don(db)
    block_edit_approved_order(db, po, POUpdate(items=[_dong(
        it, invoice_name="Tên trên hóa đơn", expected_date="2026-09-01",
        warehouse_code="KHO2", note="NCC hẹn lại", document_delivery_date="2026-09-02",
    )]))


def test_da_duyet_khong_them_dong_moi(db):
    po, it = _don(db)
    new = POItemIn(product_code="SP002", product_name="Hàng C", unit="Cái", qty_order=5)
    with pytest.raises(HTTPException) as e:
        block_edit_approved_order(db, po, POUpdate(items=[_dong(it), new]))
    assert "không thêm dòng hàng mới" in e.value.detail


def test_da_duyet_khong_xoa_dong(db):
    po, it = _don(db)
    with pytest.raises(HTTPException) as e:
        block_edit_approved_order(db, po, POUpdate(items=[]))
    assert "không xóa dòng hàng" in e.value.detail


def test_luu_lai_y_nguyen_khong_bao_loi_oan(db):
    """Màn hình gửi nguyên cả đơn mỗi lần Lưu; Decimal/float và None/'' phải coi là bằng nhau."""
    po, it = _don(db)
    block_edit_approved_order(db, po, POUpdate(
        supplier_code="NCC01", supplier_name="NCC Một", department="Thu mua",
        vat_rate=0.08, misa_code="", note="", items=[_dong(it)],
    ))


def test_don_nhap_khong_bi_chan(db):
    po, it = _don(db, status="draft")
    block_edit_approved_order(db, po, POUpdate(supplier_name="NCC Hai",
                                           items=[_dong(it, qty_order=99, price=7)]))


def test_dong_hoan_thanh_khong_chan_them(db):
    """Dòng Hoàn thành đã bị _save_items bỏ qua nguyên dòng — không cần chặn thêm ở đây."""
    po, it = _don(db, progress_status=PROG_COMPLETED)
    block_edit_approved_order(db, po, POUpdate(items=[_dong(it, price=9999)]))


# ───────────────────────── Hủy duyệt ─────────────────────────
def test_huy_duyet_dua_don_ve_nhap(db):
    po, it = _don(db)
    out = unapprove_po(db, po.id, user_id=1, reason="Sai đơn giá")
    assert out.status == "draft"
    assert out.approve_note == "Sai đơn giá"


def test_khong_huy_duyet_don_chua_duyet(db):
    po, it = _don(db, status="draft")
    with pytest.raises(HTTPException) as e:
        unapprove_po(db, po.id, user_id=1, reason="x")
    assert e.value.status_code == 400


def test_khong_huy_duyet_khi_da_nhan_hang(db):
    po, it = _don(db, status="partial", qty_received=3)
    with pytest.raises(HTTPException) as e:
        unapprove_po(db, po.id, user_id=1, reason="x")
    assert "đã nhận hàng" in e.value.detail


def test_khong_huy_duyet_khi_co_dong_hoan_thanh(db):
    po, it = _don(db, progress_status=PROG_COMPLETED)
    with pytest.raises(HTTPException) as e:
        unapprove_po(db, po.id, user_id=1, reason="x")
    assert "Hoàn thành" in e.value.detail


def _yctt(db, po, status="submitted"):
    pr = PaymentRequest(code="YCTT01", status=status)
    db.add(pr)
    db.flush()
    db.add(PaymentRequestLine(request_id=pr.id, po_code=po.code, amount=1000))
    db.commit()
    return pr


def test_khong_huy_duyet_khi_da_co_yeu_cau_thanh_toan(db):
    po, it = _don(db)
    _yctt(db, po)
    with pytest.raises(HTTPException) as e:
        unapprove_po(db, po.id, user_id=1, reason="x")
    assert "yêu cầu thanh toán" in e.value.detail


def test_yctt_da_huy_thi_van_huy_duyet_duoc(db):
    po, it = _don(db)
    _yctt(db, po, status="cancelled")
    assert unapprove_po(db, po.id, user_id=1, reason="x").status == "draft"
