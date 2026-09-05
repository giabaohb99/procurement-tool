"""Tool phiếu hỗ trợ của Trợ lý AI (CR-218) — `ticket_create` (soạn nháp) + `my_tickets`.

`ticket_create` theo khuôn draft_tool: KHÔNG ghi DB, chỉ trả bản đề xuất cho FE mở form
điền sẵn; giá trị model bịa (nhóm tiếp nhận / ưu tiên lạ) phải quy về mặc định chứ không
đổ thẳng vào ô chọn. `my_tickets` chính chủ theo CẢ created_by lẫn requester_id — phòng
phiếu do người khác tạo hộ.
"""
from app.modules.assistant import tools as T
from app.modules.ticket.model import Ticket
from app.modules.user.model import User


# ── ticket_create ───────────────────────────────────────────────────────────────────────

def test_tao_phieu_thieu_quyen_thi_tu_choi(db, seed):
    user = db.get(User, seed.u_req_id)
    out = T.run_tool(db, user, "ticket_create", {"subject": "Lỗi tải báo cáo",
                                                 "body": "Bấm là trang trắng"})
    assert out.get("denied") is True
    assert "draft" not in out


def test_tao_phieu_chuan_hoa_gia_tri_model_dien(db, seed, grant_role):
    """Nhóm tiếp nhận / ưu tiên ngoài danh sách -> về mặc định; draft mang kind='ticket'
    để FE phân biệt với bản nháp YCBG/YCMH/nghỉ phép; và KHÔNG có phiếu nào bị ghi DB."""
    grant_role(seed.u_req_id, "ticket", scope="all", create=True)
    user = db.get(User, seed.u_req_id)

    out = T.run_tool(db, user, "ticket_create", {
        "subject": "  Lỗi tải báo cáo thu mua  ",
        "body": "Bấm Tải báo cáo thì trang trắng.",
        "department": "Phòng bịa đặt",
        "priority": "sieu-khan",
    })
    assert out["status"] == "ready"
    assert out["total"] == 1
    draft = out["draft"]
    assert draft["kind"] == "ticket"
    assert draft["subject"] == "Lỗi tải báo cáo thu mua"
    assert draft["department"] == "Hệ thống / CNTT"     # bịa -> mặc định của form
    assert draft["priority"] == "normal"                # lạ -> normal
    assert "CHƯA được tạo" in out["reminder"]
    assert db.query(Ticket).count() == 0                # soạn nháp thật sự không ghi gì


def test_tao_phieu_giu_gia_tri_hop_le(db, seed, grant_role):
    grant_role(seed.u_req_id, "ticket", scope="all", create=True)
    user = db.get(User, seed.u_req_id)
    out = T.run_tool(db, user, "ticket_create", {
        "subject": "Xin cấp quyền xem công nợ",
        "body": "Cần xem công nợ NCC để đối chiếu.",
        "department": "Kế toán / Tài chính",
        "priority": "high",
    })
    assert out["draft"]["department"] == "Kế toán / Tài chính"
    assert out["draft"]["priority"] == "high"
    assert out["priority_label"]                        # nhãn tiếng Việt cho model tóm tắt


def test_tao_phieu_thieu_subject_hoac_body_bao_loi_mem(db, seed, grant_role):
    grant_role(seed.u_req_id, "ticket", scope="all", create=True)
    user = db.get(User, seed.u_req_id)
    assert "error" in T.run_tool(db, user, "ticket_create", {"subject": "", "body": "x"})
    assert "error" in T.run_tool(db, user, "ticket_create", {"subject": "x", "body": "   "})


# ── my_tickets ──────────────────────────────────────────────────────────────────────────

def _tao_phieu_ho_tro(db, seed):
    """3 phiếu: tự tạo · người khác tạo HỘ (requester_id là mình) · của hẳn người khác."""
    rows = [
        Ticket(code="TK-001", subject="Lỗi tải báo cáo", department="Hệ thống / CNTT",
               priority="normal", status="open",
               created_by=seed.u_req_id, requester_id=seed.emp_req_id),
        Ticket(code="TK-002", subject="Tạo hộ xin cấp quyền", department="Khác",
               priority="high", status="answered",
               created_by=seed.u_nstm_id, requester_id=seed.emp_req_id),
        Ticket(code="TK-003", subject="Phiếu của người khác", department="Khác",
               priority="normal", status="open",
               created_by=seed.u_nstm_id, requester_id=seed.emp_nstm_id),
    ]
    db.add_all(rows)
    db.commit()
    return rows


def test_phieu_cua_toi_thieu_quyen_thi_tu_choi(db, seed):
    _tao_phieu_ho_tro(db, seed)
    out = T.run_tool(db, db.get(User, seed.u_req_id), "my_tickets", {})
    assert out.get("denied") is True
    assert "items" not in out


def test_phieu_cua_toi_chinh_chu_theo_ca_hai_cot(db, seed, grant_role):
    """Thấy cả phiếu người khác tạo HỘ (requester_id = hồ sơ nhân sự mình); phiếu của hẳn
    người khác thì không — dù quyền read scope=all, điều kiện chính chủ vẫn chặt hơn."""
    grant_role(seed.u_req_id, "ticket", scope="all", read=True)
    rows = _tao_phieu_ho_tro(db, seed)

    out = T.run_tool(db, db.get(User, seed.u_req_id), "my_tickets", {})
    assert out["total"] == 2
    assert [i["code"] for i in out["items"]] == ["TK-002", "TK-001"]   # mới nhất trước
    assert out["items"][0]["status_label"] == "Đã trả lời"
    assert out["items"][0]["url"] == f"/support/tickets/{rows[1].id}"


def test_phieu_cua_toi_loc_trang_thai_va_kep_limit(db, seed, grant_role):
    grant_role(seed.u_req_id, "ticket", scope="all", read=True)
    _tao_phieu_ho_tro(db, seed)
    user = db.get(User, seed.u_req_id)

    da_tra_loi = T.run_tool(db, user, "my_tickets", {"status": "answered"})
    assert [i["code"] for i in da_tra_loi["items"]] == ["TK-002"]

    #  status rác -> bỏ lọc chứ không nổ; limit rác -> về mặc định.
    rac = T.run_tool(db, user, "my_tickets", {"status": "sieu-trang-thai", "limit": "mười"})
    assert rac["total"] == 2

    mot = T.run_tool(db, user, "my_tickets", {"limit": 1})
    assert mot["total"] == 1
