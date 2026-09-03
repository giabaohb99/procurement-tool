"""
test_payment_request_cr066.py — CR-066: bản nháp YCTT nhập tay được, cổng chặn dời sang GỬI DUYỆT.

Luật nghiệp vụ:
1. TẠO phiếu KHÔNG còn bắt buộc có Số hóa đơn — bản nháp để trống, in ra trình ký rồi điền tay.
2. GỬI DUYỆT thì mỗi dòng phải khớp một khoản công nợ CÒN NỢ (theo NCC + loại + mã PO + số HĐ).
   Thiếu điều kiện này, lúc "Ghi nhận đã chi" tiền không trừ vào đâu -> công nợ treo,
   dòng ĐMH không bao giờ lên "Hoàn thành".
3. Bản nháp cho sửa Số hóa đơn · Ngày hóa đơn · Đề nghị trả ngay trên bảng.
   Tổng nợ / Đã trả / Hạn trả vẫn ĐỌC từ Công nợ, không lưu trên phiếu.
4. Duyệt xong là KHÓA — chặn ở backend, không chỉ ẩn nút trên giao diện.
5. Tạo được phiếu từ FORM TRẮNG (không đi từ màn Công nợ).
"""
import pytest
from fastapi import HTTPException

from app.modules.payable.model import Payable
from app.modules.payment_request import service as S
from app.modules.payment_request.controller import _line
from app.modules.payment_request.schema import LineIn, PRequestCreate, PRequestUpdate
from app.modules.purchase_order.model import PODelivery, POItem, PurchaseOrder


def _payable(db, seed, *, po_code="PO-66-01", invoice_no="HD-66", total=1000000,
             paid=0.0, ref_id=0):
    p = Payable(company_id=seed.company_id, supplier_code="NX", supplier_name=seed.sup_name,
                source_type="goods", ref_type="delivery", ref_id=ref_id,
                po_code=po_code, invoice_no=invoice_no,
                incur_date="2026-08-04", due_date="2026-09-04",
                total=total, paid_amount=paid, remaining=total - paid,
                created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(p)
    db.commit()
    return p


def _create(db, seed, lines, **kw):
    data = PRequestCreate(request_date="2026-08-04", lines=lines, **kw)
    return S.create_requests(db, data, seed.u_req_id)[0]


@pytest.fixture
def payable(db, seed):
    return _payable(db, seed)


class TestTaoPhieuKhongCanHoaDon:
    def test_khoan_no_chua_co_so_hoa_don_van_tao_duoc(self, db, seed):
        """Trước CR-066 chỗ này báo lỗi 400; nay bản nháp được phép trống để in trình ký."""
        p = _payable(db, seed, invoice_no="")
        req = _create(db, seed, [LineIn(payable_id=p.id, amount=500000)])
        assert req.status == "draft"
        assert S.lines_of(db, req.id)[0].invoice_no == ""

    def test_nguoi_dung_go_tay_so_hoa_don_thi_luu_theo_ban_go(self, db, seed):
        """Khoản nợ chưa có số HĐ nhưng kế toán đã cầm hóa đơn trên tay -> gõ thẳng vào phiếu."""
        p = _payable(db, seed, invoice_no="")
        req = _create(db, seed, [LineIn(payable_id=p.id, invoice_no="HD-TAY", invoice_date="2026-08-02")])
        ln = S.lines_of(db, req.id)[0]
        assert (ln.invoice_no, ln.invoice_date) == ("HD-TAY", "2026-08-02")

    def test_khong_go_gi_thi_lay_theo_khoan_no(self, db, seed, payable):
        ln = S.lines_of(db, _create(db, seed, [LineIn(payable_id=payable.id)]).id)[0]
        assert ln.invoice_no == "HD-66" and ln.po_code == "PO-66-01"
        assert float(ln.amount) == 1000000        # bỏ trống số tiền -> còn phải trả

    def test_ngay_hoa_don_mac_dinh_lay_tu_dong_giao_hang(self, db, seed):
        """Ngày hóa đơn gốc nằm ở tab_po_delivery.invoice_date, không phải ngày tạo phiếu."""
        po = PurchaseOrder(code="PO-66-01", supplier_code="NX", created_by=seed.u_req_id)
        db.add(po)
        db.flush()
        item = POItem(po_id=po.id, product_name="Hàng A", created_by=seed.u_req_id)
        db.add(item)
        db.flush()
        d = PODelivery(po_id=po.id, po_item_id=item.id, invoice_no="HD-66",
                       invoice_date="2026-08-01", created_by=seed.u_req_id)
        db.add(d)
        db.commit()
        p = _payable(db, seed, ref_id=d.id)
        req = _create(db, seed, [LineIn(payable_id=p.id)])
        assert S.lines_of(db, req.id)[0].invoice_date == "2026-08-01"


class TestCongGuiDuyet:
    def test_thieu_so_hoa_don_thi_khong_gui_duyet_duoc(self, db, seed):
        p = _payable(db, seed, invoice_no="")
        req = _create(db, seed, [LineIn(payable_id=p.id, amount=500000)])
        with pytest.raises(HTTPException) as e:
            S.set_status(db, req.id, "submitted", seed.u_req_id)
        assert "chưa có Số hóa đơn" in e.value.detail
        assert S.get_request(db, req.id).status == "draft"

    def test_so_hoa_don_khong_khop_khoan_no_nao(self, db, seed, payable):
        """Gõ nhầm số hóa đơn -> chặn ngay, đừng để tới lúc chi tiền mới phát hiện."""
        req = _create(db, seed, [LineIn(payable_id=payable.id, invoice_no="HD-GO-NHAM")])
        with pytest.raises(HTTPException) as e:
            S.set_status(db, req.id, "submitted", seed.u_req_id)
        assert "không có khoản công nợ nào khớp" in e.value.detail

    def test_khoan_no_da_tat_toan_thi_chan(self, db, seed):
        p = _payable(db, seed, total=1000000, paid=1000000)
        req = _create(db, seed, [LineIn(payable_id=p.id, amount=1000000)])
        with pytest.raises(HTTPException) as e:
            S.set_status(db, req.id, "submitted", seed.u_req_id)
        assert "đã tất toán" in e.value.detail

    def test_phieu_khong_co_dong_nao_thi_chan(self, db, seed, payable):
        req = _create(db, seed, [LineIn(payable_id=payable.id)])
        S.update_request(db, req.id, PRequestUpdate(lines=[]), seed.u_req_id)
        with pytest.raises(HTTPException) as e:
            S.set_status(db, req.id, "submitted", seed.u_req_id)
        assert "chưa có dòng" in e.value.detail.lower()

    def test_khop_du_dieu_kien_thi_gui_duyet_duoc(self, db, seed, payable):
        req = _create(db, seed, [LineIn(payable_id=payable.id, amount=1000000)])
        assert S.set_status(db, req.id, "submitted", seed.u_req_id).status == "submitted"

    def test_dong_go_tay_khop_cong_no_thi_van_gui_duyet_duoc(self, db, seed, payable):
        """Form trắng: dòng không gắn payable_id, chỉ cần mã PO + số HĐ trỏ đúng khoản nợ."""
        req = _create(db, seed, [LineIn(po_code="PO-66-01", invoice_no="HD-66", amount=400000)],
                      supplier_code="NX", company_id=seed.company_id)
        assert S.lines_of(db, req.id)[0].payable_id == 0
        assert S.set_status(db, req.id, "submitted", seed.u_req_id).status == "submitted"


class TestSuaTrenBanNhap:
    def test_sua_so_hoa_don_ngay_hoa_don_so_tien(self, db, seed, payable):
        req = _create(db, seed, [LineIn(payable_id=payable.id, amount=1000000)])
        ln = S.lines_of(db, req.id)[0]
        S.update_request(db, req.id, PRequestUpdate(lines=[
            LineIn(payable_id=ln.payable_id, po_code="PO-66-01", invoice_no="HD-SUA",
                   invoice_date="2026-08-09", amount=600000)]), seed.u_req_id)
        ln2 = S.lines_of(db, req.id)[0]
        assert (ln2.invoice_no, ln2.invoice_date, float(ln2.amount)) == ("HD-SUA", "2026-08-09", 600000)
        assert float(S.get_request(db, req.id).total) == 600000

    def test_xoa_trang_so_hoa_don_thi_khong_bi_dien_de_lai(self, db, seed, payable):
        """Lúc SỬA thì không lấy đè theo khoản nợ — người dùng có quyền xóa trắng ô."""
        req = _create(db, seed, [LineIn(payable_id=payable.id)])
        S.update_request(db, req.id, PRequestUpdate(lines=[
            LineIn(payable_id=payable.id, po_code="PO-66-01", invoice_no="", amount=100000)]), seed.u_req_id)
        assert S.lines_of(db, req.id)[0].invoice_no == ""

    def test_them_dong_go_tay_vao_ban_nhap(self, db, seed, payable):
        req = _create(db, seed, [LineIn(payable_id=payable.id, amount=1000000)])
        S.update_request(db, req.id, PRequestUpdate(lines=[
            LineIn(payable_id=payable.id, po_code="PO-66-01", invoice_no="HD-66", amount=1000000),
            LineIn(po_code="PO-66-02", invoice_no="HD-77", invoice_date="2026-08-10", amount=250000)]),
            seed.u_req_id)
        lines = S.lines_of(db, req.id)
        assert len(lines) == 2
        assert float(S.get_request(db, req.id).total) == 1250000

    def test_tong_no_da_tra_van_doc_tu_cong_no(self, db, seed):
        """Số tiền nợ KHÔNG lưu trên phiếu: sửa khoản nợ thì phiếu hiển thị theo số mới."""
        p = _payable(db, seed, total=1000000, paid=200000)
        req = _create(db, seed, [LineIn(payable_id=p.id, amount=800000)])
        p.paid_amount = 300000
        db.commit()
        d = _line(db, S.lines_of(db, req.id)[0])
        assert d["payable_total"] == 1000000 and d["payable_paid"] == 300000
        assert d["due_date"] == "2026-09-04" and d["matched"] is True

    def test_dong_chua_khop_thi_cot_no_ve_0(self, db, seed):
        req = _create(db, seed, [LineIn(po_code="PO-LA", invoice_no="HD-LA", amount=90000)],
                      supplier_code="NX", company_id=seed.company_id)
        d = _line(db, S.lines_of(db, req.id)[0])
        assert d["payable_total"] == 0 and d["payable_paid"] == 0 and d["matched"] is False


class TestKhoaSauKhiDuyet:
    @pytest.mark.parametrize("status", ["submitted", "approved", "paid", "cancelled"])
    def test_khong_con_nhap_thi_khong_sua_duoc(self, db, seed, payable, status):
        """Giao diện đã ẩn nút, nhưng phải chặn ở BACKEND vì gọi thẳng API vẫn sửa được."""
        req = _create(db, seed, [LineIn(payable_id=payable.id, amount=1000000)])
        req.status = status
        db.commit()
        with pytest.raises(HTTPException) as e:
            S.update_request(db, req.id, PRequestUpdate(lines=[
                LineIn(payable_id=payable.id, invoice_no="HD-LEN", amount=999999)]), seed.u_req_id)
        assert e.value.status_code == 400
        assert float(S.lines_of(db, req.id)[0].amount) == 1000000

    def test_duyet_xong_khong_doi_duoc_so_tien(self, db, seed, payable):
        req = _create(db, seed, [LineIn(payable_id=payable.id, amount=1000000)])
        S.set_status(db, req.id, "submitted", seed.u_req_id)
        S.set_status(db, req.id, "approved", seed.u_req_id)
        with pytest.raises(HTTPException) as e:
            S.update_request(db, req.id, PRequestUpdate(note="đổi lén"), seed.u_req_id)
        assert "đã duyệt" in e.value.detail.lower()


class TestFormTrang:
    def test_tao_phieu_khong_di_tu_cong_no(self, db, seed):
        req = _create(db, seed, [LineIn(po_code="PO-TRANG", invoice_no="", amount=1500000)],
                      supplier_code="NX", company_id=seed.company_id, source_type="goods")
        assert req.supplier_code == "NX" and req.supplier_name == seed.sup_name
        assert req.company_id == seed.company_id and float(req.total) == 1500000
        assert S.lines_of(db, req.id)[0].payable_id == 0

    def test_thieu_nha_cung_cap_thi_bao_loi(self, db, seed):
        with pytest.raises(HTTPException) as e:
            _create(db, seed, [LineIn(po_code="PO-TRANG", amount=100000)])
        assert "nhà cung cấp" in e.value.detail.lower()

    def test_hai_dong_trong_cung_po_khong_bi_gop(self, db, seed):
        """Chưa có số hóa đơn thì chưa biết có cùng một hóa đơn hay không -> để riêng."""
        req = _create(db, seed, [LineIn(po_code="PO-TRANG", amount=100000),
                                 LineIn(po_code="PO-TRANG", amount=250000)],
                      supplier_code="NX", company_id=seed.company_id)
        assert len(S.lines_of(db, req.id)) == 2

    def test_cung_po_cung_so_hoa_don_thi_gop_1_dong(self, db, seed):
        """Một hóa đơn cho nhiều lần giao -> vẫn gộp về 1 dòng như trước CR-066."""
        p1 = _payable(db, seed, invoice_no="HD-GOP", total=300000)
        p2 = _payable(db, seed, invoice_no="HD-GOP", total=200000)
        req = _create(db, seed, [LineIn(payable_id=p1.id), LineIn(payable_id=p2.id)])
        lines = S.lines_of(db, req.id)
        assert len(lines) == 1 and float(lines[0].amount) == 500000


class TestTachTheoCongTy:
    """bao-CR-274: khoản nợ của nhiều pháp nhân không được gom chung một phiếu — phiếu
    phải đứng tên đúng công ty nhận hóa đơn (trước đây company_id lấy theo khoản nợ đầu
    tiên nên phiếu đóng dấu nhầm công ty)."""

    def test_no_hai_cong_ty_thi_tach_hai_phieu(self, db, seed):
        from app.modules.company.model import Company

        cty2 = Company(name="Cty Hai", code="CT02", is_active=True)
        db.add(cty2)
        db.flush()
        p1 = _payable(db, seed, po_code="PO-C1", invoice_no="HD-C1")
        p2 = Payable(company_id=cty2.id, supplier_code="NX", supplier_name=seed.sup_name,
                     source_type="goods", po_code="PO-C2", invoice_no="HD-C2",
                     incur_date="2026-08-04", due_date="2026-09-04",
                     total=200000, paid_amount=0, remaining=200000,
                     created_by=seed.u_req_id, updated_by=seed.u_req_id)
        db.add(p2)
        db.commit()

        data = PRequestCreate(request_date="2026-08-04",
                              lines=[LineIn(payable_id=p1.id), LineIn(payable_id=p2.id)])
        reqs = S.create_requests(db, data, seed.u_req_id)
        assert len(reqs) == 2
        by_company = {r.company_id: r for r in reqs}
        assert set(by_company) == {seed.company_id, cty2.id}
        # Mỗi phiếu chỉ mang dòng của đúng công ty đó — tổng tiền không lẫn nhau.
        assert float(by_company[seed.company_id].total) == 1000000
        assert float(by_company[cty2.id].total) == 200000
        assert all(r.supplier_code == "NX" for r in reqs)

    def test_dong_go_tay_di_chung_phieu_khi_mot_cong_ty(self, db, seed, payable):
        """Form vừa có khoản nợ vừa có dòng gõ tay, tất cả một công ty -> vẫn 1 phiếu
        như hành vi cũ, không tách vô cớ."""
        data = PRequestCreate(request_date="2026-08-04", supplier_code="NX",
                              lines=[LineIn(payable_id=payable.id),
                                     LineIn(po_code="PO-TAY", amount=50000)])
        reqs = S.create_requests(db, data, seed.u_req_id)
        assert len(reqs) == 1
        assert reqs[0].company_id == seed.company_id
        assert len(S.lines_of(db, reqs[0].id)) == 2


class TestPhamViKhoanNoKhiTao:
    """bao-CR-274: endpoint tạo phiếu chặn payable_id NGOÀI phạm vi `payable` được xem —
    service lấy theo id nên gõ thẳng id qua API từng kéo được nợ pháp nhân khác vào phiếu."""

    def test_go_id_ngoai_pham_vi_thi_403(self, db, seed, cap_quyen):
        from app.modules.payment_request import controller as C
        from app.modules.user.model import User

        p = _payable(db, seed)   # created_by = u_req
        cap_quyen(seed.u_nstm_id, "payment_request", scope="all", create=True)
        cap_quyen(seed.u_nstm_id, "payable", scope="own", read=True)  # chỉ thấy nợ mình tạo
        data = PRequestCreate(request_date="2026-08-04", lines=[LineIn(payable_id=p.id)])
        with pytest.raises(HTTPException) as e:
            C.create_(data, db=db, user=db.get(User, seed.u_nstm_id))
        assert e.value.status_code == 403
        assert "ngoài phạm vi" in e.value.detail

    def test_dung_pham_vi_thi_tao_binh_thuong(self, db, seed, cap_quyen):
        from app.modules.payment_request import controller as C
        from app.modules.payment_request.model import PaymentRequest
        from app.modules.user.model import User

        p = _payable(db, seed)
        cap_quyen(seed.u_req_id, "payment_request", scope="all", create=True)
        cap_quyen(seed.u_req_id, "payable", scope="own", read=True)
        data = PRequestCreate(request_date="2026-08-04", lines=[LineIn(payable_id=p.id)])
        C.create_(data, db=db, user=db.get(User, seed.u_req_id))
        assert db.query(PaymentRequest).count() == 1


class TestChiTien:
    def test_dong_go_tay_van_tru_dung_khoan_no(self, db, seed, payable):
        """Phân bổ khớp theo (NCC + loại + PO + số HĐ) trước, nên dòng gõ tay vẫn trừ đúng."""
        req = _create(db, seed, [LineIn(po_code="PO-66-01", invoice_no="HD-66", amount=400000)],
                      supplier_code="NX", company_id=seed.company_id)
        S.set_status(db, req.id, "submitted", seed.u_req_id)
        S.set_status(db, req.id, "approved", seed.u_req_id)
        S.set_status(db, req.id, "paid", seed.u_req_id)
        db.refresh(payable)
        assert float(payable.paid_amount) == 400000
