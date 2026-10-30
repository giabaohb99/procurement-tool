"""Nạp dữ liệu cho báo cáo F1 "Sử dụng phòng họp" (duoc-CR-689, khóa 28).

Hai loại hàng đưa cho khung báo cáo (cộng bằng Python, cùng một danh sách):
  - hàng `booking`: một phiếu đặt phòng trong kỳ (theo ngày BẮT ĐẦU). Phiếu ĐÃ DUYỆT góp lượt đặt + giờ
    đã đặt + người dự; phiếu Đã hủy / Từ chối chỉ góp vào "đặt rồi hủy". Nháp / chờ duyệt / trả về bỏ qua;
  - hàng `capacity`: giờ làm việc chuẩn của MỘT phòng trong MỘT ngày (hoặc một khung giờ khi xem theo giờ)
    theo lịch làm việc HỆ THỐNG, trừ ngày lễ của pháp nhân sở hữu phòng. Chỉ góp "Giờ làm việc".

Số truy vấn CỐ ĐỊNH: phòng (1) · phiếu (1) · lịch làm việc hệ thống (3) · ngày lễ (1).
Thời gian phiếu lưu giờ địa phương (không múi giờ) nên dùng thẳng, không cộng bù UTC.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from types import SimpleNamespace

from sqlalchemy.orm import Session

from app.modules.leave.holiday_calendar import date_range, holiday_names_many
from app.modules.work_schedule.day_rules import day_hours, worked_hours
from app.modules.work_schedule.resolver_many import load_day_plans_many

from .constants import RB_APPROVED, RB_CANCELLED, RB_REJECTED
from .model import MeetingRoom, RoomBooking

CAPACITY_KIND = "capacity"
#  Khóa nhóm riêng của hàng sức chứa ở chiều KHÔNG áp được cho nó (phòng ban đặt) — sẽ bị bỏ khỏi `groups`.
NO_GROUP = "__capacity__"


@dataclass(slots=True)
class UsageRow:
    kind: str                    # "booking" | "capacity"
    day: date
    room_id: int
    room_company_id: int
    department_id: int = -1      # -1 = hàng sức chứa (không có phòng ban đặt)
    hour: int = -1               # giờ bắt đầu (booking) hoặc khung giờ (capacity theo giờ); -1 = cả ngày
    approved: bool = False
    lead: bool = True            # hàng ĐẦU của phiếu; hàng chia giờ phụ (xem theo giờ) là False, không đếm lượt
    cancelled: bool = False
    booked_hours: float = 0.0
    available_hours: float = 0.0
    attendees: int = 0
    room_capacity: int = 0
    booking: object = None       # phiếu gốc, chỉ để dựng danh sách `/rows`


def _day_bounds(d_from: date, d_to: date) -> tuple[datetime, datetime]:
    return datetime.combine(d_from, time.min), datetime.combine(d_to + timedelta(days=1), time.min)


def load_rooms(db: Session, company_id: int | None) -> list[MeetingRoom]:
    """Mọi phòng (kể cả đã ngừng dùng — phiếu cũ vẫn trỏ vào); `company_id` lọc theo pháp nhân sở hữu phòng."""
    q = db.query(MeetingRoom)
    if company_id is not None:
        q = q.filter(MeetingRoom.company_id == company_id)
    return q.order_by(MeetingRoom.sort_order, MeetingRoom.id).all()


def hours_by_clock_hour(start: datetime, end: datetime) -> dict[int, float]:
    """{giờ trong ngày 0–23: số giờ phiếu phủ khung đó}. Phiếu 09:30–11:15 -> {9: .5, 10: 1, 11: .25}.
    Phiếu qua nửa đêm cộng dồn vào giờ cùng số của các ngày (tối đa 31 ngày, chặn phiếu hỏng)."""
    out: dict[int, float] = {}
    cur = start.replace(minute=0, second=0, microsecond=0)
    for _ in range(24 * 31):
        if cur >= end:
            break
        nxt = cur + timedelta(hours=1)
        part = (min(end, nxt) - max(start, cur)).total_seconds() / 3600.0
        if part > 0:
            out[cur.hour] = out.get(cur.hour, 0.0) + part
        cur = nxt
    return out


def load_booking_rows(db: Session, booking_q, d_from: date, d_to: date, rooms: dict[int, MeetingRoom],
                      company_id: int | None, department_id: int | None, by_hour: bool = False) -> list[UsageRow]:
    """Phiếu ĐÃ DUYỆT + Đã hủy / Từ chối có ngày bắt đầu trong kỳ. `company_id` lọc theo pháp nhân
    sở hữu PHÒNG, `department_id` theo phòng ban đặt — cả hai chỉ thu hẹp sau `apply_scope`.
    `by_hour`: phiếu đã duyệt CHIA giờ vào từng khung giờ nó phủ (hàng đầu giữ lượt đặt + người dự, hàng phụ
    chỉ góp giờ) để giờ đã đặt của mỗi khung không vượt giờ làm việc của khung đó."""
    lo, hi = _day_bounds(d_from, d_to)
    q = booking_q.filter(RoomBooking.is_deleted.is_(False), RoomBooking.start_at >= lo, RoomBooking.start_at < hi,
                         RoomBooking.status.in_((RB_APPROVED, RB_CANCELLED, RB_REJECTED)))
    if department_id is not None:
        q = q.filter(RoomBooking.department_id == department_id)
    if company_id is not None:
        q = q.filter(RoomBooking.room_id.in_(list(rooms) or [0]))
    out = []
    for b in q.all():
        room = rooms.get(b.room_id)
        approved = b.status == RB_APPROVED
        hours = max((b.end_at - b.start_at).total_seconds() / 3600.0, 0.0) if approved else 0.0
        args = (b.start_at.date(), b.room_id, int(getattr(room, "company_id", 0) or 0), int(b.department_id or 0))
        cap = int(getattr(room, "capacity", 0) or 0)
        if by_hour and approved:
            parts = sorted(hours_by_clock_hour(b.start_at, b.end_at).items(),
                           key=lambda kv: (kv[0] != b.start_at.hour, kv[0]))      # khung giờ bắt đầu đứng đầu
            for i, (h, part) in enumerate(parts):
                out.append(UsageRow("booking", *args, h, True, i == 0, False, part, 0.0,
                                    int(b.attendee_count or 0) if i == 0 else 0, cap if i == 0 else 0, b))
            if parts:
                continue
        out.append(UsageRow("booking", *args, b.start_at.hour, approved, True, not approved, hours, 0.0,
                            int(b.attendee_count or 0) if approved else 0, cap, b))
    return out


def load_capacity_rows(db: Session, rooms: list[MeetingRoom], d_from: date, d_to: date, by_hour: bool
                       ) -> list[UsageRow]:
    """Giờ làm việc chuẩn mỗi phòng × ngày (hoặc × giờ khi `by_hour`) theo lịch HỆ THỐNG."""
    rooms = [r for r in rooms if r.is_active]
    if not rooms:
        return []
    plans = load_day_plans_many(db, [SimpleNamespace(id=0, department_id=0, company_id=0)], d_from, d_to)
    holidays = holiday_names_many(db, {r.company_id or 0 for r in rooms}, d_from, d_to)
    out = []
    for day in date_range(d_from, d_to):
        spec, _sid = plans.at(0, day)
        whole = day_hours(spec)
        if whole <= 0:
            continue
        #  Cả khung giờ làm: mỗi giờ nguyên góp phần giờ công của nó (trừ nghỉ trưa); tổng = `whole`.
        hourly = [(h, worked_hours(spec, time(h), time(h + 1) if h < 23 else time(23, 59))) for h in range(24)] if by_hour else []
        for room in rooms:
            cid = int(room.company_id or 0)
            if day in holidays.get(cid, {}):
                continue
            if by_hour:
                out += [UsageRow(CAPACITY_KIND, day, room.id, cid, hour=h, available_hours=w)
                        for h, w in hourly if w > 0]
            else:
                out.append(UsageRow(CAPACITY_KIND, day, room.id, cid, available_hours=whole))
    return out
