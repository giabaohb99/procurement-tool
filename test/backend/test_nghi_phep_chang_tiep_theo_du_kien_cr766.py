"""duoc-CR-766 — các chặng CHƯA MỞ của phiên duyệt đang chạy, kèm người duyệt dự kiến.

Thẻ Lịch sử phê duyệt của đơn nghỉ phép chỉ kể được người đang giữ việc (bảng
việc chỉ có chặng đã mở). `upcoming_stages_service` tính trước người của các
chặng sau bằng đúng vòng lặp của màn xem trước người duyệt, nên các bài dưới chốt
ba luật phải khớp lúc chặng mở thật: chặng hiện tại không lặp lại, bỏ qua khi
trùng người, và phiên đã xong thì không còn gì phía trước.
"""
from datetime import date
from types import SimpleNamespace

import pytest

from app.modules.approval import action_service
from app.modules.approval.flow_model import (APPROVER_EMPLOYEE, MULTI_ALL, MULTI_ANY,
                                             SKIP_ADJACENT, ApprovalFlow, ApprovalNode,
                                             ApprovalSwitch)
from app.modules.approval.instance_model import ApprovalInstance
from app.modules.approval.upcoming_stages_service import list_upcoming_stages
from app.modules.employee.model import Employee
from app.modules.leave import approval_bridge, request_service
from app.modules.leave.catalog_model import LeaveType
from app.modules.leave.schema import LeaveRequestCreate

ACTOR = 1
ENTITY = "leave_request"
MONDAY = date(2026, 1, 5)


def _employee(db, code, name):
    obj = Employee(code=code, full_name=name, company_id=1, department_id=7, is_active=True)
    db.add(obj)
    db.flush()
    return obj


@pytest.fixture()
def people(db):
    return SimpleNamespace(
        submitter=_employee(db, "NV_NOP", "Người nộp"),
        lead=_employee(db, "NV_TP", "Trưởng phòng"),
        hr=_employee(db, "NV_HR", "Trưởng Nhân sự"),
        ceo=_employee(db, "NV_GD", "Giám đốc"),
    )


@pytest.fixture()
def leave_type(db):
    obj = LeaveType(code="annual", name="Phép năm", counts_balance=True, annual_quota_days=12.0)
    db.add(obj)
    db.flush()
    return obj


def _flow(db, approver_ids, skip_duplicate=0, first_multi_mode=MULTI_ANY):
    """Luồng nhiều chặng, mỗi chặng khai đích danh (một id hoặc nhiều id cách dấu phẩy)."""
    row = ApprovalFlow(entity=ENTITY, code="NP-766", name="Duyệt nghỉ phép (thử)",
                       is_active=True, created_by=ACTOR, updated_by=ACTOR)
    db.add(row)
    db.flush()
    for seq, emp_ids in enumerate(approver_ids, start=1):
        db.add(ApprovalNode(flow_id=row.id, seq=seq, name=f"Chặng thử {seq}",
                            approver_kind=APPROVER_EMPLOYEE, approver_ref=str(emp_ids),
                            skip_duplicate=skip_duplicate,
                            multi_mode=first_multi_mode if seq == 1 else MULTI_ANY,
                            created_by=ACTOR, updated_by=ACTOR))
    db.add(ApprovalSwitch(entity=ENTITY, is_enabled=True, created_by=ACTOR, updated_by=ACTOR))
    db.commit()
    return row


def _submit(db, leave_type, employee) -> ApprovalInstance:
    user = SimpleNamespace(id=1, employee_id=employee.id)
    obj = request_service.create(db, LeaveRequestCreate(
        leave_type_id=leave_type.id, from_date=MONDAY, to_date=MONDAY, reason="Việc riêng"), user)
    emp = request_service.prepare_submit(db, obj, user)
    instance_id = approval_bridge.start_approval(db, obj, user)
    request_service.mark_submitted(db, obj, emp, user, instance_id)
    return db.get(ApprovalInstance, instance_id)


def _names(steps):
    return [(s["seq"], [a["name"] for a in s["approvers"]]) for s in steps]


def test_lists_only_stages_after_current_with_expected_approver(db, people, leave_type):
    _flow(db, [people.lead.id, people.hr.id, people.ceo.id])
    instance = _submit(db, leave_type, people.submitter)

    assert instance.current_seq == 1
    assert _names(list_upcoming_stages(db, instance)) == [
        (2, ["Trưởng Nhân sự"]), (3, ["Giám đốc"])]


def test_upcoming_shrinks_as_stages_get_approved(db, people, leave_type):
    _flow(db, [people.lead.id, people.hr.id, people.ceo.id])
    instance = _submit(db, leave_type, people.submitter)

    action_service.approve(db, instance, people.lead.id, ACTOR, {}, "")
    db.refresh(instance)

    assert instance.current_seq == 2
    assert _names(list_upcoming_stages(db, instance)) == [(3, ["Giám đốc"])]


def test_last_stage_and_finished_instance_have_nothing_ahead(db, people, leave_type):
    _flow(db, [people.lead.id])
    instance = _submit(db, leave_type, people.submitter)
    assert list_upcoming_stages(db, instance) == []

    action_service.approve(db, instance, people.lead.id, ACTOR, {}, "")
    db.refresh(instance)
    assert list_upcoming_stages(db, instance) == []


def test_same_person_next_stage_is_shown_as_auto_pass_when_skip_duplicate(db, people, leave_type):
    """Chặng 2 cùng người với chặng 1 + bật bỏ qua khi trùng người kề trước: lúc mở
    thật nó tự qua, nên dự kiến phải nói không ai cần bấm thêm, không được nêu tên
    người đó lần nữa."""
    _flow(db, [people.lead.id, people.lead.id, people.ceo.id], skip_duplicate=SKIP_ADJACENT)
    instance = _submit(db, leave_type, people.submitter)

    steps = list_upcoming_stages(db, instance)
    assert _names(steps) == [(2, []), (3, ["Giám đốc"])]
    assert "tự động qua" in steps[0]["note"]
    assert steps[0]["unresolved_reason"] == ""


@pytest.mark.parametrize("mode, expected", [
    #  "Một người là đủ": chưa biết ai trong hai người sẽ ký, việc của người kia bị
    #  hủy, nên chặng sau KHÔNG được báo tự động qua (rà mã duoc-CR-766).
    (MULTI_ANY, ["Trưởng phòng"]),
    #  "Tất cả phải duyệt": Trưởng phòng chắc chắn ký chặng 1 nên chặng 2 tự qua.
    (MULTI_ALL, []),
])
def test_current_stage_with_several_assignees_only_counts_as_signed_when_all_must_sign(
        db, people, leave_type, mode, expected):
    _flow(db, [f"{people.lead.id},{people.hr.id}", people.lead.id],
          skip_duplicate=SKIP_ADJACENT, first_multi_mode=mode)
    instance = _submit(db, leave_type, people.submitter)

    assert _names(list_upcoming_stages(db, instance)) == [(2, expected)]


# ── Trợ lý AI: my_requests_status trả thêm các chặng sau ───────────────────────

def test_assistant_tool_tells_who_approves_the_next_stages(db, people, leave_type):
    """Câu 'đơn của tôi duyệt xong thì tới ai' — trợ lý phải trả lời cùng phép tính với màn chi tiết."""
    from app.modules.assistant.tools.approval_tool import _run_my_requests_status
    from app.modules.assistant.tools.base import ToolContext

    _flow(db, [people.lead.id, people.hr.id, people.ceo.id])
    _submit(db, leave_type, people.submitter)

    user = SimpleNamespace(id=1, employee_id=people.submitter.id)
    out = _run_my_requests_status(ToolContext(db=db, user=user, _profile={"grants": []}), {})

    item = out["items"][0]
    assert item["waiting_on"] == ["Trưởng phòng"]
    assert [(s["seq"], s["expected_approvers"]) for s in item["next_steps"]] == [
        (2, ["Trưởng Nhân sự"]), (3, ["Giám đốc"])]


def test_assistant_tool_has_no_next_steps_for_finished_requests(db, people, leave_type):
    from app.modules.assistant.tools.approval_tool import _run_my_requests_status
    from app.modules.assistant.tools.base import ToolContext

    _flow(db, [people.lead.id])
    instance = _submit(db, leave_type, people.submitter)
    action_service.approve(db, instance, people.lead.id, ACTOR, {}, "")

    user = SimpleNamespace(id=1, employee_id=people.submitter.id)
    out = _run_my_requests_status(ToolContext(db=db, user=user, _profile={"grants": []}), {})
    assert "next_steps" not in out["items"][0]
