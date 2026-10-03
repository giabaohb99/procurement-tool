"""bao-CR-579 — Đặt xe và Duyệt dấu khai được NHIỀU luồng theo điều kiện.

Người có quyền cấu hình luồng khai nhiều luồng cho cùng một loại phiếu (ví dụ:
giao hàng thì thêm Giám đốc), và chọn «người tạo chọn người duyệt» như app cũ.
Ba thứ phải đúng thì điều đó mới chạy:

1. Bối cảnh phiếu đưa sang bộ máy duyệt có đủ ô, và ô người là id NHÂN SỰ. Trên
   phiếu, `requester_id` / `first_approver_id` là id TÀI KHOẢN; đưa thẳng sang là
   điều kiện «người tạo thuộc danh sách» không bao giờ khớp và bước «lấy từ ô»
   giao việc cho một nhân sự trùng số với tài khoản — người khác hẳn.
2. Luồng có điều kiện, ưu tiên cao được chọn trước luồng mặc định.
3. Danh sách luồng nói được mỗi luồng đang có bao nhiêu phiếu chạy.
"""
from types import SimpleNamespace

from app.modules.approval.approver_resolver import resolve
from app.modules.approval.flow_model import APPROVER_FIELD, ApprovalFlow
from app.modules.approval.flow_service import pick_flow
from app.modules.approval.instance_model import (INSTANCE_APPROVED, INSTANCE_RUNNING,
                                                 ApprovalInstance)
from app.modules.approval.serializer import count_running_instances
from app.modules.employee.model import Employee
from app.modules.seal_request.approval_bridge import entity_context as seal_context
from app.modules.seal_request.model import SealRequest
from app.modules.user.model import User
from app.modules.vehicle_booking.approval_bridge import entity_context as booking_context
from app.modules.vehicle_booking.model import TYPE_CAR, TYPE_DELIVERY, VehicleBooking


def _account(db, code: str) -> tuple[Employee, User]:
    """Tạo nhân sự + tài khoản với id LỆCH nhau, để bắt lỗi lẫn hai loại id."""
    db.add(Employee(code=f"PAD{code}", full_name="Đệm id", is_active=True))
    emp = Employee(code=code, full_name=f"Nhân sự {code}", is_active=True)
    db.add(emp)
    db.flush()
    user = User(email=f"{code.lower()}@dego.test", employee_id=emp.id, is_active=True)
    db.add(user)
    db.flush()
    assert user.id != emp.id
    return emp, user


def _booking(db, requester: User, approver: User, request_type: int) -> VehicleBooking:
    booking = VehicleBooking(code="DX9001", purpose="Thử", request_type=request_type,
                             requester_id=requester.id, first_approver_id=approver.id,
                             company_id=1, department_id=17)
    db.add(booking)
    db.flush()
    return booking


def test_booking_context_gives_employee_ids_not_account_ids(db):
    req_emp, req_user = _account(db, "TAO")
    apv_emp, apv_user = _account(db, "DUYET")

    ctx = booking_context(_booking(db, req_user, apv_user, TYPE_DELIVERY))

    assert ctx["request_type"] == TYPE_DELIVERY
    assert ctx["requester_employee_id"] == req_emp.id
    assert ctx["first_approver_employee_id"] == apv_emp.id
    assert ctx["requester_id"] == req_user.id   # khóa cũ giữ nguyên cho luồng đã khai


def test_booking_context_without_approver_is_zero_not_crash(db):
    _, req_user = _account(db, "TAO2")
    booking = VehicleBooking(code="DX9002", purpose="Thử", request_type=TYPE_CAR,
                             requester_id=req_user.id, first_approver_id=0)
    db.add(booking)
    db.flush()

    assert booking_context(booking)["first_approver_employee_id"] == 0


def test_field_step_routes_to_the_approver_the_requester_picked(db):
    _, req_user = _account(db, "TAO3")
    apv_emp, apv_user = _account(db, "DUYET3")
    ctx = booking_context(_booking(db, req_user, apv_user, TYPE_CAR))
    node = SimpleNamespace(approver_kind=APPROVER_FIELD, approver_ref="first_approver_employee_id")

    assert resolve(db, node, ctx, None) == [apv_emp.id]


def test_seal_context_has_seal_type_and_employee_ids(db):
    req_emp, req_user = _account(db, "TAO4")
    apv_emp, apv_user = _account(db, "DUYET4")
    req = SealRequest(code="DD9001", purpose="Thử", seal_type_id=7, company_id=1,
                      department_id=17, requester_id=req_user.id,
                      first_approver_id=apv_user.id)
    db.add(req)
    db.flush()

    ctx = seal_context(req)

    assert ctx["seal_type_id"] == 7
    assert ctx["requester_employee_id"] == req_emp.id
    assert ctx["first_approver_employee_id"] == apv_emp.id


def _flow(db, code: str, priority: int = 0, condition: str = "") -> ApprovalFlow:
    flow = ApprovalFlow(entity="vehicle_booking", code=code, name=code, is_active=True,
                        priority=priority, condition=condition)
    db.add(flow)
    db.flush()
    return flow


def test_conditional_flow_wins_for_delivery_default_for_car(db):
    default = _flow(db, "MAC-DINH")
    delivery = _flow(db, "GIAO-HANG", priority=10,
                     condition='[{"field": "request_type", "op": "eq", "value": 2}]')

    assert pick_flow(db, "vehicle_booking", {"request_type": TYPE_DELIVERY}).id == delivery.id
    assert pick_flow(db, "vehicle_booking", {"request_type": TYPE_CAR}).id == default.id


def test_condition_on_requester_uses_employee_ids(db):
    req_emp, req_user = _account(db, "TAO5")
    _, apv_user = _account(db, "DUYET5")
    default = _flow(db, "MAC-DINH-2")
    special = _flow(db, "RIENG", priority=5,
                    condition=f'[{{"field": "requester_employee_id", "op": "in", "value": [{req_emp.id}]}}]')
    ctx = booking_context(_booking(db, req_user, apv_user, TYPE_CAR))

    assert pick_flow(db, "vehicle_booking", ctx).id == special.id
    assert pick_flow(db, "vehicle_booking", {**ctx, "requester_employee_id": 0}).id == default.id


def test_running_count_only_counts_unfinished_tickets(db):
    flow = _flow(db, "DEM")
    for entity_id, status in ((1, INSTANCE_RUNNING), (2, INSTANCE_RUNNING), (3, INSTANCE_APPROVED)):
        db.add(ApprovalInstance(entity="vehicle_booking", entity_id=entity_id, flow_id=flow.id,
                                flow_snapshot="{}", status=status, current_seq=1))
    db.flush()

    assert count_running_instances(db, flow.id) == 2
    assert count_running_instances(db, flow.id + 999) == 0
