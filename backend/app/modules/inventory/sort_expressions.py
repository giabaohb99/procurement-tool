"""Biểu thức SẮP XẾP tại server cho màn Tồn kho (duoc-CR-744).

Trước đây `GET /api/inventory` không đọc `sort_by`/`sort_dir` (chỉ xếp cố định theo mã sản phẩm) nên tiêu
đề cột không bấm được; bản v1 xếp được chỉ vì ôm 500 dòng về trình duyệt. Nay mỗi cột xếp theo ĐÚNG thứ ô
đang hiện, trên CẢ TẬP (đúng qua phân trang):

- Công ty: xếp theo TÊN (giao diện hiện tên công ty; `company_id` ra thứ tự số vô nghĩa). Công ty không còn
  trong danh mục -> ô trống, xuống CUỐI.
- Cột chữ: ô trống (hiện "—") luôn xuống CUỐI, cả chiều tăng lẫn giảm.
- Cột số (Tồn hiện tại, Đơn giá BQ, Giá trị tồn): xếp theo số thật, tồn ÂM nằm trước tồn dương khi tăng dần.
- Khóa phụ luôn là `id` giảm dần để thứ tự ổn định giữa các trang.
"""
from sqlalchemy import select

from app.core.sort_order import build_blank_last_order, with_stable_tiebreak
from app.modules.company.model import Company

from .model import Inventory

#  (biểu thức, là cột chữ?) — cột chữ thì chuỗi rỗng cũng là ô trống.
_SPEC: dict = {
    "id": (Inventory.id, False),
    "company": (select(Company.name).where(Company.id == Inventory.company_id).limit(1).scalar_subquery(), True),
    "warehouse_code": (Inventory.warehouse_code, True),
    "product_code": (Inventory.product_code, True),
    "product_name": (Inventory.product_name, True),
    "unit": (Inventory.unit, True),
    "qty": (Inventory.qty, False),
    "avg_cost": (Inventory.avg_cost, False),
    "value": (Inventory.value, False),
}


def build_order_by(sort_by: str, sort_dir: str) -> list:
    """Danh sách mệnh đề ORDER BY (đã gồm khóa phụ `id`); rỗng nếu khóa lạ -> nơi gọi dùng thứ tự mặc định."""
    spec = _SPEC.get((sort_by or "").strip())
    if spec is None:
        return []
    expr, is_text = spec
    direction = "desc" if (sort_dir or "").strip().lower() == "desc" else "asc"
    return with_stable_tiebreak(build_blank_last_order(expr, direction, is_text), Inventory.id)
