"""bao-CR-584 — người ĐANG được giao duyệt phiếu Đặt xe / Duyệt dấu thì đọc được phiếu đó.

Luồng cấu hình giao việc cho người ngoài phạm vi dữ liệu của phiếu: Pháp lý kiểm tra
dấu của mọi phòng, Giám đốc duyệt dấu (phạm vi của họ chỉ thấy phiếu ĐÃ duyệt),
trưởng bộ phận được người tạo chọn ở phòng khác. Trước bản vá, ba cửa cùng chặn họ:

1. trang chi tiết — `require(..., "read")` ở mức route trả 403 trước cả đường lùi;
2. tệp chứng từ — người kiểm không mở được thứ mình phải kiểm;
3. ô Trao đổi — «không tải được nội dung trao đổi» (thấy tận mắt 03/10/2026).

Luật: chỉ nới khi việc CÒN TREO, chỉ cho loại chứng từ khai trong `APPROVER_READABLE`.
"""
import json

import pytest
from fastapi import HTTPException

from app.modules.approval.instance_model import (INSTANCE_RUNNING, TASK_APPROVED, TASK_PENDING,
                                                 ApprovalInstance, ApprovalTask)
from app.modules.approval.pending_reader import APPROVER_READABLE, is_pending_approver
from app.modules.attachment.controller import _check as check_attachment
from app.modules.comment.service import resolve_doc
from app.modules.employee.model import Employee
from app.modules.seal_request.controller import get_seal_request
from app.modules.seal_request.model import SealRequest
from app.modules.user.model import User
from app.modules.vehicle_booking.controller import get_booking
from app.modules.vehicle_booking.model import TYPE_CAR, VehicleBooking


def _account(db, code: str) -> User:
    emp = Employee(code=code, full_name=f"Nhân sự {code}", is_active=True)
    db.add(emp)
    db.flush()
    user = User(email=f"{code.lower()}@dego.test", employee_id=emp.id, is_active=True)
    db.add(user)
    db.flush()
    return user


def _seal(db) -> SealRequest:
    req = SealRequest(code="DD7001", purpose="Hợp đồng đại lý", company_id=1,
                      department_id=17, requester_id=999, status=2)
    db.add(req)
    db.flush()
    return req


def _booking(db) -> VehicleBooking:
    booking = VehicleBooking(code="DX7001", purpose="Đi Cần Thơ", request_type=TYPE_CAR,
                             requester_id=999, company_id=1, department_id=17, status=2)
    db.add(booking)
    db.flush()
    return booking


def _give_task(db, entity: str, entity_id: int, user: User, status: int = TASK_PENDING):
    inst = ApprovalInstance(entity=entity, entity_id=entity_id, flow_id=1, flow_snapshot="{}",
                            status=INSTANCE_RUNNING, current_seq=2)
    db.add(inst)
    db.flush()
    task = ApprovalTask(instance_id=inst.id, node_seq=2, node_name="Pháp lý kiểm tra",
                        order_no=1, assignee_employee_id=user.employee_id, status=status)
    db.add(task)
    db.flush()
    return task


def _body(resp) -> dict:
    return json.loads(resp.body)["data"]


def test_seal_detail_opens_for_the_pending_approver_without_any_seal_permission(db):
    legal = _account(db, "PHAPLY")
    req = _seal(db)
    _give_task(db, "seal_request", req.id, legal)

    assert _body(get_seal_request(req.id, db, legal))["code"] == "DD7001"


def test_seal_detail_closes_again_once_the_task_is_done(db):
    legal = _account(db, "PHAPLY2")
    req = _seal(db)
    task = _give_task(db, "seal_request", req.id, legal)
    task.status = TASK_APPROVED
    db.flush()

    with pytest.raises(HTTPException) as err:
        get_seal_request(req.id, db, legal)
    assert err.value.status_code == 404


def test_seal_detail_stays_closed_for_someone_without_a_task(db):
    outsider = _account(db, "NGOAI")
    req = _seal(db)
    _give_task(db, "seal_request", req.id, _account(db, "AIKHAC"))

    with pytest.raises(HTTPException) as err:
        get_seal_request(req.id, db, outsider)
    assert err.value.status_code == 404


def test_booking_detail_opens_for_the_pending_approver_without_booking_permission(db):
    #  Trước bản vá: đường lùi `booking_for_approver` đã có, nhưng `require("vehicle_booking",
    #  "read")` ở mức route chặn 403 TRƯỚC khi tới nó — người không có vai trò Đặt xe nào
    #  thì đường lùi vô dụng.
    manager = _account(db, "QLDIEUPHOI")
    booking = _booking(db)
    _give_task(db, "vehicle_booking", booking.id, manager)

    assert _body(get_booking(booking.id, db, manager))["code"] == "DX7001"


def test_seal_attachments_readable_by_pending_approver_only(db):
    legal = _account(db, "PHAPLY3")
    outsider = _account(db, "NGOAI3")
    req = _seal(db)
    _give_task(db, "seal_request", req.id, legal)

    check_attachment(db, legal, "seal_request", "read", req.id)   # không ném
    with pytest.raises(HTTPException) as err:
        check_attachment(db, outsider, "seal_request", "read", req.id)
    assert err.value.status_code == 403


def test_pending_approver_cannot_upload_attachments(db):
    legal = _account(db, "PHAPLY4")
    req = _seal(db)
    _give_task(db, "seal_request", req.id, legal)

    with pytest.raises(HTTPException):
        check_attachment(db, legal, "seal_request", "manage", req.id)


def test_comments_open_for_pending_approver(db):
    legal = _account(db, "PHAPLY5")
    req = _seal(db)
    _give_task(db, "seal_request", req.id, legal)

    doc, _, _ = resolve_doc(db, legal, "seal_request", req.id)
    assert doc.id == req.id


def test_rule_only_covers_declared_entities(db):
    user = _account(db, "VANBAN")
    _give_task(db, "document", 5, user)

    assert "document" not in APPROVER_READABLE
    assert is_pending_approver(db, "document", 5, user) is False


def test_user_without_employee_profile_never_matches(db):
    user = User(email="khongho@dego.test", employee_id=0, is_active=True)
    db.add(user)
    db.flush()

    assert is_pending_approver(db, "seal_request", 1, user) is False


def test_legal_role_is_a_standard_seal_role():
    from app.seed import ROLE_DESCRIPTIONS, STD_ROLES

    role = STD_ROLES["seal_legal"]
    assert role["perms"]["seal_request"] == (["read"], "all")
    assert "seal_legal" in ROLE_DESCRIPTIONS
