"""K3 (01/10/2026) — cách chọn người duyệt thứ tám: QUẢN LÝ TRỰC TIẾP của người nộp.

Đọc `Employee.manager_id` trên hồ sơ người nộp. Không dùng được (chưa gán, đã nghỉ,
tài khoản khóa, trùng chính người nộp) thì LÙI về trưởng bộ phận người nộp — đúng câu ô
«Quản lý trực tiếp» trên hồ sơ đã hứa, và để một hồ sơ chưa kịp gán không làm kẹt đơn.

Trước 01/10 ô `manager_id` có trên hồ sơ nhưng bộ máy duyệt KHÔNG đọc nó: nhân sự gán
quản lý, tin đơn sẽ tới người đó, còn đơn vẫn đi trưởng bộ phận mà không gì báo.
"""
from types import SimpleNamespace

import pytest

from app.modules.approval import action_service, approver_resolver, instance_service, preview_service
from app.modules.approval.flow_model import (APPROVER_DIRECT_MANAGER, APPROVER_KIND_LABELS,
                                             SKIP_NONE, ApprovalFlow, ApprovalNode)
from app.modules.approval.instance_model import (INSTANCE_APPROVED, INSTANCE_RUNNING,
                                                 TASK_PENDING)
from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.user.model import User

ACTOR = 1
ENTITY = "document"
NODE = SimpleNamespace(approver_kind=APPROVER_DIRECT_MANAGER, approver_ref="")


@pytest.fixture()
def org(db, seed):
    """Người nộp, quản lý trực tiếp của họ, và trưởng bộ phận của phòng."""
    def add(code, **kw):
        employee = Employee(code=code, full_name=f"Người {code}", company_id=seed.company_id,
                            department_id=seed.dept_id, is_active=True, **kw)
        db.add(employee)
        db.flush()
        return employee

    head = add("TRUONG_PHONG")
    manager = add("QUAN_LY")
    submitter = add("NGUOI_NOP", manager_id=manager.id)
    db.get(Department, seed.dept_id).manager_id = head.id
    db.commit()
    return SimpleNamespace(head=head, manager=manager, submitter=submitter, seed=seed)


def _resolve(db, submitter_id, subject=None):
    return approver_resolver.resolve(db, NODE, subject or {}, submitter_id)


def test_label_is_offered_in_the_flow_designer():
    assert APPROVER_KIND_LABELS[APPROVER_DIRECT_MANAGER] == "Quản lý trực tiếp người nộp"


def test_routes_to_the_direct_manager_not_the_department_head(db, org):
    assert _resolve(db, org.submitter.id) == [org.manager.id]


def test_unassigned_manager_falls_back_to_department_head(db, org):
    org.submitter.manager_id = 0
    db.commit()
    assert _resolve(db, org.submitter.id) == [org.head.id]


def test_resigned_manager_falls_back_to_department_head(db, org):
    org.manager.is_active = False
    db.commit()
    assert _resolve(db, org.submitter.id) == [org.head.id]


def test_manager_with_every_account_locked_falls_back(db, org):
    #  Có tài khoản nhưng mọi tài khoản đều khóa = không bấm duyệt được (duoc-CR-398).
    db.add(User(email="quanly@example.com", password_hash="x",
                employee_id=org.manager.id, is_active=False))
    db.commit()
    assert _resolve(db, org.submitter.id) == [org.head.id]


def test_manager_pointing_to_self_falls_back_instead_of_self_approval(db, org):
    org.submitter.manager_id = org.submitter.id
    db.commit()
    assert _resolve(db, org.submitter.id) == [org.head.id]


def test_unknown_submitter_falls_back_to_department_on_the_document(db, org):
    assert _resolve(db, None, {"department_id": org.seed.dept_id}) == [org.head.id]


def test_manager_id_pointing_to_a_deleted_profile_falls_back(db, org):
    org.submitter.manager_id = 99_999_999
    db.commit()
    assert _resolve(db, org.submitter.id) == [org.head.id]


def _flow_with_direct_manager_step(db):
    flow = ApprovalFlow(entity=ENTITY, code="LUONG-QLTT", name="Luồng quản lý trực tiếp",
                        is_active=True, created_by=ACTOR, updated_by=ACTOR)
    db.add(flow)
    db.commit()
    db.add(ApprovalNode(flow_id=flow.id, seq=1, name="Quản lý trực tiếp duyệt",
                        approver_kind=APPROVER_DIRECT_MANAGER, approver_ref="",
                        skip_duplicate=SKIP_NONE, created_by=ACTOR, updated_by=ACTOR))
    db.commit()
    return flow


def test_running_instance_assigns_the_task_to_the_direct_manager(db, org):
    _flow_with_direct_manager_step(db)
    instance = instance_service.start(db, ENTITY, 501, {}, org.submitter.id, ACTOR,
                                      entity_code="VB-QLTT", entity_title="Thử quản lý trực tiếp")
    assert instance.status == INSTANCE_RUNNING
    pending = [t for t in instance_service.tasks_of_instance(db, instance.id)
               if t.status == TASK_PENDING]
    assert [t.assignee_employee_id for t in pending] == [org.manager.id]
    action_service.approve(db, instance, org.manager.id, ACTOR, {})
    assert instance.status == INSTANCE_APPROVED


def test_preview_explains_the_fallback_when_no_manager_is_assigned(db, org):
    org.submitter.manager_id = 0
    db.commit()
    flow = _flow_with_direct_manager_step(db)
    node = db.query(ApprovalNode).filter(ApprovalNode.flow_id == flow.id).one()
    step = preview_service._stage_step(db, node, {}, org.submitter.id, set(), set())
    assert [a["employee_id"] for a in step["approvers"]] == [org.head.id]
    assert "chưa gán quản lý trực tiếp" in step["note"]
