"""ai-CR-182 — phase 15.1: SỔ THAY ĐỔI do bot ghi + HOÀN TÁC 24 giờ (đại ca chốt 13/10/2026).

Luật: mỗi lần người dùng xác nhận cho bot ghi phiếu (tạo · sửa · xóa · dùng lại nháp · gửi duyệt · lập bộ tài
khoản) thì có MỘT dòng `tab_assistant_change` (DB ERP). Hoàn tác được trong 24 giờ, chính người đó (hoặc quản lý bot
AI `agent_group.read`), phiếu chưa gửi duyệt và chưa bị ai sửa chen vào; làm ngược qua đúng service của form.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.core.auth import get_current_user
from app.core.database import get_db
from app.modules.agent_hub import draft_create as dc
from app.modules.assistant import change_service as cs
from app.modules.assistant import tools as T
from app.modules.assistant.change_model import AssistantChange, ChangeAction, UndoStatus
from app.modules.assistant.tools.update_tool import confirm_update
from app.modules.audit.model import AuditLog
from app.modules.purchase_request.model import PurchaseRequest, PurchaseRequestItem
from app.modules.survey_request.model import SurveyRequest, SurveyRequestLine
from app.modules.user.model import User


# ── Dựng dữ liệu ─────────────────────────────────────────────────────────────────────────

def _ycmh(db, seed, created_by, status="draft", code="YCMH-182"):
    pr = PurchaseRequest(code=code, company_id=seed.company_id, department_id=seed.dept_id,
                         purpose="Mua văn phòng phẩm", need_date="2026-10-20", status=status,
                         created_by=created_by, updated_by=created_by)
    db.add(pr)
    db.flush()
    db.add_all([PurchaseRequestItem(pr_id=pr.id, product_name="Giấy A4", qty=10, unit="ram",
                                    required_date="2026-10-20", created_by=created_by),
                PurchaseRequestItem(pr_id=pr.id, product_name="Bút bi", qty=20, unit="cây",
                                    required_date="2026-10-20", created_by=created_by)])
    db.commit()
    db.refresh(pr)
    return pr


def _ycbg(db, seed, created_by, code="YCBG-182"):
    sr = SurveyRequest(code=code, company_id=seed.company_id, department_id=seed.dept_id, purpose="Khảo sát decal",
                       status="draft", created_by=created_by, updated_by=created_by)
    db.add(sr)
    db.flush()
    db.add(SurveyRequestLine(survey_request_id=sr.id, requirement_detail="Nhãn decal", request_qty=100, uom="tờ",
                             created_by=created_by))
    db.commit()
    db.refresh(sr)
    return sr


def _don_nghi(db, seed, status=1, code="NP-182"):
    from app.modules.leave.catalog_model import LeaveType
    from app.modules.leave.request_model import LeaveRequest, LeaveRequestLine

    phep = db.query(LeaveType).filter(LeaveType.code == "ANNUAL").first()
    if phep is None:
        phep = LeaveType(code="ANNUAL", name="Phép năm", counts_balance=False, is_active=True, sort_order=1)
        db.add(phep)
        db.flush()
    don = LeaveRequest(code=code, company_id=seed.company_id, department_id=seed.dept_id, employee_id=seed.emp_req_id,
                       leave_type_id=phep.id, from_date=date(2026, 10, 12), to_date=date(2026, 10, 12), total_days=1,
                       status=status, reason="Việc riêng", created_by=seed.u_req_id)
    db.add(don)
    db.flush()
    db.add(LeaveRequestLine(request_id=don.id, leave_type_id=phep.id, days=1, sort_order=1))
    db.commit()
    db.refresh(don)
    return don


def _dong(db, pr_id):
    return (db.query(PurchaseRequestItem).filter(PurchaseRequestItem.pr_id == pr_id)
            .order_by(PurchaseRequestItem.id).all())


def _rows(db, **flt):
    q = db.query(AssistantChange)
    for k, v in flt.items():
        q = q.filter(getattr(AssistantChange, k) == v)
    return q.order_by(AssistantChange.id).all()


def _me(db, seed):
    return db.get(User, seed.u_req_id)


def _sua_don_nghi(db, seed, to_date="2026-10-13", source=0):
    """Đề xuất + xác nhận sửa đến ngày của NP-182 — trả dòng sổ UPDATE."""
    out = T.run_tool(db, _me(db, seed), "propose_document_update",
                     {"entity": "leave_request", "code": "NP-182", "changes": {"to_date": to_date}})
    assert out["status"] == "ready", out
    confirm_update(db, _me(db, seed), out["proposal"]["confirm_token"], source=source)
    rows = _rows(db, entity="leave_request", action=int(ChangeAction.UPDATE))
    assert rows
    return rows[-1]


# ── 1. Ghi sổ ở từng đường ───────────────────────────────────────────────────────────────

def test_ghi_so_khi_sua_phieu_qua_the_xac_nhan(db, seed, cap_quyen):
    cap_quyen(seed.u_req_id, "leave_request", scope="own", read=True, write=True)
    _don_nghi(db, seed)
    row = _sua_don_nghi(db, seed, source=2)
    assert row.user_id == seed.u_req_id and row.doc_code == "NP-182" and row.source == 2
    assert row.before["fields"] == {"to_date": "2026-10-12"} and row.after["fields"] == {"to_date": "2026-10-13"}
    assert row.before["leave"]["to_date"] == "2026-10-12" and row.after["leave"]["to_date"] == "2026-10-13"
    assert "Đến ngày" in row.summary and row.after_sig and row.undo_status == int(UndoStatus.NONE)


def test_ghi_so_khi_sua_dong_hang_ycmh(db, seed, cap_quyen):
    cap_quyen(seed.u_req_id, "purchase_request", scope="own", read=True, write=True)
    pr = _ycmh(db, seed, seed.u_req_id)
    out = T.run_tool(db, _me(db, seed), "propose_document_update", {
        "entity": "purchase_request", "code": "YCMH-182", "changes": {"purpose": "Mua giấy in"},
        "line_ops": [{"op": "set_qty", "line_no": 1, "qty": 15}, {"op": "remove", "line_no": 2}]})
    confirm_update(db, _me(db, seed), out["proposal"]["confirm_token"])
    row = _rows(db, entity="purchase_request")[-1]
    assert row.action == int(ChangeAction.UPDATE) and row.entity_id == pr.id
    assert row.before["fields"] == {"purpose": "Mua văn phòng phẩm"}
    assert [(ln["product_name"], ln["qty"]) for ln in row.before["lines"]] == [("Giấy A4", 10.0), ("Bút bi", 20.0)]
    assert [(ln["product_name"], ln["qty"]) for ln in row.after["lines"]] == [("Giấy A4", 15.0)]
    assert row.after_sig == cs.state_sig(db, "purchase_request", pr)


def test_ghi_so_khi_xoa_phieu_qua_the_xac_nhan(db, seed, cap_quyen):
    cap_quyen(seed.u_req_id, "survey_request", scope="own", read=True, delete=True)
    sr = _ycbg(db, seed, seed.u_req_id)
    out = T.run_tool(db, _me(db, seed), "propose_document_delete", {"entity": "survey_request", "code": "YCBG-182"})
    confirm_update(db, _me(db, seed), out["proposal"]["confirm_token"], source=1)
    row = _rows(db, entity="survey_request")[-1]
    assert row.action == int(ChangeAction.DELETE) and row.after is None and row.source == 1
    assert row.before["fields"]["purpose"] == "Khảo sát decal" and len(row.before["lines"]) == 1
    db.refresh(sr)
    assert sr.is_deleted is True and row.after_sig == cs.state_sig(db, "survey_request", sr)


def test_ghi_so_khi_tao_phieu_nhap_tu_chat(db, seed, cap_quyen):
    cap_quyen(seed.u_req_id, "purchase_request", scope="own", read=True, create=True)
    code, oid = dc.create(db, _me(db, seed), "purchase", {
        "purpose": "mua bút", "lines": [{"product_name": "Bút bi", "qty": 5, "unit": "cây"}]}, source=1)
    row = _rows(db, entity="purchase_request")[-1]
    assert row.action == int(ChangeAction.CREATE) and row.entity_id == oid and row.doc_code == code
    assert row.before is None and row.after["fields"]["purpose"] == "mua bút" and len(row.after["lines"]) == 1
    assert row.summary.startswith("Tạo yêu cầu mua hàng (YCMH) ") and row.source == 1


def test_ghi_so_khi_dung_lai_nhap_va_xoa_nhap_va_sua_de_don_nghi(db, seed, cap_quyen, monkeypatch):
    import app.core.auth as auth

    cap_quyen(seed.u_req_id, "purchase_request", scope="own", read=True, write=True, delete=True)
    me = _me(db, seed)
    pr = _ycmh(db, seed, me.id)
    out = dc.update_doc_draft(db, me, "purchase", pr.id,
                              {"lines": [{"product_name": "Kẹp giấy", "qty": 3, "unit": "hộp"}]}, "append")
    assert out["code"] == "YCMH-182"
    row = _rows(db, entity="purchase_request")[-1]
    assert row.action == int(ChangeAction.REUSE) and len(row.before["lines"]) == 2 and len(row.after["lines"]) == 3
    assert "Thêm dòng vào" in row.summary

    #  xóa bớt nháp
    out = dc.delete_mine(db, me, [{"kind": "purchase", "id": pr.id}])
    assert out["deleted"] == ["YCMH-182"]
    row = _rows(db, entity="purchase_request")[-1]
    assert row.action == int(ChangeAction.DELETE) and row.after is None and len(row.before["lines"]) == 3

    #  sửa đè đơn nghỉ nháp trùng ngày
    monkeypatch.setattr(auth, "user_has_permission", lambda db, user, entity, action="read": True)
    don = _don_nghi(db, seed)
    dc.update_leave(db, me, don.id, {"from_date": "2026-10-12", "to_date": "2026-10-12", "reason": "khám bệnh",
                                     "lines": [{"leave_type_id": don.leave_type_id, "days": 1}]})
    row = _rows(db, entity="leave_request")[-1]
    assert row.action == int(ChangeAction.REUSE) and row.before["fields"]["reason"] == "Việc riêng"
    assert row.after["fields"]["reason"] == "khám bệnh"


def test_ghi_so_khi_gui_duyet_va_khong_hoan_tac_duoc(db, seed, monkeypatch):
    monkeypatch.setattr("app.core.auth.user_has_permission", lambda db, user, entity, action: True)
    me = _me(db, seed)
    pr = _ycmh(db, seed, me.id)

    def fake_submit(pid, background_tasks, db, user):
        db.get(PurchaseRequest, pid).status = "submitted"
        db.commit()

    monkeypatch.setattr("app.modules.purchase_request.controller.submit_pr", fake_submit)
    dc.submit(db, me, "purchase", pr.id, source=1)
    row = _rows(db, entity="purchase_request")[-1]
    assert row.action == int(ChangeAction.SUBMIT) and row.before == {"status": "draft"} and row.after["status"] == "submitted"
    ok, reason = cs.can_undo(db, me, row)
    assert not ok and "gửi duyệt" in reason
    with pytest.raises(HTTPException) as e:
        cs.undo(db, me, row.id)
    assert e.value.status_code == 400


def test_ghi_so_khi_lap_bo_tai_khoan(db, seed, cap_quyen):
    from app.modules.role.model import Permission, Role
    from app.modules.assistant.tools.account_setup_tool import confirm_account_setup

    actor = db.query(User).filter(User.email == "DEMOTP").first()
    cap_quyen(actor.id, "user", scope="all", read=True, write=True)
    cap_quyen(actor.id, "role", scope="all", read=True)
    cap_quyen(actor.id, "employee", scope="all", read=True)
    role = Role(code="employee", name="Nhân sự")
    db.add(role)
    db.flush()
    db.add(Permission(role_id=role.id, entity="employee", scope="all", can_read=True))
    db.commit()
    out = T.run_tool(db, actor, "propose_account_setup", {"employee": "TESTREQ", "role_codes": ["employee"]})
    assert out["status"] == "ready", out
    result = confirm_account_setup(db, actor, out["proposal"]["confirm_token"], source=2)
    assert result["updated"]
    row = _rows(db, entity="account_setup")[-1]
    assert row.action == int(ChangeAction.ACCOUNT) and row.entity_id == seed.u_req_id and row.user_id == actor.id
    assert row.before["roles"] == [] and row.after["roles"] == ["Nhân sự"]
    ok, reason = cs.can_undo(db, actor, row)
    assert not ok and "Phân quyền" in reason


def test_ghi_so_hong_khong_lam_hong_duong_ghi_chinh(db, seed, cap_quyen, monkeypatch):
    cap_quyen(seed.u_req_id, "leave_request", scope="own", read=True, write=True)
    don = _don_nghi(db, seed)

    def boom(*a, **k):
        raise RuntimeError("sổ hỏng")

    monkeypatch.setattr(cs, "_fit", boom)
    out = T.run_tool(db, _me(db, seed), "propose_document_update",
                     {"entity": "leave_request", "code": "NP-182", "changes": {"to_date": "2026-10-13"}})
    done = confirm_update(db, _me(db, seed), out["proposal"]["confirm_token"])
    assert done["code"] == "NP-182"
    db.refresh(don)
    assert don.to_date == date(2026, 10, 13) and _rows(db) == []


# ── 2. Hoàn tác ──────────────────────────────────────────────────────────────────────────

def test_hoan_tac_sua_don_nghi_dua_ngay_ve_cu(db, seed, cap_quyen):
    cap_quyen(seed.u_req_id, "leave_request", scope="own", read=True, write=True)
    don = _don_nghi(db, seed)
    row = _sua_don_nghi(db, seed)
    me = _me(db, seed)
    assert cs.can_undo(db, me, row) == (True, "")
    out = cs.undo(db, me, row.id, source=2)
    db.refresh(don)
    assert don.to_date == date(2026, 10, 12) and float(don.total_days) == 1.0
    db.refresh(row)
    assert row.undo_status == int(UndoStatus.UNDONE) and row.undone_by == me.id and row.undone_at is not None
    new = db.get(AssistantChange, out["id"])
    assert new.undo_of == row.id and new.action == int(ChangeAction.UPDATE) and new.summary.startswith("Hoàn tác: ")
    assert new.after["fields"] == {"to_date": "2026-10-12"} and new.source == 2
    assert db.query(AuditLog).filter(AuditLog.entity == "leave_request", AuditLog.action == "undo",
                                     AuditLog.entity_id == don.id).count() == 1
    #  dòng ngược không hoàn tác lại; dòng gốc không hoàn tác lần hai
    assert not cs.can_undo(db, me, new)[0] and "đã được hoàn tác" in cs.can_undo(db, me, row)[1]
    with pytest.raises(HTTPException) as e:
        cs.undo(db, me, row.id)
    assert e.value.status_code == 409


def test_hoan_tac_tao_ycmh_thi_xoa_mem_con_trong_db(db, seed, cap_quyen):
    cap_quyen(seed.u_req_id, "purchase_request", scope="own", read=True, create=True, delete=True)
    me = _me(db, seed)
    code, oid = dc.create(db, me, "purchase", {"purpose": "mua bút",
                                               "lines": [{"product_name": "Bút bi", "qty": 5, "unit": "cây"}]})
    row = _rows(db, entity="purchase_request", action=int(ChangeAction.CREATE))[-1]
    out = cs.undo(db, me, row.id)
    pr = db.get(PurchaseRequest, oid)
    assert pr is not None and pr.is_deleted is True
    assert out["action"] == int(ChangeAction.DELETE) and out["undo_of"] == row.id
    new = db.get(AssistantChange, out["id"])
    assert new.after is None and new.before["fields"]["purpose"] == "mua bút"


def test_hoan_tac_xoa_ycbg_thi_khoi_phuc(db, seed, cap_quyen):
    cap_quyen(seed.u_req_id, "survey_request", scope="own", read=True, delete=True)
    sr = _ycbg(db, seed, seed.u_req_id)
    me = _me(db, seed)
    out = T.run_tool(db, me, "propose_document_delete", {"entity": "survey_request", "code": "YCBG-182"})
    confirm_update(db, me, out["proposal"]["confirm_token"])
    db.refresh(sr)
    assert sr.is_deleted is True
    row = _rows(db, entity="survey_request")[-1]
    out = cs.undo(db, me, row.id)
    db.refresh(sr)
    assert sr.is_deleted is False and sr.deleted_at is None and sr.deleted_by == 0 and sr.status == "draft"
    assert out["action"] == int(ChangeAction.CREATE)
    assert db.query(AuditLog).filter(AuditLog.entity == "survey_request", AuditLog.action == "restore",
                                     AuditLog.entity_id == sr.id).count() == 1
    #  phiếu đã khôi phục rồi thì dòng xóa không hoàn tác lại
    assert "đã được hoàn tác" in cs.can_undo(db, me, row)[1]


def test_hoan_tac_dung_lai_nhap_dua_dong_ve_cu(db, seed, cap_quyen):
    cap_quyen(seed.u_req_id, "purchase_request", scope="own", read=True, write=True)
    me = _me(db, seed)
    pr = _ycmh(db, seed, me.id)
    dc.update_doc_draft(db, me, "purchase", pr.id, {"purpose": "mua mực in",
                                                    "lines": [{"product_name": "Mực in", "qty": 2}]}, "replace")
    db.refresh(pr)
    assert pr.purpose == "mua mực in" and [r.product_name for r in _dong(db, pr.id)] == ["Mực in"]
    row = _rows(db, entity="purchase_request", action=int(ChangeAction.REUSE))[-1]
    cs.undo(db, me, row.id)
    db.refresh(pr)
    assert pr.purpose == "Mua văn phòng phẩm"
    assert [(r.product_name, float(r.qty)) for r in _dong(db, pr.id)] == [("Giấy A4", 10.0), ("Bút bi", 20.0)]


def test_hoan_tac_xoa_viec_du_an_khoi_phuc_deleted_at(db, seed):
    from app.modules.work.task_model import WorkTask
    from app.modules.user.model import User as U

    me = db.get(U, seed.u_req_id)
    t = WorkTask(list_id=1, title="Việc thử", creator_employee_id=seed.emp_req_id, status=1, company_id=seed.company_id)
    db.add(t)
    db.commit()
    t.deleted_at = datetime.utcnow()
    db.commit()
    cs.restore_soft_deleted(db, "work_task", t, me)
    db.refresh(t)
    assert t.deleted_at is None
    assert db.query(AuditLog).filter(AuditLog.entity == "work_task", AuditLog.action == "restore").count() == 1


# ── 3. Chặn hoàn tác ────────────────────────────────────────────────────────────────────

def test_chan_qua_24_gio(db, seed, cap_quyen):
    cap_quyen(seed.u_req_id, "leave_request", scope="own", read=True, write=True)
    _don_nghi(db, seed)
    row = _sua_don_nghi(db, seed)
    row.created_at = datetime.utcnow() - timedelta(hours=24, minutes=1)
    db.commit()
    ok, reason = cs.can_undo(db, _me(db, seed), row)
    assert not ok and "24 giờ" in reason
    with pytest.raises(HTTPException) as e:
        cs.undo(db, _me(db, seed), row.id)
    assert e.value.status_code == 400
    row.created_at = datetime.utcnow() - timedelta(hours=23)
    db.commit()
    assert cs.can_undo(db, _me(db, seed), row)[0]


def test_chan_nguoi_khac_tru_quan_ly_bot_ai(db, seed, cap_quyen):
    cap_quyen(seed.u_req_id, "purchase_request", scope="own", read=True, write=True)
    me = _me(db, seed)
    pr = _ycmh(db, seed, me.id)
    out = T.run_tool(db, me, "propose_document_update",
                     {"entity": "purchase_request", "code": "YCMH-182", "changes": {"purpose": "Mua giấy in"}})
    confirm_update(db, me, out["proposal"]["confirm_token"])
    row = _rows(db, entity="purchase_request")[-1]
    other = db.get(User, seed.u_nstm_id)
    cap_quyen(other.id, "purchase_request", scope="all", read=True, write=True)
    assert cs.get_for(db, other, row.id) is None                   # không thấy dòng của người khác
    with pytest.raises(HTTPException) as e:
        cs.undo(db, other, row.id)
    assert e.value.status_code == 404
    #  Quản lý bot AI (agent_group.read) thấy và hoàn tác được, bằng quyền + phạm vi của chính mình.
    cap_quyen(other.id, "agent_group", scope="all", read=True)
    assert cs.get_for(db, other, row.id) is not None and cs.can_undo(db, other, row) == (True, "")
    out = cs.undo(db, other, row.id)
    assert db.get(AssistantChange, out["id"]).user_id == other.id
    db.refresh(row)
    db.refresh(pr)
    assert row.undone_by == other.id and pr.purpose == "Mua văn phòng phẩm"
    #  Quản lý nhưng KHÔNG có quyền write trên loại phiếu đó thì vẫn bị chặn (dùng quyền của chính mình).
    out = T.run_tool(db, me, "propose_document_update",
                     {"entity": "purchase_request", "code": "YCMH-182", "changes": {"note": "ghi chú mới"}})
    confirm_update(db, me, out["proposal"]["confirm_token"])
    fresh = _rows(db, entity="purchase_request")[-1]
    third = db.query(User).filter(User.email == "DEMOTP").first()
    cap_quyen(third.id, "agent_group", scope="all", read=True)
    ok, reason = cs.can_undo(db, third, fresh)
    assert not ok and "quyền write" in reason


def test_chan_phieu_bi_sua_chen_va_danh_dau_blocked(db, seed, cap_quyen):
    cap_quyen(seed.u_req_id, "leave_request", scope="own", read=True, write=True)
    don = _don_nghi(db, seed)
    row = _sua_don_nghi(db, seed)
    don.reason = "người khác sửa tay"
    db.commit()
    ok, reason = cs.can_undo(db, _me(db, seed), row)
    assert not ok and "sửa sau lúc bot ghi" in reason
    with pytest.raises(HTTPException) as e:
        cs.undo(db, _me(db, seed), row.id)
    assert e.value.status_code == 409
    db.refresh(row)
    assert row.undo_status == int(UndoStatus.BLOCKED)
    db.refresh(don)
    assert don.to_date == date(2026, 10, 13)                       # không ghi gì


def test_chan_phieu_da_gui_duyet(db, seed, cap_quyen):
    cap_quyen(seed.u_req_id, "purchase_request", scope="own", read=True, write=True)
    me = _me(db, seed)
    pr = _ycmh(db, seed, me.id)
    out = T.run_tool(db, me, "propose_document_update",
                     {"entity": "purchase_request", "code": "YCMH-182", "changes": {"purpose": "Mua giấy in"}})
    confirm_update(db, me, out["proposal"]["confirm_token"])
    row = _rows(db, entity="purchase_request")[-1]
    pr.status = "submitted"
    db.commit()
    ok, reason = cs.can_undo(db, me, row)
    assert not ok and "gửi duyệt" in reason
    with pytest.raises(HTTPException) as e:
        cs.undo(db, me, row.id)
    assert e.value.status_code == 409
    db.refresh(pr)
    assert pr.purpose == "Mua giấy in"


def test_chan_khi_mat_quyen_hoac_mat_pham_vi(db, seed, cap_quyen):
    from app.core.auth import perm_cache_clear
    from app.modules.role.model import Permission

    role = cap_quyen(seed.u_req_id, "leave_request", scope="own", read=True, write=True)
    _don_nghi(db, seed)
    row = _sua_don_nghi(db, seed)
    perm = db.query(Permission).filter(Permission.role_id == role.id).one()
    perm.can_write = False
    db.commit()
    perm_cache_clear()
    ok, reason = cs.can_undo(db, _me(db, seed), row)
    assert not ok and "quyền write" in reason
    with pytest.raises(HTTPException) as e:
        cs.undo(db, _me(db, seed), row.id)
    assert e.value.status_code == 403
    #  có quyền nhưng phạm vi không với tới phiếu (đơn do người khác lập, mình chỉ xem được của mình)
    perm.can_write = True
    db.commit()
    perm_cache_clear()
    row.entity_id = 999999
    db.commit()
    ok, reason = cs.can_undo(db, _me(db, seed), row)
    assert not ok and "không còn" in reason


# ── 4. Danh sách ─────────────────────────────────────────────────────────────────────────

def test_list_for_chi_cua_minh_quan_ly_thay_het(db, seed, cap_quyen):
    cap_quyen(seed.u_req_id, "leave_request", scope="own", read=True, write=True)
    _don_nghi(db, seed)
    _sua_don_nghi(db, seed)
    other = db.get(User, seed.u_nstm_id)
    cap_quyen(other.id, "purchase_request", scope="own", read=True, create=True)
    dc.create(db, other, "purchase", {"purpose": "x", "lines": [{"product_name": "Bút", "qty": 1}]})
    mine = cs.list_for(db, _me(db, seed))
    assert [x["entity"] for x in mine] == ["leave_request"]
    assert mine[0]["can_undo"] is True and mine[0]["url"].startswith("/hr/leave-requests/")
    assert mine[0]["action_label"] == "Sửa" and mine[0]["entity_label"] == "Đơn nghỉ phép"
    with pytest.raises(HTTPException) as e:
        cs.list_for(db, _me(db, seed), all_users=True)
    assert e.value.status_code == 403
    cap_quyen(other.id, "agent_group", scope="all", read=True)
    everyone = cs.list_for(db, other, all_users=True)
    assert sorted(x["entity"] for x in everyone) == ["leave_request", "purchase_request"]
    assert [x["entity"] for x in cs.list_for(db, other)] == ["purchase_request"]


def test_anh_qua_lon_bi_cat_bot_dong(db):
    data = {"fields": {"purpose": "x"}, "lines": [{"product_name": "a" * 1000, "qty": 1}] * 200}
    out = cs._fit(data)
    assert out["truncated"] is True and len(out["lines"]) < 200 and cs._size(out) <= cs.MAX_JSON_BYTES


# ── 5. API web + cổng B ─────────────────────────────────────────────────────────────────

@pytest.fixture
def web(db, seed):
    from app.core import app_settings
    from app.modules.assistant.change_controller import router

    app_settings._cache["ai_enabled"] = "true"
    app = FastAPI()
    app.include_router(router)
    who = {"id": seed.u_req_id}
    app.dependency_overrides[get_current_user] = lambda: db.get(User, who["id"])
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app), who


def test_api_web_xem_so_va_hoan_tac(db, seed, cap_quyen, web):
    client, who = web
    cap_quyen(seed.u_req_id, "assistant", scope="all", read=True)
    cap_quyen(seed.u_req_id, "leave_request", scope="own", read=True, write=True)
    don = _don_nghi(db, seed)
    row = _sua_don_nghi(db, seed)
    r = client.get("/api/assistant/changes?limit=10")
    assert r.status_code == 200 and r.json()["success"]
    items = r.json()["data"]["items"]
    assert len(items) == 1 and items[0]["id"] == row.id and items[0]["can_undo"] is True
    r = client.get(f"/api/assistant/changes/{row.id}")
    assert r.json()["data"]["before"]["fields"] == {"to_date": "2026-10-12"}
    assert client.get("/api/assistant/changes?all=1").status_code == 403
    r = client.post(f"/api/assistant/changes/{row.id}/undo")
    assert r.status_code == 200 and r.json()["data"]["undo_of"] == row.id
    db.refresh(don)
    assert don.to_date == date(2026, 10, 12)
    assert client.post(f"/api/assistant/changes/{row.id}/undo").status_code == 409
    #  Người khác không thấy dòng này.
    who["id"] = seed.u_nstm_id
    cap_quyen(seed.u_nstm_id, "assistant", scope="all", read=True)
    assert client.get(f"/api/assistant/changes/{row.id}").status_code == 404
    assert client.get("/api/assistant/changes").json()["data"]["items"] == []


SECRET = "khoa-ky-thu-nghiem"


@pytest.fixture
def gateway(db, monkeypatch):
    """Cổng B + dịch vụ AI ở chế độ service nối qua TestClient (cùng khuôn test_agent_hub_tach_dich_vu)."""
    from app.core.config import settings
    from app.modules.agent_gateway.controller import router as gw_router
    from app.modules.agent_hub import erp

    gw = FastAPI()
    gw.include_router(gw_router)
    gw.dependency_overrides[get_db] = lambda: db
    client = TestClient(gw)
    monkeypatch.setattr(settings, "AGENT_SERVICE_SECRET", SECRET)
    monkeypatch.setattr(settings, "AGENT_GATEWAY_URL", "http://erp.test")
    monkeypatch.setattr(settings, "AGENT_MODE", "service")
    monkeypatch.setattr(erp, "_remote", None)
    calls: list[tuple[str, str]] = []

    def fake_request(method, url, params=None, data=None, headers=None, timeout=0, **kw):
        path = url.replace("http://erp.test", "")
        calls.append((method, path))
        return client.request(method, path, params=params, content=data, headers=headers)

    monkeypatch.setattr(erp.requests, "request", fake_request)
    erp._impl()._tool_defs = (0.0, [])
    return calls


def test_cong_b_so_thay_doi_va_hoan_tac(db, seed, cap_quyen, gateway):
    from app.modules.agent_hub import erp

    cap_quyen(seed.u_req_id, "leave_request", scope="own", read=True, write=True)
    don = _don_nghi(db, seed)
    u = erp.user_by_id(db, seed.u_req_id)
    out = erp.run_tool(db, u, "propose_document_update",
                       {"entity": "leave_request", "code": "NP-182", "changes": {"to_date": "2026-10-13"}})
    erp.confirm_proposal(db, u, out["proposal"]["confirm_token"])
    row = _rows(db, entity="leave_request")[-1]
    assert row.source == 1                                          # cổng B ghi kênh Telegram
    mine = erp.my_changes(db, u, 10)
    assert ("GET", "/api/agent-gw/changes/mine") in gateway
    assert len(mine) == 1 and mine[0]["id"] == row.id and mine[0]["can_undo"] is True
    done = erp.undo_change(db, u, row.id)
    assert ("POST", "/api/agent-gw/changes/undo") in gateway and done["undo_of"] == row.id
    db.refresh(don)
    assert don.to_date == date(2026, 10, 12)
    with pytest.raises(HTTPException) as e:                       # lỗi nghiệp vụ đi nguyên về
        erp.undo_change(db, u, row.id)
    assert e.value.status_code == 409
    with pytest.raises(HTTPException) as e:
        erp.undo_change(db, erp.user_by_id(db, seed.u_nstm_id), row.id)
    assert e.value.status_code == 404
