"""Biểu thức SẮP XẾP tại server cho danh sách Nhân sự (duoc-CR-744).

Trước đây bảng chỉ bấm được 3 cột (Mã NV, Họ tên, Ngày cập nhật); các cột còn lại trên màn không có
`sortable` nên tiêu đề không bấm được. Mỗi khóa dưới đây xếp theo ĐÚNG thứ ô đang hiện, trên CẢ TẬP
(đúng qua phân trang):

- Cột chữ: ô trống (hiện "—") luôn xuống CUỐI, cả chiều tăng lẫn giảm.
- Công ty / Phòng ban / Quản lý trực tiếp: xếp theo TÊN (giao diện hiện tên; `*_id` ra thứ tự số vô nghĩa).
- Hình thức / Cấp bậc: mã số đã đi theo thứ tự nghiệp vụ (Toàn thời gian → Thực tập; Nhân viên → Ban TGĐ),
  `0` = chưa khai nên đọc là ô trống.
- Tình trạng: theo thứ tự khai của bộ mã (Chính thức → Nghỉ việc), không theo chữ cái của mã.
- Khóa phụ luôn là `id` giảm dần để thứ tự ổn định giữa các trang.

⚠️ Danh sách trắng, KHÔNG tự động nhận mọi cột vật lý như `apply_sort_from_request`: bản cũ cho xếp theo cả
`date_of_birth`, `tax_code`, `id_number`, `bank_account_no`… tức người KHÔNG có `employee_sensitive.read` vẫn
đoán được thứ tự của dữ liệu họ không được xem. Lương bị chặn riêng ở controller (400, duoc-CR-693).
"""
from sqlalchemy import func, select
from sqlalchemy.orm import aliased

from app.core.code_rank_sql import build_code_rank_expression
from app.core.sort_order import build_blank_last_order, with_stable_tiebreak
from app.core.status_codes import EMPLOYEE_STATUS
from app.modules.company.model import Company
from app.modules.department.model import Department

from .model import Employee

_MANAGER = aliased(Employee)


def _name_of(id_column, name_column, fk_column):
    """Tên của bản ghi mà `fk_column` trỏ tới (`id_column` khớp `fk_column`); không có -> NULL (ô trống)."""
    return select(name_column).where(id_column == fk_column).limit(1).scalar_subquery()


#  (biểu thức, là cột chữ?) — cột chữ thì chuỗi rỗng cũng là ô trống.
_SPEC: dict = {
    "id": (Employee.id, False),
    "code": (Employee.code, True),
    "full_name": (Employee.full_name, True),
    "email": (Employee.email, True),
    "position": (Employee.position, True),
    "company_name": (_name_of(Company.id, Company.name, Employee.company_id), True),
    "department_name": (_name_of(Department.id, Department.name, Employee.department_id), True),
    "direct_manager_name": (_name_of(_MANAGER.id, _MANAGER.full_name, Employee.manager_id), True),
    #  Mã số 0 = chưa khai: đổi thành NULL để rơi vào nhóm ô trống.
    "employment_type_label": (func.nullif(Employee.employment_type, 0), False),
    "job_level_label": (func.nullif(Employee.job_level, 0), False),
    "status": (build_code_rank_expression(Employee.status, EMPLOYEE_STATUS), False),
    "hire_date": (Employee.hire_date, False),
    "created_at": (Employee.created_at, False),
    "updated_at": (Employee.updated_at, False),
}

SORTABLE_KEYS = frozenset(_SPEC)


def build_order_by(sort_by: str, sort_dir: str) -> list:
    """Danh sách mệnh đề ORDER BY (đã gồm khóa phụ `id`); rỗng nếu khóa lạ -> nơi gọi dùng thứ tự mặc định."""
    spec = _SPEC.get((sort_by or "").strip())
    if spec is None:
        return []
    expr, is_text = spec
    direction = "desc" if (sort_dir or "").strip().lower() == "desc" else "asc"
    return with_stable_tiebreak(build_blank_last_order(expr, direction, is_text), Employee.id)
