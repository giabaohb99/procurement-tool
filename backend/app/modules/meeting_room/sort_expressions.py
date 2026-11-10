"""Biểu thức SẮP XẾP tại server cho màn danh sách Phiếu đặt phòng họp (duoc-CR-744)."""
from sqlalchemy import func, select

from app.modules.employee.model import Employee

from .model import MeetingRoom, RoomBooking


def list_sort_allow() -> dict:
    """Map {khóa cột ở giao diện: biểu thức SQLAlchemy} cho `apply_sort_from_request`.

    Cột "Phòng" và "Người đặt" hiện TÊN (phòng, nhân sự) còn bảng chỉ lưu id, nên xếp theo tên
    chứ không theo id. Cột "Số người" hiện "—" khi bằng 0 (chưa khai), nên 0 được coi là ô trống và
    xuống cuối ở cả hai chiều. Các cột còn lại (Số phiếu, Trạng thái, Nội dung, Ngày họp) là cột thật.
    """
    room_name = (select(MeetingRoom.name).where(MeetingRoom.id == RoomBooking.room_id)
                 .limit(1).scalar_subquery())
    requester_name = (select(Employee.full_name)
                      .where(Employee.id == RoomBooking.requester_employee_id)
                      .limit(1).scalar_subquery())
    return {
        "room_name": room_name,
        "requester_name": requester_name,
        "attendee_count": func.nullif(RoomBooking.attendee_count, 0),
    }
