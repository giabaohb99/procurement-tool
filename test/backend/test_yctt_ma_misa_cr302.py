"""
test_yctt_ma_misa_cr302.py — Ticket #26 (bao-CR-302): dòng YCTT hiển thị mã MISA của ĐMH.

Dòng phiếu chỉ chụp lại mã PO dạng chuỗi (không có po_id), còn mã MISA nhập/sửa trên ĐMH
sau khi phiếu đã lập — nên phải join theo mã lúc đọc (misa_by_po_code), không lưu lên dòng.
"""
from app.modules.payable.model import Payable
from app.modules.payment_request import service as S
from app.modules.payment_request.controller import _line
from app.modules.payment_request.schema import LineIn, PRequestCreate
from app.modules.purchase_order.model import PurchaseOrder


def _po(db, seed, code, misa=""):
    po = PurchaseOrder(code=code, supplier_code="NX", misa_code=misa, created_by=seed.u_req_id)
    db.add(po)
    db.commit()
    return po


def _payable(db, seed, po_code):
    p = Payable(company_id=seed.company_id, supplier_code="NX", supplier_name=seed.sup_name,
                source_type="goods", ref_type="delivery", ref_id=0,
                po_code=po_code, invoice_no="HD-302",
                incur_date="2026-09-01", due_date="2026-10-01",
                total=1000000, paid_amount=0, remaining=1000000,
                created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(p)
    db.commit()
    return p


class TestMisaByPoCode:
    def test_gom_mot_truy_van_va_khop_theo_ma(self, db, seed):
        _po(db, seed, "PO-302-A", misa="MS-A")
        _po(db, seed, "PO-302-B")          # ĐMH chưa nhập mã MISA
        m = S.misa_by_po_code(db, ["PO-302-A", " PO-302-B ", "", "PO-KHONG-TON-TAI"])
        assert m == {"PO-302-A": "MS-A", "PO-302-B": ""}

    def test_khong_co_ma_po_nao_thi_khoi_truy_van(self, db, seed):
        assert S.misa_by_po_code(db, ["", "   "]) == {}


class TestLocTheoMaMisa:
    def test_loc_ra_dung_phieu_theo_ma_misa(self, db, seed):
        from app.modules.payment_request.model import PaymentRequest
        _po(db, seed, "PO-302-A", misa="MS-A")
        _po(db, seed, "PO-302-B", misa="MS-B")
        pa = _payable(db, seed, "PO-302-A")
        pb = _payable(db, seed, "PO-302-B")
        req_a = S.create_requests(db, PRequestCreate(
            request_date="2026-09-01", lines=[LineIn(payable_id=pa.id)]), seed.u_req_id)[0]
        req_b = S.create_requests(db, PRequestCreate(
            request_date="2026-09-01", lines=[LineIn(payable_id=pb.id)]), seed.u_req_id)[0]
        ids = [r.id for r in S.filter_by_misa_code(db.query(PaymentRequest), "MS-A").all()]
        assert req_a.id in ids and req_b.id not in ids

    def test_ma_khong_ton_tai_thi_rong(self, db, seed):
        from app.modules.payment_request.model import PaymentRequest
        _po(db, seed, "PO-302-A", misa="MS-A")
        p = _payable(db, seed, "PO-302-A")
        S.create_requests(db, PRequestCreate(
            request_date="2026-09-01", lines=[LineIn(payable_id=p.id)]), seed.u_req_id)
        assert S.filter_by_misa_code(db.query(PaymentRequest), "KHONG-CO").all() == []


class TestGopMaMisaChoDanhSach:
    def test_phieu_nhieu_po_gop_chuoi_khong_trung(self, db, seed):
        _po(db, seed, "PO-302-A", misa="MS-A")
        _po(db, seed, "PO-302-B", misa="MS-B")
        p1 = _payable(db, seed, "PO-302-A")
        p2 = _payable(db, seed, "PO-302-B")
        p3 = _payable(db, seed, "PO-302-A")      # trùng PO -> mã chỉ hiện một lần
        data = PRequestCreate(request_date="2026-09-01", lines=[
            LineIn(payable_id=p1.id), LineIn(payable_id=p2.id), LineIn(payable_id=p3.id)])
        req = S.create_requests(db, data, seed.u_req_id)[0]
        assert S.misa_codes_by_request(db, [req.id]) == {req.id: "MS-A, MS-B"}

    def test_khong_co_id_thi_tra_rong(self, db, seed):
        assert S.misa_codes_by_request(db, []) == {}


class TestDongPhieuCoMaMisa:
    def _line_of(self, db, seed, po_code):
        p = _payable(db, seed, po_code)
        data = PRequestCreate(request_date="2026-09-01", lines=[LineIn(payable_id=p.id)])
        req = S.create_requests(db, data, seed.u_req_id)[0]
        return S.lines_of(db, req.id)[0]

    def test_dong_tra_ma_misa_cua_dmh(self, db, seed):
        _po(db, seed, "PO-302-A", misa="MS-A")
        ln = self._line_of(db, seed, "PO-302-A")
        misa = S.misa_by_po_code(db, [ln.po_code])
        assert _line(db, ln, misa)["misa_code"] == "MS-A"

    def test_ma_po_go_tay_khong_khop_dmh_thi_rong(self, db, seed):
        ln = self._line_of(db, seed, "PO-GO-TAY")
        misa = S.misa_by_po_code(db, [ln.po_code])
        assert _line(db, ln, misa)["misa_code"] == ""

    def test_goi_khong_kem_map_van_chay(self, db, seed):
        """_line còn chỗ gọi cũ không truyền map -> misa rỗng, không nổ."""
        ln = self._line_of(db, seed, "PO-302-A")
        assert _line(db, ln)["misa_code"] == ""
