"""Biểu thức SẮP XẾP tại server cho danh mục Pháp nhân (duoc-CR-744).

Bảng chỉ bấm được Tên, Mã và Ngày cập nhật; các cột còn lại (Cấp, Mã số hiệu, Tên viết tắt, MST,
Người đại diện, Email hóa đơn, Trạng thái) không có `sortable`. Mỗi khóa dưới đây xếp theo ĐÚNG thứ ô
đang hiện, trên CẢ TẬP (đúng qua phân trang):

- Cột chữ: ô trống (hiện "—") luôn xuống CUỐI, cả chiều tăng lẫn giảm.
- Người đại diện: xếp theo TÊN nhân sự (giao diện hiện tên), không theo `legal_representative_id`.
- Cấp: mã 1 Tập đoàn · 2 Công ty thành viên · 3 Đơn vị trực thuộc đã theo thứ tự cấp bậc.
- Khóa phụ luôn là `id` giảm dần để thứ tự ổn định giữa các trang.
"""
from sqlalchemy import select
from sqlalchemy.orm import aliased

from app.core.sort_order import build_blank_last_order, with_stable_tiebreak
from app.modules.employee.model import Employee

from .model import Company

#  Bí danh để câu con KHÔNG tự "tương quan" nhầm với bảng nhân sự khác trong câu truy vấn ngoài.
_LEGAL_REP = aliased(Employee)

#  (biểu thức, là cột chữ?) — cột chữ thì chuỗi rỗng cũng là ô trống.
_SPEC: dict = {
    "id": (Company.id, False),
    "code": (Company.code, True),
    "name": (Company.name, True),
    "level": (Company.level, False),
    "issue_code": (Company.issue_code, True),
    "short_name": (Company.short_name, True),
    "tax_code": (Company.tax_code, True),
    "legal_rep_name": (
        select(_LEGAL_REP.full_name).where(_LEGAL_REP.id == Company.legal_representative_id)
        .limit(1).scalar_subquery(), True),
    "invoice_email": (Company.invoice_email, True),
    "is_active": (Company.is_active, False),
    "created_at": (Company.created_at, False),
    "updated_at": (Company.updated_at, False),
}


def build_order_by(sort_by: str, sort_dir: str) -> list:
    """Danh sách mệnh đề ORDER BY (đã gồm khóa phụ `id`); rỗng nếu khóa lạ -> nơi gọi dùng đường cũ."""
    spec = _SPEC.get((sort_by or "").strip())
    if spec is None:
        return []
    expr, is_text = spec
    direction = "desc" if (sort_dir or "").strip().lower() == "desc" else "asc"
    return with_stable_tiebreak(build_blank_last_order(expr, direction, is_text), Company.id)
