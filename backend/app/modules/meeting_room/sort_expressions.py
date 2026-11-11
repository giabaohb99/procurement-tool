"""Biểu thức SẮP XẾP tại server cho màn danh sách Phiếu đặt phòng họp (duoc-CR-744)."""
from sqlalchemy import func, select

from app.core.int_code_rank_sql import build_int_rank_expression
from app.modules.employee.model import Employee

from .constants import RB_APPROVED, RB_CANCELLED, RB_DRAFT, RB_PENDING, RB_REJECTED, RB_RETURNED
from .model import MeetingRoom, RoomBooking

#  Thứ tự DÒNG ĐỜI của phiếu đặt phòng (duoc-CR-748): Nháp -> Chờ duyệt -> Trả về chỉnh sửa -> Đã duyệt -> Từ chối
#  -> Đã hủy. Mã số thô (3 Đã duyệt, 4 Từ chối, 5 Trả về) đặt "Trả về" sau "Từ chối", sai dòng đời; cùng thứ tự với
#  đơn nghỉ phép (`leave/sort_expressions.py`) để hai màn bấm cột Trạng thái ra cùng một kiểu.
BOOKING_LIFECYCLE_ORDER = (RB_DRAFT, RB_PENDING, RB_RETURNED, RB_APPROVED, RB_REJECTED, RB_CANCELLED)


def list_sort_allow() -> dict:
    """Map {khóa cột ở giao diện: biểu thức SQLAlchemy} cho `apply_sort_from_request`.

    Cột "Phòng" và "Người đặt" hiện TÊN (phòng, nhân sự) còn bảng chỉ lưu id, nên xếp theo tên
    chứ không theo id. Cột "Số người" hiện "—" khi bằng 0 (chưa khai), nên 0 được coi là ô trống và
    xuống cuối ở cả hai chiều. Cột "Trạng thái" xếp theo hạng DÒNG ĐỜI (`BOOKING_LIFECYCLE_ORDER`), không theo mã số
    thô (duoc-CR-748). Các cột còn lại (Số phiếu, Nội dung, Ngày họp) là cột thật.
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
        "status": build_int_rank_expression(RoomBooking.status, BOOKING_LIFECYCLE_ORDER),
    }
