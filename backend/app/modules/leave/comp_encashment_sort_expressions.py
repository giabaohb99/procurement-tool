"""Biểu thức SẮP XẾP tại server cho hai danh sách Phiếu nghỉ bù và Phiếu thanh toán nghỉ phép (duoc-CR-744).

Trước đây bảng không khai `sortable` nên không bấm được cột nào. Mỗi khóa dưới đây xếp theo ĐÚNG thứ ô
đang hiện, trên CẢ TẬP (đúng qua phân trang):

- Người nghỉ / Người được thanh toán: xếp theo HỌ TÊN nhân sự (giao diện hiện tên kèm mã), không theo
  `employee_id` (ra thứ tự số vô nghĩa). Nhân sự đã xóa -> ô trống, xuống CUỐI cả hai chiều.
- Loại nghỉ: xếp theo TÊN loại nghỉ.
- Trạng thái phiếu: xếp theo hạng DÒNG ĐỜI Nháp → Chờ duyệt → Trả về chỉnh sửa → Đã duyệt → Từ chối → Đã hủy
  (duoc-CR-748; mã số thô 3 Đã duyệt, 4 Từ chối, 5 Trả về đặt "Trả về" sai chỗ). Lý do thanh toán: 1 Phép dư
  cuối năm → 2 Nghỉ việc.
- Trạng thái chi (đọc từ YCTT sinh ra khi duyệt): xếp theo HẠNG vòng đời Nháp → Chờ duyệt → Đã duyệt → Đã chi
  → Đã từ chối; phiếu chưa có YCTT là ô trống, xuống CUỐI.
- Khóa phụ luôn là `id` giảm dần để thứ tự ổn định giữa các trang.
"""
from sqlalchemy import func, select
from sqlalchemy.orm import aliased

from app.core.code_rank_sql import build_value_rank_expression
from app.core.int_code_rank_sql import build_int_rank_expression
from app.core.sort_order import build_blank_last_order, with_stable_tiebreak
from app.modules.employee.model import Employee
from app.modules.payment_request.model import PaymentRequest

from .catalog_model import LeaveType
from .comp_request_model import LeaveCompRequest
from .encashment_model import LeaveEncashment
from .sort_expressions import APPROVAL_LIFECYCLE_ORDER

#  Bí danh để câu con không tự "tương quan" nhầm với bảng nhân sự khác trong truy vấn ngoài (ô tìm `q`).
_EMPLOYEE = aliased(Employee)

#  Vòng đời YCTT theo thứ tự đọc: nhãn "Nháp" < "Chờ duyệt" < "Đã duyệt" < "Đã chi" < "Đã từ chối".
_PAYMENT_STATUS_ORDER = ("draft", "submitted", "approved", "paid", "cancelled")


def _employee_name(employee_id_column):
    """Họ tên nhân sự; không có hồ sơ -> NULL (ô trống)."""
    return select(_EMPLOYEE.full_name).where(_EMPLOYEE.id == employee_id_column).limit(1).scalar_subquery()


def _order_by(spec: dict, id_column, sort_by: str, sort_dir: str) -> list:
    entry = spec.get((sort_by or "").strip())
    if entry is None:
        return []
    expr, is_text = entry
    direction = "desc" if (sort_dir or "").strip().lower() == "desc" else "asc"
    return with_stable_tiebreak(build_blank_last_order(expr, direction, is_text), id_column)


_COMP_SPEC: dict = {
    "id": (LeaveCompRequest.id, False),
    "code": (LeaveCompRequest.code, True),
    "employee_name": (_employee_name(LeaveCompRequest.employee_id), True),
    "work_date": (LeaveCompRequest.work_date, False),
    "days": (LeaveCompRequest.days, False),
    "status": (build_int_rank_expression(LeaveCompRequest.status, APPROVAL_LIFECYCLE_ORDER), False),
    "reason": (LeaveCompRequest.reason, True),
    "created_at": (LeaveCompRequest.created_at, False),
}

_ENCASH_PAYMENT_STATUS = (
    select(PaymentRequest.status).where(PaymentRequest.id == LeaveEncashment.payment_request_id)
    .limit(1).scalar_subquery()
)

_ENCASH_SPEC: dict = {
    "id": (LeaveEncashment.id, False),
    "code": (LeaveEncashment.code, True),
    "employee_name": (_employee_name(LeaveEncashment.employee_id), True),
    "leave_type_name": (
        select(LeaveType.name).where(LeaveType.id == LeaveEncashment.leave_type_id).limit(1).scalar_subquery(), True),
    "balance_year": (LeaveEncashment.balance_year, False),
    "reason_kind": (LeaveEncashment.reason_kind, False),
    "days": (LeaveEncashment.days, False),
    "status": (build_int_rank_expression(LeaveEncashment.status, APPROVAL_LIFECYCLE_ORDER), False),
    #  Hạng 0 (chưa có YCTT / mã lạ ở đầu) đổi thành NULL để rơi vào nhóm ô trống.
    "payment_status": (
        func.nullif(build_value_rank_expression(_ENCASH_PAYMENT_STATUS, _PAYMENT_STATUS_ORDER), 0), False),
    "note": (LeaveEncashment.note, True),
    "created_at": (LeaveEncashment.created_at, False),
}


def build_comp_order_by(sort_by: str, sort_dir: str) -> list:
    """ORDER BY của Phiếu nghỉ bù (đã gồm khóa phụ `id`); rỗng nếu khóa lạ -> nơi gọi dùng đường cũ."""
    return _order_by(_COMP_SPEC, LeaveCompRequest.id, sort_by, sort_dir)


def build_encashment_order_by(sort_by: str, sort_dir: str) -> list:
    """ORDER BY của Phiếu thanh toán nghỉ phép (đã gồm khóa phụ `id`); rỗng nếu khóa lạ -> nơi gọi dùng đường cũ."""
    return _order_by(_ENCASH_SPEC, LeaveEncashment.id, sort_by, sort_dir)
