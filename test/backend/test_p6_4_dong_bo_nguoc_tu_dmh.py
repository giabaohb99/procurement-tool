"""P6-4 (bao-CR-282) — đồng bộ ngược qty_ordered · qty_received · line_status từ ĐMH
về tab_survey_request_line (doc/erp/12 §P6-4). Đây là chỗ doc gọi là "dễ vỡ nhất của
cả kế hoạch" nên test viết TRƯỚC khi sửa; luật chép từ
purchase_request.service.sync_from_purchase_orders (khớp theo product_code):

- Chỉ tính ĐMH đã duyệt trở đi (bỏ nháp/chờ duyệt/bị trả lại/từ chối/hủy).
- Dòng ĐMH progress "cancelled": không cộng SL; "paused": dùng mức trước khi tạm ngưng.
- Mã có đơn (kể cả Nháp) nhưng chưa đặt -> "not_ordered"; đã đặt -> "ordered";
  nhận một phần -> "received"; mọi dòng ĐMH xong -> "completed" (= LS_COMPLETED,
  cùng chuỗi -> tiến độ dòng ra Hoàn thành).
- KHÁC YCMH ở ba chỗ: (1) dòng mã RỖNG bỏ qua hẳn (không có khóa để khớp);
  (2) dòng KHÔNG có ĐMH nào để yên (đời sống trước-PO của YCBG dùng "" có nghĩa);
  (3) "resurvey"/"confirmed" là mã CỦA NGƯỜI YÊU CẦU — sync chỉ ghi SL, không được
  giẫm (dòng đang chốt lại để mua lại mà bị sync đè là gãy chu trình mua lại).
"""
import pytest
from fastapi import HTTPException

from app.modules.purchase_order import service as po_service
from app.modules.purchase_order.model import PODelivery, POItem, PurchaseOrder
from app.modules.purchase_request.model import PurchaseRequest
from app.modules.survey_request import line_state, service
from app.modules.survey_request.model import (LS_CONFIRMED, LS_RESURVEY,
                                              SurveyRequest, SurveyRequestLine,
                                              SurveyRequestOption,
                                              SurveyRequestPr)


def _sr(db, status: str = "pr_created", code: str = "YCBG-P64"):
    s = SurveyRequest(code=code, status=status)
    db.add(s)
    db.commit()
    return s


def _line(db, sid: int, product_code: str = "VT-P64-01", **kw):
    ln = SurveyRequestLine(survey_request_id=sid, item_group="Thùng",
                           product_code=product_code,
                           request_qty=kw.pop("request_qty", 10), **kw)
    db.add(ln)
    db.commit()
    return ln


def _po(db, survey_code: str, status: str = "approved", code: str = ""):
    po = PurchaseOrder(code=code or f"PO-P64-{status}", survey_code=survey_code,
                       status=status)
    db.add(po)
    db.commit()
    return po


def _po_item(db, po_id: int, product_code: str = "VT-P64-01", qty: float = 7,
             progress: str = "ordered", **kw):
    it = POItem(po_id=po_id, product_code=product_code, qty_order=qty,
                progress_status=progress, **kw)
    db.add(it)
    db.commit()
    return it


def _delivery(db, item, qty: float):
    db.add(PODelivery(po_id=item.po_id, po_item_id=item.id, received_qty=qty))
    db.commit()


# ───────────────────────── suy trạng thái + cộng SL theo mã ─────────────────────────

def test_po_nhap_ra_not_ordered_va_chua_cong_sl(db, seed):
    s = _sr(db)
    ln = _line(db, s.id)
    po = _po(db, s.code, status="draft")
    _po_item(db, po.id, progress="not_ordered")

    service.sync_lines_from_purchase_orders(db, s.code)

    db.refresh(ln)
    assert ln.line_status == "not_ordered", "có đơn (kể cả Nháp) là phải thấy 'Chưa đặt hàng'"
    assert float(ln.qty_ordered) == 0, "đơn Nháp chưa phải cam kết — không cộng SL"


def test_da_dat_ra_ordered_va_cong_sl_dat(db, seed):
    s = _sr(db)
    ln = _line(db, s.id)
    po = _po(db, s.code)
    _po_item(db, po.id, qty=7, progress="ordered")

    service.sync_lines_from_purchase_orders(db, s.code)

    db.refresh(ln)
    assert ln.line_status == "ordered"
    assert float(ln.qty_ordered) == 7 and float(ln.qty_received) == 0


def test_nhan_mot_phan_ra_received_va_cong_sl_nhan(db, seed):
    s = _sr(db)
    ln = _line(db, s.id)
    po = _po(db, s.code, status="partial")
    it = _po_item(db, po.id, qty=7, progress="received")
    _delivery(db, it, 3)

    service.sync_lines_from_purchase_orders(db, s.code)

    db.refresh(ln)
    assert ln.line_status == "received"
    assert float(ln.qty_ordered) == 7 and float(ln.qty_received) == 3


def test_moi_dong_xong_ra_completed_va_tien_do_hoan_thanh(db, seed):
    s = _sr(db)
    ln = _line(db, s.id)
    po = _po(db, s.code, status="completed")
    it = _po_item(db, po.id, qty=7, progress="completed")
    _delivery(db, it, 7)

    service.sync_lines_from_purchase_orders(db, s.code)

    db.refresh(ln)
    assert ln.line_status == "completed"
    # "completed" cùng chuỗi LS_COMPLETED -> tiến độ dòng khép lại thành Hoàn thành
    assert line_state.progress_state(ln, False, 1) == line_state.STATE_DONE


def test_mua_lai_cong_don_va_lay_muc_kem_tien_nhat(db, seed):
    """1 dòng lên đơn 2 lần (mua lại): SL cộng dồn cả hai, trạng thái theo đơn KÉM nhất."""
    s = _sr(db)
    ln = _line(db, s.id)
    po1 = _po(db, s.code, status="completed", code="PO-P64-A")
    it1 = _po_item(db, po1.id, qty=7, progress="completed")
    _delivery(db, it1, 7)
    po2 = _po(db, s.code, status="approved", code="PO-P64-B")
    _po_item(db, po2.id, qty=5, progress="ordered")

    service.sync_lines_from_purchase_orders(db, s.code)

    db.refresh(ln)
    assert ln.line_status == "received", "đợt cũ đã nhận đủ nhưng đợt mới chưa xong -> chưa Hoàn thành"
    assert float(ln.qty_ordered) == 12 and float(ln.qty_received) == 7


def test_tam_ngung_dung_muc_truoc_khi_ngung(db, seed):
    s = _sr(db)
    ln = _line(db, s.id)
    po = _po(db, s.code)
    _po_item(db, po.id, qty=7, progress="paused", status_before_pause="ordered")

    service.sync_lines_from_purchase_orders(db, s.code)

    db.refresh(ln)
    assert ln.line_status == "ordered"
    assert float(ln.qty_ordered) == 7


def test_huy_het_dong_dmh_ra_cancelled_khong_cong_sl(db, seed):
    s = _sr(db)
    ln = _line(db, s.id)
    po = _po(db, s.code)
    _po_item(db, po.id, qty=7, progress="cancelled")

    service.sync_lines_from_purchase_orders(db, s.code)

    db.refresh(ln)
    assert ln.line_status == "cancelled"
    assert float(ln.qty_ordered) == 0 and float(ln.qty_received) == 0


# ───────────────────── ba chỗ KHÁC YCMH: mã rỗng · không đơn · mã người YC ─────────────────────

def test_dong_ma_rong_bo_qua_han(db, seed):
    """Không có mã thì không có khóa để khớp — 2 dòng mã rỗng mà cộng chung là sai gấp đôi."""
    s = _sr(db)
    ln = _line(db, s.id, product_code="", line_status=LS_RESURVEY)
    po = _po(db, s.code)
    _po_item(db, po.id, product_code="", qty=7, progress="ordered")

    service.sync_lines_from_purchase_orders(db, s.code)

    db.refresh(ln)
    assert ln.line_status == LS_RESURVEY and float(ln.qty_ordered) == 0


def test_dong_khong_co_don_nao_de_yen(db, seed):
    """Dòng chưa từng lên đơn: đời sống trước-PO (chưa xác định/khảo sát lại) phải để nguyên."""
    s = _sr(db)
    ln = _line(db, s.id, product_code="VT-KHAC", line_status=LS_RESURVEY)
    po = _po(db, s.code)
    _po_item(db, po.id, product_code="VT-P64-01", qty=7, progress="ordered")

    service.sync_lines_from_purchase_orders(db, s.code)

    db.refresh(ln)
    assert ln.line_status == LS_RESURVEY and float(ln.qty_ordered) == 0


def test_khong_giam_len_ma_nguoi_yeu_cau_dang_giu(db, seed):
    """Dòng đang 'confirmed' (chốt lại để MUA LẠI) hay 'resurvey': sync chỉ ghi SL,
    KHÔNG được đè trạng thái — đè là gãy chu trình mua lại giữa chừng."""
    s = _sr(db)
    for owned in (LS_CONFIRMED, LS_RESURVEY):
        ln = _line(db, s.id, product_code=f"VT-{owned}", line_status=owned)
        po = _po(db, s.code, code=f"PO-{owned}")
        _po_item(db, po.id, product_code=f"VT-{owned}", qty=7, progress="ordered")

        service.sync_lines_from_purchase_orders(db, s.code)

        db.refresh(ln)
        assert ln.line_status == owned, f"sync không được giẫm mã người YC ({owned})"
        assert float(ln.qty_ordered) == 7, "SL thì vẫn phải tươi"


# ───────────────────── móc gọi từ nghiệp vụ ĐMH + trạng thái phiếu ─────────────────────

def test_tao_don_xong_dong_ra_not_ordered(db, seed):
    """create_pos_from_confirmed phải tự sync cuối hàm: dòng vừa lên đơn hiện ngay
    'Chưa đặt hàng' (đối xứng CR-074 bên YCMH) thay vì nằm ở '' vô danh."""
    s = _sr(db, status="survey_done")
    ln = _line(db, s.id)
    o = SurveyRequestOption(survey_request_line_id=ln.id, public_id=1,
                            supplier_code="NCC-A", is_chosen=True,
                            system_product_code="VT-P64-01")
    db.add(o)
    db.commit()
    service.confirm_line_option(db, s.id, ln.id, True, user_id=1)

    service.create_pos_from_confirmed(db, s.id, user_id=1)

    db.refresh(ln)
    assert ln.line_status == "not_ordered"
    assert ln.po_code, "vẫn phải ghi ĐMH gần nhất"


def test_nghiep_vu_dmh_keo_sync_chay(db, seed):
    """Đổi trạng thái ĐƠN qua service ĐMH phải kéo sync về YCBG (móc _sync_survey)."""
    s = _sr(db)
    ln = _line(db, s.id)
    po = _po(db, s.code, status="draft")
    _po_item(db, po.id, qty=7, progress="ordered")

    po_service.set_status(db, po.id, "approved", user_id=1)

    db.refresh(ln)
    assert ln.line_status == "ordered" and float(ln.qty_ordered) == 7


def test_phieu_tu_hoan_thanh_khi_moi_don_xong(db, seed):
    s = _sr(db)
    ln = _line(db, s.id)
    po = _po(db, s.code, status="completed")
    it = _po_item(db, po.id, qty=7, progress="completed")
    _delivery(db, it, 7)

    service.sync_lines_from_purchase_orders(db, s.code)

    db.refresh(s)
    assert s.status == "done"


def test_phieu_chua_hoan_thanh_khi_con_don_dang_chay(db, seed):
    s = _sr(db)
    _line(db, s.id)
    po1 = _po(db, s.code, status="completed", code="PO-P64-A")
    _po_item(db, po1.id, qty=7, progress="completed")
    po2 = _po(db, s.code, status="approved", code="PO-P64-B")
    _po_item(db, po2.id, product_code="VT-P64-02", qty=5, progress="ordered")

    service.sync_lines_from_purchase_orders(db, s.code)

    db.refresh(s)
    assert s.status == "pr_created"


def test_nguon_kep_ycmh_chua_xong_thi_chua_done(db, seed):
    """P6-5 hai nguồn cùng tồn tại: phiếu vừa có YCMH cũ vừa có ĐMH thẳng — mọi ĐMH
    xong nhưng YCMH còn chạy thì CHƯA được tự Hoàn thành (và chiều ngược lại y vậy)."""
    s = _sr(db)
    ln = _line(db, s.id)
    po = _po(db, s.code, status="completed")
    _po_item(db, po.id, qty=7, progress="completed")
    pr = PurchaseRequest(code="PYC-P64-01", status="processing")
    db.add(pr)
    db.commit()
    db.add(SurveyRequestPr(survey_request_id=s.id, survey_request_line_id=ln.id,
                           pr_id=pr.id, pr_code=pr.code))
    db.commit()

    service.sync_lines_from_purchase_orders(db, s.code)
    db.refresh(s)
    assert s.status == "pr_created", "YCMH nguồn còn chạy — chưa được done"

    # Chiều ngược: YCMH xong nhưng ĐMH thẳng còn chạy -> auto_complete_from_pr cũng phải đứng
    pr.status = "completed"
    po.status = "approved"
    db.commit()
    service.auto_complete_from_pr(db, pr.id, user_id=1)
    db.refresh(s)
    assert s.status == "pr_created", "ĐMH thẳng còn chạy — auto_complete_from_pr phải đứng lại"
