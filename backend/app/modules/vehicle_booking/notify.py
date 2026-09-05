"""Bắn CHUÔNG + EMAIL cho các bước của phiếu đặt xe (best-effort).

Ai NHẬN là luật nghiệp vụ nằm ở đây, KHÔNG cho sửa trên UI (tránh gửi nhầm). Nội
dung email lấy từ mẫu sửa được `tab_email_template` theo event; chuông in-app luôn
được tạo (không chịu công tắc email). Mọi lỗi thông báo được NUỐT — không để hỏng
việc chuyển trạng thái phiếu.

Người nhận theo event (MỖI EVENT = MỘT nhóm người nhận, để mỗi nhóm một mẫu email):
  dx_submitted            → người duyệt (TBP phòng của người tạo)
  dx_approved_dispatcher  → vai trò Điều phối viên   ("có chuyến cần điều phối")
  dx_approved_creator     → người tạo                ("phiếu đã được duyệt")
  dx_returned/rejected    → người tạo
  dx_dispatched           → tài xế được phân (nội bộ)
  dx_driver_accepted      → điều phối viên
  dx_driver_rejected      → điều phối viên
  dx_completed_dispatcher → điều phối viên
  dx_completed_creator    → người tạo
"""
from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from .model import Driver, Vehicle, VehicleBooking

logger = logging.getLogger(__name__)

#  Vai trò được coi là "điều phối viên" (nhận chuyến để điều phối / theo dõi).
_DISPATCHER_ROLE_CODES = ["booking_dispatcher", "booking_manager"]

#  Câu tóm tắt cho CHUÔNG (in-app) theo từng event.
_BELL_BODY = {
    "dx_submitted": "Có yêu cầu đặt xe mới cần bạn phê duyệt.",
    "dx_approved_dispatcher": "Yêu cầu đặt xe đã được duyệt — vui lòng điều phối xe và tài xế.",
    "dx_approved_creator": "Yêu cầu đặt xe của bạn đã được duyệt, đang chờ điều phối.",
    "dx_returned": "Yêu cầu đặt xe của bạn bị trả lại để chỉnh sửa.",
    "dx_rejected": "Yêu cầu đặt xe của bạn đã bị từ chối.",
    "dx_dispatched": "Bạn được phân một chuyến xe — vui lòng xác nhận.",
    "dx_driver_accepted": "Tài xế đã nhận chuyến.",
    "dx_driver_rejected": "Tài xế đã từ chối chuyến — cần điều phối lại.",
    "dx_completed_dispatcher": "Chuyến xe đã hoàn tất.",
    "dx_completed_creator": "Chuyến xe của bạn đã hoàn tất.",
}


def _creator(db: Session, booking: VehicleBooking):
    from app.modules.user.model import User
    if not booking.requester_id:
        return None
    return db.get(User, booking.requester_id)


def _dispatchers(db: Session):
    from app.modules.notification.service import get_users_by_role_codes
    return get_users_by_role_codes(db, _DISPATCHER_ROLE_CODES)


def _approvers(db: Session, booking: VehicleBooking):
    from app.modules.notification.service import (
        get_approvers_for_entity,
        get_dept_approver_recipients,
    )
    people = get_dept_approver_recipients(db, "", booking.department_id or 0)
    if not people:
        #  Không xác định được TBP phòng → lùi về người có quyền duyệt entity.
        people = get_approvers_for_entity(db, "vehicle_booking")
    return people


def _assigned_driver_user(db: Session, booking: VehicleBooking):
    from app.modules.user.model import User
    if not booking.assigned_driver_id:
        return None
    driver = db.get(Driver, booking.assigned_driver_id)
    if not driver or not driver.user_id:
        return None  # tài xế thuê ngoài không có tài khoản → không nhận kênh này
    return db.get(User, driver.user_id)


def _recipients_for(db: Session, event: str, booking: VehicleBooking) -> list:
    if event == "dx_submitted":
        return _approvers(db, booking)
    if event in ("dx_approved_dispatcher", "dx_driver_accepted", "dx_driver_rejected",
                 "dx_completed_dispatcher"):
        return _dispatchers(db)
    if event in ("dx_approved_creator", "dx_returned", "dx_rejected", "dx_completed_creator"):
        return [_creator(db, booking)]
    if event == "dx_dispatched":
        return [_assigned_driver_user(db, booking)]
    return []


def _context(db: Session, booking: VehicleBooking, reason: str = "") -> dict:
    from app.modules.notification.service import _abs_link

    driver_name = ""
    if booking.assigned_driver_id:
        driver = db.get(Driver, booking.assigned_driver_id)
        driver_name = driver.name if driver else ""
    vehicle_label = ""
    if booking.assigned_vehicle_id:
        vehicle = db.get(Vehicle, booking.assigned_vehicle_id)
        if vehicle:
            vehicle_label = vehicle.license_plate + (f" — {vehicle.model}" if vehicle.model else "")
    return {
        "code": booking.code or "",
        "purpose": booking.purpose or "",
        "creator_name": booking.requester or "",
        "driver_name": driver_name,
        "vehicle_label": vehicle_label,
        "start_time": booking.start_time or "",
        "end_location": booking.end_location or "",
        "reason": (reason or "").strip(),
        "link": _abs_link(f"/vehicle-booking/{booking.id}"),
    }


def notify(db: Session, event: str, booking: VehicleBooking, background_tasks=None,
           actor=None, reason: str = "") -> None:
    """Tạo chuông cho người liên quan + gửi email theo mẫu. Nuốt mọi lỗi."""
    try:
        recipients = [r for r in _recipients_for(db, event, booking) if r]
        if not recipients:
            return
        ctx = _context(db, booking, reason)

        from app.modules.notification.email_template_service import get_effective
        from app.modules.notification.model import Notification
        from app.modules.notification.service import render_template

        eff = get_effective(db, event)
        title = render_template(eff["subject"], ctx) if eff else (booking.code or "Đặt xe")
        body = _BELL_BODY.get(event, "")
        actor_id = int(getattr(actor, "id", 0) or 0)

        seen: set[int] = set()
        for r in recipients:
            if getattr(r, "id", None) in seen:
                continue
            seen.add(r.id)
            db.add(Notification(user_id=r.id, title=title, body=body,
                                link=ctx["link"], created_by=actor_id))
        db.commit()

        ctx["actor_id"] = actor_id
        from app.modules.notification.email_template_service import send_event_email
        send_event_email(db, event, background_tasks, recipients, ctx)
    except Exception:  # noqa: BLE001 — thông báo không được làm hỏng nghiệp vụ
        logger.exception("notify %s thất bại cho phiếu %s", event, getattr(booking, "id", None))


def notify_approved(db: Session, booking: VehicleBooking, background_tasks=None, actor=None) -> None:
    """Duyệt xong: gửi HAI mẫu khác nhau — Điều phối viên (có chuyến cần điều phối) + Người tạo."""
    notify(db, "dx_approved_dispatcher", booking, background_tasks, actor=actor)
    notify(db, "dx_approved_creator", booking, background_tasks, actor=actor)


def notify_completed(db: Session, booking: VehicleBooking, background_tasks=None, actor=None) -> None:
    """Hoàn tất: gửi HAI mẫu khác nhau — Điều phối viên + Người tạo."""
    notify(db, "dx_completed_dispatcher", booking, background_tasks, actor=actor)
    notify(db, "dx_completed_creator", booking, background_tasks, actor=actor)
