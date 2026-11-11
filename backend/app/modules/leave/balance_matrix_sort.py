"""Biểu thức SẮP XẾP tại server cho thẻ "Theo nhân sự" của Quỹ phép năm (duoc-CR-748).

Thẻ phân trang theo NGƯỜI (truy vấn gốc là bảng nhân sự), mặc định xếp `mã NV, id`. Các khóa cho xếp, theo
ĐÚNG chữ ô đang hiện:

- `code` ("Mã NV") và `name` ("Họ tên"): cột chữ thật của hồ sơ.
- `department_name` ("Phòng ban"): TÊN phòng ban hiện tại của người đó, không theo `department_id`; người chưa
  gắn phòng (ô hiện "Chưa gắn") là ô trống, xuống CUỐI cả hai chiều.
- Các cột từng loại nghỉ, "Tổng còn lại" và "Chính sách" KHÔNG cho xếp: số ngày dùng được tính bằng Python
  (`available_days_map`, loại cộng dần trừ phần chưa tới tháng, thu hồi phép mang sang quá hạn) trên TRANG đang
  xem, nên không có biểu thức SQL khớp con số trên màn; xếp tạm theo cột thô sẽ ra thứ tự sai chữ đang hiện.
- Khóa lạ / không chọn -> thứ tự mặc định cũ; khóa phụ luôn là `id` (tăng dần ở thứ tự mặc định, giảm dần khi
  người dùng chọn cột, như mọi bảng khác).

Dùng chung cho bảng và tệp Excel (`/matrix/export`) để hai nơi cùng thứ tự.
"""
from sqlalchemy import select

from app.core.sort_order import build_blank_last_order, with_stable_tiebreak
from app.modules.department.model import Department
from app.modules.employee.model import Employee

#  (biểu thức, là cột chữ?) — cột chữ thì chuỗi rỗng cũng là ô trống.
_SPEC: dict = {
    "code": (Employee.code, True),
    "name": (Employee.full_name, True),
    "department_name": (select(Department.name).where(Department.id == Employee.department_id)
                        .correlate(Employee).limit(1).scalar_subquery(), True),
}

SORTABLE_KEYS = frozenset(_SPEC)


def build_order_by(sort_by: str, sort_dir: str) -> list:
    """Danh sách ORDER BY (đã gồm khóa phụ `id`); khóa lạ / không chọn -> `mã NV, id` như cũ (không lỗi)."""
    spec = _SPEC.get((sort_by or "").strip())
    if spec is None:
        return [Employee.code, Employee.id]
    expr, is_text = spec
    direction = "desc" if (sort_dir or "").strip().lower() == "desc" else "asc"
    return with_stable_tiebreak(build_blank_last_order(expr, direction, is_text), Employee.id)
