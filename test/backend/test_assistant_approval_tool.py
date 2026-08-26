"""Tool hộp việc phê duyệt của Trợ lý AI: `my_approval_tasks` + `my_requests_status`.

Chốt các điều: (1) tài khoản chưa gắn hồ sơ nhân sự trả rỗng kèm lời giải thích chứ
không lỗi, (2) việc chờ duyệt đi đúng hàm của màn «Chờ tôi duyệt» và kèm đường dẫn mở
thẳng phiếu, (3) trạng thái phiếu đã trình chỉ thấy phiếu CỦA CHÍNH người hỏi — phiếu
đang chạy nói rõ đang chờ ai ở bước nào, phiếu bị trả lại nói rõ lý do, (4) loại chứng
từ chưa có màn bên v2 thì `url` rỗng chứ không bịa đường dẫn.
"""
from datetime import datetime

from app.modules.approval.instance_model import (INSTANCE_RETURNED,
                                                 INSTANCE_RUNNING,
                                                 TASK_PENDING, ApprovalInstance,
                                                 ApprovalTask)
from app.modules.assistant.tools.approval_tool import (_run_my_approval_tasks,
                                                       _run_my_requests_status)
from app.modules.assistant.tools.base import ToolContext

ACTOR = 1


def _ctx(db, user) -> ToolContext:
    #  Hai tool này không đụng `ctx.profile` (dữ liệu của chính người hỏi, không cần
    #  apply_scope) nên khỏi dựng hồ sơ quyền.
    return ToolContext(db=db, user=user, _profile={"grants": []})


def _phien(db, *, entity="document", entity_id=1, code="01/QD", title="Phiếu test",
           status=INSTANCE_RUNNING, started_by=None, finish_reason=""):
    row = ApprovalInstance(entity=entity, entity_id=entity_id, entity_code=code,
                           entity_title=title, flow_id=1, status=status,
                           started_by_employee_id=started_by,
                           started_at=datetime(2026, 8, 20, 9, 0),
                           finish_reason=finish_reason,
                           created_by=ACTOR, updated_by=ACTOR)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _viec(db, instance, assignee, *, node_name="Trưởng phòng duyệt", due_at=None):
    row = ApprovalTask(instance_id=instance.id, node_seq=1, node_name=node_name,
                       assignee_employee_id=assignee, status=TASK_PENDING,
                       due_at=due_at, created_by=ACTOR, updated_by=ACTOR)
    db.add(row)
    db.commit()
    return row


def _user_khong_ho_so(db):
    from app.modules.user.model import User

    row = User(email="NOEMP", password_hash="x", is_active=True)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


# ── my_approval_tasks ───────────────────────────────────────────────────────────────────

def test_cho_toi_duyet_khong_ho_so_tra_rong_kem_giai_thich(db, seed):
    out = _run_my_approval_tasks(_ctx(db, _user_khong_ho_so(db)), {})
    assert out["total"] == 0 and out["items"] == []
    assert "hồ sơ nhân sự" in out["note"]


def test_cho_toi_duyet_tra_viec_kem_duong_dan(db, seed):
    from app.modules.user.model import User

    phien = _phien(db, entity_id=7, code="05/QDI-DEGO", title="Quy định công tác phí",
                   started_by=seed.emp_req_id)
    _viec(db, phien, seed.emp_nstm_id)

    out = _run_my_approval_tasks(_ctx(db, db.get(User, seed.u_nstm_id)), {})
    assert out["total"] == 1
    dong = out["items"][0]
    assert dong["code"] == "05/QDI-DEGO"
    assert dong["step"] == "Trưởng phòng duyệt"
    assert dong["submitted_by"] == "Người YC"        # tên người trình, không phải id
    assert dong["url"] == "/document/documents/7"    # link mở thẳng văn bản bên v2
    assert out["inbox_url"] == "/document/pending-approval"


def test_cho_toi_duyet_khong_thay_viec_cua_nguoi_khac(db, seed):
    from app.modules.user.model import User

    phien = _phien(db, started_by=seed.emp_req_id)
    _viec(db, phien, seed.emp_nstm_id)   # việc của NSTM, không phải của người hỏi

    out = _run_my_approval_tasks(_ctx(db, db.get(User, seed.u_req_id)), {})
    assert out["total"] == 0


# ── my_requests_status ──────────────────────────────────────────────────────────────────

def test_phieu_cua_toi_dang_chay_noi_ro_dang_cho_ai(db, seed):
    from app.modules.user.model import User

    phien = _phien(db, entity_id=3, code="12/CV", title="Công văn xin xe",
                   started_by=seed.emp_req_id)
    _viec(db, phien, seed.emp_nstm_id, node_name="NSTM soát nội dung")

    out = _run_my_requests_status(_ctx(db, db.get(User, seed.u_req_id)), {})
    assert out["total"] == 1
    dong = out["items"][0]
    assert dong["status"] == "Đang chạy"
    assert dong["waiting_step"] == "NSTM soát nội dung"
    assert dong["waiting_on"] == ["NSTM Chính"]      # TÊN người đang giữ phiếu
    assert dong["url"] == "/document/documents/3"


def test_phieu_bi_tra_lai_tra_kem_ly_do(db, seed):
    from app.modules.user.model import User

    _phien(db, status=INSTANCE_RETURNED, started_by=seed.emp_req_id,
           finish_reason="Thiếu chữ ký nháy của kế toán")

    out = _run_my_requests_status(_ctx(db, db.get(User, seed.u_req_id)), {})
    dong = out["items"][0]
    assert dong["status"] == "Trả lại"
    assert dong["finish_reason"] == "Thiếu chữ ký nháy của kế toán"
    assert "waiting_on" not in dong                  # phiếu đã đóng thì không còn ai giữ


def test_phieu_cua_toi_khong_lan_phieu_nguoi_khac_va_loc_only_open(db, seed):
    from app.modules.user.model import User

    #  entity_id phải khác nhau giữa hai phiếu ĐANG MỞ — khóa `running_slot` ép mỗi
    #  chứng từ chỉ một phiếu đang chạy.
    _phien(db, entity_id=1, code="CUA-TOI-MO", started_by=seed.emp_req_id)
    _phien(db, entity_id=2, code="CUA-TOI-XONG", status=INSTANCE_RETURNED,
           started_by=seed.emp_req_id)
    _phien(db, entity_id=3, code="CUA-NGUOI-KHAC", started_by=seed.emp_nstm_id)

    ctx = _ctx(db, db.get(User, seed.u_req_id))
    tat_ca = _run_my_requests_status(ctx, {})
    assert tat_ca["total"] == 2
    assert {d["code"] for d in tat_ca["items"]} == {"CUA-TOI-MO", "CUA-TOI-XONG"}

    con_mo = _run_my_requests_status(ctx, {"only_open": True})
    assert [d["code"] for d in con_mo["items"]] == ["CUA-TOI-MO"]


def test_loai_chung_tu_chua_co_man_thi_url_rong(db, seed):
    """Đừng bịa đường dẫn: entity ngoài bảng ánh xạ (vd bộ máy duyệt mở cho loại mới)
    thì `url` rỗng để model khỏi gắn link 404."""
    from app.modules.user.model import User

    _phien(db, entity="leave_request", started_by=seed.emp_req_id)
    out = _run_my_requests_status(_ctx(db, db.get(User, seed.u_req_id)), {})
    assert out["items"][0]["url"] == ""
