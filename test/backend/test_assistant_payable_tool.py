"""Tool công nợ + soạn nháp YCTT của Trợ lý AI (`tools/payable_tool.py`).

CHỈ kiểm phần vừa làm: gác quyền hai lớp, tổng hợp số liệu, và luật CHỈ chọn khoản còn
phải trả khi soạn nháp (bài học lỗi phân bổ thanh toán 82ce6ad — tiền dồn vào khoản đã
tất toán là công nợ âm).
"""
import pytest

from app.modules.assistant import tools as T
from app.modules.payable.model import Payable
from app.modules.user.model import User


@pytest.fixture
def khoan_no(db, seed):
    """4 khoản nợ: NCC A có 2 khoản còn nợ + 1 đã tất toán; NCC B 1 khoản còn nợ."""
    rows = [
        Payable(company_id=seed.company_id, supplier_code="NCCA", supplier_name="NCC Anpha",
                source_type="goods", po_code="PO-01", incur_date="2026-08-05", period="2026",
                due_date="2026-09-05", total=1000, paid_amount=0, remaining=1000,
                status="unpaid"),
        Payable(company_id=seed.company_id, supplier_code="NCCA", supplier_name="NCC Anpha",
                source_type="goods", po_code="PO-02", incur_date="2026-08-10", period="2026",
                due_date="2026-08-20", total=500, paid_amount=200, remaining=300,
                status="partial"),
        Payable(company_id=seed.company_id, supplier_code="NCCA", supplier_name="NCC Anpha",
                source_type="goods", po_code="PO-03", incur_date="2026-07-01", period="2026",
                due_date="2026-08-01", total=700, paid_amount=700, remaining=0,
                status="paid"),
        Payable(company_id=seed.company_id, supplier_code="NCCB", supplier_name="NCC Beta",
                source_type="goods", po_code="PO-04", incur_date="2026-08-15", period="2026",
                due_date="2026-09-15", total=400, paid_amount=0, remaining=400,
                status="unpaid"),
    ]
    db.add_all(rows)
    db.commit()
    return rows


def test_lookup_thieu_quyen_thi_denied(db, seed, khoan_no):
    """Không có `payable.read` -> denied, không lộ số nợ lẫn tên NCC."""
    user = db.get(User, seed.u_req_id)
    out = T.run_tool(db, user, "payable_lookup", {"supplier": "NCCA"})
    assert out.get("denied") is True
    assert "summary" not in out and "items" not in out


def test_lookup_loc_ncc_va_tong_con_lai(db, seed, khoan_no, cap_quyen):
    """Lọc theo NCC, mặc định CHỈ khoản còn phải trả; summary tính đúng còn lại."""
    cap_quyen(seed.u_req_id, "payable", scope="all", read=True)
    user = db.get(User, seed.u_req_id)

    out = T.run_tool(db, user, "payable_lookup", {"supplier": "NCCA"})
    assert out["total"] == 2                       # khoản paid bị loại theo mặc định
    assert out["summary"]["remaining"] == 1300.0   # 1000 + 300
    assert {i["payable_id"] for i in out["items"]} == {khoan_no[0].id, khoan_no[1].id}

    # status=all thì thấy cả khoản đã tất toán.
    ca_paid = T.run_tool(db, user, "payable_lookup", {"supplier": "NCCA", "status": "all"})
    assert ca_paid["total"] == 3


def test_lookup_cong_ty_khong_khop_thi_bao_danh_muc(db, seed, khoan_no, cap_quyen):
    """Tên công ty ngoài danh mục -> error + danh sách hợp lệ, KHÔNG lặng lẽ bỏ lọc."""
    cap_quyen(seed.u_req_id, "payable", scope="all", read=True)
    user = db.get(User, seed.u_req_id)
    out = T.run_tool(db, user, "payable_lookup", {"company": "Cong ty khong ton tai"})
    assert out.get("error")
    assert out.get("companies")


def test_draft_can_du_hai_quyen(db, seed, khoan_no, cap_quyen):
    """Soạn nháp YCTT cần CẢ payment_request.create lẫn payable.read — thiếu một là denied."""
    # Chỉ có quyền xem công nợ, không có quyền tạo YCTT.
    cap_quyen(seed.u_req_id, "payable", scope="all", read=True)
    user = db.get(User, seed.u_req_id)
    out = T.run_tool(db, user, "draft_payment_request", {"supplier": "NCCA"})
    assert out.get("denied") is True

    # Chỉ có quyền tạo YCTT, không được xem công nợ — không được vòng qua hàng rào payable.
    user2 = db.get(User, seed.u_nstm_id)
    cap_quyen(seed.u_nstm_id, "payment_request", scope="all", create=True)
    out2 = T.run_tool(db, user2, "draft_payment_request", {"supplier": "NCCA"})
    assert out2.get("denied") is True


def test_draft_chi_chon_khoan_con_no(db, seed, khoan_no, cap_quyen):
    """Nháp theo NCC chỉ gom khoản remaining > 0; khoản đã tất toán không được lọt vào."""
    cap_quyen(seed.u_req_id, "payable", scope="all", read=True)
    cap_quyen(seed.u_req_id, "payment_request", scope="all", create=True)
    user = db.get(User, seed.u_req_id)

    out = T.run_tool(db, user, "draft_payment_request", {"supplier": "NCCA"})
    assert out["status"] == "ready"
    assert out["draft"]["kind"] == "payment_request"
    assert set(out["draft"]["payable_ids"]) == {khoan_no[0].id, khoan_no[1].id}
    assert out["total"] == 2
    assert out["draft"]["total_remaining"] == 1300.0
    assert out["draft"]["suppliers"][0]["supplier_code"] == "NCCA"


def test_draft_theo_ids_loai_khoan_tat_toan(db, seed, khoan_no, cap_quyen):
    """Truyền payable_ids có lẫn khoản đã tất toán -> khoản đó vào skipped_ids."""
    cap_quyen(seed.u_req_id, "payable", scope="all", read=True)
    cap_quyen(seed.u_req_id, "payment_request", scope="all", create=True)
    user = db.get(User, seed.u_req_id)

    ids = [khoan_no[0].id, khoan_no[2].id]   # khoan_no[2] đã paid
    out = T.run_tool(db, user, "draft_payment_request", {"payable_ids": ids})
    assert out["draft"]["payable_ids"] == [khoan_no[0].id]
    assert out["skipped_ids"] == [khoan_no[2].id]


def test_draft_thieu_ncc_lan_ids_thi_hoi_lai(db, seed, khoan_no, cap_quyen):
    """Không có supplier lẫn payable_ids -> error bảo model hỏi lại, không gom nợ cả hệ."""
    cap_quyen(seed.u_req_id, "payable", scope="all", read=True)
    cap_quyen(seed.u_req_id, "payment_request", scope="all", create=True)
    user = db.get(User, seed.u_req_id)
    out = T.run_tool(db, user, "draft_payment_request", {})
    assert out.get("error")
    assert "draft" not in out


# ── payment_request_read (CR-218) ───────────────────────────────────────────────────────

def _tao_yctt(db, seed, created_by):
    import json

    from app.modules.payment_request.model import PaymentRequest, PaymentRequestLine

    req = PaymentRequest(code="YCTT-TEST-1", supplier_code="NCCA", supplier_name="NCC Anpha",
                         company_id=seed.company_id, source_type="goods",
                         request_date="2026-08-20", payment_method="transfer",
                         print_texts=json.dumps({"content": "Thanh toán đợt 1"},
                                                ensure_ascii=False),
                         total=1300, status="approved",
                         created_by=created_by, updated_by=created_by)
    db.add(req)
    db.flush()
    db.add_all([
        PaymentRequestLine(request_id=req.id, po_code="PO-01", invoice_no="HD-001",
                           invoice_date="2026-08-18", amount=1000,
                           created_by=created_by, updated_by=created_by),
        PaymentRequestLine(request_id=req.id, po_code="PO-02", invoice_no="",
                           amount=300, created_by=created_by, updated_by=created_by),
    ])
    db.commit()
    db.refresh(req)
    return req


def test_doc_yctt_thieu_quyen_thi_denied(db, seed):
    _tao_yctt(db, seed, created_by=seed.u_req_id)
    out = T.run_tool(db, db.get(User, seed.u_req_id), "payment_request_read",
                     {"code": "YCTT-TEST-1"})
    assert out.get("denied") is True
    assert "lines" not in out


def test_doc_yctt_ngoai_pham_vi_bao_khong_thay(db, seed, cap_quyen):
    """Scope `own` mà phiếu của người khác -> 'Không tìm thấy', không lộ số tiền lẫn NCC."""
    cap_quyen(seed.u_req_id, "payment_request", scope="own", read=True)
    _tao_yctt(db, seed, created_by=seed.u_nstm_id)
    out = T.run_tool(db, db.get(User, seed.u_req_id), "payment_request_read",
                     {"code": "YCTT-TEST-1"})
    assert "Không tìm thấy" in out["error"]


def test_doc_yctt_recap_du_hinh(db, seed, cap_quyen):
    """Happy path: header + dòng + print_texts đã parse + url — mã thường cũng khớp
    (tool tự upper), hình thức thanh toán trả NHÃN tiếng Việt chứ không trả mã."""
    cap_quyen(seed.u_req_id, "payment_request", scope="own", read=True)
    req = _tao_yctt(db, seed, created_by=seed.u_req_id)

    out = T.run_tool(db, db.get(User, seed.u_req_id), "payment_request_read",
                     {"code": "yctt-test-1"})
    assert out["code"] == "YCTT-TEST-1"
    assert out["status"] == "approved" and out["status_label"]
    assert out["payment_method"] == "Chuyển khoản"
    assert out["total"] == 1300.0
    assert out["print_texts"] == {"content": "Thanh toán đợt 1"}
    assert out["total_lines"] == 2
    assert out["lines"][0] == {"po_code": "PO-01", "invoice_no": "HD-001",
                               "invoice_date": "2026-08-18", "amount": 1000.0}
    assert out["url"] == f"/finance/payment-requests/{req.id}"
    # Phiếu THƯỜNG (prepay=0) thì KHÔNG có sổ treo — đừng làm model tưởng phiếu nào cũng treo.
    assert "prepay_hanging_total" not in out
    assert "hanging" not in out["lines"][0]


# ── Tiền treo trả trước (CR-268) ────────────────────────────────────────────────────────

def _tao_phieu_treo(db, seed, created_by, po_code="", allocated=0, refunded=0):
    """Phiếu trả trước ĐÃ CHI 1 dòng 800: treo còn = 800 - allocated - refunded."""
    from app.modules.payment_request.model import PaymentRequest, PaymentRequestLine

    req = PaymentRequest(code=f"YCTT-TREO-{po_code or 'NCC'}", supplier_code="NCCA",
                         supplier_name="NCC Anpha", company_id=seed.company_id,
                         source_type="goods", request_date="2026-08-25",
                         payment_method="transfer", prepay=1, total=800, status="paid",
                         created_by=created_by, updated_by=created_by)
    db.add(req)
    db.flush()
    db.add(PaymentRequestLine(request_id=req.id, po_code=po_code, invoice_no="",
                              amount=800, allocated_amount=allocated,
                              refunded_amount=refunded,
                              created_by=created_by, updated_by=created_by))
    db.commit()
    db.refresh(req)
    return req


def test_lookup_dinh_kem_tien_treo_khi_du_quyen(db, seed, khoan_no, cap_quyen):
    """Lọc về đúng 1 NCC còn treo -> kèm `prepay_hanging` (tách phần unlinked); nhưng
    thiếu quyền payment_request thì KHÔNG đính kèm — treo là dữ liệu phân hệ YCTT."""
    cap_quyen(seed.u_req_id, "payable", scope="all", read=True)
    user = db.get(User, seed.u_req_id)
    _tao_phieu_treo(db, seed, created_by=seed.u_req_id, po_code="", refunded=300)

    # Chưa có payment_request.read -> im lặng, không lộ treo qua tool công nợ.
    out = T.run_tool(db, user, "payable_lookup", {"supplier": "NCCA"})
    assert "prepay_hanging" not in out

    cap_quyen(seed.u_req_id, "payment_request", scope="all", read=True)
    out2 = T.run_tool(db, user, "payable_lookup", {"supplier": "NCCA"})
    assert out2["prepay_hanging"]["total"] == 500.0      # 800 - 300 hoàn
    assert out2["prepay_hanging"]["unlinked"] == 500.0   # dòng không gắn đơn
    assert out2["prepay_hanging"]["hint"]

    # Kết quả trộn NHIỀU NCC thì không đính kèm — không biết treo của ai để gợi ý.
    out3 = T.run_tool(db, user, "payable_lookup", {})
    assert "prepay_hanging" not in out3


def test_doc_yctt_tra_truoc_kem_so_treo(db, seed, cap_quyen):
    """Phiếu trả trước đã chi: từng dòng kèm allocated/refunded/hanging + tổng treo + hint."""
    cap_quyen(seed.u_req_id, "payment_request", scope="own", read=True)
    _tao_phieu_treo(db, seed, created_by=seed.u_req_id, po_code="PO-01", allocated=600)

    out = T.run_tool(db, db.get(User, seed.u_req_id), "payment_request_read",
                     {"code": "YCTT-TREO-PO-01"})
    assert out["prepay"] is True
    assert out["lines"][0]["allocated_amount"] == 600.0
    assert out["lines"][0]["hanging"] == 200.0
    assert out["prepay_hanging_total"] == 200.0
    assert out["prepay_hint"]
