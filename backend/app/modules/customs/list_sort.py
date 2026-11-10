"""Sắp xếp tại SERVER dùng chung cho các bảng của Tra cứu thị trường (duoc-CR-744).

Trước đây bấm tiêu đề cột ở màn Giá thị trường / Tra cứu hóa chất / Thuốc BVTV / Lịch sử nạp không có
gì xảy ra: giao diện không gửi `sort_by`, backend cũng không đọc. Nay mỗi bảng khai MỘT bản đồ
`khóa cột -> biểu thức SQL` đúng giá trị ô đang HIỂN THỊ, và hàm ở đây dựng mệnh đề ORDER BY theo hai luật
chung của mọi màn (`app/core/sort_order.py`):

  · Ô trống xuống CUỐI ở cả hai chiều. Cột chữ coi cả chuỗi rỗng / toàn khoảng trắng là trống (`text_col`);
    cột số chỉ coi NULL là trống (so số với '' trong MySQL ép '' thành 0 -> số 0 thật bị coi là trống).
  · Khóa phụ cuối cùng là `id` giảm dần để lật trang không lặp / sót dòng khi nhiều dòng bằng nhau.

Khóa lạ -> `None` (nơi gọi dùng thứ tự mặc định): không bao giờ ném lỗi, không nối chuỗi người dùng vào SQL.
Một khóa có thể gồm NHIỀU biểu thức (cột ghép: ngưỡng kg / hỗn hợp % / năm cấm) — chiều sắp áp cho tất cả.
"""
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from sqlalchemy.sql.elements import ColumnElement

from app.core.sort_order import build_blank_last_order, with_stable_tiebreak


@dataclass(frozen=True)
class SortKey:
    """Một biểu thức sắp xếp kèm cờ cột chữ (chuỗi rỗng = ô trống) hay cột số / ngày (chỉ NULL là ô trống)."""
    expr: ColumnElement
    is_text: bool
    #  False = khóa NHÓM: luôn xếp tăng dù cột đang xếp giảm (vd cột ghép "Ngưỡng / Mức cấm": nhóm cấm -> ngưỡng
    #  kg -> hỗn hợp % giữ nguyên thứ tự, chỉ GIÁ TRỊ trong nhóm đảo chiều — không trộn kg với % thành một dãy).
    follow_direction: bool = True


SortExpression = SortKey | ColumnElement | Sequence["SortKey | ColumnElement"]


def text_col(expr) -> SortKey:
    """Biểu thức CHỮ: chuỗi rỗng / toàn khoảng trắng cũng là ô trống."""
    return SortKey(expr, True)


def group_col(expr) -> SortKey:
    """Khóa NHÓM (số): luôn tăng dần, không đảo theo chiều sắp của cột."""
    return SortKey(expr, False, follow_direction=False)


def normalize_direction(sort_dir: str | None) -> str:
    return "desc" if str(sort_dir or "").strip().lower() == "desc" else "asc"


def build_order(sort_by: str | None, sort_dir: str | None, sort_map: Mapping[str, SortExpression],
                id_column: ColumnElement) -> list[ColumnElement] | None:
    """Mệnh đề ORDER BY cho cột `sort_by`; `None` nếu khóa không có trong bản đồ."""
    key = (sort_by or "").strip()
    expression = sort_map.get(key) if key else None
    if expression is None:
        return None
    items = list(expression) if isinstance(expression, (list, tuple)) else [expression]
    direction = normalize_direction(sort_dir)
    order: list[ColumnElement] = []
    for item in items:
        if isinstance(item, SortKey):
            order.extend(build_blank_last_order(item.expr, direction if item.follow_direction else "asc",
                                                item.is_text))
        else:
            order.extend(build_blank_last_order(item, direction, False))
    return with_stable_tiebreak(order, id_column)
