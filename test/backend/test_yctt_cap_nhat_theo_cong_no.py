"""
test_yctt_cap_nhat_theo_cong_no.py — bao-CR-509: nút «Cập nhật theo công nợ» của YCTT.

Luật nghiệp vụ (khách chốt 28/09/2026):
1. Dòng phiếu lưu BẢN CHỤP số đề nghị chi. Sửa ĐMH làm công nợ đổi thì phiếu NHÁP nạp lại
   được: số mới = nợ còn lại hiện tại (total - paid) trừ phần cấn trừ (CR-260), sàn 0.
2. Xem trước KHÔNG ghi gì; ghi thì tính lại từ DB ngay lúc ghi.
3. Dòng gõ tay không gắn công nợ -> giữ nguyên. Khoản nợ tất toán / bị xóa -> số về 0,
   dòng KHÔNG bị tự bỏ.
4. Chỉ phiếu NHÁP ghi được; phiếu trả trước (CR-268) không có công nợ -> chặn.
5. Phiếu đã gửi duyệt lệch công nợ thì màn chi tiết phải thấy cờ `out_of_sync`.
"""
import pytest
from fastapi import HTTPException

from app.modules.audit.model import AuditLog
from app.modules.payable.model import Payable
from app.modules.payment_request import service as S
from app.modules.payment_request.controller import _out
from app.modules.payment_request.schema import LineIn, PRequestCreate, PRequestUpdate
from app.modules.purchase_order.model import PODelivery, POItem, PurchaseOrder


def _payable(db, seed, *, po_code="PO-509", invoice_no="HD-509", total=1_000_000,
             paid=0.0, ref_id=0, source_type="goods"):
    p = Payable(company_id=seed.company_id, supplier_code="NX", supplier_name=seed.sup_name,
                source_type=source_type, ref_type="delivery", ref_id=ref_id,
                po_code=po_code, invoice_no=invoice_no,
                incur_date="2026-09-20", due_date="2026-10-20",
                total=total, paid_amount=paid, remaining=total - paid,
                created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(p)
    db.commit()
    return p


def _create(db, seed, lines, **kw):
    kw.setdefault("supplier_code", "NX")
    kw.setdefault("company_id", seed.company_id)
    data = PRequestCreate(request_date="2026-09-28", lines=lines, **kw)
    return S.create_requests(db, data, seed.u_req_id)[0]


def _set_payable(db, p, *, total=None, paid=None):
    """Mô phỏng sửa ĐMH làm công nợ đổi (recompute_effects cập nhật total / paid)."""
    if total is not None:
        p.total = total
    if paid is not None:
        p.paid_amount = paid
    p.remaining = float(p.total) - float(p.paid_amount)
    db.commit()


def _amounts(db, req):
    return [float(ln.amount) for ln in S.lines_of(db, req.id)]


class TestNapLaiPhieuNhap:
    def test_cong_no_tang_thi_so_de_nghi_tang_theo(self, db, seed):
        p = _payable(db, seed)
        req = _create(db, seed, [LineIn(payable_id=p.id)])
        assert _amounts(db, req) == [1_000_000]
        _set_payable(db, p, total=1_500_000)

        plan = S.plan_refresh(db, req)
        row = plan["lines"][0]
        assert (row["amount_old"], row["amount_new"], row["state"]) == (1_000_000, 1_500_000, S.SYNC_CHANGED)
        assert (plan["old_total"], plan["new_total"], plan["changed_count"]) == (1_000_000, 1_500_000, 1)
        assert plan["can_apply"] is True

        req, _ = S.apply_refresh(db, req.id, seed.u_req_id)
        assert _amounts(db, req) == [1_500_000]
        assert float(req.total) == 1_500_000

    def test_cong_no_giam_va_da_tra_mot_phan(self, db, seed):
        p = _payable(db, seed)
        req = _create(db, seed, [LineIn(payable_id=p.id)])
        _set_payable(db, p, total=800_000, paid=100_000)
        req, plan = S.apply_refresh(db, req.id, seed.u_req_id)
        assert plan["lines"][0]["payable_remaining"] == 700_000
        assert _amounts(db, req) == [700_000] and float(req.total) == 700_000

    def test_xem_truoc_khong_ghi_gi(self, db, seed):
        p = _payable(db, seed)
        req = _create(db, seed, [LineIn(payable_id=p.id)])
        _set_payable(db, p, total=2_000_000)
        logs_before = db.query(AuditLog).count()
        S.plan_refresh(db, req)
        db.expire_all()
        assert _amounts(db, req) == [1_000_000]
        assert float(S.get_request(db, req.id).total) == 1_000_000
        assert db.query(AuditLog).count() == logs_before

    def test_ghi_co_nhat_ky_ghi_ro_so_cu_so_moi(self, db, seed):
        p = _payable(db, seed)
        req = _create(db, seed, [LineIn(payable_id=p.id)])
        _set_payable(db, p, total=1_200_000)
        S.apply_refresh(db, req.id, seed.u_req_id)
        log = (db.query(AuditLog).filter(AuditLog.entity == "payment_request",
                                         AuditLog.entity_id == req.id)
               .order_by(AuditLog.id.desc()).first())
        assert "Cập nhật theo công nợ" in log.message
        assert "1,000,000" in log.message and "1,200,000" in log.message

    def test_da_khop_thi_khong_ghi_va_khong_them_nhat_ky(self, db, seed):
        p = _payable(db, seed)
        req = _create(db, seed, [LineIn(payable_id=p.id)])
        logs_before = db.query(AuditLog).count()
        _req, plan = S.apply_refresh(db, req.id, seed.u_req_id)
        assert plan["changed_count"] == 0
        assert plan["lines"][0]["state"] == S.SYNC_UNCHANGED
        assert db.query(AuditLog).count() == logs_before

    def test_ghi_tinh_lai_tu_db_khong_theo_ban_xem_truoc(self, db, seed):
        """Công nợ đổi thêm lần nữa giữa lúc xem trước và lúc bấm Cập nhật -> ghi số MỚI NHẤT."""
        p = _payable(db, seed)
        req = _create(db, seed, [LineIn(payable_id=p.id)])
        _set_payable(db, p, total=1_300_000)
        assert S.plan_refresh(db, req)["new_total"] == 1_300_000
        _set_payable(db, p, total=1_400_000)
        req, _ = S.apply_refresh(db, req.id, seed.u_req_id)
        assert _amounts(db, req) == [1_400_000]


class TestCanTru:
    def test_tru_phan_can_tru_cr260(self, db, seed):
        p = _payable(db, seed)
        req = _create(db, seed, [LineIn(payable_id=p.id, amount=800_000, offset_amount=200_000)])
        _set_payable(db, p, total=1_200_000)
        req, plan = S.apply_refresh(db, req.id, seed.u_req_id)
        ln = S.lines_of(db, req.id)[0]
        assert float(ln.amount) == 1_000_000
        assert float(ln.offset_amount) == 200_000        # phần cấn trừ KHÔNG bị đụng
        assert "cấn trừ" in plan["lines"][0]["reason"]

    def test_can_tru_vuot_no_thi_san_0_va_bao_ro(self, db, seed):
        p = _payable(db, seed)
        req = _create(db, seed, [LineIn(payable_id=p.id, amount=500_000, offset_amount=500_000)])
        _set_payable(db, p, total=300_000)
        row = S.plan_refresh(db, req)["lines"][0]
        assert row["amount_new"] == 0
        assert "VƯỢT nợ còn lại" in row["reason"]


class TestDongDacBiet:
    def test_dong_go_tay_khong_gan_cong_no_giu_nguyen(self, db, seed):
        p = _payable(db, seed)
        req = _create(db, seed, [LineIn(payable_id=p.id),
                                 LineIn(po_code="PO-TAY", invoice_no="HD-TAY", amount=250_000)])
        _set_payable(db, p, total=1_100_000)
        plan = S.plan_refresh(db, req)
        manual = next(r for r in plan["lines"] if r["po_code_old"] == "PO-TAY")
        assert manual["state"] == S.SYNC_MANUAL
        assert manual["amount_new"] == 250_000 and not manual["changed"]
        assert "giữ nguyên" in manual["reason"]
        req, _ = S.apply_refresh(db, req.id, seed.u_req_id)
        assert sorted(_amounts(db, req)) == [250_000, 1_100_000]
        assert float(req.total) == 1_350_000

    def test_cong_no_da_tat_toan_thi_ve_0_nhung_khong_bo_dong(self, db, seed):
        p = _payable(db, seed)
        req = _create(db, seed, [LineIn(payable_id=p.id)])
        _set_payable(db, p, paid=1_000_000)
        row = S.plan_refresh(db, req)["lines"][0]
        assert (row["state"], row["amount_new"]) == (S.SYNC_PAID_OFF, 0)
        assert "tất toán" in row["reason"]
        req, _ = S.apply_refresh(db, req.id, seed.u_req_id)
        assert _amounts(db, req) == [0]                  # dòng vẫn còn, số về 0
        assert float(req.total) == 0

    def test_tra_du_so_voi_no_khong_ra_so_am(self, db, seed):
        p = _payable(db, seed)
        req = _create(db, seed, [LineIn(payable_id=p.id)])
        _set_payable(db, p, paid=1_200_000)              # công nợ âm do trả dư
        assert S.plan_refresh(db, req)["lines"][0]["amount_new"] == 0

    def test_khoan_no_bi_xoa_thi_ve_0(self, db, seed):
        p = _payable(db, seed)
        req = _create(db, seed, [LineIn(payable_id=p.id)])
        db.delete(p)
        db.commit()
        row = S.plan_refresh(db, req)["lines"][0]
        assert (row["state"], row["amount_new"]) == (S.SYNC_PAYABLE_MISSING, 0)
        req, _ = S.apply_refresh(db, req.id, seed.u_req_id)
        assert _amounts(db, req) == [0]

    def test_hai_dong_cung_mot_khoan_no_khong_tinh_gap_doi(self, db, seed):
        """Dòng 1 trỏ khoản nợ qua payable_id (chưa gõ số HĐ), dòng 2 gõ đúng PO + số HĐ của
        cùng khoản đó: nợ chỉ tính cho dòng 1, dòng 2 về 0 — nếu không phiếu chi gấp đôi."""
        p = _payable(db, seed)
        req = _create(db, seed, [LineIn(payable_id=p.id)])
        S.update_request(db, req.id, PRequestUpdate(lines=[
            LineIn(payable_id=p.id, po_code="PO-509", invoice_no="", amount=400_000),
            LineIn(po_code="PO-509", invoice_no="HD-509", amount=600_000),
        ]), seed.u_req_id)
        plan = S.plan_refresh(db, req)
        first, second = plan["lines"]
        assert first["amount_new"] == 1_000_000
        assert first["invoice_no_new"] == "HD-509"       # số HĐ lấy theo công nợ
        assert (second["state"], second["amount_new"]) == (S.SYNC_DUPLICATE, 0)
        assert plan["new_total"] == 1_000_000

    def test_so_hd_go_tay_giu_khi_cong_no_chua_co(self, db, seed):
        """Khoản chi phí nhập khẩu sinh nợ trước khi có số HĐ (bao-CR-319 P5) — người lập gõ số
        HĐ trên phiếu; cập nhật không được xóa trắng số đó."""
        p = _payable(db, seed, invoice_no="", source_type="import_cost")
        req = _create(db, seed, [LineIn(payable_id=p.id, invoice_no="HD-TAY", amount=100)],
                      source_type="import_cost")
        _set_payable(db, p, total=900_000)
        req, _ = S.apply_refresh(db, req.id, seed.u_req_id)
        ln = S.lines_of(db, req.id)[0]
        assert (ln.invoice_no, float(ln.amount)) == ("HD-TAY", 900_000)

    def test_ngay_hd_theo_dot_giao_neu_co_con_khong_thi_giu_ngay_go_tay(self, db, seed):
        po = PurchaseOrder(code="PO-509", supplier_code="NX", created_by=seed.u_req_id)
        db.add(po)
        db.flush()
        item = POItem(po_id=po.id, product_name="Hàng A", created_by=seed.u_req_id)
        db.add(item)
        db.flush()
        d = PODelivery(po_id=po.id, po_item_id=item.id, invoice_no="HD-509",
                       invoice_date="", created_by=seed.u_req_id)
        db.add(d)
        db.commit()
        p = _payable(db, seed, ref_id=d.id)
        req = _create(db, seed, [LineIn(payable_id=p.id, invoice_date="2026-09-15")])
        # Đợt giao chưa gõ ngày HĐ -> ngày nhận hàng KHÔNG được đè ngày gõ tay
        assert S.plan_refresh(db, req)["lines"][0]["invoice_date_new"] == "2026-09-15"
        d.invoice_date = "2026-09-18"                    # sửa ĐMH, gõ ngày HĐ thật
        db.commit()
        row = S.plan_refresh(db, req)["lines"][0]
        assert row["invoice_date_new"] == "2026-09-18" and row["changed"]


class TestChan:
    def test_phieu_da_gui_duyet_thi_400(self, db, seed):
        p = _payable(db, seed)
        req = _create(db, seed, [LineIn(payable_id=p.id)])
        S.set_status(db, req.id, "submitted", seed.u_req_id)
        _set_payable(db, p, total=1_500_000)
        with pytest.raises(HTTPException) as e:
            S.apply_refresh(db, req.id, seed.u_req_id)
        assert e.value.status_code == 400 and "Nháp" in e.value.detail
        assert _amounts(db, req) == [1_000_000]
        plan = S.plan_refresh(db, req)                   # xem trước vẫn được, chỉ không ghi
        assert plan["can_apply"] is False and plan["blocked_reason"]

    @pytest.mark.parametrize("status", ["approved", "paid", "cancelled"])
    def test_cac_trang_thai_khac_nhap_deu_400(self, db, seed, status):
        p = _payable(db, seed)
        req = _create(db, seed, [LineIn(payable_id=p.id)])
        req.status = status
        db.commit()
        with pytest.raises(HTTPException) as e:
            S.apply_refresh(db, req.id, seed.u_req_id)
        assert e.value.status_code == 400

    def test_phieu_tra_truoc_thi_400(self, db, seed):
        req = _create(db, seed, [LineIn(po_code="PO-509", amount=5_000_000)], prepay=1)
        with pytest.raises(HTTPException) as e:
            S.apply_refresh(db, req.id, seed.u_req_id)
        assert e.value.status_code == 400 and "thanh toán trước" in e.value.detail.lower()


class TestCoLechOManChiTiet:
    def test_phieu_cho_duyet_lech_cong_no_bat_co(self, db, seed):
        p = _payable(db, seed)
        req = _create(db, seed, [LineIn(payable_id=p.id)])
        S.set_status(db, req.id, "submitted", seed.u_req_id)
        assert _out(db, req)["out_of_sync"] is False
        _set_payable(db, p, total=1_300_000)
        out = _out(db, S.get_request(db, req.id))
        assert out["out_of_sync"] is True
        line = out["lines"][0]
        assert line["out_of_sync"] is True
        assert (line["payable_remaining"], line["expected_amount"]) == (1_300_000, 1_300_000)

    def test_phieu_da_duyet_khong_tru_can_tru_hai_lan(self, db, seed):
        """Duyệt xong phần cấn trừ đã vào paid_amount — so tiếp với (nợ còn lại - cấn trừ)
        là trừ hai lần và bật cờ lệch oan."""
        p = _payable(db, seed)
        req = _create(db, seed, [LineIn(payable_id=p.id, amount=700_000, offset_amount=300_000)])
        req.status = "approved"
        _set_payable(db, p, paid=300_000)                # cấn trừ đã thực thi lúc duyệt
        out = _out(db, S.get_request(db, req.id))
        assert out["out_of_sync"] is False

    def test_phieu_da_chi_khong_bat_co(self, db, seed):
        p = _payable(db, seed)
        req = _create(db, seed, [LineIn(payable_id=p.id)])
        req.status = "paid"
        _set_payable(db, p, paid=1_000_000)
        out = _out(db, S.get_request(db, req.id))
        assert out["out_of_sync"] is False and out["lines"][0]["expected_amount"] is None

    def test_phieu_tra_truoc_khong_bat_co(self, db, seed):
        req = _create(db, seed, [LineIn(po_code="PO-509", amount=5_000_000)], prepay=1)
        assert _out(db, req)["out_of_sync"] is False
