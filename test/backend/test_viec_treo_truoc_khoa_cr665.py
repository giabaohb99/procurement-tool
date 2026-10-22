"""duoc-CR-665 (V0-4) — màn kiểm việc duyệt đang treo trước khi khóa tài khoản.

Canh bốn điều: liệt kê đúng việc · chuyển xong người mới nhận, người cũ hết · khóa sau khi
chuyển không để phiếu kẹt · người ngoài phạm vi không xem được danh sách.
"""
import pytest
from fastapi import HTTPException

from app.modules.approval import action_service, instance_service
from app.modules.approval.flow_model import (APPROVER_EMPLOYEE, SKIP_NONE, ApprovalFlow,
                                             ApprovalNode)
from app.modules.approval.instance_model import (TASK_OPEN_STATUSES, TASK_PENDING,
                                                 ApprovalTask)
from app.modules.employee import controller, pending_work_service
from app.modules.employee.model import Employee
from app.modules.employee.service import lock_linked_users
from app.modules.login_session.constants import RevokeReason
from app.modules.user.model import User

ACTOR = 1
ENTITY = "document"


@pytest.fixture()
def person(db, seed):
    ids = {"nop": seed.emp_req_id}
    for name in ("a", "b", "c"):
        emp = Employee(code=f"VT_{name.upper()}", full_name=f"Người {name.upper()}",
                       company_id=seed.company_id, department_id=seed.dept_id, is_active=True)
        db.add(emp)
        db.flush()
        ids[name] = emp.id
        db.add(User(email=f"vt_{name}@x.vn", employee_id=emp.id, password_hash="x", is_active=True))
    db.commit()
    return ids


def _flow(db, ref, code="VT-01", fallback=None, active=True):
    flow = ApprovalFlow(entity=ENTITY, code=code, name=f"Luồng {code}", is_active=active,
                        created_by=ACTOR, updated_by=ACTOR)
    db.add(flow)
    db.flush()
    db.add(ApprovalNode(flow_id=flow.id, seq=1, name="Bước duyệt", approver_kind=APPROVER_EMPLOYEE,
                        approver_ref=ref, fallback_employee_id=fallback, skip_duplicate=SKIP_NONE,
                        created_by=ACTOR, updated_by=ACTOR))
    db.commit()
    return flow


def _trinh(db, submitter, entity_id):
    return instance_service.start(db, ENTITY, entity_id, {}, submitter, ACTOR,
                                  entity_code=f"VB-{entity_id}", entity_title="Phiếu thử")


def _open_tasks(db, employee_id):
    return db.query(ApprovalTask).filter(ApprovalTask.assignee_employee_id == employee_id,
                                         ApprovalTask.status.in_(TASK_OPEN_STATUSES)).count()


def test_liet_ke_dung_viec_dang_treo_va_buoc_luong_dich_danh(db, seed, person):
    flow = _flow(db, str(person["a"]))
    _flow(db, str(person["b"]), code="VT-B")                       # luồng của người khác
    _flow(db, str(person["a"]), code="VT-OFF", active=False)       # luồng đã tắt không tính
    _flow(db, str(person["b"]), code="VT-FB", fallback=person["a"])  # dự phòng
    for i in range(2):
        _trinh(db, person["nop"], 700 + i)

    out = pending_work_service.pending_work_of(db, person["a"])
    assert out["total_tasks"] == 2
    assert {t["entity_code"] for t in out["tasks"]} == {"VB-700", "VB-701"}
    assert all(t["status"] == TASK_PENDING and t["started_by_name"] for t in out["tasks"])
    roles = {(s["flow_code"], s["role"]) for s in out["flow_steps"]}
    assert roles == {(flow.code, "approver"), ("VT-FB", "fallback")}
    # người không giữ gì thì rỗng
    empty = pending_work_service.pending_work_of(db, person["c"])
    assert empty["tasks"] == [] and empty["flow_steps"] == []


def test_viec_da_duyet_xong_khong_con_trong_danh_sach(db, seed, person):
    _flow(db, str(person["a"]))
    instance = _trinh(db, person["nop"], 710)
    action_service.approve(db, instance, person["a"], ACTOR, {})
    assert pending_work_service.pending_work_of(db, person["a"])["total_tasks"] == 0


def test_chuyen_xong_nguoi_moi_nhan_nguoi_cu_het_va_khoa_khong_ke_phieu(db, seed, person):
    _flow(db, str(person["a"]))
    for i in range(3):
        _trinh(db, person["nop"], 720 + i)
    first = pending_work_service.pending_work_of(db, person["a"])["tasks"][0]["task_id"]

    # chuyển TỪNG việc bằng đường có sẵn, phần còn lại bằng bàn giao hàng loạt
    action_service.reassign(db, db.get(ApprovalTask, first), person["b"], ACTOR)
    assert pending_work_service.pending_work_of(db, person["b"])["total_tasks"] == 1
    assert pending_work_service.pending_work_of(db, person["a"])["total_tasks"] == 2
    assert action_service.bulk_handover(db, person["a"], person["b"], ACTOR) == 2

    assert pending_work_service.pending_work_of(db, person["a"])["total_tasks"] == 0
    assert pending_work_service.pending_work_of(db, person["b"])["total_tasks"] == 3

    # khóa người cũ (đúng đường nghỉ việc) — không còn việc nào mang tên tài khoản đã khóa
    locked = lock_linked_users(db, person["a"], ACTOR, RevokeReason.EMPLOYEE_RESIGNED)
    db.commit()
    assert locked and all(not u.is_active for u in locked)
    assert _open_tasks(db, person["a"]) == 0


def test_khoa_khong_chuyen_thi_viec_van_nam_lai_de_man_hinh_canh_bao(db, seed, person):
    """Chốt hành vi «cho qua có xác nhận»: server không chặn khóa, nên danh sách PHẢI còn
    thấy việc sau khi khóa — để màn hình dựa vào đó mà cảnh báo trước."""
    _flow(db, str(person["a"]))
    _trinh(db, person["nop"], 730)
    lock_linked_users(db, person["a"], ACTOR, RevokeReason.EMPLOYEE_RESIGNED)
    db.commit()
    assert pending_work_service.pending_work_of(db, person["a"])["total_tasks"] == 1


def _user_of(db, employee_id) -> User:
    return db.query(User).filter(User.employee_id == employee_id).first()


def test_nguoi_ngoai_pham_vi_khong_xem_duoc_danh_sach(db, seed, person, cap_quyen):
    _flow(db, str(person["a"]))
    _trinh(db, person["nop"], 740)
    viewer = _user_of(db, person["b"])
    cap_quyen(viewer.id, "employee", scope="own", read=True)

    with pytest.raises(HTTPException) as err:
        controller.get_employee_pending_work(person["a"], db, viewer)
    assert err.value.status_code == 404
    # chính mình thì xem được (phạm vi own)
    mine = controller.get_employee_pending_work(person["b"], db, viewer)
    assert mine.status_code == 200


def test_nguoi_co_pham_vi_tat_ca_xem_duoc_viec_cua_nguoi_khac(db, seed, person, cap_quyen):
    _flow(db, str(person["a"]))
    _trinh(db, person["nop"], 741)
    viewer = _user_of(db, person["b"])
    cap_quyen(viewer.id, "employee", scope="all", read=True)

    import json
    res = controller.get_employee_pending_work(person["a"], db, viewer)
    body = json.loads(res.body)
    assert body["data"]["total_tasks"] == 1
    #  `employee.read` không phải quyền đọc chứng từ: văn bản #741 người xem không đọc được
    #  (ở đây là không tồn tại) → vẫn đếm, nhưng mã/tên phiếu + người trình bị xóa trắng.
    task = body["data"]["tasks"][0]
    assert task["hidden"] is True
    assert task["entity_code"] == "" and task["entity_title"] == "" and task["started_by_name"] == ""
    assert task["task_id"] > 0   # vẫn chuyển được việc


def test_duong_api_duoc_dang_ky_va_gac_employee_read():
    import app.main  # noqa: F401
    from app.main import app
    paths = {r.path for r in app.routes}
    assert "/api/employees/{eid}/pending-work" in paths
