"""Dựng một dòng PHIẾU ĐẶT PHÒNG để trả ra giao diện.

Tách khỏi controller vì cả đường danh sách lẫn đường chi tiết đều dùng, và sau
này hộp việc duyệt cũng sẽ dùng — để hàm dump trong controller thì chỗ thứ hai
phải nhập chéo controller (vòng nhập, khó đọc).

Mọi hàm ở đây tra cứu **theo lô**: danh sách hai mươi dòng mà mỗi dòng tự đi hỏi
tên phòng và tên người đặt là bốn mươi lượt vào cơ sở dữ liệu cho một lần mở
trang.
"""
from sqlalchemy.orm import Session

from app.modules.employee.model import Employee

from .constants import ROOM_BOOKING_STATUS_LABELS
from .model import MeetingRoom, RoomBooking, RoomBookingAttendee
from .schema import RoomBookingResponse


def names_of(db: Session, employee_ids: set[int]) -> dict[int, str]:
    """Tên nhân sự theo id — một lượt truy vấn cho cả trang, không N+1."""
    ids = {i for i in employee_ids if i}
    if not ids:
        return {}
    rows = db.query(Employee.id, Employee.full_name).filter(Employee.id.in_(ids)).all()
    return {r[0]: r[1] for r in rows}


def room_map(db: Session, room_ids: set[int]) -> dict[int, MeetingRoom]:
    ids = {i for i in room_ids if i}
    if not ids:
        return {}
    rows = db.query(MeetingRoom).filter(MeetingRoom.id.in_(ids)).all()
    return {r.id: r for r in rows}


def dump_booking(obj: RoomBooking, rooms: dict[int, MeetingRoom],
                 names: dict[int, str]) -> dict:
    data = RoomBookingResponse.model_validate(obj).model_dump()
    room = rooms.get(obj.room_id)
    data["room_name"] = room.name if room else ""
    data["room_code"] = room.code if room else ""
    data["requester_name"] = names.get(obj.requester_employee_id, "")
    #  Số + nhãn, đúng quy ước R2: giao diện đọc số để so sánh, đọc nhãn để hiện.
    data["status_label"] = ROOM_BOOKING_STATUS_LABELS.get(obj.status, "")
    return data


def dump_attendees(db: Session, obj: RoomBooking) -> list[dict]:
    """Người được mời dự. Tra tên một lượt cho cả danh sách."""
    rows = (db.query(RoomBookingAttendee)
            .filter(RoomBookingAttendee.booking_id == obj.id)
            .order_by(RoomBookingAttendee.sort_order).all())
    names = names_of(db, {r.employee_id for r in rows})
    return [
        {"id": r.id, "employee_id": r.employee_id,
         "employee_name": names.get(r.employee_id, ""),
         "role": r.role, "sort_order": r.sort_order}
        for r in rows
    ]
