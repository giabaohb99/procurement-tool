"""bao-CR-293 (ticket 20) — Ngày tiếp nhận của YCMH tính từ lúc THU MUA DUYỆT ĐIỀU PHỐI.

Trước đây `request_date` điền lúc lập phiếu (frontend prefill = hôm nay) và cho sửa tay,
nên thời gian quy định có hàng đếm từ lúc người yêu cầu gõ phiếu — phiếu nằm chờ duyệt
một tuần thì NSTM mất oan một tuần SLA. Nay `dispatch_pr` ghi đè `request_date` = ngày
điều phối, và dời theo các dòng mà "Thời gian dự kiến có hàng" vẫn là giá trị TỰ ĐIỀN
theo mốc cũ; dòng NSTM đã sửa tay hoặc cố ý để trống thì giữ nguyên.
"""
from datetime import date, timedelta

from app.modules.catalog import lead_time
from app.modules.purchase_request import service as S
from app.modules.purchase_request.model import PurchaseRequest, PurchaseRequestItem


def _old_base(days: int = 10) -> str:
    return (date.today() - timedelta(days=days)).isoformat()


def _make_pr(db, seed, code: str, request_date: str, lines: list[dict]):
    """lines: [{"group": ..., "expected": ...}] — expected=None nghĩa là để trống."""
    pr = PurchaseRequest(code=code, company_id=seed.company_id, requester="Người YC",
                         requester_id=seed.emp_req_id, department="Phòng Test",
                         status="approved", request_date=request_date,
                         created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(pr)
    db.flush()
    for i, ln in enumerate(lines):
        db.add(PurchaseRequestItem(pr_id=pr.id, product_code=f"SP-T20-{i:02d}",
                                   product_name=f"Hàng {i}", item_group=ln["group"],
                                   qty=5, unit="cái", price=1000,
                                   expected_date=ln.get("expected") or "",
                                   created_by=seed.u_req_id, updated_by=seed.u_req_id))
    db.commit()
    db.refresh(pr)
    return pr


def test_dieu_phoi_ghi_de_ngay_tiep_nhan(db, seed):
    """Phiếu lập 10 ngày trước → điều phối hôm nay thì Ngày tiếp nhận = hôm nay."""
    pr = _make_pr(db, seed, "PYC-T20-01", _old_base(), [{"group": "Nhãn"}])
    pr2, _, _ = S.dispatch_pr(db, pr.id, seed.u_req_id)
    assert pr2.status == "dispatched"
    assert pr2.request_date == date.today().isoformat()


def test_dong_tu_dien_thi_doi_theo_moc_moi(db, seed):
    """Dòng còn nguyên giá trị tự điền (= ngày QĐ theo mốc cũ) → dời sang ngày QĐ theo mốc mới."""
    std = lead_time.std_days_map(db)
    old = _old_base()
    pr = _make_pr(db, seed, "PYC-T20-02", old,
                  [{"group": "Nhãn", "expected": lead_time.regulated_date(std, "Nhãn", old)}])
    S.dispatch_pr(db, pr.id, seed.u_req_id)
    it = S.items_of(db, pr.id)[0]
    assert it.expected_date == lead_time.regulated_date(std, "Nhãn", date.today().isoformat())


def test_dong_nstm_sua_tay_thi_giu_nguyen(db, seed):
    """NSTM đã sửa ngày dự kiến (khác bản tự điền) → điều phối KHÔNG được ghi đè."""
    ngay_tay = (date.today() + timedelta(days=3)).isoformat()
    pr = _make_pr(db, seed, "PYC-T20-03", _old_base(),
                  [{"group": "Nhãn", "expected": ngay_tay}])
    S.dispatch_pr(db, pr.id, seed.u_req_id)
    assert S.items_of(db, pr.id)[0].expected_date == ngay_tay


def test_dong_de_trong_thi_van_trong(db, seed):
    """Dòng cố ý xóa trắng ngày dự kiến → vẫn trống sau điều phối (luật cũ của _save_items)."""
    pr = _make_pr(db, seed, "PYC-T20-04", _old_base(), [{"group": "Nhãn", "expected": None}])
    S.dispatch_pr(db, pr.id, seed.u_req_id)
    assert S.items_of(db, pr.id)[0].expected_date == ""


def test_phieu_khong_co_moc_cu_van_dien_duoc(db, seed):
    """Phiếu cũ `request_date` trống (dữ liệu legacy) → điều phối vẫn điền được, không nổ."""
    pr = _make_pr(db, seed, "PYC-T20-05", "", [{"group": "Nhãn"}])
    pr2, _, _ = S.dispatch_pr(db, pr.id, seed.u_req_id)
    assert pr2.request_date == date.today().isoformat()
