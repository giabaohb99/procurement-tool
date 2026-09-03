"""
test_tien_treo_cr268.py — CR-268: TIỀN TREO của phiếu THANH TOÁN TRƯỚC (prepay=1).

Luật nghiệp vụ:
1. Phiếu prepay=1 được đi hết vòng đời draft→submitted→approved→paid dù CHƯA có công
   nợ khớp (miễn cổng CR-066); phiếu thường (prepay=0) vẫn bị chặn như cũ.
2. Tiền đã chi mà chưa trừ được vào đâu = TIỀN TREO, theo dõi trên dòng phiếu:
   hanging = amount - allocated_amount - refunded_amount.
3. Treo GẮN ĐƠN (dòng có po_code): nhận hàng sinh công nợ là TỰ ĐỘNG đối trừ vào
   công nợ hàng của đúng đơn đó (apply_prepay_offsets trong recompute_effects).
4. Treo CẤP NCC (po_code rỗng): KHÔNG tự trừ — kế toán bấm tay (offset_supplier_hanging)
   hoặc ghi nhận NCC hoàn tiền (record_refund).
5. Trần CỨNG mọi lần đối trừ: min(treo còn lại, nợ còn lại) — không bao giờ đẩy công
   nợ âm (vết xe payment-allocation-bug 82ce6ad).
"""
import pytest
from fastapi import HTTPException

from app.modules.payable.model import Payable
from app.modules.payment_request import service as S
from app.modules.payment_request.schema import LineIn, PRequestCreate
from app.modules.purchase_order.model import PODelivery, POItem, PurchaseOrder
from app.modules.purchase_order.service import recompute_effects


def _prepay_request(db, seed, *, po_code="", amount=30_000_000, invoice_no="", pay=True):
    """Lập + chi 1 phiếu trả trước qua đúng đường người dùng đi (form trắng, prepay=1)."""
    data = PRequestCreate(request_date="2026-09-01", prepay=1, supplier_code="NX",
                          company_id=seed.company_id, source_type="goods",
                          lines=[LineIn(po_code=po_code, invoice_no=invoice_no, amount=amount)])
    req = S.create_requests(db, data, seed.u_req_id)[0]
    S.set_status(db, req.id, "submitted", seed.u_req_id)
    S.set_status(db, req.id, "approved", seed.u_req_id)
    if pay:
        S.set_status(db, req.id, "paid", seed.u_req_id)
    return req


def _po_with_receipt(db, seed, *, code="PO-252", price=10_000_000, qty=5, vat=0):
    """Đơn hàng đã nhận đủ -> recompute_effects sinh công nợ hàng (và tự đối trừ treo)."""
    po = PurchaseOrder(code=code, status="approved", order_date="2026-09-01",
                       supplier_code="NX", supplier_name=seed.sup_name,
                       company_id=seed.company_id, created_by=seed.u_req_id)
    db.add(po)
    db.flush()
    it = POItem(po_id=po.id, product_code="SP252", product_name="Hàng CR265", unit="cái",
                qty_order=qty, price=price, vat=vat, item_group="Nhãn", created_by=seed.u_req_id)
    db.add(it)
    db.flush()
    d = PODelivery(po_id=po.id, po_item_id=it.id, delivery_no=1, ship_qty=qty,
                   received_qty=qty, received_date="2026-09-02", invoice_no="HD-252",
                   created_by=seed.u_req_id)
    db.add(d)
    db.flush()
    recompute_effects(db, po, seed.u_req_id)
    db.commit()
    return po


def _payable_of(db, po_code):
    return db.query(Payable).filter(Payable.po_code == po_code,
                                    Payable.source_type == "goods").one()


def _hang(db, po_code=None):
    return S.summarize_hanging(db, "NX", "goods", po_code)


class TestVongDoiPhieuTraTruoc:
    def test_prepay_khong_co_cong_no_van_di_het_vong_doi(self, db, seed):
        """Trước CR-268: check_submit (CR-066) chặn vĩnh viễn -> tiền treo ngoài hệ thống."""
        req = _prepay_request(db, seed, po_code="PO-252", amount=10_000_000)
        assert req.status == "paid"

    def test_phieu_thuong_khong_khop_cong_no_van_bi_chan(self, db, seed):
        """Miễn cổng CHỈ cho prepay=1 — phiếu thường lọt qua là thủng luôn CR-066."""
        data = PRequestCreate(request_date="2026-09-01", prepay=0, supplier_code="NX",
                              company_id=seed.company_id,
                              lines=[LineIn(po_code="PO-KHONG-CO", amount=1_000_000)])
        req = S.create_requests(db, data, seed.u_req_id)[0]
        with pytest.raises(HTTPException):
            S.set_status(db, req.id, "submitted", seed.u_req_id)

    def test_prepay_dong_tien_bang_0_bi_chan_gui_duyet(self, db, seed):
        data = PRequestCreate(request_date="2026-09-01", prepay=1, supplier_code="NX",
                              company_id=seed.company_id, lines=[LineIn(po_code="PO-252")])
        req = S.create_requests(db, data, seed.u_req_id)[0]
        with pytest.raises(HTTPException) as e:
            S.set_status(db, req.id, "submitted", seed.u_req_id)
        assert "không dương" in e.value.detail

    def test_chi_xong_toan_bo_thanh_tien_treo(self, db, seed):
        req = _prepay_request(db, seed, po_code="PO-252", amount=10_000_000)
        ln = S.lines_of(db, req.id)[0]
        assert float(ln.allocated_amount) == 0
        assert S.line_hanging(ln) == 10_000_000
        assert _hang(db)["total"] == 10_000_000


class TestTuDongDoiTruGanDon:
    def test_treo_nho_hon_no_thi_tru_het_treo(self, db, seed):
        req = _prepay_request(db, seed, po_code="PO-252", amount=10_000_000)
        _po_with_receipt(db, seed, code="PO-252", price=10_000_000, qty=5)  # nợ 50tr
        p = _payable_of(db, "PO-252")
        assert float(p.paid_amount) == 10_000_000 and float(p.remaining) == 40_000_000
        ln = S.lines_of(db, req.id)[0]
        assert float(ln.allocated_amount) == 10_000_000 and S.line_hanging(ln) == 0

    def test_treo_lon_hon_no_thi_chi_tru_bang_no_khong_am(self, db, seed):
        """Trần min(treo, nợ): đơn co lại còn 30tr mà đã ứng 50tr -> nợ = 0, treo dư 20tr."""
        req = _prepay_request(db, seed, po_code="PO-252", amount=50_000_000)
        _po_with_receipt(db, seed, code="PO-252", price=10_000_000, qty=3)  # nợ 30tr
        p = _payable_of(db, "PO-252")
        assert float(p.paid_amount) == 30_000_000 and float(p.remaining) == 0
        assert p.status == "paid"
        assert S.line_hanging(S.lines_of(db, req.id)[0]) == 20_000_000

    def test_chay_lai_khong_tru_them(self, db, seed):
        """recompute_effects gọi lại mỗi lần lưu đơn — đối trừ phải idempotent."""
        _prepay_request(db, seed, po_code="PO-252", amount=10_000_000)
        po = _po_with_receipt(db, seed, code="PO-252", price=10_000_000, qty=5)
        recompute_effects(db, po, seed.u_req_id)
        db.commit()
        assert float(_payable_of(db, "PO-252").paid_amount) == 10_000_000

    def test_hai_phieu_treo_an_theo_phieu_cu_truoc(self, db, seed):
        r1 = _prepay_request(db, seed, po_code="PO-252", amount=8_000_000)
        r2 = _prepay_request(db, seed, po_code="PO-252", amount=8_000_000)
        _po_with_receipt(db, seed, code="PO-252", price=10_000_000, qty=1)  # nợ 10tr
        assert S.line_hanging(S.lines_of(db, r1.id)[0]) == 0            # phiếu cũ ăn trước
        assert S.line_hanging(S.lines_of(db, r2.id)[0]) == 6_000_000
        assert float(_payable_of(db, "PO-252").remaining) == 0

    def test_treo_don_khac_khong_bi_hut_vao(self, db, seed):
        req = _prepay_request(db, seed, po_code="PO-KHAC", amount=10_000_000)
        _po_with_receipt(db, seed, code="PO-252", price=10_000_000, qty=5)
        assert float(_payable_of(db, "PO-252").paid_amount) == 0
        assert S.line_hanging(S.lines_of(db, req.id)[0]) == 10_000_000

    def test_treo_cap_ncc_khong_tu_dong_tru(self, db, seed):
        """po_code rỗng = treo cấp NCC: có thể NCC sẽ hoàn tiền, máy không tự quyết."""
        req = _prepay_request(db, seed, po_code="", amount=30_000_000)
        _po_with_receipt(db, seed, code="PO-252", price=10_000_000, qty=5)
        assert float(_payable_of(db, "PO-252").paid_amount) == 0
        assert S.line_hanging(S.lines_of(db, req.id)[0]) == 30_000_000

    def test_prepay_chi_sau_khi_nhan_hang_khong_sinh_treo_ao(self, db, seed):
        """Chi SAU khi công nợ đã có + khớp số HĐ -> phân bổ thẳng, allocated ghi đủ."""
        _po_with_receipt(db, seed, code="PO-252", price=10_000_000, qty=5)  # nợ 50tr
        req = _prepay_request(db, seed, po_code="PO-252", invoice_no="HD-252",
                              amount=20_000_000)
        p = _payable_of(db, "PO-252")
        assert float(p.paid_amount) == 20_000_000
        ln = S.lines_of(db, req.id)[0]
        assert float(ln.allocated_amount) == 20_000_000 and S.line_hanging(ln) == 0


class TestCanTruTayCapNcc:
    """Kịch bản đại ca đưa: ứng NCC 30tr không gắn đơn; đơn sau 50tr -> chỉ trả thêm 20tr."""

    def test_can_tru_toi_da_vao_khoan_no(self, db, seed):
        req = _prepay_request(db, seed, po_code="", amount=30_000_000)
        _po_with_receipt(db, seed, code="PO-252", price=10_000_000, qty=5)  # nợ 50tr
        p = _payable_of(db, "PO-252")
        taken = S.offset_supplier_hanging(db, p, 0, seed.u_req_id)   # 0 = trừ tối đa
        assert taken == 30_000_000
        assert float(p.paid_amount) == 30_000_000 and float(p.remaining) == 20_000_000
        assert S.line_hanging(S.lines_of(db, req.id)[0]) == 0

    def test_tran_cung_khong_vuot_no_con_lai(self, db, seed):
        _prepay_request(db, seed, po_code="", amount=30_000_000)
        _po_with_receipt(db, seed, code="PO-252", price=10_000_000, qty=1)  # nợ 10tr
        p = _payable_of(db, "PO-252")
        taken = S.offset_supplier_hanging(db, p, 999_000_000, seed.u_req_id)
        assert taken == 10_000_000                       # min(treo 30, nợ 10, đòi 999)
        assert float(p.remaining) == 0 and p.status == "paid"

    def test_tran_cung_khong_vuot_treo_con_lai(self, db, seed):
        _prepay_request(db, seed, po_code="", amount=5_000_000)
        _po_with_receipt(db, seed, code="PO-252", price=10_000_000, qty=5)  # nợ 50tr
        p = _payable_of(db, "PO-252")
        taken = S.offset_supplier_hanging(db, p, 50_000_000, seed.u_req_id)
        assert taken == 5_000_000
        assert float(p.remaining) == 45_000_000

    def test_khong_an_treo_gan_don_cua_don_khac(self, db, seed):
        """Nút cấn trừ tay CHỈ tiêu treo cấp NCC — treo gắn đơn để dành cho đúng đơn nó."""
        _prepay_request(db, seed, po_code="PO-DANH-RIENG", amount=30_000_000)
        _po_with_receipt(db, seed, code="PO-252", price=10_000_000, qty=5)
        p = _payable_of(db, "PO-252")
        with pytest.raises(HTTPException) as e:
            S.offset_supplier_hanging(db, p, 0, seed.u_req_id)
        assert "không còn tiền treo" in e.value.detail

    def test_khoan_no_da_tat_toan_thi_chan(self, db, seed):
        _prepay_request(db, seed, po_code="", amount=30_000_000)
        _po_with_receipt(db, seed, code="PO-252", price=10_000_000, qty=5)
        p = _payable_of(db, "PO-252")
        p.paid_amount = 50_000_000
        db.commit()
        with pytest.raises(HTTPException) as e:
            S.offset_supplier_hanging(db, p, 0, seed.u_req_id)
        assert "đã tất toán" in e.value.detail


class TestNccHoanTien:
    def test_hoan_mot_phan_roi_hoan_not(self, db, seed):
        req = _prepay_request(db, seed, po_code="", amount=30_000_000)
        assert S.record_refund(db, req.id, 10_000_000, "hoàn đợt 1", seed.u_req_id) == 10_000_000
        ln = S.lines_of(db, req.id)[0]
        assert float(ln.refunded_amount) == 10_000_000 and S.line_hanging(ln) == 20_000_000
        assert S.record_refund(db, req.id, 0, "hoàn nốt", seed.u_req_id) == 20_000_000
        assert S.line_hanging(S.lines_of(db, req.id)[0]) == 0

    def test_hoan_vuot_tien_treo_bi_chan(self, db, seed):
        req = _prepay_request(db, seed, po_code="", amount=30_000_000)
        with pytest.raises(HTTPException) as e:
            S.record_refund(db, req.id, 30_000_001, "", seed.u_req_id)
        assert "vượt tiền treo" in e.value.detail

    def test_phieu_thuong_hoac_chua_chi_khong_ghi_hoan_duoc(self, db, seed):
        req = _prepay_request(db, seed, po_code="", amount=30_000_000, pay=False)
        with pytest.raises(HTTPException):
            S.record_refund(db, req.id, 1_000_000, "", seed.u_req_id)   # mới approved

    def test_da_doi_tru_het_thi_khong_con_gi_de_hoan(self, db, seed):
        req = _prepay_request(db, seed, po_code="PO-252", amount=10_000_000)
        _po_with_receipt(db, seed, code="PO-252", price=10_000_000, qty=5)
        with pytest.raises(HTTPException) as e:
            S.record_refund(db, req.id, 0, "", seed.u_req_id)
        assert "không còn tiền treo" in e.value.detail


class TestTraCuuTienTreo:
    def test_loc_theo_don_va_loc_cap_ncc(self, db, seed):
        _prepay_request(db, seed, po_code="PO-252", amount=10_000_000)
        _prepay_request(db, seed, po_code="", amount=30_000_000)
        assert _hang(db)["total"] == 40_000_000              # tất cả
        assert _hang(db, "PO-252")["total"] == 10_000_000    # gắn đúng đơn
        assert _hang(db, "")["total"] == 30_000_000          # cấp NCC
        assert _hang(db, "PO-KHAC")["total"] == 0

    def test_phieu_chua_chi_khong_tinh_la_treo(self, db, seed):
        _prepay_request(db, seed, po_code="PO-252", amount=10_000_000, pay=False)
        assert _hang(db)["total"] == 0
