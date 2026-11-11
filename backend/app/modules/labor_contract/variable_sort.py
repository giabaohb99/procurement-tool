"""Biểu thức SẮP XẾP tại server cho bảng Danh sách biến mẫu HĐLĐ (duoc-CR-748).

Trước đây danh sách cố định `nguồn, thứ tự, mã` và tiêu đề cột không bấm được. Mỗi khóa dưới đây xếp theo
ĐÚNG chữ ô đang hiện (`variable_serializer` + `labor-contract-variable-columns.tsx`), trên CẢ TẬP:

- `code` ("Biến", hiện `{{ mã }}`) và `label` ("Tên hiển thị"): cột chữ thật.
- `group` ("Nhóm"): biến hệ thống thì nhóm khai ở `placeholder_catalog`, biến tùy chỉnh thì "Biến tùy chỉnh"
  - dựng bằng `CASE mã WHEN ... THEN nhóm` đúng như serializer chọn.
- `value_type` ("Kiểu"): biến hệ thống hiện "—" nên là ô trống (xuống CUỐI); biến tùy chỉnh theo mã số
  đã đúng thứ tự khai (Chữ → Chữ nhiều dòng → Số → Ngày → Tiền).
- `example`: cột chữ thật, ô trống hiện "—".
- `is_required` ("Bắt buộc"): chỉ biến tùy chỉnh mới hiện nhãn; không bắt buộc là 0, bắt buộc là 1 để bấm hai
  chiều đổi được thứ tự (nếu coi "—" là ô trống thì cả hai chiều trùng nhau, người dùng thấy bấm không ăn).
- `status` ("Trạng thái"): theo DÒNG ĐỜI 1 Đang dùng → 2 Ẩn (biến hệ thống bị ẩn khỏi khung chèn, vẫn dùng được)
  → 3 Ngừng (biến tùy chỉnh đã ngừng, không nhận vào mẫu mới) — đúng nhãn `renderVariableStatusBadge`.
- "Số mẫu dùng" (`template_count`) tính bằng Python quét mảng JSON của mọi mẫu nên KHÔNG có biểu thức SQL
  tương ứng: không cho xếp (khóa lạ rơi về thứ tự mặc định).
- Khóa phụ luôn là `id` giảm dần.
"""
from sqlalchemy import case

from app.core.labor_contract_codes import LaborContractVariableSource as Src
from app.core.sort_order import build_blank_last_order, with_stable_tiebreak

from .placeholder_catalog import PLACEHOLDERS
from .variable_model import LaborContractVariable as V
from .variable_serializer import CUSTOM_GROUP

_IS_SYSTEM = V.source == int(Src.SYSTEM)

#  Nhóm của biến hệ thống theo mã; mã không có trong danh mục (hoặc biến tùy chỉnh) -> "Biến tùy chỉnh".
_GROUP = case(*[(_IS_SYSTEM & (V.code == p.key), p.group) for p in PLACEHOLDERS], else_=CUSTOM_GROUP)

_STATUS_RANK = case(
    (_IS_SYSTEM & (V.is_hidden == True), 2),  # noqa: E712
    (_IS_SYSTEM, 1),
    (V.is_active == True, 1),  # noqa: E712
    else_=3,
)

#  (biểu thức, là cột chữ?) — cột chữ thì chuỗi rỗng cũng là ô trống.
_SPEC: dict = {
    "code": (V.code, True),
    "label": (V.label, True),
    "group": (_GROUP, True),
    "value_type": (case((_IS_SYSTEM, None), else_=V.value_type), False),
    "example": (V.example, True),
    "is_required": (case(((~_IS_SYSTEM) & (V.is_required == True), 1), else_=0), False),  # noqa: E712
    "status": (_STATUS_RANK, False),
}

SORTABLE_KEYS = frozenset(_SPEC)


def build_order_by(sort_by: str, sort_dir: str) -> list:
    """Danh sách ORDER BY (đã gồm khóa phụ `id`); khóa lạ / không chọn -> thứ tự mặc định cũ (không lỗi)."""
    spec = _SPEC.get((sort_by or "").strip())
    if spec is None:
        return [V.source, V.sort_order, V.code]
    expr, is_text = spec
    direction = "desc" if (sort_dir or "").strip().lower() == "desc" else "asc"
    return with_stable_tiebreak(build_blank_last_order(expr, direction, is_text), V.id)
