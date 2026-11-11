"""Biểu thức SẮP XẾP tại server cho bảng Mẫu hợp đồng lao động (duoc-CR-748).

Trước đây danh sách cố định `pháp nhân, loại HĐ, tên` và tiêu đề cột không bấm được. Mỗi khóa dưới đây
xếp theo ĐÚNG thứ ô đang hiện, trên CẢ TẬP (đúng qua phân trang):

- `name`: tên mẫu.
- `company`: TÊN pháp nhân (ô hiện tên kèm mã), không theo `company_id` (thứ tự số vô nghĩa); mẫu mà
  pháp nhân đã bị xóa ra ô trống, xuống CUỐI.
- `contract_type`: mã số đã theo thứ tự nghiệp vụ (Thử việc → Xác định thời hạn → ... → Khác).
- `contract_count`: "Số HĐ đã dùng" = đếm hợp đồng CHƯA xóa mềm tham chiếu mẫu (đúng phép đếm của
  `template_serializer`), một truy vấn con tương quan nên vẫn chỉ một câu SQL cho cả trang.
- `is_active`: nhãn "Đang dùng" đứng trước "Ngừng" khi xếp tăng.
- `created_at`: ngày tạo. Cột "Tệp gốc" KHÔNG cho xếp (tên tệp kèm dung lượng, không có giá trị đơn nhất).
- Khóa lạ -> thứ tự mặc định cũ; khóa phụ luôn là `id` giảm dần.
"""
from sqlalchemy import case, func, select

from app.core.sort_order import build_blank_last_order, with_stable_tiebreak
from app.modules.company.model import Company

from .model import LaborContract
from .template_model import LaborContractTemplate as T

_CONTRACT_COUNT = (
    select(func.count(LaborContract.id))
    .where(LaborContract.template_id == T.id, LaborContract.is_deleted == False)  # noqa: E712
    .correlate(T).scalar_subquery()
)

#  (biểu thức, là cột chữ?) — cột chữ thì chuỗi rỗng cũng là ô trống.
_SPEC: dict = {
    "id": (T.id, False),
    "name": (T.name, True),
    "company": (select(Company.name).where(Company.id == T.company_id).correlate(T).limit(1).scalar_subquery(), True),
    "contract_type": (func.nullif(T.contract_type, 0), False),
    "contract_count": (_CONTRACT_COUNT, False),
    "is_active": (case((T.is_active == True, 1), else_=2), False),  # noqa: E712
    "created_at": (T.created_at, False),
}

SORTABLE_KEYS = frozenset(_SPEC)


def build_order_by(sort_by: str, sort_dir: str) -> list:
    """Danh sách ORDER BY (đã gồm khóa phụ `id`); khóa lạ / không chọn -> thứ tự mặc định cũ (không lỗi)."""
    spec = _SPEC.get((sort_by or "").strip())
    if spec is None:
        return [T.company_id, T.contract_type, T.name]
    expr, is_text = spec
    direction = "desc" if (sort_dir or "").strip().lower() == "desc" else "asc"
    return with_stable_tiebreak(build_blank_last_order(expr, direction, is_text), T.id)
