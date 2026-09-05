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


def test_lookup_loc_ncc_va_tong_con_lai(db, seed, khoan_no, grant_role):
    """Lọc theo NCC, mặc định CHỈ khoản còn phải trả; summary tính đúng còn lại."""
    grant_role(seed.u_req_id, "payable", scope="all", read=True)
    user = db.get(User, seed.u_req_id)

    out = T.run_tool(db, user, "payable_lookup", {"supplier": "NCCA"})
    assert out["total"] == 2                       # khoản paid bị loại theo mặc định
    assert out["summary"]["remaining"] == 1300.0   # 1000 + 300
    assert {i["payable_id"] for i in out["items"]} == {khoan_no[0].id, khoan_no[1].id}

    # status=all thì thấy cả khoản đã tất toán.
    ca_paid = T.run_tool(db, user, "payable_lookup", {"supplier": "NCCA", "status": "all"})
    assert ca_paid["total"] == 3


def test_lookup_cong_ty_khong_khop_thi_bao_danh_muc(db, seed, khoan_no, grant_role):
    """Tên công ty ngoài danh mục -> error + danh sách hợp lệ, KHÔNG lặng lẽ bỏ lọc."""
    grant_role(seed.u_req_id, "payable", scope="all", read=True)
    user = db.get(User, seed.u_req_id)
    out = T.run_tool(db, user, "payable_lookup", {"company": "Cong ty khong ton tai"})
    assert out.get("error")
    assert out.get("companies")


def test_draft_can_du_hai_quyen(db, seed, khoan_no, grant_role):
    """Soạn nháp YCTT cần CẢ payment_request.create lẫn payable.read — thiếu một là denied."""
    # Chỉ có quyền xem công nợ, không có quyền tạo YCTT.
    grant_role(seed.u_req_id, "payable", scope="all", read=True)
    user = db.get(User, seed.u_req_id)
    out = T.run_tool(db, user, "draft_payment_request", {"supplier": "NCCA"})
    assert out.get("denied") is True

    # Chỉ có quyền tạo YCTT, không được xem công nợ — không được vòng qua hàng rào payable.
    user2 = db.get(User, seed.u_nstm_id)
    grant_role(seed.u_nstm_id, "payment_request", scope="all", create=True)
    out2 = T.run_tool(db, user2, "draft_payment_request", {"supplier": "NCCA"})
    assert out2.get("denied") is True


def test_draft_chi_chon_khoan_con_no(db, seed, khoan_no, grant_role):
    """Nháp theo NCC chỉ gom khoản remaining > 0; khoản đã tất toán không được lọt vào."""
    grant_role(seed.u_req_id, "payable", scope="all", read=True)
    grant_role(seed.u_req_id, "payment_request", scope="all", create=True)
    user = db.get(User, seed.u_req_id)

    out = T.run_tool(db, user, "draft_payment_request", {"supplier": "NCCA"})
    assert out["status"] == "ready"
    assert out["draft"]["kind"] == "payment_request"
    assert set(out["draft"]["payable_ids"]) == {khoan_no[0].id, khoan_no[1].id}
    assert out["total"] == 2
    assert out["draft"]["total_remaining"] == 1300.0
    assert out["draft"]["suppliers"][0]["supplier_code"] == "NCCA"


def test_draft_theo_ids_loai_khoan_tat_toan(db, seed, khoan_no, grant_role):
    """Truyền payable_ids có lẫn khoản đã tất toán -> khoản đó vào skipped_ids."""
    grant_role(seed.u_req_id, "payable", scope="all", read=True)
    grant_role(seed.u_req_id, "payment_request", scope="all", create=True)
    user = db.get(User, seed.u_req_id)

    ids = [khoan_no[0].id, khoan_no[2].id]   # khoan_no[2] đã paid
    out = T.run_tool(db, user, "draft_payment_request", {"payable_ids": ids})
    assert out["draft"]["payable_ids"] == [khoan_no[0].id]
    assert out["skipped_ids"] == [khoan_no[2].id]


def test_draft_thieu_ncc_lan_ids_thi_hoi_lai(db, seed, khoan_no, grant_role):
    """Không có supplier lẫn payable_ids -> error bảo model hỏi lại, không gom nợ cả hệ."""
    grant_role(seed.u_req_id, "payable", scope="all", read=True)
    grant_role(seed.u_req_id, "payment_request", scope="all", create=True)
    user = db.get(User, seed.u_req_id)
    out = T.run_tool(db, user, "draft_payment_request", {})
    assert out.get("error")
    assert "draft" not in out


# ── Lọc hạn trả + tổng hợp nhóm + nhắc tách công ty (bao-CR-273) ────────────────────────

def test_lookup_loc_theo_han_tra(db, seed, khoan_no, grant_role):
    """due_from/due_to lọc theo HẠN TRẢ chứ không phải ngày phát sinh — 'cần thanh toán
    trong tháng 8' chỉ ra PO-02 (hạn 20/08) dù PO-01 cũng phát sinh trong tháng 8."""
    grant_role(seed.u_req_id, "payable", scope="all", read=True)
    user = db.get(User, seed.u_req_id)

    out = T.run_tool(db, user, "payable_lookup",
                     {"due_from": "2026-08-01", "due_to": "2026-08-31"})
    assert out["total"] == 1
    assert out["items"][0]["payable_id"] == khoan_no[1].id
    assert out["summary"]["remaining"] == 300.0


def test_lookup_gom_nhom_theo_ncc(db, seed, khoan_no, grant_role):
    """group_by=supplier: mỗi NCC một dòng tổng hợp, xếp còn-nợ giảm dần, quá hạn tính
    đúng từng nhóm (hôm nay sau 20/08 nên PO-02 của NCCA quá hạn 300); không liệt kê
    từng khoản nữa."""
    grant_role(seed.u_req_id, "payable", scope="all", read=True)
    user = db.get(User, seed.u_req_id)

    out = T.run_tool(db, user, "payable_lookup", {"group_by": "supplier"})
    assert out["group_count"] == 2
    assert "items" not in out
    assert [g["supplier_code"] for g in out["groups"]] == ["NCCA", "NCCB"]
    ncca = out["groups"][0]
    assert ncca["count"] == 2 and ncca["remaining"] == 1300.0 and ncca["overdue"] == 300.0
    assert out["groups"][1]["remaining"] == 400.0
    # summary vẫn tính trên toàn bộ để model nói được tổng cục.
    assert out["summary"]["remaining"] == 1700.0

    sai = T.run_tool(db, user, "payable_lookup", {"group_by": "ncc"})
    assert sai.get("error")


def test_lookup_gom_nhom_theo_cong_ty(db, seed, khoan_no, grant_role):
    """group_by=company: gom theo pháp nhân nợ tiền, kèm TÊN công ty tra từ danh mục."""
    grant_role(seed.u_req_id, "payable", scope="all", read=True)
    user = db.get(User, seed.u_req_id)

    out = T.run_tool(db, user, "payable_lookup", {"group_by": "company"})
    assert out["group_count"] == 1
    g = out["groups"][0]
    assert g["company_id"] == seed.company_id
    assert g["company_name"] == "Cty Test"
    assert g["count"] == 3 and g["remaining"] == 1700.0


def test_draft_nhieu_cong_ty_thi_bao_tach_theo_cong_ty(db, seed, khoan_no, grant_role):
    """Khoản nợ trải trên 2 công ty: từ bao-CR-274 hệ thống tách phiếu theo cả công ty
    nhận hóa đơn, reminder phải BÁO TRƯỚC việc tách đó; một công ty thì không nhắc."""
    from app.modules.company.model import Company

    grant_role(seed.u_req_id, "payable", scope="all", read=True)
    grant_role(seed.u_req_id, "payment_request", scope="all", create=True)
    user = db.get(User, seed.u_req_id)

    # Một công ty -> không được nhắc vô cớ.
    mot = T.run_tool(db, user, "draft_payment_request", {"supplier": "NCC"})
    assert "companies" not in mot["draft"]
    assert "CÔNG TY khác nhau" not in mot["reminder"]

    cty2 = Company(name="Cty Hai", code="CT02", is_active=True)
    db.add(cty2)
    db.flush()
    db.add(Payable(company_id=cty2.id, supplier_code="NCCA", supplier_name="NCC Anpha",
                   source_type="goods", po_code="PO-05", incur_date="2026-08-20",
                   period="2026", due_date="2026-09-20", total=600, paid_amount=0,
                   remaining=600, status="unpaid"))
    db.commit()

    hai = T.run_tool(db, user, "draft_payment_request", {"supplier": "NCC"})
    assert hai["draft"]["companies"] == ["Cty Hai", "Cty Test"]
    assert "2 CÔNG TY khác nhau" in hai["reminder"]
    assert "tách" in hai["reminder"]


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


def test_doc_yctt_ngoai_pham_vi_bao_khong_thay(db, seed, grant_role):
    """Scope `own` mà phiếu của người khác -> 'Không tìm thấy', không lộ số tiền lẫn NCC."""
    grant_role(seed.u_req_id, "payment_request", scope="own", read=True)
    _tao_yctt(db, seed, created_by=seed.u_nstm_id)
    out = T.run_tool(db, db.get(User, seed.u_req_id), "payment_request_read",
                     {"code": "YCTT-TEST-1"})
    assert "Không tìm thấy" in out["error"]


def test_doc_yctt_recap_du_hinh(db, seed, grant_role):
    """Happy path: header + dòng + print_texts đã parse + url — mã thường cũng khớp
    (tool tự upper), hình thức thanh toán trả NHÃN tiếng Việt chứ không trả mã."""
    grant_role(seed.u_req_id, "payment_request", scope="own", read=True)
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
    # Phiếu không có phần cấn trừ thì cũng KHÔNG có cụm offset (CR-260) — tránh nhiễu.
    assert "offset_total" not in out and "offset_check" not in out


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


def test_lookup_dinh_kem_tien_treo_khi_du_quyen(db, seed, khoan_no, grant_role):
    """Lọc về đúng 1 NCC còn treo -> kèm `prepay_hanging` (tách phần unlinked); nhưng
    thiếu quyền payment_request thì KHÔNG đính kèm — treo là dữ liệu phân hệ YCTT."""
    grant_role(seed.u_req_id, "payable", scope="all", read=True)
    user = db.get(User, seed.u_req_id)
    _tao_phieu_treo(db, seed, created_by=seed.u_req_id, po_code="", refunded=300)

    # Chưa có payment_request.read -> im lặng, không lộ treo qua tool công nợ.
    out = T.run_tool(db, user, "payable_lookup", {"supplier": "NCCA"})
    assert "prepay_hanging" not in out

    grant_role(seed.u_req_id, "payment_request", scope="all", read=True)
    out2 = T.run_tool(db, user, "payable_lookup", {"supplier": "NCCA"})
    assert out2["prepay_hanging"]["total"] == 500.0      # 800 - 300 hoàn
    assert out2["prepay_hanging"]["unlinked"] == 500.0   # dòng không gắn đơn
    assert out2["prepay_hanging"]["hint"]

    # Kết quả trộn NHIỀU NCC thì không đính kèm — không biết treo của ai để gợi ý.
    out3 = T.run_tool(db, user, "payable_lookup", {})
    assert "prepay_hanging" not in out3


def test_doc_yctt_tra_truoc_kem_so_treo(db, seed, grant_role):
    """Phiếu trả trước đã chi: từng dòng kèm allocated/refunded/hanging + tổng treo + hint."""
    grant_role(seed.u_req_id, "payment_request", scope="own", read=True)
    _tao_phieu_treo(db, seed, created_by=seed.u_req_id, po_code="PO-01", allocated=600)

    out = T.run_tool(db, db.get(User, seed.u_req_id), "payment_request_read",
                     {"code": "YCTT-TREO-PO-01"})
    assert out["prepay"] is True
    assert out["lines"][0]["allocated_amount"] == 600.0
    assert out["lines"][0]["hanging"] == 200.0
    assert out["prepay_hanging_total"] == 200.0
    assert out["prepay_hint"]


# ── Cấn trừ tiền treo ghi trên phiếu (CR-260) ───────────────────────────────────────────

def _tao_yctt_can_tru(db, seed, created_by, status, offset=300.0, amount=200.0):
    """Phiếu THƯỜNG 1 dòng: chi `amount` + cấn trừ `offset`, trỏ khoản nợ (PO-CT, HD-CT-1)."""
    from app.modules.payment_request.model import PaymentRequest, PaymentRequestLine

    req = PaymentRequest(code="YCTT-CT-1", supplier_code="NCCA", supplier_name="NCC Anpha",
                         company_id=seed.company_id, source_type="goods",
                         request_date="2026-09-01", payment_method="transfer",
                         total=amount, status=status,
                         created_by=created_by, updated_by=created_by)
    db.add(req)
    db.flush()
    db.add(PaymentRequestLine(request_id=req.id, po_code="PO-CT", invoice_no="HD-CT-1",
                              amount=amount, offset_amount=offset,
                              created_by=created_by, updated_by=created_by))
    db.commit()
    return req


def _tao_no_khop_hd(db, seed, total=500.0, paid=0.0):
    """Khoản nợ khớp đúng (NCCA, goods, PO-CT, HD-CT-1) mà dòng cấn trừ trỏ tới."""
    p = Payable(company_id=seed.company_id, supplier_code="NCCA", supplier_name="NCC Anpha",
                source_type="goods", po_code="PO-CT", invoice_no="HD-CT-1",
                incur_date="2026-08-28", period="2026", due_date="2026-09-28",
                total=total, paid_amount=paid, remaining=total - paid,
                status="unpaid" if paid <= 0 else "partial")
    db.add(p)
    db.commit()
    return p


def test_doc_yctt_nhap_can_tru_chi_la_y_dinh(db, seed, grant_role):
    """Bản nháp có cấn trừ: dòng kèm offset_amount, có offset_total + hint nói rõ đây mới
    là Ý ĐỊNH; KHÔNG chạy soát khô (offset_check) cho nháp — nháp sửa thoải mái."""
    grant_role(seed.u_req_id, "payment_request", scope="own", read=True)
    _tao_yctt_can_tru(db, seed, created_by=seed.u_req_id, status="draft")

    out = T.run_tool(db, db.get(User, seed.u_req_id), "payment_request_read",
                     {"code": "YCTT-CT-1"})
    assert out["lines"][0]["offset_amount"] == 300.0
    assert out["lines"][0]["amount"] == 200.0          # amount = phần CHI THẬT, tách bạch
    assert out["offset_total"] == 300.0
    assert "Ý ĐỊNH" in out["offset_hint"]
    assert "offset_check" not in out


def test_doc_yctt_cho_duyet_soat_kho_ok(db, seed, grant_role):
    """Chờ duyệt + treo đủ + nợ đủ -> offset_check.ok=True, không có problems."""
    grant_role(seed.u_req_id, "payment_request", scope="own", read=True)
    _tao_phieu_treo(db, seed, created_by=seed.u_req_id)     # treo cấp NCC còn 800
    _tao_no_khop_hd(db, seed)                               # nợ còn 500 >= cấn trừ 300
    _tao_yctt_can_tru(db, seed, created_by=seed.u_req_id, status="submitted")

    out = T.run_tool(db, db.get(User, seed.u_req_id), "payment_request_read",
                     {"code": "YCTT-CT-1"})
    assert out["offset_check"] == {"ok": True, "problems": []}
    assert "hợp lệ" in out["offset_hint"]


def test_doc_yctt_cho_duyet_bao_thieu_treo(db, seed, grant_role):
    """Chờ duyệt mà NCC KHÔNG còn treo -> ok=False, problems nói vượt tiền treo, hint
    chỉ đúng luật: không duyệt một phần, Từ chối để người lập tạo phiếu mới."""
    grant_role(seed.u_req_id, "payment_request", scope="own", read=True)
    _tao_no_khop_hd(db, seed)
    _tao_yctt_can_tru(db, seed, created_by=seed.u_req_id, status="submitted")

    out = T.run_tool(db, db.get(User, seed.u_req_id), "payment_request_read",
                     {"code": "YCTT-CT-1"})
    assert out["offset_check"]["ok"] is False
    assert any("vượt tiền treo" in p for p in out["offset_check"]["problems"])
    assert "TỪ CHỐI" in out["offset_hint"]


def test_doc_yctt_cho_duyet_bao_no_khong_du(db, seed, grant_role):
    """Nợ đích đã bị trả bớt nơi khác (còn 100 < cấn trừ 300) -> problems nêu đúng dòng.
    Đây là đúng tình huống chặn duyệt của apply_line_offsets — soát khô phải bắt được."""
    grant_role(seed.u_req_id, "payment_request", scope="own", read=True)
    _tao_phieu_treo(db, seed, created_by=seed.u_req_id)     # treo đủ 800
    _tao_no_khop_hd(db, seed, total=500, paid=400)          # nợ chỉ còn 100
    _tao_yctt_can_tru(db, seed, created_by=seed.u_req_id, status="submitted")

    out = T.run_tool(db, db.get(User, seed.u_req_id), "payment_request_read",
                     {"code": "YCTT-CT-1"})
    assert out["offset_check"]["ok"] is False
    assert any("PO-CT" in p for p in out["offset_check"]["problems"])


def test_doc_yctt_da_duyet_bao_da_thuc_thi(db, seed, grant_role):
    """Phiếu đã duyệt: không soát khô nữa, hint nói phần cấn trừ ĐÃ trừ lúc duyệt."""
    grant_role(seed.u_req_id, "payment_request", scope="own", read=True)
    _tao_yctt_can_tru(db, seed, created_by=seed.u_req_id, status="approved")

    out = T.run_tool(db, db.get(User, seed.u_req_id), "payment_request_read",
                     {"code": "YCTT-CT-1"})
    assert out["offset_total"] == 300.0
    assert "offset_check" not in out
    assert "ĐÃ" in out["offset_hint"] and "DUYỆT" in out["offset_hint"]


# ── Nháp YCTT tự chia cấn trừ FIFO (CR-264) ─────────────────────────────────────────────

def test_draft_chia_can_tru_fifo_theo_han(db, seed, khoan_no, grant_role):
    """NCC còn treo 800: nháp chia cấn trừ theo FIFO hạn nợ — PO-02 (hạn 20/08, nợ 300)
    ăn trước, PO-01 (hạn 05/09) nhận phần còn lại 500; cash_total = tổng nợ - cấn trừ."""
    grant_role(seed.u_req_id, "payable", scope="all", read=True)
    grant_role(seed.u_req_id, "payment_request", scope="all", create=True, read=True)
    _tao_phieu_treo(db, seed, created_by=seed.u_req_id)      # treo cấp NCC = 800
    user = db.get(User, seed.u_req_id)

    out = T.run_tool(db, user, "draft_payment_request", {"supplier": "NCCA"})
    assert out["draft"]["offsets"] == {khoan_no[1].id: 300.0, khoan_no[0].id: 500.0}
    assert out["draft"]["offset_total"] == 800.0
    assert out["draft"]["cash_total"] == 500.0               # 1300 nợ - 800 cấn trừ
    assert out["draft"]["suppliers"][0]["offset"] == 800.0
    assert "cấn trừ" in out["reminder"]


def test_draft_khong_treo_thi_khong_de_xuat_can_tru(db, seed, khoan_no, grant_role):
    """NCC không còn treo -> nháp KHÔNG có cụm offsets, reminder không nhắc cấn trừ vô cớ."""
    grant_role(seed.u_req_id, "payable", scope="all", read=True)
    grant_role(seed.u_req_id, "payment_request", scope="all", create=True, read=True)
    user = db.get(User, seed.u_req_id)

    out = T.run_tool(db, user, "draft_payment_request", {"supplier": "NCCA"})
    assert "offsets" not in out["draft"]
    assert "offset_total" not in out["draft"]


def test_draft_thieu_quyen_doc_yctt_thi_khong_chia_treo(db, seed, khoan_no, grant_role):
    """Chỉ có payment_request.create (không read): vẫn nháp được nhưng KHÔNG đề xuất
    cấn trừ — số treo là dữ liệu phân hệ YCTT, quyền tạo không kéo theo quyền đọc."""
    grant_role(seed.u_req_id, "payable", scope="all", read=True)
    grant_role(seed.u_req_id, "payment_request", scope="all", create=True)
    _tao_phieu_treo(db, seed, created_by=seed.u_req_id)      # treo có thật nhưng không được lộ
    user = db.get(User, seed.u_req_id)

    out = T.run_tool(db, user, "draft_payment_request", {"supplier": "NCCA"})
    assert out["status"] == "ready"
    assert "offsets" not in out["draft"]


def test_draft_treo_it_hon_no_chi_chia_du_treo(db, seed, khoan_no, grant_role):
    """Treo chỉ còn 250 (< nợ 1300): FIFO cấp hết 250 cho khoản tới hạn sớm nhất (PO-02),
    khoản sau không được chia — tổng cấn trừ không bao giờ vượt treo còn lại."""
    grant_role(seed.u_req_id, "payable", scope="all", read=True)
    grant_role(seed.u_req_id, "payment_request", scope="all", create=True, read=True)
    _tao_phieu_treo(db, seed, created_by=seed.u_req_id, refunded=550)   # treo còn 250
    user = db.get(User, seed.u_req_id)

    out = T.run_tool(db, user, "draft_payment_request", {"supplier": "NCCA"})
    assert out["draft"]["offsets"] == {khoan_no[1].id: 250.0}
    assert out["draft"]["offset_total"] == 250.0
    assert out["draft"]["cash_total"] == 1050.0
