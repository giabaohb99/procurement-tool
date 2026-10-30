"""Danh sách "bấm số ra lượt đặt" của báo cáo F1 (duoc-CR-689): `GET /api/room-usage/summary/rows`."""
from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.report_drilldown import ROWS_LIMIT, Col, filter_group, rows_response
from app.core.report_period import Period
from app.modules.employee.model import Employee
from app.modules.employee.profile_gaps_report_data import load_group_names

from .constants import ROOM_BOOKING_STATUS_LABELS
from .report_data import load_rooms
from .report_service import METRICS, build_spec, load_rows

COLUMNS = [Col("code", "Mã phiếu"), Col("room", "Phòng"), Col("title", "Tiêu đề"), Col("requester", "Người đặt"),
           Col("department", "Phòng ban"), Col("start_at", "Bắt đầu", "text"), Col("end_at", "Kết thúc", "text"),
           Col("attendees", "Số người", "int"), Col("status", "Trạng thái")]


def build_rows(db: Session, booking_q, period: Period, metric: str, group_by: str | None, group_key: str | None,
               company_id=None, department_id=None) -> dict:
    company_name, department_name = load_group_names(db, None, always=True)
    rooms = {r.id: r for r in load_rooms(db, company_id)}
    dims = build_spec(rooms, company_name, department_name).dimensions
    if group_by and group_by not in dims:
        raise HTTPException(422, f"Xem theo không hợp lệ: {group_by}")
    rows = load_rows(db, booking_q, rooms, period.date_from, period.date_to, company_id, department_id,
                     group_by == "hour", with_capacity=False)
    want_cancel = metric == "cancelled"
    rows = [r for r in rows if (r.cancelled if want_cancel else r.approved and (r.lead or metric == "booked_hours"))]
    rows = filter_group(rows, dims.get(group_by) if group_by else None, group_key)
    rows = list({r.booking.id: r for r in rows}.values())       # xem theo giờ: một phiếu có thể nằm ở nhiều khung
    rows.sort(key=lambda r: (r.booking.start_at, r.booking.id))
    shown = rows[:ROWS_LIMIT]
    ids = {r.booking.requester_employee_id for r in shown}
    names = {e.id: e.full_name for e in db.query(Employee.id, Employee.full_name).filter(Employee.id.in_(ids)).all()} \
        if ids else {}
    out = []
    for r in shown:
        b, room = r.booking, rooms.get(r.room_id)
        out.append({"code": b.code, "room": f"{room.code} — {room.name}".strip(" —") if room else "",
                    "title": b.title, "requester": names.get(b.requester_employee_id, ""),
                    "department": department_name.get(b.department_id, ""),
                    "start_at": b.start_at.strftime("%d/%m/%Y %H:%M"), "end_at": b.end_at.strftime("%d/%m/%Y %H:%M"),
                    "attendees": b.attendee_count or 0,
                    "status": ROOM_BOOKING_STATUS_LABELS.get(b.status, ""),
                    "link": f"/hr/room-bookings/{b.id}"})
    resp = rows_response(metric, METRICS[metric], COLUMNS, out)
    resp["total"], resp["truncated"] = len(rows), len(rows) > ROWS_LIMIT
    return resp
