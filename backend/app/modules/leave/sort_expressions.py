"""Biểu thức SẮP XẾP tại server cho màn danh sách Đơn nghỉ phép (duoc-CR-744)."""
from sqlalchemy import select

from app.core.int_code_rank_sql import build_int_rank_expression
from app.modules.employee.model import Employee

from .catalog_model import LeaveType
from .constants import LR_APPROVED, LR_CANCELLED, LR_DRAFT, LR_PENDING, LR_REJECTED, LR_RETURNED
from .request_model import LeaveRequest

#  Thứ tự DÒNG ĐỜI của phiếu nội bộ chạy qua bộ máy duyệt (duoc-CR-748): Nháp -> Chờ duyệt -> Trả về chỉnh sửa
#  (đã vào luồng nhưng bị đưa lại cho người nộp) -> Đã duyệt -> Từ chối -> Đã hủy. Mã số khai theo thứ tự thêm
#  vào hệ thống (3 Đã duyệt, 4 Từ chối, 5 Trả về) nên xếp thẳng theo số là đặt "Trả về" sau "Từ chối", sai dòng
#  đời. Dùng chung cho đơn nghỉ phép, phiếu nghỉ bù và phiếu thanh toán phép (ba bộ mã cùng số).
APPROVAL_LIFECYCLE_ORDER = (LR_DRAFT, LR_PENDING, LR_RETURNED, LR_APPROVED, LR_REJECTED, LR_CANCELLED)


def list_sort_allow() -> dict:
    """Map {khóa cột ở giao diện: biểu thức SQLAlchemy} cho `apply_sort_from_request`.

    Cột "Người nghỉ" hiện TÊN nhân sự; `employee_id` thì ra thứ tự số vô nghĩa nên xếp theo tên.
    Cột "Loại nghỉ" hiện "tên loại chính +N" (N = số loại nghỉ còn lại của đơn nhiều loại), nên xếp theo
    TÊN loại chính - đúng phần đầu của chữ đang hiện; phần "+N" không tham gia, các đơn cùng loại chính
    rồi đến khóa phụ `id`. Loại chính là `leave_type_id` của đơn (loại chiếm nhiều ngày nhất).
    Cột "Trạng thái" xếp theo hạng DÒNG ĐỜI (`APPROVAL_LIFECYCLE_ORDER`), không theo mã số thô (duoc-CR-748).
    Các cột còn lại (Số đơn, Từ ngày, Đến ngày, Số ngày, Lý do) là cột thật của bảng.
    """
    employee_name = (select(Employee.full_name).where(Employee.id == LeaveRequest.employee_id)
                     .limit(1).scalar_subquery())
    main_type_name = (select(LeaveType.name).where(LeaveType.id == LeaveRequest.leave_type_id)
                      .limit(1).scalar_subquery())
    return {
        "employee_name": employee_name,
        "leave_type_name": main_type_name,
        "status": build_int_rank_expression(LeaveRequest.status, APPROVAL_LIFECYCLE_ORDER),
    }
