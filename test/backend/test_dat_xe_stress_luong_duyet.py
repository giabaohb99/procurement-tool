"""ÉP TẢI (21/09/2026) — PHIẾU ĐẶT XE chạy qua BỘ MÁY DUYỆT NHIỀU BƯỚC.

`test_dat_xe_luong_duyet_runtime.py` kiểm từng mảnh của cái nối (`approval_bridge`)
bằng cách gọi thẳng hook. `test_dat_xe_luong_6_buoc.py` chạy vòng đời đẹp ở đường
duyệt MỘT BƯỚC. Tệp này chạy phần XẤU của đường NHIỀU BƯỚC — đúng cảnh khách mô
tả: **một người lập phiếu, một người khác được phân quyền vào duyệt**, rồi ép vào
những chỗ dễ vỡ:

    ai ĐỌC được phiếu mình phải duyệt · ba nút duyệt thẳng bị khóa tới đâu ·
    hai nút của ĐIỀU PHỐI có bị khóa không · điều phối phiếu CHƯA duyệt ·
    xóa phiếu đang bay · nhấp đúp · ai đứng tên NGƯỜI KÝ trên phiếu

**Sợi chỉ xuyên suốt: MỘT PHIẾU CHỈ CÓ MỘT ĐƯỜNG ĐỔI TRẠNG THÁI.** Đang chạy
trong luồng nhiều bước thì mọi cửa khác phải đóng — không thì có hai nguồn sự
thật cho cùng một phiếu, và cái thắng là cái bấm sau. Đó là lý do
`block_legacy_path` tồn tại; các bài dưới đây đo xem nó đứng đủ chỗ chưa.
"""
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.modules.approval import action_service, instance_service
from app.modules.approval.flow_model import (APPROVER_DEPT_HEAD,
                                             APPROVER_EMPLOYEE, MULTI_ANY,
                                             NO_APPROVER_BLOCK, SKIP_NONE,
                                             ApprovalFlow, ApprovalNode,
                                             ApprovalSwitch)
from app.modules.approval.instance_model import (INSTANCE_APPROVED,
                                                 INSTANCE_BLOCKED,
                                                 INSTANCE_REJECTED,
                                                 INSTANCE_RETURNED,
                                                 INSTANCE_RUNNING,
                                                 TASK_APPROVED, TASK_CANCELLED,
                                                 TASK_PENDING)
from app.modules.vehicle_booking import approval_bridge as bridge
from app.modules.vehicle_booking import model as m
from app.modules.vehicle_booking import service
from app.modules.vehicle_booking.schema import (DispatchIn, ReasonIn,
                                                VehicleBookingCreate)
from scope_factory import build_world  # noqa: F401 — fixture `world` dùng nó

ACTOR = 1
ENTITY = "vehicle_booking"


# ══════════════════════════════════════════════════════════════════════════════
#  Dựng cảnh
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture()
def flow(db):
    """Luồng RỖNG cho đặt xe, cờ đã bật. Mỗi bài tự khai bước của riêng nó."""
    row = ApprovalFlow(entity=ENTITY, code="DX-STRESS", name="Ép tải đặt xe",
                       is_active=True, created_by=ACTOR, updated_by=ACTOR)
    db.add(row)
    db.add(ApprovalSwitch(entity=ENTITY, is_enabled=True,
                          created_by=ACTOR, updated_by=ACTOR))
    db.flush()
    return row


def make_node(db, flow, seq, name, *, employee_ids=(), kind=APPROVER_EMPLOYEE,
              multi_mode=MULTI_ANY):
    node = ApprovalNode(
        flow_id=flow.id, seq=seq, name=name, approver_kind=kind,
        approver_ref=",".join(str(i) for i in employee_ids),
        multi_mode=multi_mode, skip_duplicate=SKIP_NONE,
        on_no_approver=NO_APPROVER_BLOCK,
        created_by=ACTOR, updated_by=ACTOR)
    db.add(node)
    db.flush()
    return node


@pytest.fixture()
def cast(db, world):
    """Ba vai của cảnh, gắn quyền ĐÚNG như phân quyền thật của phân hệ Đặt xe.

    * `creator` — nhân viên phòng Kế toán A: tạo & theo dõi phiếu CỦA MÌNH
      (phạm vi `own`, đúng mặc định của vai trò nhân viên).
    * `approver` — trưởng phòng Kế toán A: `approve` phạm vi `dept`, tức ĐỌC
      ĐƯỢC phiếu của người trong phòng mình.
    * `outsider_approver` — trưởng phòng Thu mua A: cũng `approve` phạm vi
      `dept`, nhưng phiếu của phòng Kế toán NẰM NGOÀI phạm vi họ. Đây là hình
      dạng dữ liệu bình thường nhất của một luồng hai chặng (chặng 2 là Hành
      chính / Nhân sự, ở phòng khác), nên nó phải chạy được.
    * `dispatcher` — điều phối viên: `vehicle_booking` write/approve phạm vi
      `all` (đúng seed `booking_dispatcher`).
    """
    world.grant("a1", ENTITY, scope="own", actions=("read", "create", "write", "delete"))
    world.grant("a2", ENTITY, scope="dept", actions=("read", "approve"))
    world.grant("a3", ENTITY, scope="dept", actions=("read", "approve"))
    world.grant("b1", ENTITY, scope="all", actions=("read", "write", "approve"))
    return SimpleNamespace(
        creator=world.actor("a1"),
        approver=world.actor("a2"),
        outsider_approver=world.actor("a3"),
        dispatcher=world.actor("b1"),
    )


def build_payload(**over):
    data = dict(request_type=1, purpose="Đón đối tác ở sân bay", start_location="VP",
                end_location="Sân bay", start_time="2026-10-01T08:00",
                end_time="2026-10-01T12:00", passenger_count=2)
    data.update(over)
    return VehicleBookingCreate(**data)


def submit_booking(db, actor, **over):
    """Người ta lập phiếu rồi bấm GỬI DUYỆT — đúng đường controller đi."""
    booking = service.create_booking(db, build_payload(**over), actor.user, submit=True)
    return booking, instance_service.running_instance(db, ENTITY, booking.id)


def save_draft(db, actor, **over):
    return service.create_booking(db, build_payload(**over), actor.user, submit=False)


def add_fleet(db):
    vehicle = m.Vehicle(license_plate="51A-123.45", model="Innova")
    driver = m.Driver(name="Tài Xế A", phone="0909000111")
    db.add_all([vehicle, driver])
    db.flush()
    return vehicle, driver


def list_tasks(db, instance, *, seq=None):
    rows = instance_service.tasks_of_instance(db, instance.id)
    return [t for t in rows if seq is None or t.node_seq == seq]


def list_states(db, instance, seq=None):
    return sorted((t.assignee_employee_id, t.status) for t in list_tasks(db, instance, seq=seq))


def call_dispatch_return(db, booking_id, reason, actor):
    """Gọi ĐÚNG hàm controller — chốt `block_legacy_path` nằm ở đó, không ở service.

    Cố ý vậy: bộ máy duyệt gọi thẳng hàm service khi phiên kết thúc, nên đặt chốt
    ở service là nó tự chặn chính mình (xem `approval_bridge.block_legacy_path`).
    """
    from fastapi import BackgroundTasks

    from app.modules.vehicle_booking import controller

    return controller.dispatch_return_booking(
        booking_id, ReasonIn(reason=reason), BackgroundTasks(), db, actor.user)


def call_dispatch_reject(db, booking_id, reason, actor):
    from fastapi import BackgroundTasks

    from app.modules.vehicle_booking import controller

    return controller.dispatch_reject_booking(
        booking_id, ReasonIn(reason=reason), BackgroundTasks(), db, actor.user)


def sign(db, instance, actor, comment=""):
    """Người duyệt bấm DUYỆT trên hộp «Việc của tôi»."""
    return action_service.approve(db, instance, actor.employee.id, actor.user.id,
                                  bridge._context_by_id(db, instance.entity_id), comment)


# ══════════════════════════════════════════════════════════════════════════════
#  1. Một người tạo — một người khác duyệt (đường sống)
# ══════════════════════════════════════════════════════════════════════════════

def test_submit_opens_instance_and_assigns_first_step(db, flow, cast):
    make_node(db, flow, 1, "Trưởng bộ phận", employee_ids=[cast.approver.employee.id])
    booking, instance = submit_booking(db, cast.creator)

    assert booking.status == m.BK_PENDING
    assert instance is not None and instance.status == INSTANCE_RUNNING
    #  Người NỘP phải là người BẤM GỬI DUYỆT, không phải một hằng số nào khác —
    #  mọi luật I08 («không tự duyệt phiếu của mình») bám vào cột này.
    assert instance.started_by_employee_id == cast.creator.employee.id
    assert list_states(db, instance) == [(cast.approver.employee.id, TASK_PENDING)]


def test_signing_first_of_two_steps_does_not_move_booking(db, flow, cast):
    """Ký nửa chừng mà phiếu đã «Đã duyệt» thì điều phối viên gọi xe cho một
    chuyến chưa ai duyệt xong."""
    make_node(db, flow, 1, "Trưởng bộ phận", employee_ids=[cast.approver.employee.id])
    make_node(db, flow, 2, "Hành chính", employee_ids=[cast.outsider_approver.employee.id])
    booking, instance = submit_booking(db, cast.creator)

    sign(db, instance, cast.approver)
    db.refresh(booking)

    assert booking.status == m.BK_PENDING
    assert list_states(db, instance, seq=2) == [
        (cast.outsider_approver.employee.id, TASK_PENDING)]


def test_signing_both_steps_approves_the_booking(db, flow, cast):
    make_node(db, flow, 1, "Trưởng bộ phận", employee_ids=[cast.approver.employee.id])
    make_node(db, flow, 2, "Hành chính", employee_ids=[cast.outsider_approver.employee.id])
    booking, instance = submit_booking(db, cast.creator)

    sign(db, instance, cast.approver)
    sign(db, instance, cast.outsider_approver)
    db.refresh(booking)
    db.refresh(instance)

    assert (booking.status, instance.status) == (m.BK_APPROVED, INSTANCE_APPROVED)


def test_second_step_approver_cannot_sign_before_the_first(db, flow, cast):
    """Ký vượt chặng = phiếu có hiệu lực mà trưởng bộ phận chưa hề xem."""
    make_node(db, flow, 1, "Trưởng bộ phận", employee_ids=[cast.approver.employee.id])
    make_node(db, flow, 2, "Hành chính", employee_ids=[cast.outsider_approver.employee.id])
    booking, instance = submit_booking(db, cast.creator)

    with pytest.raises(HTTPException) as caught:
        sign(db, instance, cast.outsider_approver)
    assert "không có việc nào đang chờ" in caught.value.detail
    db.refresh(booking)
    assert booking.status == m.BK_PENDING


def test_rejecting_at_engine_locks_the_booking(db, flow, cast):
    make_node(db, flow, 1, "Trưởng bộ phận", employee_ids=[cast.approver.employee.id])
    booking, instance = submit_booking(db, cast.creator)

    action_service.reject(db, instance, cast.approver.employee.id,
                          cast.approver.user.id, "Không thuộc mục đích công tác")
    db.refresh(booking)
    db.refresh(instance)

    assert (booking.status, instance.status) == (m.BK_REJECTED, INSTANCE_REJECTED)
    #  Phiếu bị từ chối thì đường duyệt thẳng cũng phải câm.
    with pytest.raises(HTTPException):
        service.approve_booking(db, booking, cast.dispatcher.user)


def test_sending_back_lets_the_creator_fix_and_resubmit(db, flow, cast):
    make_node(db, flow, 1, "Trưởng bộ phận", employee_ids=[cast.approver.employee.id])
    booking, instance = submit_booking(db, cast.creator)

    action_service.send_back(db, instance, cast.approver.employee.id,
                             cast.approver.user.id, "Thiếu người tham gia",
                             bridge._context_by_id(db, booking.id))
    db.refresh(booking)
    db.refresh(instance)

    assert (booking.status, instance.status) == (m.BK_RETURNED, INSTANCE_RETURNED)
    assert bridge.running_instance(db, booking.id) is None

    #  Sửa rồi gửi lại → mở phiên MỚI, không vá lại phiên cũ.
    from app.modules.vehicle_booking.schema import VehicleBookingUpdate
    service.update_booking(db, booking, VehicleBookingUpdate(attendees="Anh Nam, chị Lan"),
                           cast.creator.user, submit=True)
    db.refresh(booking)
    again = bridge.running_instance(db, booking.id)

    assert booking.status == m.BK_PENDING
    assert again is not None and again.id != instance.id


def test_creator_who_is_also_department_head_cannot_self_approve(db, flow, cast, world):
    """I08 — bước «Trưởng bộ phận» tính ra đúng người vừa nộp thì phiếu KẸT.

    Không được tự đi tiếp: chuyến xe có hiệu lực mà không ai ngoài người xin
    chịu trách nhiệm.
    """
    from app.modules.department.model import Department

    dept = db.get(Department, cast.creator.employee.department_id)
    dept.manager_id = cast.creator.employee.id
    db.flush()
    make_node(db, flow, 1, "Trưởng bộ phận duyệt", kind=APPROVER_DEPT_HEAD)

    booking, instance = submit_booking(db, cast.creator)
    db.refresh(instance)

    assert instance.status == INSTANCE_BLOCKED
    assert booking.status == m.BK_PENDING


# ══════════════════════════════════════════════════════════════════════════════
#  2. NGƯỜI DUYỆT CÓ ĐỌC ĐƯỢC PHIẾU HỌ PHẢI DUYỆT KHÔNG
# ══════════════════════════════════════════════════════════════════════════════

def test_assigned_approver_in_scope_can_read_the_booking(db, flow, cast):
    """Đối chứng: trưởng phòng CÙNG phòng thì phạm vi `dept` đã đủ."""
    make_node(db, flow, 1, "Trưởng bộ phận", employee_ids=[cast.approver.employee.id])
    booking, _ = submit_booking(db, cast.creator)

    assert bridge._can_read_booking(db, booking.id, cast.approver.user) is True


def test_assigned_approver_outside_scope_can_still_read_the_booking(db, flow, cast):
    """⚠️ Bộ máy GIAO VIỆC cho họ thì phải cho họ ĐỌC thứ họ phải ký.

    Chặng 2 của một luồng thật hầu như luôn là người phòng khác (Hành chính,
    Nhân sự, Ban giám đốc), mà phạm vi dữ liệu của họ không với tới phiếu của
    phòng Kế toán. Không nới thì bộ máy giao việc rồi chặn chính người được
    giao: `/api/approvals/of/vehicle_booking/{id}` trả `null`, mở chi tiết phiếu
    ăn 404 — họ **bấm Duyệt được mà không đọc được thứ mình duyệt**.

    Nghỉ phép đã vá đúng chỗ này (CR-260: `can_read_request` nới khi đang có
    việc `TASK_PENDING`). Đặt xe dùng `get_scoped` trơ.
    """
    make_node(db, flow, 1, "Trưởng bộ phận", employee_ids=[cast.approver.employee.id])
    make_node(db, flow, 2, "Hành chính", employee_ids=[cast.outsider_approver.employee.id])
    booking, instance = submit_booking(db, cast.creator)
    sign(db, instance, cast.approver)   # tới lượt người phòng khác

    #  Họ ký được…
    assert [t.status for t in list_tasks(db, instance, seq=2)] == [TASK_PENDING]
    #  …nhưng đọc được không?
    assert bridge._can_read_booking(db, booking.id, cast.outsider_approver.user) is True


def test_assigned_approver_outside_scope_can_open_the_booking_detail(db, flow, cast):
    """Đo thứ NGƯỜI DÙNG BẤM VÀO: `GET /api/vehicle-bookings/{id}`.

    Mở cửa ở `entity_hooks` thôi thì chưa đủ — nút Duyệt nằm trong
    `BookingApprovalPanel`, mà panel đó nằm TRONG trang chi tiết phiếu. Chi tiết
    404 là người duyệt không tới được nút của mình, dù thư báo dẫn thẳng vào đây.
    """
    import json

    from app.modules.vehicle_booking import controller

    make_node(db, flow, 1, "Trưởng bộ phận", employee_ids=[cast.approver.employee.id])
    make_node(db, flow, 2, "Hành chính", employee_ids=[cast.outsider_approver.employee.id])
    booking, instance = submit_booking(db, cast.creator)
    sign(db, instance, cast.approver)

    body = json.loads(controller.get_booking(booking.id, db,
                                             cast.outsider_approver.user).body)
    assert body["data"]["code"] == booking.code


def test_booking_detail_stays_404_for_an_approver_with_no_pending_task(db, flow, cast):
    """Chốt ngược: chưa tới lượt thì vẫn 404. Nới theo quyền `approve` là mở
    toang phạm vi dữ liệu của cả phân hệ."""
    from app.modules.vehicle_booking import controller

    make_node(db, flow, 1, "Trưởng bộ phận", employee_ids=[cast.approver.employee.id])
    make_node(db, flow, 2, "Hành chính", employee_ids=[cast.outsider_approver.employee.id])
    booking, _ = submit_booking(db, cast.creator)

    with pytest.raises(HTTPException) as caught:
        controller.get_booking(booking.id, db, cast.outsider_approver.user)
    assert caught.value.status_code == 404


def test_approver_without_pending_task_still_cannot_read_other_dept_booking(db, flow, cast):
    """Chốt ngược của bài trên: nới phải nới ĐÚNG LÚC ĐANG TREO VIỆC.

    Nới theo kiểu «ai có quyền approve cũng đọc được tất» là mở toang phạm vi
    dữ liệu của cả phân hệ.
    """
    make_node(db, flow, 1, "Trưởng bộ phận", employee_ids=[cast.approver.employee.id])
    booking, _ = submit_booking(db, cast.creator)

    assert bridge._can_read_booking(db, booking.id, cast.outsider_approver.user) is False


# ══════════════════════════════════════════════════════════════════════════════
#  3. ĐANG CHẠY LUỒNG THÌ MỌI CỬA KHÁC PHẢI ĐÓNG
# ══════════════════════════════════════════════════════════════════════════════

def test_three_direct_buttons_are_locked_while_flow_runs(db, flow, cast):
    make_node(db, flow, 1, "Trưởng bộ phận", employee_ids=[cast.approver.employee.id])
    booking, _ = submit_booking(db, cast.creator)

    for label in ("approve", "return", "reject"):
        with pytest.raises(HTTPException) as caught:
            bridge.block_legacy_path(db, booking)
        assert "luồng duyệt nhiều bước" in caught.value.detail, label


def test_dispatcher_send_back_is_locked_while_flow_runs(db, flow, cast):
    """⚠️ `/{id}/dispatch/return` KHÔNG gọi `block_legacy_path`.

    Hai cửa của điều phối viên (`dispatch/return` · `dispatch/reject`) chạy đúng
    hai hàm service mà ba nút kia chạy, và `_RETURNABLE` nhận cả **Chờ duyệt** —
    nên người có `vehicle_booking.write` trả phiếu về NGAY TRONG LÚC luồng đang
    ở chặng 1. Phiên duyệt vẫn MỞ, việc vẫn treo trong hộp người duyệt.
    """
    make_node(db, flow, 1, "Trưởng bộ phận", employee_ids=[cast.approver.employee.id])
    booking, instance = submit_booking(db, cast.creator)

    with pytest.raises(HTTPException) as caught:
        call_dispatch_return(db, booking.id, "Đổi lịch", cast.dispatcher)
    assert "luồng duyệt nhiều bước" in caught.value.detail
    db.refresh(booking)
    db.refresh(instance)
    assert (booking.status, instance.status) == (m.BK_PENDING, INSTANCE_RUNNING)


def test_dispatcher_reject_is_locked_while_flow_runs(db, flow, cast):
    """Cùng lỗ với bài trên, nhưng hậu quả nặng hơn: phiếu bị KHÓA."""
    make_node(db, flow, 1, "Trưởng bộ phận", employee_ids=[cast.approver.employee.id])
    booking, instance = submit_booking(db, cast.creator)

    with pytest.raises(HTTPException) as caught:
        call_dispatch_reject(db, booking.id, "Không bố trí được xe", cast.dispatcher)
    assert "luồng duyệt nhiều bước" in caught.value.detail
    db.refresh(booking)
    assert booking.status == m.BK_PENDING


def test_rejected_booking_must_not_be_resurrected_by_a_late_signature(db, flow, cast):
    """CHỐT CUỐI ở tầng hook, độc lập với mọi cửa phía trước.

    Cảnh gốc: điều phối viên từ chối phiếu lúc nó còn Chờ duyệt (cửa
    `dispatch/reject` khi đó chưa khóa) → phiếu Từ chối nhưng phiên duyệt vẫn
    chạy → người duyệt bấm Duyệt → `_on_approved` đặt «Đã duyệt» VÔ ĐIỀU KIỆN,
    phiếu đã từ chối SỐNG LẠI. Cửa kia nay đã khóa, nhưng chốt phải nằm cả ở
    đây: hook là đường vào cuối cùng và nó không biết ai vừa đổi trạng thái
    bằng đường nào.

    Dựng cảnh bằng cách đặt thẳng trạng thái — đúng hình dạng dữ liệu mà bất kỳ
    cửa nào lọt cũng để lại.
    """
    make_node(db, flow, 1, "Trưởng bộ phận", employee_ids=[cast.approver.employee.id])
    booking, instance = submit_booking(db, cast.creator)

    booking.status = m.BK_REJECTED
    db.commit()

    sign(db, instance, cast.approver)
    db.refresh(booking)
    assert booking.status == m.BK_REJECTED


def test_dispatching_before_approval_is_allowed_and_survives_the_signature(db, flow, cast):
    """GHIM một QUYẾT ĐỊNH, không phải mô tả lỗi (đại ca chốt 21/09/2026).

    `dispatch_booking` chỉ chặn `_CLOSED_STATUSES` (hủy · từ chối · hoàn thành),
    nên điều phối viên gán được xe + tài xế cho phiếu **chưa ai ký** — giữ lại vì
    có chuyến gấp phải gọi xe trước chữ ký.

    Cái PHẢI đúng là nhịp sau đó: người duyệt ký xong thì phiếu **giữ nguyên «Đã
    điều phối»**, không bị đẩy lùi về «Đã duyệt». Đẩy lùi là xóa mất bước đã đi
    trong khi xe và tài xế vẫn đang giữ chuyến, và `driver_status` («Chờ tài xế»)
    thì cãi nhau với `status` — tài xế thấy chuyến trong «Chuyến của tôi» còn
    phiếu thì hiện «Đã duyệt».
    """
    make_node(db, flow, 1, "Trưởng bộ phận", employee_ids=[cast.approver.employee.id])
    booking, instance = submit_booking(db, cast.creator)
    vehicle, driver = add_fleet(db)

    service.dispatch_booking(
        db, booking,
        DispatchIn(assigned_vehicle_id=vehicle.id, assigned_driver_id=driver.id),
        cast.dispatcher.user)
    assert (booking.status, booking.driver_status) == (m.BK_DISPATCHED, m.DRV_WAITING)

    sign(db, instance, cast.approver)
    db.refresh(booking)

    assert (booking.status, booking.driver_status) == (m.BK_DISPATCHED, m.DRV_WAITING)
    #  Chữ ký vẫn phải được ghi lại, dù trạng thái phiếu không nhúc nhích.
    assert booking.approved_by == cast.approver.user.id and booking.approved_at


def test_dispatching_a_draft_booking_is_allowed(db, flow, cast):
    """Cùng quyết định với bài trên: phiếu còn NHÁP cũng điều phối được."""
    booking = save_draft(db, cast.creator)
    vehicle, driver = add_fleet(db)
    assert booking.status == m.BK_DRAFT

    service.dispatch_booking(
        db, booking,
        DispatchIn(assigned_vehicle_id=vehicle.id, assigned_driver_id=driver.id),
        cast.dispatcher.user)
    assert booking.status == m.BK_DISPATCHED


def test_engine_rejection_releases_a_vehicle_dispatched_early(db, flow, cast):
    """Điều phối sớm rồi bị TỪ CHỐI thì phải nhả xe/tài xế ra.

    Không nhả thì phép chống trùng khung giờ (`_find_time_conflict`) vẫn tính xe
    đó đang bận vì một phiếu đã khóa — xe nằm không mà không ai gán được.
    """
    make_node(db, flow, 1, "Trưởng bộ phận", employee_ids=[cast.approver.employee.id])
    booking, instance = submit_booking(db, cast.creator)
    vehicle, driver = add_fleet(db)
    service.dispatch_booking(
        db, booking,
        DispatchIn(assigned_vehicle_id=vehicle.id, assigned_driver_id=driver.id),
        cast.dispatcher.user)

    action_service.reject(db, instance, cast.approver.employee.id,
                          cast.approver.user.id, "Không bố trí được xe")
    db.refresh(booking)

    assert booking.status == m.BK_REJECTED
    assert not booking.assigned_vehicle_id and not booking.assigned_driver_id
    assert booking.driver_status == m.DRV_NONE


def test_creator_cannot_edit_the_booking_while_flow_runs(db, flow, cast):
    from app.modules.vehicle_booking.schema import VehicleBookingUpdate

    make_node(db, flow, 1, "Trưởng bộ phận", employee_ids=[cast.approver.employee.id])
    booking, _ = submit_booking(db, cast.creator)

    with pytest.raises(HTTPException) as caught:
        service.update_booking(db, booking, VehicleBookingUpdate(end_location="Chỗ khác"),
                               cast.creator.user, submit=False)
    assert "không sửa được" in caught.value.detail


# ══════════════════════════════════════════════════════════════════════════════
#  4. NGƯỜI KÝ là ai — phiếu và bản in phải nói đúng
# ══════════════════════════════════════════════════════════════════════════════

def test_engine_approval_records_the_real_signer_and_timestamp(db, flow, cast):
    """⚠️ `_on_approved` chỉ đặt `status` + `updated_by`, KHÔNG đặt
    `approved_by` / `approved_at` như đường duyệt một bước.

    Hai chỗ đọc hai cột đó và cùng nói sai:

    * `serialize_booking` → `approver_name = _emp_name_of_user(approved_by or
      first_approver_id)` ⇒ lùi về **người mà NGƯỜI TẠO tự chọn trong biểu mẫu**
      — người có thể chưa hề ký, hoặc không nằm trong luồng;
    * `build-booking-stages.ts` vẽ chặng «Đã phê duyệt» với `time =
      approved_at` ⇒ ô thời gian TRỐNG, và `actor` là tên người nói trên.

    Chính phiếu là chỗ người ta tin, không phải dấu vết bộ máy.
    """
    make_node(db, flow, 1, "Trưởng bộ phận", employee_ids=[cast.approver.employee.id])
    booking, instance = submit_booking(
        db, cast.creator, first_approver_id=cast.dispatcher.user.id)

    sign(db, instance, cast.approver)
    db.refresh(booking)

    assert booking.status == m.BK_APPROVED
    assert booking.approved_by == cast.approver.user.id
    assert booking.approved_at


def test_booking_shows_the_signer_not_the_person_the_creator_picked(db, flow, cast):
    """Cùng gốc với bài trên, nhưng đo thứ NGƯỜI DÙNG THẤY."""
    make_node(db, flow, 1, "Trưởng bộ phận", employee_ids=[cast.approver.employee.id])
    booking, instance = submit_booking(
        db, cast.creator, first_approver_id=cast.dispatcher.user.id)
    sign(db, instance, cast.approver)
    db.refresh(booking)

    out = service.serialize_booking(db, booking, viewer=cast.approver.user)
    assert out["approver_name"] == cast.approver.employee.full_name


# ══════════════════════════════════════════════════════════════════════════════
#  5. Xóa phiếu đang bay · nhấp đúp · gửi duyệt hai lần
# ══════════════════════════════════════════════════════════════════════════════

def test_deleting_a_booking_closes_its_running_instance(db, flow, cast):
    """⚠️ Xóa mềm phiếu KHÔNG dọn phiên duyệt (`instance_service.delete_by_entity`
    có sẵn, module đặt xe không gọi).

    Việc vẫn nằm trong hộp «Việc của tôi» của người duyệt — `my_tasks` chỉ lọc
    phiên ĐÃ ĐÓNG, còn phiên này vẫn mở. Bấm vào thì `_can_read_booking` trả
    False (phiếu `is_deleted`) ⇒ 404, mà bấm **Duyệt** thì đường duyệt KHÔNG
    kiểm quyền đọc: `_on_approved` đặt lại `status` cho một phiếu đã xóa.
    """
    from app.modules.vehicle_booking import controller

    make_node(db, flow, 1, "Trưởng bộ phận", employee_ids=[cast.approver.employee.id])
    booking, instance = submit_booking(db, cast.creator)

    instance_id = instance.id
    controller.delete_booking(booking.id, db, cast.creator.user)

    assert bridge.running_instance(db, booking.id) is None
    #  Việc mồ côi cũng phải dọn: `my_tasks` chỉ lọc phiên ĐÃ ĐÓNG nên việc treo
    #  trên một phiên còn sót vẫn hiện trong hộp người duyệt.
    from app.modules.approval.instance_model import ApprovalTask
    assert db.query(ApprovalTask).filter(ApprovalTask.instance_id == instance_id).count() == 0


def test_deleted_booking_cannot_be_approved_through_the_engine(db, flow, cast):
    """Chốt cuối ở tầng hook — phiếu đã xóa thì bộ máy không đặt trạng thái nữa.

    Đường xóa chính thức nay dọn luôn phiên duyệt (bài trên), nhưng dữ liệu cũ
    còn phiên mồ côi, và đường duyệt cố ý KHÔNG kiểm quyền đọc — nên hook vẫn
    phải tự kiểm.
    """
    make_node(db, flow, 1, "Trưởng bộ phận", employee_ids=[cast.approver.employee.id])
    booking, instance = submit_booking(db, cast.creator)
    booking.is_deleted = True
    db.commit()

    sign(db, instance, cast.approver)
    db.refresh(booking)
    assert booking.status == m.BK_PENDING


def test_double_click_on_submit_does_not_open_two_instances(db, flow, cast):
    make_node(db, flow, 1, "Trưởng bộ phận", employee_ids=[cast.approver.employee.id])
    booking, instance = submit_booking(db, cast.creator)

    with pytest.raises(HTTPException) as caught:
        bridge.submit_for_approval(db, booking, cast.creator.user.id)
    assert "chưa kết thúc" in caught.value.detail
    from app.modules.approval.instance_model import ApprovalInstance
    assert db.query(ApprovalInstance).filter(
        ApprovalInstance.entity == ENTITY,
        ApprovalInstance.entity_id == booking.id).count() == 1


def test_double_click_on_approve_records_one_signature(db, flow, cast):
    """Nhấp đúp nút Duyệt: lượt hai phải ăn 409, không ghi chữ ký thứ hai."""
    make_node(db, flow, 1, "Trưởng bộ phận", employee_ids=[cast.approver.employee.id])
    booking, instance = submit_booking(db, cast.creator)

    sign(db, instance, cast.approver)
    with pytest.raises(HTTPException):
        sign(db, instance, cast.approver)

    signed = [t for t in list_tasks(db, instance) if t.status == TASK_APPROVED]
    assert len(signed) == 1
    db.refresh(booking)
    assert booking.status == m.BK_APPROVED


def test_withdrawing_returns_the_booking_to_draft_and_frees_the_flow(db, flow, cast):
    make_node(db, flow, 1, "Trưởng bộ phận", employee_ids=[cast.approver.employee.id])
    booking, instance = submit_booking(db, cast.creator)

    action_service.withdraw(db, instance, cast.creator.employee.id,
                            cast.creator.user.id, "Đổi kế hoạch")
    db.refresh(booking)

    assert booking.status == m.BK_DRAFT
    assert bridge.running_instance(db, booking.id) is None
    assert [t.status for t in list_tasks(db, instance)] == [TASK_CANCELLED]


def test_only_the_submitter_can_withdraw(db, flow, cast):
    make_node(db, flow, 1, "Trưởng bộ phận", employee_ids=[cast.approver.employee.id])
    booking, instance = submit_booking(db, cast.creator)

    with pytest.raises(HTTPException) as caught:
        action_service.withdraw(db, instance, cast.dispatcher.employee.id,
                                cast.dispatcher.user.id, "Tôi thấy không cần")
    assert "người trình duyệt" in caught.value.detail
    db.refresh(booking)
    assert booking.status == m.BK_PENDING


# ══════════════════════════════════════════════════════════════════════════════
#  6. Đường duyệt MỘT BƯỚC (cờ tắt) — vẫn là đường đang chạy thật
# ══════════════════════════════════════════════════════════════════════════════

def test_direct_path_blocks_a_normal_user_approving_their_own_booking(db, cast):
    """I08 cho đường duyệt MỘT BƯỚC — đường ĐANG CHẠY THẬT (cờ bộ máy mặc định tắt).

    `approve_booking` trước 21/09/2026 chỉ hỏi «phiếu có đang Chờ duyệt không».
    Người kiêm một vai có `vehicle_booking.approve` tự ký phiếu xe của chính mình
    và nhật ký đọc xuôi tới mức không ai soi.
    """
    booking = service.create_booking(db, build_payload(), cast.approver.user, submit=True)
    assert booking.status == m.BK_PENDING

    with pytest.raises(HTTPException) as caught:
        service.approve_booking(db, booking, cast.approver.user)
    assert "người lập phiếu" in caught.value.detail
    db.refresh(booking)
    assert booking.status == m.BK_PENDING


def test_direct_path_still_lets_a_global_scope_dispatcher_approve_their_own(db, cast):
    """Ngoại lệ đã chốt: phạm vi `all` thì vẫn tự duyệt được.

    Điều phối viên / quản lý điều phối là người chốt xe cho cả công ty; phiếu của
    chính họ cũng chỉ có họ duyệt. Chặn cứng là khóa việc thường ngày của đúng
    hai vai trò vận hành phân hệ này.
    """
    booking = service.create_booking(db, build_payload(), cast.dispatcher.user, submit=True)

    service.approve_booking(db, booking, cast.dispatcher.user)
    assert booking.status == m.BK_APPROVED
