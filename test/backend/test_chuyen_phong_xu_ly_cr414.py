"""bao-CR-414 GĐ5 — nút CHUYỂN PHÒNG XỬ LÝ (đường 2) + TRẢ VỀ phòng lập, YCMH và YCBG.

Luật đã chốt (doc/erp/12 §5.1.7): chỉ chuyển được khi việc mua CHƯA thật sự bắt đầu ngoài đời.
  · YCMH: phiếu `approved`/`dispatched`, mọi dòng chưa hủy còn `no_po`. Chuyển = gỡ NSTM mọi
    dòng, đổi phòng, phiếu về `approved` để phòng nhận điều phối lại.
  · YCBG: phiếu `approved`/`processing`, chưa dòng nào hoàn thành, chưa phương án nào được
    chọn, chưa sinh YCMH. Chuyển = gỡ NSTM + ngày tiếp nhận mọi dòng; trạng thái giữ nguyên.
  · Ai bấm: quản lý thu mua của phòng ĐANG CẦM phiếu (bậc `dept_proc` có quyền duyệt) hoặc
    thu mua toàn quyền (`proc`/`all`). Trưởng bộ phận (bậc `dept`) và NSTM không duyệt: không.
  · Lý do BẮT BUỘC, ghi vào nhật ký `transfer_dept` / `return_dept`. Trả về = đích 0.
  · Không chuyển một phần dòng.
"""
import json

import pytest
from fastapi import BackgroundTasks, HTTPException

from app.core.auth import get_perm_profile, perm_cache_clear
from app.core.scoping import holds_handling_dept
from app.modules.audit.model import AuditLog
from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.notification.model import Notification
from app.modules.purchase_request import controller as pr_ctl
from app.modules.purchase_request import service as pr_service
from app.modules.purchase_request.model import PurchaseRequest, PurchaseRequestItem
from app.modules.purchase_request.schema import TransferDeptIn as PrTransferIn
from app.modules.role.model import Permission, Role
from app.modules.survey_request import controller as sr_ctl
from app.modules.survey_request import service as sr_service
from app.modules.survey_request.model import (LS_COMPLETED, LS_RESURVEY, SurveyRequest,
                                              SurveyRequestLine, SurveyRequestOption,
                                              SurveyRequestPr)
from app.modules.survey_request.schema import TransferDeptIn as SrTransferIn
from app.modules.user.model import User, UserRole


@pytest.fixture(autouse=True)
def _clear_perm_cache():
    perm_cache_clear()
    yield
    perm_cache_clear()


@pytest.fixture
def two_departments(db, seed):
    factory = Department(code="NM5", name="Nhà máy", company_id=seed.company_id, is_active=True)
    purchasing = Department(code="TM5", name="Thu mua", company_id=seed.company_id, is_active=True)
    db.add_all([factory, purchasing])
    db.flush()
    return factory.id, purchasing.id


_counter = {"n": 0}


def _actor(db, seed, entity: str, scope: str, dept_id: int | None, *, approve: bool = True,
           write: bool = False):
    """Một người có quyền `entity` bậc `scope` ở phòng `dept_id`; mặc định có quyền DUYỆT."""
    _counter["n"] += 1
    n = _counter["n"]
    emp = Employee(code=f"T414{n:02d}", full_name=f"Người chuyển {n}", company_id=seed.company_id,
                   department_id=dept_id or 0, is_active=True)
    db.add(emp)
    db.flush()
    user = User(email=f"T414{n:02d}", employee_id=emp.id, password_hash="x", is_active=True)
    db.add(user)
    db.flush()
    role = Role(code=f"RT414{n:02d}", name="Vai trò test")
    db.add(role)
    db.flush()
    db.add(Permission(role_id=role.id, entity=entity, scope=scope, can_read=True,
                      can_approve=approve, can_write=write))
    db.add(UserRole(user_id=user.id, role_id=role.id))
    db.flush()
    perm_cache_clear()
    return user


def _add_pr(db, seed, code: str, dept_id: int, *, status: str = "approved", handler_dept_id: int = 0,
            lines: tuple[tuple[str, str], ...] = (("no_po", "NSTM01"),)) -> PurchaseRequest:
    """YCMH có `lines` = ((line_status, assignee), ...)."""
    pr = PurchaseRequest(code=code, company_id=seed.company_id, department_id=dept_id,
                         department="Phòng lập", handler_dept_id=handler_dept_id, status=status,
                         requester_id=seed.emp_req_id, created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(pr)
    db.flush()
    for i, (st, who) in enumerate(lines):
        db.add(PurchaseRequestItem(pr_id=pr.id, product_name=f"Hàng {i + 1}", line_status=st,
                                   assignee=who, created_by=seed.u_req_id, updated_by=seed.u_req_id))
    db.commit()
    return pr


def _add_sr(db, seed, code: str, dept_id: int, *, status: str = "processing", handler_dept_id: int = 0,
            lines: tuple[dict, ...] = ({"assignee": "NSTM01", "received_date": "2026-09-01"},)) -> SurveyRequest:
    s = SurveyRequest(code=code, company_id=seed.company_id, department_id=dept_id,
                      department="Phòng lập", handler_dept_id=handler_dept_id, status=status,
                      requester_id=seed.emp_req_id, created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(s)
    db.flush()
    for i, ln in enumerate(lines):
        db.add(SurveyRequestLine(survey_request_id=s.id, item_group=f"Nhóm {i + 1}",
                                 created_by=seed.u_req_id, updated_by=seed.u_req_id, **ln))
    db.commit()
    return s


def _audit(db, entity: str, entity_id: int) -> list[AuditLog]:
    return (db.query(AuditLog).filter(AuditLog.entity == entity, AuditLog.entity_id == entity_id)
            .order_by(AuditLog.id).all())


def _data(resp) -> dict:
    return json.loads(resp.body)["data"]


def _pr_transfer(db, user, pid: int, target: int, reason: str = "Nhà máy tự mua gần hơn") -> dict:
    return _data(pr_ctl.transfer_dept_(pid, PrTransferIn(handler_dept_id=target, reason=reason),
                                       BackgroundTasks(), db, user))


def _pr_return(db, user, pid: int, reason: str = "Phòng lập tự mua") -> dict:
    return _data(pr_ctl.return_dept_(pid, PrTransferIn(reason=reason), BackgroundTasks(), db, user))


def _sr_transfer(db, user, sid: int, target: int, reason: str = "Nhà máy khảo sát tại chỗ") -> dict:
    return _data(sr_ctl.transfer_dept_(sid, SrTransferIn(handler_dept_id=target, reason=reason),
                                       BackgroundTasks(), db, user))


def _sr_return(db, user, sid: int, reason: str = "Phòng lập tự khảo sát") -> dict:
    return _data(sr_ctl.return_dept_(sid, SrTransferIn(reason=reason), BackgroundTasks(), db, user))


# ── Ai được bấm: holds_handling_dept ─────────────────────────────────────────────────────

def test_holding_dept_manager_may_transfer_but_other_dept_manager_may_not(db, seed, two_departments):
    factory_id, purchasing_id = two_departments
    pr = _add_pr(db, seed, "PYC-TM-NHO-NM", purchasing_id, handler_dept_id=factory_id)
    holder = _actor(db, seed, "purchase_request", "dept_proc", factory_id)
    origin = _actor(db, seed, "purchase_request", "dept_proc", purchasing_id)
    assert holds_handling_dept(get_perm_profile(db, holder), "purchase_request", pr) is True
    # Phòng lập đã nhờ đi rồi thì quản lý thu mua phòng lập KHÔNG kéo lại được.
    assert holds_handling_dept(get_perm_profile(db, origin), "purchase_request", pr) is False


def test_full_scope_manager_may_transfer_any_ticket(db, seed, two_departments):
    factory_id, purchasing_id = two_departments
    pr = _add_pr(db, seed, "PYC-NM", factory_id)
    for scope in ("proc", "all"):
        user = _actor(db, seed, "purchase_request", scope, purchasing_id)
        assert holds_handling_dept(get_perm_profile(db, user), "purchase_request", pr) is True


def test_dept_head_and_staff_without_approve_may_not_transfer(db, seed, two_departments):
    factory_id, _ = two_departments
    pr = _add_pr(db, seed, "PYC-NM", factory_id)
    head = _actor(db, seed, "purchase_request", "dept", factory_id)              # TBP: duyệt bậc dept
    staff = _actor(db, seed, "purchase_request", "dept_proc", factory_id, approve=False, write=True)
    assert holds_handling_dept(get_perm_profile(db, head), "purchase_request", pr) is False
    assert holds_handling_dept(get_perm_profile(db, staff), "purchase_request", pr) is False


def test_dept_proc_manager_of_requesting_dept_holds_ticket_when_not_handed_over(db, seed, two_departments):
    factory_id, _ = two_departments
    pr = _add_pr(db, seed, "PYC-NM", factory_id)                                 # handler = 0
    user = _actor(db, seed, "purchase_request", "dept_proc", factory_id)
    assert holds_handling_dept(get_perm_profile(db, user), "purchase_request", pr) is True


# ── YCMH: điều kiện chuyển ───────────────────────────────────────────────────────────────

def test_pr_transferable_only_before_any_line_has_a_po(db, seed, two_departments):
    factory_id, _ = two_departments
    ok = _add_pr(db, seed, "PYC-OK", factory_id, status="dispatched",
                 lines=(("no_po", "A"), ("cancelled", "B")))     # dòng đã hủy bỏ qua
    has_po = _add_pr(db, seed, "PYC-PO", factory_id, lines=(("no_po", "A"), ("not_ordered", "B")))
    purchasing = _add_pr(db, seed, "PYC-MUA", factory_id, status="purchasing")
    submitted = _add_pr(db, seed, "PYC-CHO", factory_id, status="submitted")
    assert pr_service.can_transfer_dept(db, ok) is True
    assert pr_service.can_transfer_dept(db, has_po) is False
    assert pr_service.can_transfer_dept(db, purchasing) is False
    assert pr_service.can_transfer_dept(db, submitted) is False


def test_pr_transfer_clears_assignees_moves_dept_and_logs_reason(db, seed, two_departments):
    factory_id, purchasing_id = two_departments
    pr = _add_pr(db, seed, "PYC-CHUYEN", purchasing_id, status="dispatched",
                 lines=(("no_po", seed.emp_nstm_code), ("no_po", seed.emp_nstm_code)))
    pr.assignee_id = 99
    db.commit()
    user = _actor(db, seed, "purchase_request", "dept_proc", purchasing_id)

    out = _pr_transfer(db, user, pr.id, factory_id, reason="Nhà máy mua trực tiếp tại địa phương")

    db.refresh(pr)
    assert pr.handler_dept_id == factory_id
    assert pr.status == "approved"                    # về «Đã duyệt» để phòng nhận điều phối lại
    assert pr.assignee_id == 0
    assert all(it.assignee == "" for it in pr_service.items_of(db, pr.id))
    assert all(it.line_status == "no_po" for it in pr_service.items_of(db, pr.id))
    assert out["handler_dept_id"] == factory_id
    logs = _audit(db, "purchase_request", pr.id)
    assert logs[-1].action == "transfer_dept"
    assert "Nhà máy mua trực tiếp tại địa phương" in logs[-1].message
    assert "Phòng lập -> Nhà máy" in logs[-1].message
    # Người lập + NSTM bị gỡ đều có chuông.
    titles = {n.user_id: n.title for n in db.query(Notification).all()}
    assert titles.get(seed.u_req_id, "").startswith("PYC-CHUYEN — Chuyển")
    assert titles.get(seed.u_nstm_id, "").startswith("PYC-CHUYEN — Gỡ phân công")


def test_pr_transfer_by_other_department_manager_is_forbidden(db, seed, two_departments):
    factory_id, purchasing_id = two_departments
    pr = _add_pr(db, seed, "PYC-TM", purchasing_id)
    outsider = _actor(db, seed, "purchase_request", "dept_proc", factory_id)
    # Ngoài phạm vi xem của bậc dept_proc -> 404 (không lộ phiếu), trước cả chốt 403.
    with pytest.raises(HTTPException) as e:
        _pr_transfer(db, outsider, pr.id, factory_id)
    assert e.value.status_code in (403, 404)
    db.refresh(pr)
    assert pr.handler_dept_id == 0


def test_pr_transfer_by_requesting_dept_after_handover_is_forbidden(db, seed, two_departments):
    """Phiếu đã nhờ nhà máy: quản lý phòng lập vẫn THẤY (phòng lập) nhưng không kéo lại được."""
    factory_id, purchasing_id = two_departments
    pr = _add_pr(db, seed, "PYC-TM-NHO-NM", purchasing_id, handler_dept_id=factory_id)
    origin = _actor(db, seed, "purchase_request", "dept_proc", purchasing_id)
    with pytest.raises(HTTPException) as e:
        _pr_return(db, origin, pr.id)
    assert e.value.status_code == 403


def test_pr_transfer_requires_reason_and_a_real_different_active_target(db, seed, two_departments):
    factory_id, purchasing_id = two_departments
    pr = _add_pr(db, seed, "PYC-TM", purchasing_id)
    user = _actor(db, seed, "purchase_request", "all", purchasing_id)
    with pytest.raises(HTTPException) as e:
        _pr_transfer(db, user, pr.id, factory_id, reason="   ")
    assert e.value.status_code == 400 and "lý do" in e.value.detail.lower()
    with pytest.raises(HTTPException) as e:
        _pr_transfer(db, user, pr.id, purchasing_id)           # trùng phòng lập (handler = 0)
    assert e.value.status_code == 400 and "trùng" in e.value.detail.lower()
    with pytest.raises(HTTPException) as e:
        _pr_transfer(db, user, pr.id, 999_999)
    assert e.value.status_code == 400 and "không tồn tại" in e.value.detail.lower()
    dead = Department(code="NGUNG5", name="Đã ngừng", company_id=seed.company_id, is_active=False)
    db.add(dead)
    db.commit()
    with pytest.raises(HTTPException) as e:
        _pr_transfer(db, user, pr.id, dead.id)
    assert e.value.status_code == 400
    db.refresh(pr)
    assert pr.handler_dept_id == 0 and _audit(db, "purchase_request", pr.id) == []


def test_pr_transfer_refused_once_a_line_has_a_po(db, seed, two_departments):
    factory_id, purchasing_id = two_departments
    pr = _add_pr(db, seed, "PYC-DA-DAT", purchasing_id, lines=(("no_po", "A"), ("ordered", "B")))
    user = _actor(db, seed, "purchase_request", "all", purchasing_id)
    with pytest.raises(HTTPException) as e:
        _pr_transfer(db, user, pr.id, factory_id)
    assert e.value.status_code == 400
    db.refresh(pr)
    assert pr.handler_dept_id == 0
    assert [it.assignee for it in pr_service.items_of(db, pr.id)] == ["A", "B"]   # không đụng dòng


def test_pr_return_resets_handler_dept_and_logs_return(db, seed, two_departments):
    factory_id, purchasing_id = two_departments
    pr = _add_pr(db, seed, "PYC-TRA", purchasing_id, handler_dept_id=factory_id, status="dispatched")
    holder = _actor(db, seed, "purchase_request", "dept_proc", factory_id)
    out = _pr_return(db, holder, pr.id, reason="Nhà máy không có NCC mặt hàng này")
    db.refresh(pr)
    assert pr.handler_dept_id == 0 and pr.status == "approved"
    assert out["can_return_dept"] is False                 # đã ở phòng lập, hết gì để trả
    logs = _audit(db, "purchase_request", pr.id)
    assert logs[-1].action == "return_dept"
    assert "Nhà máy -> Phòng lập" in logs[-1].message


def test_pr_return_when_already_at_requesting_dept_is_refused(db, seed, two_departments):
    _, purchasing_id = two_departments
    pr = _add_pr(db, seed, "PYC-TM", purchasing_id)
    user = _actor(db, seed, "purchase_request", "all", purchasing_id)
    with pytest.raises(HTTPException) as e:
        _pr_return(db, user, pr.id)
    assert e.value.status_code == 400


def test_pr_out_exposes_transfer_flags_per_viewer(db, seed, two_departments):
    factory_id, purchasing_id = two_departments
    pr = _add_pr(db, seed, "PYC-CO", purchasing_id, handler_dept_id=factory_id)
    holder = _actor(db, seed, "purchase_request", "dept_proc", factory_id)
    staff = _actor(db, seed, "purchase_request", "dept_proc", factory_id, approve=False, write=True)
    d_holder = pr_ctl._out(db, pr, holder)
    d_staff = pr_ctl._out(db, pr, staff)
    assert d_holder["can_transfer_dept"] is True and d_holder["can_return_dept"] is True
    assert d_staff["can_transfer_dept"] is False and d_staff["can_return_dept"] is False
    blocked = _add_pr(db, seed, "PYC-PO", purchasing_id, handler_dept_id=factory_id,
                      lines=(("ordered", "A"),))
    assert pr_ctl._out(db, blocked, holder)["can_transfer_dept"] is False


# ── YCBG ─────────────────────────────────────────────────────────────────────────────────

def test_sr_transferable_unless_survey_really_started(db, seed, two_departments):
    factory_id, _ = two_departments
    ok = _add_sr(db, seed, "YCBG-OK", factory_id, status="approved",
                 lines=({"assignee": "A", "line_status": LS_RESURVEY},))   # khảo sát lại vẫn cho
    assert sr_service.can_transfer_dept(db, ok) is True

    done_line = _add_sr(db, seed, "YCBG-XONG-DONG", factory_id,
                        lines=({"assignee": "A", "is_completed": True, "line_status": LS_COMPLETED},))
    assert sr_service.can_transfer_dept(db, done_line) is False

    chosen = _add_sr(db, seed, "YCBG-DA-CHON", factory_id)
    ln = sr_service.lines_of(db, chosen.id)[0]
    db.add(SurveyRequestOption(survey_request_line_id=ln.id, public_id=1, is_chosen=True,
                               created_by=seed.u_req_id, updated_by=seed.u_req_id))
    db.commit()
    assert sr_service.can_transfer_dept(db, chosen) is False

    unchosen = _add_sr(db, seed, "YCBG-CHUA-CHON", factory_id)
    ln2 = sr_service.lines_of(db, unchosen.id)[0]
    db.add(SurveyRequestOption(survey_request_line_id=ln2.id, public_id=1, is_chosen=False,
                               created_by=seed.u_req_id, updated_by=seed.u_req_id))
    db.commit()
    assert sr_service.can_transfer_dept(db, unchosen) is True      # phương án có nhưng chưa chọn

    linked = _add_sr(db, seed, "YCBG-CO-YCMH", factory_id)
    ln3 = sr_service.lines_of(db, linked.id)[0]
    db.add(SurveyRequestPr(survey_request_id=linked.id, survey_request_line_id=ln3.id, pr_id=1,
                           created_by=seed.u_req_id, updated_by=seed.u_req_id))
    db.commit()
    assert sr_service.can_transfer_dept(db, linked) is False

    finished = _add_sr(db, seed, "YCBG-DONE", factory_id, status="survey_done")
    assert sr_service.can_transfer_dept(db, finished) is False
    waiting = _add_sr(db, seed, "YCBG-CHO", factory_id, status="submitted")
    assert sr_service.can_transfer_dept(db, waiting) is False


def test_sr_transfer_clears_assignee_and_received_date_but_keeps_status(db, seed, two_departments):
    factory_id, purchasing_id = two_departments
    s = _add_sr(db, seed, "YCBG-CHUYEN", purchasing_id, status="processing",
                lines=({"assignee": seed.emp_nstm_code, "received_date": "2026-09-01"},
                       {"assignee": "", "received_date": ""}))
    user = _actor(db, seed, "survey_request", "dept_proc", purchasing_id)
    out = _sr_transfer(db, user, s.id, factory_id, reason="Nhà máy nắm NCC vật tư này")
    db.refresh(s)
    assert s.handler_dept_id == factory_id
    assert s.status == "processing"
    for ln in sr_service.lines_of(db, s.id):
        assert ln.assignee == "" and ln.received_date == ""
    assert out["handler_dept_id"] == factory_id
    logs = _audit(db, "survey_request", s.id)
    assert logs[-1].action == "transfer_dept" and "Nhà máy nắm NCC" in logs[-1].message
    titles = {n.user_id: n.title for n in db.query(Notification).all()}
    assert titles.get(seed.u_req_id, "").startswith("YCBG-CHUYEN — Chuyển")
    assert titles.get(seed.u_nstm_id, "").startswith("YCBG-CHUYEN — Gỡ phân công")


def test_sr_return_and_validation_share_pr_rules(db, seed, two_departments):
    factory_id, purchasing_id = two_departments
    s = _add_sr(db, seed, "YCBG-TRA", purchasing_id, handler_dept_id=factory_id)
    holder = _actor(db, seed, "survey_request", "dept_proc", factory_id)
    with pytest.raises(HTTPException) as e:
        _sr_return(db, holder, s.id, reason="")
    assert e.value.status_code == 400
    out = _sr_return(db, holder, s.id)
    db.refresh(s)
    assert s.handler_dept_id == 0 and out["can_return_dept"] is False
    assert _audit(db, "survey_request", s.id)[-1].action == "return_dept"
    # Về phòng lập rồi thì quản lý nhà máy hết cầm phiếu -> 404/403, không đụng được nữa.
    with pytest.raises(HTTPException):
        _sr_transfer(db, holder, s.id, factory_id)


def test_sr_transfer_refused_once_an_option_is_chosen(db, seed, two_departments):
    factory_id, purchasing_id = two_departments
    s = _add_sr(db, seed, "YCBG-CHON", purchasing_id)
    ln = sr_service.lines_of(db, s.id)[0]
    db.add(SurveyRequestOption(survey_request_line_id=ln.id, public_id=1, is_chosen=True,
                               created_by=seed.u_req_id, updated_by=seed.u_req_id))
    db.commit()
    user = _actor(db, seed, "survey_request", "all", purchasing_id)
    with pytest.raises(HTTPException) as e:
        _sr_transfer(db, user, s.id, factory_id)
    assert e.value.status_code == 400
    db.refresh(s)
    assert s.handler_dept_id == 0
    assert sr_service.lines_of(db, s.id)[0].assignee == "NSTM01"


def test_sr_out_exposes_transfer_flags(db, seed, two_departments):
    factory_id, purchasing_id = two_departments
    s = _add_sr(db, seed, "YCBG-CO", purchasing_id, handler_dept_id=factory_id)
    holder = _actor(db, seed, "survey_request", "dept_proc", factory_id)
    staff = _actor(db, seed, "survey_request", "proc", factory_id, approve=False, write=True)
    d_holder = sr_ctl._out(db, s, holder)
    d_staff = sr_ctl._out(db, s, staff)
    assert d_holder["can_transfer_dept"] is True and d_holder["can_return_dept"] is True
    assert d_staff["can_transfer_dept"] is False and d_staff["can_return_dept"] is False
    assert "can_transfer_dept" in sr_ctl._out(db, s)           # không có user -> cờ tắt, không nổ
    assert sr_ctl._out(db, s)["can_transfer_dept"] is False


# ── Chưa gán bậc mới thì mọi thứ y như trước ─────────────────────────────────────────────

def test_legacy_roles_keep_prior_behaviour_when_new_tier_is_not_assigned(db, seed, two_departments):
    """`pur_manager` (bậc all, có duyệt) thấy nút; NSTM (bậc assigned) và TBP (bậc dept) không.
    Phiếu không nhờ ai (`handler_dept_id` = 0) chạy đúng luồng cũ: người lập vẫn là chủ phiếu."""
    factory_id, _ = two_departments
    pr = _add_pr(db, seed, "PYC-CU", factory_id)
    manager = _actor(db, seed, "purchase_request", "all", factory_id)
    nstm = _actor(db, seed, "purchase_request", "assigned", factory_id, approve=False, write=True)
    head = _actor(db, seed, "purchase_request", "dept", factory_id)
    assert pr_ctl._out(db, pr, manager)["can_transfer_dept"] is True
    assert pr_ctl._out(db, pr, manager)["can_return_dept"] is False      # chưa nhờ ai -> không có gì để trả
    assert pr_ctl._out(db, pr, nstm)["can_transfer_dept"] is False
    assert pr_ctl._out(db, pr, head)["can_transfer_dept"] is False
