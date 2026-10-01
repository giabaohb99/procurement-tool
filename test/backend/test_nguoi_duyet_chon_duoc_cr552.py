"""bao-CR-552 — ô «Trưởng phòng phê duyệt» và «Trưởng bộ phận» luôn chọn được (YCMH · YCBG · ĐMH).

Đại ca báo 01/10/2026: phòng «Lập trình & IT nội bộ» không có trưởng phòng duyệt theo phòng nên
cả hai ô khóa cứng. Chốt: ô phê duyệt liệt kê MỌI người duyệt được chứng từ đó, BỎ tài khoản giữ
vai trò Quản trị hệ thống, và LUÔN có Trưởng bộ phận; ô TBP luôn có trưởng phòng của phòng lập.
"""
from types import SimpleNamespace

import pytest

from app.core import approver_candidates as ac
from app.modules.department.model import Department
from app.modules.purchase_order.model import PurchaseOrder
from app.modules.purchase_request import service as pr_service
from app.modules.purchase_request.model import PurchaseRequest
from app.modules.role.model import Role
from app.modules.survey_request.model import SurveyRequest
from app.modules.user.model import User, UserRole

ENTITIES = (("purchase_request", PurchaseRequest), ("survey_request", SurveyRequest),
            ("purchase_order", PurchaseOrder))


@pytest.fixture
def world(db, seed, cap_quyen):
    """NSTM duyệt được mọi phiếu; TP giữ thêm vai trò Quản trị (phải bị loại); TBP mặc định của
    phòng là nhân sự KHÔNG có quyền duyệt (như anh Giang ở phòng IT)."""
    u_nstm = db.get(User, seed.u_nstm_id)
    u_tp = db.query(User).filter(User.email == "DEMOTP").one()
    for entity, _model in ENTITIES:
        cap_quyen(u_nstm.id, entity, scope="all", read=True, approve=True)
        cap_quyen(u_tp.id, entity, scope="all", read=True, approve=True)
    admin = db.query(Role).filter(Role.code == "admin").first() or Role(code="admin", name="Quản trị")
    db.add(admin)
    db.flush()
    db.add(UserRole(user_id=u_tp.id, role_id=admin.id))
    dept = db.get(Department, seed.dept_id)
    dept.manager_id = seed.emp_backup_id
    db.commit()
    return SimpleNamespace(dept=dept, nstm=seed.emp_nstm_id, tp=seed.emp_tp_id, head=seed.emp_backup_id)


def _ids(rows):
    return {r["employee_id"] for r in rows}


@pytest.mark.parametrize("entity,model", ENTITIES, ids=[e for e, _m in ENTITIES])
def test_draft_lists_approvers_plus_head_but_not_admins(db, seed, world, entity, model):
    fields = ac.draft_fields(db, SimpleNamespace(id=seed.u_req_id), department_id=world.dept.id,
                             company_id=seed.company_id)
    ids = _ids(ac.list_candidates_for_draft(db, model, entity, fields))
    assert world.nstm in ids, "người duyệt được phải có mặt"
    assert world.head in ids, "Trưởng bộ phận mặc định phải có mặt dù không có quyền duyệt"
    assert world.tp not in ids, "tài khoản giữ vai trò Quản trị hệ thống phải bị loại"


def test_draft_uses_the_head_picked_on_the_form(db, seed, world):
    fields = ac.draft_fields(db, SimpleNamespace(id=seed.u_req_id), department_id=world.dept.id,
                             company_id=seed.company_id)
    ids = _ids(ac.list_candidates_for_draft(db, PurchaseRequest, "purchase_request", fields,
                                            head_of_dept_id=seed.emp_req_id))
    assert seed.emp_req_id in ids


def test_saved_request_includes_its_own_head(db, seed, world):
    pr = PurchaseRequest(code="PYC-CR548", status="draft", department=world.dept.name,
                         department_id=world.dept.id, company_id=seed.company_id,
                         head_of_dept_id=seed.emp_req_id, created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(pr)
    db.commit()
    ids = _ids(ac.list_candidates_for_row(db, PurchaseRequest, "purchase_request", pr))
    assert {seed.emp_req_id, world.nstm} <= ids and world.tp not in ids


def test_head_list_always_has_the_department_head(db, seed, world):
    rows = pr_service.complete_head_choices(db, [], world.dept.id)
    assert _ids(rows) == {world.head}


def test_head_list_falls_back_to_all_department_managers(db, seed, world):
    other = Department(code="DEPT-CR548", name="Phòng chưa có trưởng", company_id=seed.company_id,
                       is_active=True)
    db.add(other)
    db.commit()
    rows = pr_service.complete_head_choices(db, [], other.id)
    assert world.head in _ids(rows), "phòng chưa có trưởng → đưa trưởng phòng các phòng khác"


def test_resigned_head_is_not_offered(db, seed, world):
    from app.modules.employee.model import Employee
    db.get(Employee, world.head).status = "resigned"
    db.commit()
    assert world.head not in _ids(pr_service.complete_head_choices(db, [], world.dept.id))
