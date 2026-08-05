"""Conditional filter — dịch query param dạng `<field>__<op>=<value>` thành điều kiện SQLAlchemy.

Đây là phần backend cho bộ lọc điều kiện ở FE (`frontend/src/components/conditional-filter/`),
port theo cách sinh query của thư viện FilterCN nhưng bỏ lớp UI shadcn/Tailwind.

Cú pháp query param
-------------------
    ?status__eq=approved&total__gte=1000&created_at__between=2026-01-01,2026-03-31&conjunction=or

- `<field>` PHẢI nằm trong whitelist `filterable` của controller (chống lọc bừa cột nhạy cảm).
- `<op>` phải thuộc `OPERATORS`; sai op -> bỏ qua param đó, KHÔNG raise (tránh vỡ trang khi
  người dùng sửa tay URL).
- `conjunction=or` -> các điều kiện có operator nối bằng OR; mặc định là AND.

Khác biệt CÓ CHỦ Ý so với FilterCN gốc
--------------------------------------
FilterCN map operator `is` thành param KHÔNG có hậu tố (`status=abc`). Ở dự án này param trần
`status=abc` đã mang nghĩa LIKE `%abc%` (xem `apply_filters`) và hàng chục màn hình đang dựa vào
đó, nên operator "bằng" được đổi hậu tố thành `__eq` để hai loại param không giẫm chân nhau.
"""
from sqlalchemy import and_, or_
from sqlalchemy.sql.elements import ColumnElement

CONJUNCTION_PARAM = "conjunction"

# Hậu tố operator hợp lệ. Giữ đúng tên FE sinh ra (helpers/operators.ts).
OPERATORS = frozenset({
    "eq", "ne", "contains", "not_contains",
    "gt", "gte", "lt", "lte", "between",
    "in", "not_in", "isnull",
})

# Operator so sánh thứ tự — dùng chung một nhánh xử lý.
_COMPARE_OPS = {"gt": "__gt__", "gte": "__ge__", "lt": "__lt__", "lte": "__le__"}


def _coerce(col, val: str):
    """Ép kiểu chuỗi từ URL về kiểu cột. Cột ngày lưu dạng String (YYYY-MM-DD) nên so sánh
    chuỗi vẫn đúng thứ tự — chỉ cần ép số cho cột số. Ép lỗi -> trả None để bỏ qua điều kiện."""
    try:
        python_type = col.type.python_type
    except (NotImplementedError, AttributeError):
        return val
    if python_type is bool:
        return str(val).strip().lower() in ("true", "1", "yes")
    if python_type in (int, float):
        try:
            return python_type(str(val).strip())
        except (ValueError, TypeError):
            return None
    return val


def _is_text_col(col) -> bool:
    try:
        return col.type.python_type is str
    except (NotImplementedError, AttributeError):
        return False


def _blank(col):
    """Điều kiện "không có giá trị": NULL, và với cột text thì chuỗi rỗng cũng tính là trống."""
    return or_(col.is_(None), col == "") if _is_text_col(col) else col.is_(None)


def _split_list(raw: str) -> list[str]:
    return [v.strip() for v in str(raw).split(",") if v.strip()]


def build_condition(col, op: str, raw: str) -> ColumnElement | None:
    """Dựng 1 điều kiện SQLAlchemy từ (cột, operator, giá trị thô). Giá trị không hợp lệ -> None."""
    raw = raw.strip() if isinstance(raw, str) else raw

    if op == "isnull":
        return _blank(col) if str(raw).lower() in ("true", "1", "yes") else ~_blank(col)

    # Các operator còn lại đều cần giá trị
    if raw in (None, ""):
        return None

    if op in ("in", "not_in"):
        values = [v for v in (_coerce(col, v) for v in _split_list(raw)) if v is not None]
        if not values:
            return None
        # NOT IN: bản ghi trống cũng được coi là "không thuộc danh sách"
        return col.in_(values) if op == "in" else or_(col.is_(None), col.notin_(values))

    if op == "between":
        parts = str(raw).split(",")
        lo = _coerce(col, parts[0].strip()) if parts[0].strip() else None
        hi = _coerce(col, parts[1].strip()) if len(parts) > 1 and parts[1].strip() else None
        # Cột ngày lưu chuỗi rỗng phải bị loại: "" <= "2026-02-01" là đúng về mặt so sánh chuỗi
        if lo is not None and hi is not None:
            return and_(~_blank(col), col >= lo, col <= hi)
        if lo is not None:
            return and_(~_blank(col), col >= lo)
        if hi is not None:
            return and_(~_blank(col), col <= hi)
        return None

    if op in ("contains", "not_contains"):
        pattern = f"%{raw}%"
        # NOT CONTAINS: giữ lại cả bản ghi trống (người dùng mong "không chứa X" bao gồm ô rỗng)
        return col.like(pattern) if op == "contains" else or_(col.is_(None), ~col.like(pattern))

    value = _coerce(col, raw)
    if value is None:
        return None

    if op == "eq":
        return col == value
    if op == "ne":
        return or_(col.is_(None), col != value)
    if op in _COMPARE_OPS:
        return and_(~_blank(col), getattr(col, _COMPARE_OPS[op])(value))
    return None


def collect_conditions(model, request, filterable: list[str]) -> list[ColumnElement]:
    """Quét query params, trả về danh sách điều kiện từ các param dạng `<field>__<op>`."""
    conditions: list[ColumnElement] = []
    for key, raw in request.query_params.multi_items():
        if "__" not in key:
            continue
        field, _, op = key.rpartition("__")
        if op not in OPERATORS or field not in filterable:
            continue
        col = getattr(model, field, None)
        if col is None:
            continue
        cond = build_condition(col, op, raw)
        if cond is not None:
            conditions.append(cond)
    return conditions


def apply_operator_filters(query, model, request, filterable: list[str]):
    """Áp bộ lọc điều kiện lên query.

    Các điều kiện có operator nối với nhau bằng AND (mặc định) hoặc OR (`conjunction=or`).
    Cả cụm đó luôn AND với các filter param trần do `apply_filters` xử lý — filter trần thường
    đến từ URL điều hướng (vd /purchase-orders?pr_code=PYC-001) nên không được nới lỏng thành OR.
    """
    conditions = collect_conditions(model, request, filterable)
    if not conditions:
        return query
    use_or = (request.query_params.get(CONJUNCTION_PARAM) or "").strip().lower() == "or"
    return query.filter(or_(*conditions) if use_or and len(conditions) > 1 else and_(*conditions))
