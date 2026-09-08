"""
test_can_tru_khi_duyet_cr260.py — CR-260: CẤN TRỪ tiền treo ghi trên dòng YCTT,
THỰC THI đúng lúc DUYỆT (không còn trừ ngay lúc bấm tạo như CR-270).

Luật nghiệp vụ:
1. `offset_amount` trên dòng phiếu chỉ là Ý ĐỊNH lúc lập — nháp sửa/xóa vô hại,
   công nợ và tiền treo KHÔNG bị đụng chừng nào phiếu chưa được duyệt.
2. Bấm DUYỆT mới thực thi (apply_line_offsets): trừ treo cấp NCC theo FIFO phiếu cũ
   trước, cộng vào paid_amount của khoản nợ khớp với dòng.
3. Lúc duyệt mà treo không còn đủ (đã bị dùng nơi khác trong lúc chờ) hoặc nợ đã
   được trả bớt -> CHẶN DUYỆT với thông báo rõ, không tự đổi số; phiếu vẫn Chờ duyệt.
4. Phiếu trả trước (prepay=1) SINH ra treo nên cấm mang offset — chặn từ lúc gửi duyệt.
5. Trần cứng min(treo, nợ) giữ nguyên CR-268 — không bao giờ đẩy công nợ âm.
"""
import pytest
from fastapi import HTTPException

from app.modules.payment_request import service as S
from app.modules.payment_request.schema import LineIn, PRequestCreate

from test_tien_treo_cr268 import _hang, _payable_of, _po_with_receipt, _prepay_request


def _offset_request(db, seed, *, amount=20_000_000, offset=30_000_000,
                    po_code="PO-252", invoice_no="HD-252", submit=True):
    """Phiếu THƯỜNG (prepay=0) mang phần cấn trừ trên dòng — đường CR-260."""
    data = PRequestCreate(request_date="2026-09-02", prepay=0, supplier_code="NX",
                          company_id=seed.company_id, source_type="goods",
                          lines=[LineIn(po_code=po_code, invoice_no=invoice_no,
                                        amount=amount, offset_amount=offset)])
    req = S.create_requests(db, data, seed.u_req_id)[0]
    if submit:
        S.set_status(db, req.id, "submitted", seed.u_req_id)
    return req


class TestYDinhTrenNhap:
    def test_nhap_mang_offset_khong_dung_cong_no(self, db, seed):
        """Đúng cái đại ca vướng ở CR-270: mới là nháp thì KHÔNG được trừ đồng nào."""
        _prepay_request(db, seed, po_code="", amount=30_000_000)
        _po_with_receipt(db, seed, code="PO-252", price=10_000_000, qty=5)  # nợ 50tr
        req = _offset_request(db, seed, submit=False)
        assert float(S.lines_of(db, req.id)[0].offset_amount) == 30_000_000
        assert float(_payable_of(db, "PO-252").paid_amount) == 0
        assert _hang(db, "")["total"] == 30_000_000

    def test_xoa_nhap_vo_hai(self, db, seed):
        _prepay_request(db, seed, po_code="", amount=30_000_000)
        _po_with_receipt(db, seed, code="PO-252", price=10_000_000, qty=5)
        req = _offset_request(db, seed, submit=False)
        S.delete_request(db, req.id, seed.u_req_id)
        assert float(_payable_of(db, "PO-252").paid_amount) == 0
        assert _hang(db, "")["total"] == 30_000_000

    def test_dong_offset_phu_het_no_khong_bi_autofill_lai(self, db, seed):
        """amount=0 + offset>0 là CỐ Ý (treo phủ hết) — autofill không được điền lại nợ."""
        _prepay_request(db, seed, po_code="", amount=50_000_000)
        _po_with_receipt(db, seed, code="PO-252", price=10_000_000, qty=5)  # nợ 50tr
        req = _offset_request(db, seed, amount=0, offset=50_000_000, submit=False)
        ln = S.lines_of(db, req.id)[0]
        assert float(ln.amount) == 0 and float(ln.offset_amount) == 50_000_000


class TestThucThiKhiDuyet:
    def test_duyet_moi_tru_that_va_chi_not_phan_con_lai(self, db, seed):
        """Kịch bản chuẩn: treo 30tr + nợ 50tr -> phiếu chi 20tr, cấn trừ 30tr."""
        _prepay_request(db, seed, po_code="", amount=30_000_000)
        _po_with_receipt(db, seed, code="PO-252", price=10_000_000, qty=5)
        req = _offset_request(db, seed)                      # submitted
        assert float(_payable_of(db, "PO-252").paid_amount) == 0   # chờ duyệt: chưa trừ
        S.set_status(db, req.id, "approved", seed.u_req_id)
        p = _payable_of(db, "PO-252")
        assert float(p.paid_amount) == 30_000_000 and float(p.remaining) == 20_000_000
        assert _hang(db, "")["total"] == 0                   # treo đã tiêu hết
        S.set_status(db, req.id, "paid", seed.u_req_id)
        p = _payable_of(db, "PO-252")
        assert float(p.remaining) == 0 and p.status == "paid"

    def test_dong_offset_phu_het_no_duyet_xong_tat_toan(self, db, seed):
        _prepay_request(db, seed, po_code="", amount=50_000_000)
        _po_with_receipt(db, seed, code="PO-252", price=10_000_000, qty=5)
        req = _offset_request(db, seed, amount=0, offset=50_000_000)
        S.set_status(db, req.id, "approved", seed.u_req_id)
        p = _payable_of(db, "PO-252")
        assert float(p.remaining) == 0 and p.status == "paid"

    def test_treo_an_theo_phieu_cu_truoc(self, db, seed):
        r1 = _prepay_request(db, seed, po_code="", amount=8_000_000)
        r2 = _prepay_request(db, seed, po_code="", amount=8_000_000)
        _po_with_receipt(db, seed, code="PO-252", price=10_000_000, qty=5)
        req = _offset_request(db, seed, amount=40_000_000, offset=10_000_000)
        S.set_status(db, req.id, "approved", seed.u_req_id)
        assert S.line_hanging(S.lines_of(db, r1.id)[0]) == 0          # phiếu cũ ăn trước
        assert S.line_hanging(S.lines_of(db, r2.id)[0]) == 6_000_000

    def test_phieu_khong_offset_duyet_nhu_cu(self, db, seed):
        """offset=0 thì DUYỆT không đụng công nợ — luồng cũ nguyên vẹn."""
        _po_with_receipt(db, seed, code="PO-252", price=10_000_000, qty=5)
        req = _offset_request(db, seed, amount=20_000_000, offset=0)
        S.set_status(db, req.id, "approved", seed.u_req_id)
        assert float(_payable_of(db, "PO-252").paid_amount) == 0


class TestChanDuyetKhiSoDaDoi:
    def test_treo_bi_dung_noi_khac_trong_luc_cho_thi_chan(self, db, seed):
        """Chờ duyệt mà kế toán đã cấn tay treo vào đơn khác -> duyệt phải CHẶN."""
        _prepay_request(db, seed, po_code="", amount=30_000_000)
        _po_with_receipt(db, seed, code="PO-252", price=10_000_000, qty=5)
        _po_with_receipt(db, seed, code="PO-253", price=10_000_000, qty=5)
        req = _offset_request(db, seed)                      # định cấn 30tr vào PO-252
        p_khac = _payable_of(db, "PO-253")
        S.offset_supplier_hanging(db, p_khac, 25_000_000, seed.u_req_id)  # treo còn 5tr
        with pytest.raises(HTTPException) as e:
            S.set_status(db, req.id, "approved", seed.u_req_id)
        assert "vượt tiền treo" in e.value.detail
        req = S.get_request(db, req.id)
        assert req.status == "submitted"                     # phiếu vẫn Chờ duyệt
        assert float(_payable_of(db, "PO-252").paid_amount) == 0   # không nửa vời

    def test_no_da_tra_bot_trong_luc_cho_thi_chan(self, db, seed):
        _prepay_request(db, seed, po_code="", amount=30_000_000)
        _po_with_receipt(db, seed, code="PO-252", price=10_000_000, qty=5)
        req = _offset_request(db, seed)
        p = _payable_of(db, "PO-252")
        p.paid_amount = 30_000_000                           # ai đó đã trả bớt, còn nợ 20tr
        db.commit()
        with pytest.raises(HTTPException) as e:
            S.set_status(db, req.id, "approved", seed.u_req_id)
        assert "nhỏ hơn phần" in e.value.detail
        assert S.get_request(db, req.id).status == "submitted"
        assert _hang(db, "")["total"] == 30_000_000          # treo còn nguyên

    def test_gui_duyet_soat_so_bo_offset_vuot_treo(self, db, seed):
        """Soát sơ bộ ngay lúc GỬI DUYỆT cho người lập biết sớm, khỏi chờ tới duyệt."""
        _prepay_request(db, seed, po_code="", amount=10_000_000)
        _po_with_receipt(db, seed, code="PO-252", price=10_000_000, qty=5)
        with pytest.raises(HTTPException) as e:
            _offset_request(db, seed, offset=30_000_000)     # treo chỉ có 10tr
        assert "vượt tiền treo" in e.value.detail


class TestPhieuTraTruocCamOffset:
    def test_prepay_mang_offset_bi_chan_gui_duyet(self, db, seed):
        """Phiếu trả trước SINH treo, không được đồng thời tiêu treo (tiền tự nuốt đuôi)."""
        _prepay_request(db, seed, po_code="", amount=30_000_000)
        data = PRequestCreate(request_date="2026-09-02", prepay=1, supplier_code="NX",
                              company_id=seed.company_id, source_type="goods",
                              lines=[LineIn(amount=10_000_000, offset_amount=5_000_000)])
        req = S.create_requests(db, data, seed.u_req_id)[0]
        with pytest.raises(HTTPException) as e:
            S.set_status(db, req.id, "submitted", seed.u_req_id)
        assert "Phiếu trả trước" in e.value.detail
