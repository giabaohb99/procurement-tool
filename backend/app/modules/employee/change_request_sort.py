"""Biểu thức SẮP XẾP tại server cho màn Duyệt sửa hồ sơ (duoc-CR-748).

Trước đây danh sách cố định `id giảm dần`, tiêu đề cột không bấm được. Mỗi khóa dưới đây xếp theo ĐÚNG
thứ ô đang hiện, trên CẢ TẬP (đúng qua phân trang):

- `employee_code` / `employee_name`: mã và họ tên của HỒ SƠ mà đề nghị trỏ tới (truy vấn đã JOIN `Employee`).
- `status`: mã số 1 Chờ duyệt → 2 Đã duyệt → 3 Từ chối → 4 Đã rút lại đã là thứ tự dòng đời nên xếp thẳng.
- `created_at`: cột "Ngày gửi".
- Cột "Nhóm thay đổi" và "Số trường" tính từ JSON `changes` / `families` ở tầng giao diện, SQL không có
  giá trị tương ứng nên KHÔNG cho xếp (khóa lạ rơi về thứ tự mặc định `id` giảm dần).
- Ô trống luôn xuống CUỐI cả hai chiều; khóa phụ luôn là `id` giảm dần.
"""
from app.core.sort_order import build_blank_last_order, with_stable_tiebreak

from .change_request_model import EmployeeChangeRequest as Req
from .model import Employee

#  (biểu thức, là cột chữ?) — cột chữ thì chuỗi rỗng cũng là ô trống.
_SPEC: dict = {
    "employee_code": (Employee.code, True),
    "employee_name": (Employee.full_name, True),
    "status": (Req.status, False),
    "created_at": (Req.created_at, False),
}

SORTABLE_KEYS = frozenset(_SPEC)


def build_order_by(sort_by: str, sort_dir: str) -> list:
    """Danh sách ORDER BY (đã gồm khóa phụ `id`); khóa lạ -> thứ tự mặc định `id` giảm dần (không lỗi)."""
    spec = _SPEC.get((sort_by or "").strip())
    if spec is None:
        return [Req.id.desc()]
    expr, is_text = spec
    direction = "desc" if (sort_dir or "").strip().lower() == "desc" else "asc"
    return with_stable_tiebreak(build_blank_last_order(expr, direction, is_text), Req.id)
