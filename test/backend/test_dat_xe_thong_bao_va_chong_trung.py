"""Phase 6 Đặt xe — thông báo/email theo bước + chống trùng giờ khi điều phối.

Ba chỗ dễ sai nhất:
- Mẫu email theo event: mặc định (code) vs bản người dùng sửa (DB) — DB thắng; tắt
  email thì render_event trả None; khôi phục thì về mặc định.
- Duyệt phiếu (dx_approved_dispatcher) phải sinh CHUÔNG cho vai trò Điều phối viên — đúng ca
  "TBP duyệt → điều phối viên có chuyến cần điều phối".
- Điều phối chống trùng giờ: 1 xe / 1 tài xế không nhận 2 chuyến chồng khung giờ;
  giáp ranh (kết thúc == bắt đầu) KHÔNG tính là trùng.
"""
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.modules.employee.model import Employee
from app.modules.notification import email_template_service as ets
from app.modules.notification.model import Notification
from app.modules.role.model import Role
from app.modules.user.model import User, UserRole
from app.modules.vehicle_booking import model as m
from app.modules.vehicle_booking.schema import DispatchIn, VehicleBookingCreate
from app.modules.vehicle_booking.service import (
    approve_booking,
    create_booking,
    dispatch_booking,
)


def _actor(db, *, uid=101, dept=7, company=3):
    emp = Employee(code="NV900", full_name="Phạm Người Tạo", email="creator@dego.vn",
                   department_id=dept, company_id=company)
    db.add(emp)
    db.flush()
    return SimpleNamespace(id=uid, employee_id=emp.id, email="creator@dego.vn")


def _payload(**over):
    data = dict(request_type=1, purpose="Đi công tác",
                start_location="VP", end_location="Q7",
                start_time="2026-09-01T08:00", end_time="2026-09-01T10:00",
                passenger_count=2)
    data.update(over)
    return VehicleBookingCreate(**data)


# ─────────────────────────── Mẫu email theo bước ───────────────────────────

def test_default_template_used_when_no_db_row(db):
    eff = ets.get_effective(db, "dx_approved_dispatcher")
    assert eff is not None
    assert eff["enabled"] is True
    assert eff["is_custom"] is False
    assert "{{ code }}" in eff["subject"]


def test_unknown_event_has_no_template(db):
    assert ets.get_effective(db, "khong_ton_tai") is None


def test_render_event_fills_placeholders(db):
    rendered = ets.render_event(db, "dx_approved_dispatcher", {"code": "DX042", "purpose": "x",
                                                    "start_time": "", "end_location": "",
                                                    "recipient_name": "Anh A", "link": "#"})
    assert rendered is not None
    subject, html = rendered
    assert subject == "Bạn có chuyến xe cần điều phối: DX042"
    assert "Anh A" in html


def test_db_override_wins_and_disable_stops_email(db):
    user = SimpleNamespace(id=1)
    ets.upsert(db, "dx_approved_dispatcher", enabled=True, subject="Sửa {{ code }}",
               body_html="<p>Xin chào {{ recipient_name }}</p>", user=user)
    eff = ets.get_effective(db, "dx_approved_dispatcher")
    assert eff["is_custom"] is True
    assert eff["subject"] == "Sửa {{ code }}"

    # Tắt email → render_event trả None (không gửi).
    ets.upsert(db, "dx_approved_dispatcher", enabled=False, subject="Sửa {{ code }}",
               body_html="<p>x</p>", user=user)
    assert ets.render_event(db, "dx_approved_dispatcher", {"code": "DX1"}) is None

    # Khôi phục → quay về mặc định trong code.
    ets.reset(db, "dx_approved_dispatcher")
    eff2 = ets.get_effective(db, "dx_approved_dispatcher")
    assert eff2["is_custom"] is False
    assert "{{ code }}" in eff2["subject"]


def test_empty_subject_falls_back_to_default(db):
    user = SimpleNamespace(id=1)
    ets.upsert(db, "dx_submitted", enabled=True, subject="", body_html="", user=user)
    eff = ets.get_effective(db, "dx_submitted")
    # Chuỗi rỗng không được ghi đè mất mẫu — lùi về mặc định.
    assert eff["subject"] == "YCĐX {{ code }} chờ bạn duyệt"


# ─────────────────── Chuông khi duyệt: TBP → điều phối viên ───────────────────

def _dispatcher(db, *, uid=201):
    role = Role(code="booking_dispatcher", name="Điều phối viên")
    db.add(role)
    db.flush()
    u = User(email="dispatch@dego.vn", is_active=True)
    u.id = uid
    db.add(u)
    db.flush()
    db.add(UserRole(user_id=u.id, role_id=role.id))
    db.flush()
    return u


def test_approve_notifies_dispatcher_role(db):
    actor = _actor(db)
    dispatcher = _dispatcher(db)
    b = create_booking(db, _payload(), actor, submit=True)  # Chờ duyệt
    approve_booking(db, b, actor)  # background_tasks=None → email bỏ qua, chuông vẫn tạo

    bells = db.query(Notification).filter(Notification.user_id == dispatcher.id).all()
    assert len(bells) == 1
    assert b.code in bells[0].title  # "Bạn có chuyến xe cần điều phối: DXxxx"


# ─────────────────────────── Chống trùng giờ ───────────────────────────

def _fleet(db):
    v1 = m.Vehicle(license_plate="51A-111.11", model="A")
    v2 = m.Vehicle(license_plate="51A-222.22", model="B")
    d1 = m.Driver(name="Tài Xế 1", phone="01")
    d2 = m.Driver(name="Tài Xế 2", phone="02")
    db.add_all([v1, v2, d1, d2])
    db.flush()
    return v1, v2, d1, d2


def test_dispatch_blocks_overlapping_vehicle(db):
    actor = _actor(db)
    v1, v2, d1, d2 = _fleet(db)
    b1 = create_booking(db, _payload(start_time="2026-09-01T08:00",
                                     end_time="2026-09-01T10:00"), actor, submit=True)
    dispatch_booking(db, b1, DispatchIn(assigned_vehicle_id=v1.id, assigned_driver_id=d1.id), actor)

    b2 = create_booking(db, _payload(start_time="2026-09-01T09:00",
                                     end_time="2026-09-01T11:00"), actor, submit=True)
    # Cùng XE, giờ chồng → chặn.
    with pytest.raises(HTTPException) as e:
        dispatch_booking(db, b2, DispatchIn(assigned_vehicle_id=v1.id, assigned_driver_id=d2.id), actor)
    assert "Xe" in e.value.detail


def test_dispatch_blocks_overlapping_driver(db):
    actor = _actor(db)
    v1, v2, d1, d2 = _fleet(db)
    b1 = create_booking(db, _payload(start_time="2026-09-01T08:00",
                                     end_time="2026-09-01T10:00"), actor, submit=True)
    dispatch_booking(db, b1, DispatchIn(assigned_vehicle_id=v1.id, assigned_driver_id=d1.id), actor)

    b2 = create_booking(db, _payload(start_time="2026-09-01T09:00",
                                     end_time="2026-09-01T11:00"), actor, submit=True)
    # Cùng TÀI XẾ (xe khác), giờ chồng → chặn.
    with pytest.raises(HTTPException) as e:
        dispatch_booking(db, b2, DispatchIn(assigned_vehicle_id=v2.id, assigned_driver_id=d1.id), actor)
    assert "Tài xế" in e.value.detail


def test_dispatch_allows_touching_slots(db):
    actor = _actor(db)
    v1, v2, d1, d2 = _fleet(db)
    b1 = create_booking(db, _payload(start_time="2026-09-01T08:00",
                                     end_time="2026-09-01T10:00"), actor, submit=True)
    dispatch_booking(db, b1, DispatchIn(assigned_vehicle_id=v1.id, assigned_driver_id=d1.id), actor)

    # Giáp ranh: 10:00 bắt đầu ngay khi chuyến trước kết thúc → KHÔNG trùng.
    b2 = create_booking(db, _payload(start_time="2026-09-01T10:00",
                                     end_time="2026-09-01T12:00"), actor, submit=True)
    out = dispatch_booking(db, b2, DispatchIn(assigned_vehicle_id=v1.id, assigned_driver_id=d1.id), actor)
    assert out.status == m.BK_DISPATCHED
