"""Biểu thức SẮP XẾP tại server cho danh mục Phòng ban (duoc-CR-744).

Bảng chỉ bấm được Mã, Tên phòng ban và Ngày cập nhật; Mã số hiệu, Loại đơn vị, Trưởng bộ phận, Trạng
thái không có `sortable`. Mỗi khóa dưới đây xếp theo ĐÚNG thứ ô đang hiện, trên CẢ TẬP:

- Cột chữ: ô trống (hiện "—") luôn xuống CUỐI, cả chiều tăng lẫn giảm.
- Trưởng bộ phận: xếp theo TÊN nhân sự (giao diện hiện tên), không theo `manager_id`.
- Loại đơn vị: mã 1 Phòng chức năng · 2 Đơn vị kinh doanh · 3 Ban dự án đã theo thứ tự hiển thị.
- Khóa phụ luôn là `id` giảm dần để thứ tự ổn định giữa các trang.
"""
from sqlalchemy import select
from sqlalchemy.orm import aliased

from app.core.sort_order import build_blank_last_order, with_stable_tiebreak
from app.modules.employee.model import Employee

from .model import Department

#  Bí danh: khi có ô tìm `q`, truy vấn ngoài đã nối sẵn bảng `Employee` để tìm theo tên trưởng bộ phận —
#  câu con dùng thẳng `Employee` sẽ tự tương quan nhầm với phép nối đó.
_MANAGER = aliased(Employee)

#  (biểu thức, là cột chữ?) — cột chữ thì chuỗi rỗng cũng là ô trống.
_SPEC: dict = {
    "id": (Department.id, False),
    "code": (Department.code, True),
    "issue_code": (Department.issue_code, True),
    "name": (Department.name, True),
    "kind": (Department.kind, False),
    "manager_name": (
        select(_MANAGER.full_name).where(_MANAGER.id == Department.manager_id)
        .limit(1).scalar_subquery(), True),
    "is_active": (Department.is_active, False),
    "created_at": (Department.created_at, False),
    "updated_at": (Department.updated_at, False),
}


def build_order_by(sort_by: str, sort_dir: str) -> list:
    """Danh sách mệnh đề ORDER BY (đã gồm khóa phụ `id`); rỗng nếu khóa lạ -> nơi gọi dùng đường cũ."""
    spec = _SPEC.get((sort_by or "").strip())
    if spec is None:
        return []
    expr, is_text = spec
    direction = "desc" if (sort_dir or "").strip().lower() == "desc" else "asc"
    return with_stable_tiebreak(build_blank_last_order(expr, direction, is_text), Department.id)
