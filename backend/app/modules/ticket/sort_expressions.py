"""Biểu thức SẮP XẾP tại server cho danh sách Phiếu hỗ trợ (duoc-CR-744).

Trước đây bảng không khai `sortable` nên không bấm được cột nào, dù `GET /api/tickets` đã đọc `sort_by`.
Mỗi khóa dưới đây xếp theo ĐÚNG thứ ô đang hiện, trên CẢ TẬP (đúng qua phân trang):

- Người gửi / Người xử lý: xếp theo TÊN HIỂN THỊ (họ tên nhân sự của tài khoản, thiếu thì email) — giống
  `controller._user_info`; cột lưu chỉ là id tài khoản. Chưa ai nhận = ô trống, xuống CUỐI cả hai chiều.
- Ưu tiên (Thấp → Trung bình → Cao → Khẩn) và Trạng thái (Mới → Đang xử lý → Đã trả lời → Đã đóng): xếp theo
  HẠNG nghiệp vụ, không theo chữ cái của mã tiếng Anh (`high` < `low` < `normal` sẽ sai thứ tự đọc).
- Khóa phụ luôn là `id` giảm dần để thứ tự ổn định giữa các trang.
"""
from sqlalchemy import func, select
from sqlalchemy.orm import aliased

from app.core.code_rank_sql import build_value_rank_expression
from app.core.sort_order import build_blank_last_order, with_stable_tiebreak
from app.modules.employee.model import Employee
from app.modules.user.model import User

from . import service
from .model import Ticket

_USER = aliased(User)
_EMPLOYEE = aliased(Employee)


def _user_display_name(user_id_column):
    """Họ tên nhân sự của tài khoản `user_id_column`, thiếu thì email; không có tài khoản (id 0) -> NULL."""
    return (
        select(func.coalesce(func.nullif(_EMPLOYEE.full_name, ""), func.nullif(_USER.email, "")))
        .select_from(_USER)
        .outerjoin(_EMPLOYEE, _EMPLOYEE.id == _USER.employee_id)
        .where(_USER.id == user_id_column)
        .limit(1)
        .scalar_subquery()
    )


#  (biểu thức, là cột chữ?) — cột chữ thì chuỗi rỗng cũng là ô trống.
_SPEC: dict = {
    "id": (Ticket.id, False),
    "subject": (Ticket.subject, True),
    "code": (Ticket.code, True),
    "department": (Ticket.department, True),
    "requester_name": (_user_display_name(Ticket.created_by), True),
    "assignee_name": (_user_display_name(Ticket.assignee_id), True),
    "priority": (build_value_rank_expression(Ticket.priority, service.PRIORITIES), False),
    "status": (build_value_rank_expression(Ticket.status, service.STATUSES), False),
    "created_at": (Ticket.created_at, False),
    "updated_at": (Ticket.updated_at, False),
    "closed_at": (Ticket.closed_at, False),
}


def build_order_by(sort_by: str, sort_dir: str) -> list:
    """Danh sách mệnh đề ORDER BY (đã gồm khóa phụ `id`); rỗng nếu khóa lạ -> nơi gọi dùng thứ tự mặc định."""
    spec = _SPEC.get((sort_by or "").strip())
    if spec is None:
        return []
    expr, is_text = spec
    direction = "desc" if (sort_dir or "").strip().lower() == "desc" else "asc"
    return with_stable_tiebreak(build_blank_last_order(expr, direction, is_text), Ticket.id)
