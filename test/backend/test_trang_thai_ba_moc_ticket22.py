"""bao-CR-292 (ticket 22) — tách «Đang xử lý» của YCMH thành BA mốc theo MISA + độ phủ mã hàng.

Luật chốt với khách 05/09/2026 (khớp nhãn tiến độ dòng của luồng gộp — doc/erp/12 P6-13):
  processing «Đang xử lý»   — NSTM đã tạo ĐMH (kể cả Nháp) nhưng CHƯA đơn nào nhập mã MISA
  purchasing «Đang mua hàng» — có ĐMH nhập MISA nhưng mới phủ MỘT PHẦN mã hàng
  purchased  «Đã mua hàng»  — MỌI mã hàng (trừ dòng Hủy) đều có ĐMH đã nhập MISA
Mốc rời 'dispatched' cũng đổi: chỉ cần có ĐMH là rời, không cần chờ bấm đặt hàng.
"""
import pytest

from app.modules.purchase_order.model import POItem, PurchaseOrder
from app.modules.purchase_request import service as S
from app.modules.purchase_request.model import PurchaseRequest, PurchaseRequestItem


def _make_pr(db, seed, code: str, codes=("SP-A", "SP-B"), status: str = "dispatched"):
    pr = PurchaseRequest(code=code, company_id=seed.company_id, requester="Người YC",
                         requester_id=seed.emp_req_id, department="Phòng Test",
                         status=status, request_date="2026-09-01",
                         created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(pr)
    db.flush()
    for c in codes:
        db.add(PurchaseRequestItem(pr_id=pr.id, product_code=c, product_name=f"Hàng {c}",
                                   item_group="Nhãn", qty=5, unit="cái", price=1000,
                                   created_by=seed.u_req_id, updated_by=seed.u_req_id))
    db.commit()
    db.refresh(pr)
    return pr


def _make_po(db, seed, pr_code: str, codes, misa: str = "", status: str = "approved",
             item_progress: str = "Đã đặt hàng"):
    po = PurchaseOrder(code=f"PO-{pr_code}-{len(codes)}-{misa or 'x'}-{status}",
                       misa_code=misa, pr_code=pr_code, company_id=seed.company_id,
                       status=status, created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(po)
    db.flush()
    for c in codes:
        db.add(POItem(po_id=po.id, product_code=c, product_name=f"Hàng {c}",
                      qty_order=5, progress_status=item_progress,
                      created_by=seed.u_req_id, updated_by=seed.u_req_id))
    db.commit()
    return po


def _set_lines(db, pr, status: str, codes=None):
    for it in S.items_of(db, pr.id):
        if codes is None or it.product_code in codes:
            it.line_status = status
    db.commit()


@pytest.fixture()
def toggle_on(monkeypatch):
    monkeypatch.setattr(S, "dispatch_enabled", lambda: True)


class TestBaMocTicket22:
    def test_chua_co_dmh_thi_van_dispatched(self, db, seed, toggle_on):
        pr = _make_pr(db, seed, "PYC-T22-00")
        S.recompute_status(db, pr)
        assert pr.status == "dispatched"

    def test_co_dmh_nhap_chua_misa_la_processing(self, db, seed, toggle_on):
        """Khách: 'NSTM tạo phiếu mua hàng nhưng chưa nhập đơn Misa' → Đang xử lý.
        Mốc mới: chỉ cần dòng 'Chưa đặt hàng' (đã có ĐMH, kể cả Nháp) là rời dispatched."""
        pr = _make_pr(db, seed, "PYC-T22-01")
        _make_po(db, seed, pr.code, ["SP-A"], misa="", status="draft",
                 item_progress="Chưa đặt hàng")
        _set_lines(db, pr, S.LINE_STATUS_NOT_ORDERED, ["SP-A"])
        S.recompute_status(db, pr)
        assert pr.status == "processing"

    def test_misa_phu_mot_phan_la_purchasing(self, db, seed, toggle_on):
        """1/2 mã hàng có ĐMH nhập MISA → Đang mua hàng."""
        pr = _make_pr(db, seed, "PYC-T22-02")
        _make_po(db, seed, pr.code, ["SP-A"], misa="MISA-001")
        _set_lines(db, pr, "Đã đặt hàng", ["SP-A"])
        S.recompute_status(db, pr)
        assert pr.status == "purchasing"

    def test_misa_phu_du_la_purchased(self, db, seed, toggle_on):
        """Mọi mã hàng đều có ĐMH nhập MISA → Đã mua hàng."""
        pr = _make_pr(db, seed, "PYC-T22-03")
        _make_po(db, seed, pr.code, ["SP-A"], misa="MISA-001")
        _make_po(db, seed, pr.code, ["SP-B"], misa="MISA-002")
        _set_lines(db, pr, "Đã đặt hàng")
        S.recompute_status(db, pr)
        assert pr.status == "purchased"

    def test_dong_huy_khong_doi_phai_phu(self, db, seed, toggle_on):
        """Mã hàng của dòng Hủy đơn không cần phủ MISA — phần còn lại đủ là 'purchased'."""
        pr = _make_pr(db, seed, "PYC-T22-04")
        _make_po(db, seed, pr.code, ["SP-A"], misa="MISA-001")
        _set_lines(db, pr, "Đã đặt hàng", ["SP-A"])
        _set_lines(db, pr, "Hủy đơn", ["SP-B"])
        S.recompute_status(db, pr)
        assert pr.status == "purchased"

    def test_don_nhap_va_don_chet_khong_tinh_misa(self, db, seed, toggle_on):
        """ĐMH Nháp/đã hủy dù có mã MISA cũng KHÔNG tính phủ → vẫn 'processing'."""
        pr = _make_pr(db, seed, "PYC-T22-05")
        _make_po(db, seed, pr.code, ["SP-A"], misa="MISA-001", status="draft")
        _make_po(db, seed, pr.code, ["SP-B"], misa="MISA-002", status="cancelled")
        _set_lines(db, pr, "Đã đặt hàng")
        S.recompute_status(db, pr)
        assert pr.status == "processing"

    def test_hoan_thanh_van_thang_muc_cao_nhat(self, db, seed, toggle_on):
        """Mọi dòng Hoàn thành → 'completed' bất kể MISA (luật cũ giữ nguyên trên đỉnh)."""
        pr = _make_pr(db, seed, "PYC-T22-06", status="purchased")
        _set_lines(db, pr, "Hoàn thành")
        S.recompute_status(db, pr)
        assert pr.status == "completed"

    def test_tu_purchased_lui_ve_purchasing_khi_them_ma_mo(self, db, seed, toggle_on):
        """Đang 'purchased', gỡ MISA khỏi một đơn (sửa lại) → tính lại còn 'purchasing'."""
        pr = _make_pr(db, seed, "PYC-T22-07", status="purchased")
        po_a = _make_po(db, seed, pr.code, ["SP-A"], misa="MISA-001")
        _make_po(db, seed, pr.code, ["SP-B"], misa="MISA-002")
        _set_lines(db, pr, "Đã đặt hàng")
        po_a.misa_code = ""
        db.commit()
        S.recompute_status(db, pr)
        assert pr.status == "purchasing"
