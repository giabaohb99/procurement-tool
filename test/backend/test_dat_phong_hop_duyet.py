"""ĐẶT PHÒNG HỌP — bốn kết cục của bộ máy duyệt và thư mời (duoc-CR-279).

Ba kết cục KHÔNG duyệt đều phải **nhả phòng**. Ở Nghỉ phép quên nhả là số ngày
treo vĩnh viễn trong quỹ; ở đây quên nhả là phòng bị khóa vĩnh viễn trong khung
giờ đó — không có triệu chứng nào cho tới khi ai đó đứng ngoài cửa một phòng
trống mà hệ thống báo đã có người.
"""
from datetime import datetime
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.modules.approval.flow_model import (APPROVER_EMPLOYEE, ApprovalFlow,
                                             ApprovalNode, ApprovalSwitch)
from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.meeting_room import approval_bridge, service
from app.modules.meeting_room.constants import (RB_APPROVED, RB_DRAFT,
                                                RB_PENDING, RB_REJECTED,
                                                RB_RETURNED)
from app.modules.meeting_room.model import MeetingRoom
from app.modules.meeting_room.schema import AttendeeItem, RoomBookingCreate
from app.modules.notification.model import Notification
from app.modules.user.model import User

MORNING = datetime(2026, 9, 10, 9, 0)


def _at_hour(h: int) -> datetime:
    return MORNING.replace(hour=h)


@pytest.fixture
def env(db):
    company = Company(name="Cty Test", code="CT01", is_active=True)
    db.add(company)
    db.flush()
    dept = Department(code="D1", name="Phòng Test", company_id=company.id, is_active=True)
    db.add(dept)
    db.flush()

    an = Employee(code="AN", full_name="Nguyễn Văn An", company_id=company.id,
                  department_id=dept.id, is_active=True)
    binh = Employee(code="BINH", full_name="Trần Thị Bình", company_id=company.id,
                    department_id=dept.id, is_active=True)
    db.add_all([an, binh])
    db.flush()
    db.add_all([
        User(email="AN", employee_id=an.id, password_hash="x", is_active=True),
        User(email="BINH", employee_id=binh.id, password_hash="x", is_active=True),
    ])
    room = MeetingRoom(code="P301", name="Phòng 301", company_id=company.id,
                        capacity=8, is_active=True, created_by=1, updated_by=1)
    db.add(room)
    db.commit()
    return SimpleNamespace(company=company, an=an, binh=binh, room=room,
                           user=SimpleNamespace(id=1, employee_id=an.id))


def _pending_booking(db, env, invitees=()):
    obj = service.create(db, RoomBookingCreate(
        room_id=env.room.id, title="Họp giao ban",
        start_at=_at_hour(9), end_at=_at_hour(10),
        attendees=[AttendeeItem(employee_id=i) for i in invitees],
    ), env.user)
    service.prepare_submit(db, obj, env.user)
    return service.reserve_slot(db, obj, env.user)


class _FakeInstance:
    """Phiên duyệt giả — chỉ hai thuộc tính mà hook thật sự đọc tới."""

    def __init__(self, reason: str = ""):
        self.updated_by = 9
        self.finish_reason = reason


def _declare_flow(db, env, *, switch_on: bool):
    """Khai một luồng MỘT bước cho đặt phòng, kèm/không kèm bật cờ.

    Khai luồng và bật cờ là HAI việc tách nhau ở màn «Bật bộ máy duyệt», nên
    tham số hoá đúng chỗ đó chứ không dựng hai hàm chép nhau.
    """
    flow = ApprovalFlow(entity=approval_bridge.ENTITY, code="PH-TEST",
                        name="Duyệt đặt phòng (thử)", is_active=True,
                        created_by=1, updated_by=1)
    db.add(flow)
    db.flush()
    db.add(ApprovalNode(flow_id=flow.id, seq=1, name="Trưởng bộ phận",
                        approver_kind=APPROVER_EMPLOYEE, approver_ref=str(env.binh.id),
                        created_by=1, updated_by=1))
    if switch_on:
        db.add(ApprovalSwitch(entity=approval_bridge.ENTITY, is_enabled=True,
                              created_by=1, updated_by=1))
    db.commit()
    return flow


# ── Công tắc «Bật bộ máy duyệt» ────────────────────────────────────────────────

def test_co_luong_nhung_co_TAT_thi_phieu_di_duong_duyet_THANG(db, env):
    """Công tắc phải THẬT SỰ cắt được, không phải nút giả.

    Trước 05/09/2026 đặt phòng trình thẳng vào bộ máy mà không hỏi cờ, nên gạt
    tắt xong phiếu vẫn chui vào luồng nhiều bước — đúng cái mà cả màn hình đó
    nói là "đường lui".
    """
    _declare_flow(db, env, switch_on=False)
    obj = _pending_booking(db, env)

    assert approval_bridge.start_approval(db, obj, env.user) == 0, \
        "Cờ TẮT mà vẫn mở phiên nghĩa là công tắc là nút giả"
    assert approval_bridge.running_instance(db, obj.id) is None

    #  Đường lui phải đi được thật: không có phiên nên chốt chặn duyệt thẳng
    #  không được ném. Thiếu khẳng định này thì phiếu vào Chờ duyệt mà không ai
    #  ký nổi — tức là phòng bị khóa vĩnh viễn, đúng nỗi lo ở đầu tệp.
    approval_bridge.block_legacy_path(db, obj)


def test_co_BAT_va_co_luong_thi_mo_phien_nhieu_buoc(db, env):
    """Bật cờ lên là phiếu đi bộ máy — và lúc đó ba nút duyệt thẳng phải khóa."""
    _declare_flow(db, env, switch_on=True)
    obj = _pending_booking(db, env)

    instance_id = approval_bridge.start_approval(db, obj, env.user)

    assert instance_id > 0, "Có luồng + cờ bật mà `start` trả 0 nghĩa là chưa nối được"
    assert approval_bridge.running_instance(db, obj.id) is not None
    with pytest.raises(HTTPException):
        approval_bridge.block_legacy_path(db, obj)


def test_chua_khai_luong_thi_bat_co_cung_khong_ket_phieu(db, env):
    """Cờ BẬT nhưng chưa luồng nào áp → vẫn rơi về đường duyệt thẳng.

    Hai đường lui khác nhau và cả hai đều phải sống: *cố ý tắt* và *tình cờ chưa
    khai luồng*. Bật cờ trước rồi mới khai luồng là thứ tự người ta hay làm.
    """
    db.add(ApprovalSwitch(entity=approval_bridge.ENTITY, is_enabled=True,
                          created_by=1, updated_by=1))
    db.commit()
    obj = _pending_booking(db, env)

    assert approval_bridge.start_approval(db, obj, env.user) == 0
    approval_bridge.block_legacy_path(db, obj)


# ── Bốn kết cục ────────────────────────────────────────────────────────────────

def test_duyet_xong_thi_phong_thuoc_ve_phieu(db, env):
    obj = _pending_booking(db, env)
    approval_bridge._on_approved(db, obj.id, _FakeInstance())
    db.commit()
    db.refresh(obj)

    assert obj.status == RB_APPROVED
    assert obj.decided_at is not None


def test_tu_choi_thi_NHA_phong(db, env):
    obj = _pending_booking(db, env)
    approval_bridge._on_rejected(db, obj.id, _FakeInstance("Trùng lịch lãnh đạo"))
    db.commit()
    db.refresh(obj)

    assert obj.status == RB_REJECTED
    assert obj.decision_note == "Trùng lịch lãnh đạo"
    #  Nhả thật: người khác đặt được đúng khung giờ đó.
    assert service.find_conflict(db, env.room.id, _at_hour(9), _at_hour(10)) is None


def test_tra_ve_thi_nha_phong_va_SUA_LAI_DUOC(db, env):
    """Khác «từ chối» đúng ở chỗ sửa lại và gửi lại được."""
    obj = _pending_booking(db, env)
    approval_bridge._on_returned(db, obj.id, _FakeInstance())
    db.commit()
    db.refresh(obj)

    assert obj.status == RB_RETURNED
    assert service.find_conflict(db, env.room.id, _at_hour(9), _at_hour(10)) is None
    service.check_editable(obj)  # không ném là sửa được


def test_nguoi_dat_tu_rut_thi_ve_NHAP(db, env):
    """Về «Nháp», không phải «Trả về»: không ai trả gì cho họ cả."""
    obj = _pending_booking(db, env)
    approval_bridge._on_withdrawn(db, obj.id, _FakeInstance())
    db.commit()
    db.refresh(obj)

    assert obj.status == RB_DRAFT
    assert service.find_conflict(db, env.room.id, _at_hour(9), _at_hour(10)) is None


def test_hook_khong_chay_lai_tren_phieu_da_chot(db, env):
    """Bộ máy bắn lại hook (thử lại, hai chặng cùng kết thúc) không được đổi gì."""
    obj = _pending_booking(db, env)
    approval_bridge._on_approved(db, obj.id, _FakeInstance())
    db.commit()
    approval_bridge._on_rejected(db, obj.id, _FakeInstance("muộn rồi"))
    db.commit()
    db.refresh(obj)

    assert obj.status == RB_APPROVED


# ── Thư mời người dự ───────────────────────────────────────────────────────────

def test_duyet_xong_thi_bao_cho_nguoi_duoc_moi(db, env):
    obj = _pending_booking(db, env, invitees=[env.binh.id])
    approval_bridge._on_approved(db, obj.id, _FakeInstance())
    db.commit()

    mails = db.query(Notification).all()
    assert len(mails) == 1
    assert "Họp giao ban" in mails[0].title
    #  Bấm vào phải đi tới đúng phiếu — thư không có link là thư vô dụng.
    assert mails[0].link == f"/hr/room-bookings/{obj.id}"


def test_KHONG_bao_truoc_khi_duyet(db, env):
    """Phiếu chưa duyệt thì cuộc họp chưa chắc diễn ra, mà thư gửi rồi không rút lại được."""
    _pending_booking(db, env, invitees=[env.binh.id])
    assert db.query(Notification).count() == 0


def test_nguoi_dat_khong_tu_moi_chinh_minh(db, env):
    obj = _pending_booking(db, env, invitees=[env.an.id])
    approval_bridge._on_approved(db, obj.id, _FakeInstance())
    db.commit()
    assert db.query(Notification).count() == 0


def test_nguoi_du_chua_co_tai_khoan_thi_bo_qua_im_lang(db, env):
    """Mời một người chưa được cấp tài khoản: không có ai để gửi, và cũng không nổ."""
    obj = _pending_booking(db, env, invitees=[999999])
    approval_bridge._on_approved(db, obj.id, _FakeInstance())
    db.commit()
    db.refresh(obj)

    assert obj.status == RB_APPROVED
    assert db.query(Notification).count() == 0


def test_bang_thong_bao_hong_KHONG_lam_hong_viec_chot_phong(db, env, monkeypatch):
    """Chuông hỏng thì thôi — phòng đã duyệt là chuyện lớn hơn một cái thư.

    Cùng lẽ (và cùng cách nuốt lỗi) với `notify_new_tasks` của bộ máy duyệt.
    """
    import app.modules.notification.model as notification_model

    class BoomOnWrite:
        def __init__(self, *a, **kw):
            raise RuntimeError("bảng thông báo có chuyện")

    monkeypatch.setattr(notification_model, "Notification", BoomOnWrite)

    obj = _pending_booking(db, env, invitees=[env.binh.id])
    #  Không ném ra ngoài, và phiếu vẫn được chốt.
    approval_bridge._on_approved(db, obj.id, _FakeInstance())
    db.commit()
    db.refresh(obj)
    assert obj.status == RB_APPROVED
