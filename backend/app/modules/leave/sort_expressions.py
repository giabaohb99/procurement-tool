"""Biểu thức SẮP XẾP tại server cho màn danh sách Đơn nghỉ phép (duoc-CR-744)."""
from sqlalchemy import select

from app.modules.employee.model import Employee

from .catalog_model import LeaveType
from .request_model import LeaveRequest


def list_sort_allow() -> dict:
    """Map {khóa cột ở giao diện: biểu thức SQLAlchemy} cho `apply_sort_from_request`.

    Cột "Người nghỉ" hiện TÊN nhân sự; `employee_id` thì ra thứ tự số vô nghĩa nên xếp theo tên.
    Cột "Loại nghỉ" hiện "tên loại chính +N" (N = số loại nghỉ còn lại của đơn nhiều loại), nên xếp theo
    TÊN loại chính - đúng phần đầu của chữ đang hiện; phần "+N" không tham gia, các đơn cùng loại chính
    rồi đến khóa phụ `id`. Loại chính là `leave_type_id` của đơn (loại chiếm nhiều ngày nhất).
    Các cột còn lại (Số đơn, Trạng thái, Từ ngày, Đến ngày, Số ngày, Lý do) là cột thật của bảng.
    """
    employee_name = (select(Employee.full_name).where(Employee.id == LeaveRequest.employee_id)
                     .limit(1).scalar_subquery())
    main_type_name = (select(LeaveType.name).where(LeaveType.id == LeaveRequest.leave_type_id)
                      .limit(1).scalar_subquery())
    return {"employee_name": employee_name, "leave_type_name": main_type_name}
