"""bao-CR-511 — hai lỗi YCTT có sẵn trên prod, sửa ngày 28/09/2026.

1. Màn cũ (`frontend/`) bấm Lưu phiếu nháp gửi dòng KHÔNG kèm `offset_amount` → schema
   mặc định 0 → phần cấn trừ tiền treo người khác nhập ở màn mới bị XÓA IM LẶNG.
2. `set_status` không kiểm trạng thái nguồn: phiếu ĐÃ TỪ CHỐI gửi duyệt lại được, phiếu
   ĐÃ CHI ghi chi lần hai được (cộng tiền trả vào công nợ hai lần).
"""
import pytest
from fastapi import HTTPException

from app.modules.payment_request import service as S
from app.modules.payment_request.schema import LineIn, PRequestUpdate

from test_can_tru_khi_duyet_cr260 import _offset_request
from test_tien_treo_cr268 import _payable_of, _po_with_receipt, _prepay_request


def _v1_lines(db, req_id):
    """Đúng khuôn màn cũ gửi lên: đủ ô trừ `offset_amount`."""
    return [LineIn.model_validate({"payable_id": ln.payable_id, "po_code": ln.po_code,
                                   "invoice_no": ln.invoice_no, "invoice_date": ln.invoice_date,
                                   "amount": float(ln.amount)})
            for ln in S.lines_of(db, req_id)]


class TestOffsetKeptWhenNotSent:
    def test_old_screen_save_keeps_offset(self, db, seed):
        _prepay_request(db, seed, po_code="", amount=30_000_000)
        _po_with_receipt(db, seed, code="PO-252", price=10_000_000, qty=5)
        req = _offset_request(db, seed, submit=False)
        S.update_request(db, req.id, PRequestUpdate(note="sửa ở màn cũ",
                                                    lines=_v1_lines(db, req.id)), seed.u_req_id)
        assert float(S.lines_of(db, req.id)[0].offset_amount) == 30_000_000

    def test_explicit_zero_still_clears_offset(self, db, seed):
        """Màn mới gửi 0 tường minh = người dùng muốn bỏ cấn trừ — phải xóa thật."""
        _prepay_request(db, seed, po_code="", amount=30_000_000)
        _po_with_receipt(db, seed, code="PO-252", price=10_000_000, qty=5)
        req = _offset_request(db, seed, submit=False)
        lines = _v1_lines(db, req.id)
        lines[0].offset_amount = 0
        S.update_request(db, req.id, PRequestUpdate(lines=lines), seed.u_req_id)
        assert float(S.lines_of(db, req.id)[0].offset_amount) == 0

    def test_explicit_new_value_wins(self, db, seed):
        _prepay_request(db, seed, po_code="", amount=30_000_000)
        _po_with_receipt(db, seed, code="PO-252", price=10_000_000, qty=5)
        req = _offset_request(db, seed, submit=False)
        lines = _v1_lines(db, req.id)
        lines[0].offset_amount = 10_000_000
        S.update_request(db, req.id, PRequestUpdate(lines=lines), seed.u_req_id)
        assert float(S.lines_of(db, req.id)[0].offset_amount) == 10_000_000

    def test_new_line_without_offset_gets_zero(self, db, seed):
        """Dòng MỚI thêm ở màn cũ không có gì để giữ lại — phải là 0, không mượn của dòng khác."""
        _prepay_request(db, seed, po_code="", amount=30_000_000)
        _po_with_receipt(db, seed, code="PO-252", price=10_000_000, qty=5)
        req = _offset_request(db, seed, submit=False)
        lines = _v1_lines(db, req.id) + [LineIn.model_validate(
            {"po_code": "PO-999", "invoice_no": "HD-999", "amount": 1_000_000})]
        S.update_request(db, req.id, PRequestUpdate(lines=lines), seed.u_req_id)
        by_po = {ln.po_code: float(ln.offset_amount) for ln in S.lines_of(db, req.id)}
        assert by_po == {"PO-252": 30_000_000, "PO-999": 0}


class TestStatusTransitions:
    def test_rejected_cannot_be_resubmitted(self, db, seed):
        _po_with_receipt(db, seed, code="PO-252", price=10_000_000, qty=5)
        req = _offset_request(db, seed, offset=0)                      # submitted
        S.set_status(db, req.id, "cancelled", seed.u_req_id, "sai số")
        with pytest.raises(HTTPException) as err:
            S.set_status(db, req.id, "submitted", seed.u_req_id)
        assert err.value.status_code == 400
        assert S.get_request(db, req.id).status == "cancelled"

    def test_paid_cannot_be_paid_twice(self, db, seed):
        _po_with_receipt(db, seed, code="PO-252", price=10_000_000, qty=5)
        req = _offset_request(db, seed, offset=0)
        S.set_status(db, req.id, "approved", seed.u_req_id)
        S.set_status(db, req.id, "paid", seed.u_req_id)
        paid_once = float(_payable_of(db, "PO-252").paid_amount)
        with pytest.raises(HTTPException):
            S.set_status(db, req.id, "paid", seed.u_req_id)
        assert float(_payable_of(db, "PO-252").paid_amount) == paid_once

    @pytest.mark.parametrize("target", ["approved", "cancelled", "paid"])
    def test_draft_cannot_skip_review(self, db, seed, target):
        _po_with_receipt(db, seed, code="PO-252", price=10_000_000, qty=5)
        req = _offset_request(db, seed, offset=0, submit=False)
        with pytest.raises(HTTPException):
            S.set_status(db, req.id, target, seed.u_req_id)
        assert S.get_request(db, req.id).status == "draft"

    def test_misa_import_path_may_pay_draft_directly(self, db, seed):
        """Công cụ nhập Misa tạo phiếu rồi ghi Đã chi ngay — đường duy nhất được bỏ qua duyệt."""
        _po_with_receipt(db, seed, code="PO-252", price=10_000_000, qty=5)
        req = _offset_request(db, seed, offset=0, submit=False)
        S.set_status(db, req.id, "paid", seed.u_req_id, allow_any_source=True)
        assert S.get_request(db, req.id).status == "paid"
