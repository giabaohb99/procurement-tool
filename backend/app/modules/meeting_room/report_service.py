"""Báo cáo F1 "Sử dụng phòng họp" (duoc-CR-689, khóa 28) — `GET /api/room-usage/summary`.

Chỉ số cộng được: lượt đặt · giờ đã đặt · giờ làm việc · đặt rồi hủy/bị từ chối. Dẫn xuất: tỷ lệ lấp đầy
(giờ đặt ÷ giờ làm việc), tỷ lệ hủy, người dự bình quân, % sức chứa. Xem theo phòng (mặc định) · pháp nhân
sở hữu phòng · phòng ban đặt · khung giờ (giờ đã đặt chia theo từng khung phiếu phủ; lượt đặt + người dự tính ở khung BẮT ĐẦU) · thứ trong tuần. Hàng dữ liệu ở `report_data.py`.
"""
from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.report_aggregate import DerivedSpec, DimensionSpec, MetricSpec, ReportSpec, build_report
from app.core.report_period import Period
from app.modules.employee.profile_gaps_report_data import load_group_names

from .report_data import NO_GROUP, UsageRow, load_booking_rows, load_capacity_rows, load_rooms

WEEKDAYS = ("Thứ hai", "Thứ ba", "Thứ tư", "Thứ năm", "Thứ sáu", "Thứ bảy", "Chủ nhật")
METRICS = {"bookings": "Lượt đặt", "booked_hours": "Giờ đã đặt", "cancelled": "Đặt rồi hủy / bị từ chối"}


def _num(fn):
    return lambda r: fn(r) if r.kind == "booking" and r.lead else 0


def build_spec(rooms: dict, company_name: dict, department_name: dict) -> ReportSpec:
    def room_key(r: UsageRow):
        room = rooms.get(r.room_id)
        return [(r.room_id, f"{room.code} — {room.name}".strip(" —") if room else f"Phòng #{r.room_id}")]

    def dept_key(r: UsageRow):
        if r.kind != "booking":
            return [(NO_GROUP, "")]       # sức chứa không thuộc phòng ban nào — bị bỏ khỏi `groups`
        return [(r.department_id, department_name.get(r.department_id, ""))] if r.department_id else []

    def hour_key(r: UsageRow):
        return [(r.hour, f"{r.hour}h")] if r.hour >= 0 else []

    dims = {
        "room": DimensionSpec("room", "Phòng họp", key_of=room_key),
        "company": DimensionSpec("company", "Pháp nhân sở hữu phòng", empty_label="Dùng chung",
                                 key_of=lambda r: [(r.room_company_id, company_name.get(r.room_company_id, ""))]),
        "department": DimensionSpec("department", "Phòng ban đặt", key_of=dept_key),
        "hour": DimensionSpec("hour", "Khung giờ", key_of=hour_key),
        "weekday": DimensionSpec("weekday", "Thứ trong tuần",
                                 key_of=lambda r: [(r.day.weekday() + 1, WEEKDAYS[r.day.weekday()])]),
    }
    metrics = [
        MetricSpec("bookings", METRICS["bookings"], value_of=_num(lambda r: 1 if r.approved and r.lead else 0)),
        MetricSpec("booked_hours", METRICS["booked_hours"], kind="hours", value_of=lambda r: r.booked_hours),
        MetricSpec("available_hours", "Giờ làm việc", kind="hours", value_of=lambda r: r.available_hours),
        MetricSpec("cancelled", METRICS["cancelled"], good="down", value_of=_num(lambda r: 1 if r.cancelled else 0)),
        #  Chỉ số PHỤ làm tử/mẫu số cho các tỷ lệ dẫn xuất (không đứng riêng trên bảng).
        MetricSpec("requests", "Tổng phiếu đã chốt", helper=True, value_of=_num(lambda r: 1)),
        MetricSpec("attendees_sum", "Tổng người dự", helper=True, value_of=lambda r: r.attendees),
        MetricSpec("attendees_cap", "Người dự (phòng có sức chứa)", helper=True,
                   value_of=lambda r: r.attendees if r.room_capacity > 0 else 0),
        MetricSpec("capacity_sum", "Tổng sức chứa", helper=True,
                   value_of=lambda r: r.room_capacity if r.approved and r.lead else 0),
    ]
    derived = [
        DerivedSpec("occupancy", "Tỷ lệ lấp đầy", num="booked_hours", den="available_hours", good="up"),
        DerivedSpec("cancel_rate", "Tỷ lệ hủy / từ chối", num="cancelled", den="requests", good="down"),
        DerivedSpec("attendees_avg", "Người dự bình quân", num="attendees_sum", den="bookings",
                    kind="number", scale=1),
        DerivedSpec("capacity_use", "% sức chứa", num="attendees_cap", den="capacity_sum"),
    ]
    return ReportSpec(date_of=lambda r: r.day, metrics=metrics, derived=derived, dimensions=dims,
                      rank_by="bookings")


def load_rows(db: Session, booking_q, rooms: dict, d_from, d_to, company_id, department_id, by_hour: bool,
              with_capacity: bool = True) -> list[UsageRow]:
    """Hàng phiếu + (nếu cần) hàng sức chứa của [d_from, d_to]. Lọc phòng ban đặt thì bỏ sức chứa."""
    rows = load_booking_rows(db, booking_q, d_from, d_to, rooms, company_id, department_id, by_hour)
    if with_capacity and department_id is None:
        rows += load_capacity_rows(db, list(rooms.values()), d_from, d_to, by_hour)
    return rows


def build_summary(db: Session, booking_q, period: Period, group_by: str | None, company_id=None,
                  department_id=None) -> dict:
    group_by = group_by if group_by and group_by != "none" else "room"
    company_name, department_name = load_group_names(db, None, always=True)
    rooms = {r.id: r for r in load_rooms(db, company_id)}
    spec = build_spec(rooms, company_name, department_name)
    if group_by not in spec.dimensions:
        raise HTTPException(422, f"Xem theo không hợp lệ: {group_by}")

    def fetch(d_from, d_to):
        return load_rows(db, booking_q, rooms, d_from, d_to, company_id, department_id, group_by == "hour")

    data = build_report(fetch, spec, period, group_by=group_by)
    data["groups"] = [g for g in data.get("groups") or [] if g["key"] != NO_GROUP]
    data["meta"]["drilldown_metrics"] = list(METRICS)
    data["notes"] = [
        "Chỉ phiếu ĐÃ DUYỆT tính vào lượt đặt, giờ đã đặt, người dự; phiếu Đã hủy / Từ chối chỉ tính vào \"Đặt "
        "rồi hủy / bị từ chối\". Nháp, chờ duyệt, trả về chưa tính. Phiếu tính vào ngày BẮT ĐẦU của nó.",
        "Giờ làm việc = giờ công của lịch làm việc HỆ THỐNG mỗi ngày (trừ nghỉ trưa và ngày lễ của pháp nhân "
        "sở hữu phòng) cho mỗi phòng đang dùng. Tỷ lệ lấp đầy = giờ đã đặt ÷ giờ làm việc; họp ngoài giờ làm "
        "việc vẫn tính vào giờ đã đặt nên tỷ lệ có thể vượt 100%.",
        "Xem theo \"Phòng ban đặt\" không có giờ làm việc nên tỷ lệ lấp đầy để trống; lọc theo phòng ban cũng vậy.",
        "Bạn chỉ thấy các phiếu nằm trong phạm vi xem phiếu đặt phòng của mình, còn giờ làm việc tính cho mọi phòng."]
    return data
