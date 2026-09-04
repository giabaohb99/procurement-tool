"""THÔNG BÁO của Đặt phòng họp — hai đường thư, hai lúc khác nhau.

1. **Gửi duyệt → người duyệt nhận thư «Chờ bạn duyệt»** (bộ máy dùng chung).
2. **Duyệt xong → người được mời nhận thư «Mời họp»** (riêng của phân hệ này).

⚠️ Cả hai đường đều **nuốt lỗi có chủ ý** — mất phiếu vì không gửi được thư thì
tệ hơn thiếu một cái thư. Nghĩa là mọi hỏng hóc ở đây đều IM LẶNG, và bài kiểm
là thứ duy nhất phát hiện ra. Hai lỗi đã có thật ở Nghỉ phép mà tệp này chốt lại
cho Đặt phòng:

* thiếu `ENTITY_LABELS` → thư mở đầu bằng *"Phiếu PH012 đang chờ bạn"*, người
  duyệt của một hệ bảy loại chứng từ không biết mình sắp mở cái gì;
* thiếu `ENTITY_LINKS` → `link` RỖNG, thư vẫn gửi nhưng bấm vào không đi đâu cả.
"""
from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest

from app.modules.approval import action_service, instance_service
from app.modules.approval.flow_model import (APPROVER_EMPLOYEE, ApprovalFlow,
                                             ApprovalNode, ApprovalSwitch)
from app.modules.approval.task_notification import ENTITY_LABELS, ENTITY_LINKS
from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.meeting_room import approval_bridge, service
from app.modules.meeting_room.model import MeetingRoom
from app.modules.meeting_room.schema import AttendeeItem, RoomBookingCreate
from app.modules.notification.model import Notification
from app.modules.user.model import User

ACTOR = 1
ENTITY = "room_booking"
MEETING_AT = datetime(2026, 9, 10, 9, 0)


def _employee_with_account(db, code, name):
    """Người nhận thư phải có TÀI KHOẢN — thư ghi theo `user_id`, không phải nhân sự.

    Nhân sự không tài khoản thì không thư nào được ghi; đó là hành vi đúng, nhưng
    nó cũng làm mọi bài kiểm ở đây xanh giả nếu quên dựng tài khoản.
    """
    employee = Employee(code=code, full_name=name, company_id=1,
                        department_id=1, is_active=True)
    db.add(employee)
    db.flush()
    user = User(email=f"{code.lower()}@demo.com", password_hash="x",
                employee_id=employee.id, is_active=True)
    db.add(user)
    db.flush()
    return employee, user


@pytest.fixture()
def env(db):
    db.add(Company(name="Cty Test", code="CT01", is_active=True))
    db.flush()
    db.add(Department(code="D1", name="Phòng Test", company_id=1, is_active=True))
    db.flush()

    requester, acc_requester = _employee_with_account(db, "DAT", "Người đặt")
    approver, acc_approver = _employee_with_account(db, "DUYET", "Hành chính")
    guest1, acc_guest1 = _employee_with_account(db, "DU1", "Người dự một")
    guest2, acc_guest2 = _employee_with_account(db, "DU2", "Người dự hai")

    room = MeetingRoom(code="P301", name="Phòng 301", company_id=1, capacity=8,
                       is_active=True, created_by=ACTOR, updated_by=ACTOR)
    db.add(room)
    db.flush()

    flow = ApprovalFlow(entity=ENTITY, code="PH-1B", name="Duyệt đặt phòng",
                        is_active=True, created_by=ACTOR, updated_by=ACTOR)
    db.add(flow)
    db.flush()
    db.add(ApprovalNode(flow_id=flow.id, seq=1, name="Hành chính duyệt",
                        approver_kind=APPROVER_EMPLOYEE, approver_ref=str(approver.id),
                        created_by=ACTOR, updated_by=ACTOR))
    db.add(ApprovalSwitch(entity=ENTITY, is_enabled=True,
                          created_by=ACTOR, updated_by=ACTOR))
    db.commit()

    return SimpleNamespace(room=room, requester=requester, approver=approver, guest1=guest1, guest2=guest2,
                           acc_approver=acc_approver, acc_guest1=acc_guest1, acc_guest2=acc_guest2,
                           acc_requester=acc_requester,
                           user_requester=SimpleNamespace(id=acc_requester.id, employee_id=requester.id))


def _book_and_submit(db, env, invitees=()):
    """Lập phiếu rồi gửi duyệt — đúng ba nhịp mà controller chạy."""
    obj = service.create(db, RoomBookingCreate(
        room_id=env.room.id, title="Họp giao ban",
        start_at=MEETING_AT, end_at=MEETING_AT + timedelta(hours=1),
        attendees=[AttendeeItem(employee_id=i) for i in invitees],
    ), env.user_requester)
    service.prepare_submit(db, obj, env.user_requester)
    obj = service.reserve_slot(db, obj, env.user_requester)
    instance_id = approval_bridge.start_approval(db, obj, env.user_requester)
    return service.attach_instance(db, obj, instance_id)


def _inbox(db, account: User) -> list[Notification]:
    return (db.query(Notification)
            .filter(Notification.user_id == account.id)
            .order_by(Notification.id.asc()).all())


# ── 1. Gửi duyệt → người duyệt nhận thư ───────────────────────────────────────

def test_gui_duyet_thi_nguoi_duyet_nhan_thu(db, env):
    assert _inbox(db, env.acc_approver) == []
    _book_and_submit(db, env)
    db.commit()

    mails = _inbox(db, env.acc_approver)
    assert len(mails) == 1, "người duyệt phải nhận đúng một thư báo việc"


def test_thu_bao_viec_goi_dung_TEN_LOAI_chung_tu(db, env):
    """Thiếu `ENTITY_LABELS` thì thư mở đầu bằng «Phiếu PH001 đang chờ bạn»."""
    assert ENTITY_LABELS.get(ENTITY) == "Phiếu đặt phòng họp"

    obj = _book_and_submit(db, env)
    db.commit()
    body_text = _inbox(db, env.acc_approver)[0].body
    assert "Phiếu đặt phòng họp" in body_text
    assert obj.code in body_text


def test_thu_bao_viec_co_LINK_bam_duoc(db, env):
    """`link` rỗng thì thư vẫn gửi nhưng bấm vào KHÔNG đi đâu cả."""
    assert ENTITY_LINKS.get(ENTITY) == "/hr/room-bookings/{id}"

    obj = _book_and_submit(db, env)
    db.commit()
    assert _inbox(db, env.acc_approver)[0].link == f"/hr/room-bookings/{obj.id}"


def test_nguoi_DAT_khong_nhan_thu_bao_viec(db, env):
    """Thư báo việc chỉ gửi cho người phải ký — người đặt đã biết mình vừa nộp."""
    _book_and_submit(db, env)
    db.commit()
    assert _inbox(db, env.acc_requester) == []


# ── 2. Duyệt xong → người được mời nhận thư ───────────────────────────────────

def test_duyet_xong_thi_nguoi_duoc_moi_nhan_thu(db, env):
    obj = _book_and_submit(db, env, invitees=[env.guest1.id, env.guest2.id])
    db.commit()
    #  Chưa duyệt thì CHƯA ai được mời nhận gì — cuộc họp chưa chắc diễn ra.
    assert _inbox(db, env.acc_guest1) == []

    instance = instance_service.running_instance(db, ENTITY, obj.id)
    action_service.approve(db, instance, env.approver.id, env.acc_approver.id, "")
    db.commit()

    for account in (env.acc_guest1, env.acc_guest2):
        mails = _inbox(db, account)
        assert len(mails) == 1, "mỗi người được mời nhận đúng một thư"
        assert "Họp giao ban" in mails[0].title
        assert mails[0].link == f"/hr/room-bookings/{obj.id}"


def test_thu_moi_noi_ro_GIO_va_PHONG(db, env):
    """Thư mời mà không có giờ và phòng thì người nhận vẫn phải mở phiếu ra xem."""
    obj = _book_and_submit(db, env, invitees=[env.guest1.id])
    instance = instance_service.running_instance(db, ENTITY, obj.id)
    action_service.approve(db, instance, env.approver.id, env.acc_approver.id, "")
    db.commit()

    body = _inbox(db, env.acc_guest1)[0].body
    assert "09:00" in body
    assert "Phòng 301" in body
    assert obj.code in body


def test_TU_CHOI_thi_khong_ai_nhan_thu_moi(db, env):
    """Cuộc họp không diễn ra thì thư mời là thư rác — mà gửi rồi không rút được."""
    obj = _book_and_submit(db, env, invitees=[env.guest1.id])
    instance = instance_service.running_instance(db, ENTITY, obj.id)
    action_service.reject(db, instance, env.approver.id, env.acc_approver.id, "Trùng lịch")
    db.commit()

    assert _inbox(db, env.acc_guest1) == []
