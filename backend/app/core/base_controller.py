from fastapi import Query, Request

from app.core.filter_operators import apply_operator_filters
from app.core.ref_filter import owns as _ref_owns


def pagination(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=5000),  # cho phép tải danh mục đầy đủ để đổ dropdown
):
    """Tham số phân trang dùng chung cho mọi danh sách."""
    return {
        "page": page,
        "page_size": page_size,
        "offset": (page - 1) * page_size,
        "limit": page_size,
    }


def apply_filters(query, model, request: Request, filterable: list[str]):
    """Filter động: đọc query params, chỉ áp dụng các trường nằm trong whitelist.

    Hai loại param cùng chạy qua đây:

    1. Param TRẦN `<field>=<val>` — hành vi cũ, giữ nguyên: text -> LIKE %val%, `is_*` -> bool,
       `id`/`*_id` -> so khớp chính xác. Luôn nối bằng AND.
    2. Param CÓ OPERATOR `<field>__<op>=<val>` (+ `conjunction=and|or`) — bộ lọc điều kiện,
       xem `app/core/filter_operators.py`.
    """
    for key, raw in request.query_params.items():
        val = raw.strip() if isinstance(raw, str) else raw   # cắt space thừa để LIKE khớp
        if _ref_owns(model, key):
            # CR-088: ô THAM CHIẾU (có đủ cặp id + tên) do `apply_ref_filters` lo, vì nó còn
            # phải kèm nhánh lùi cho dòng chưa điền lùi được id. So khớp chính xác ở đây nữa
            # là AND chồng lên, nhánh lùi coi như không tồn tại.
            continue
        if key in filterable and val not in (None, ""):
            col = getattr(model, key, None)
            if col is not None:
                if key == 'is_active' or key.startswith('is_'):
                    is_true = val.lower() in ('true', '1', 'yes')
                    query = query.filter(col == is_true)
                elif key == 'id' or key.endswith('_id'):
                    # Khóa tham chiếu -> so khớp CHÍNH XÁC (tránh LIKE %21% khớp 121, 210…)
                    if str(val).isdigit():
                        query = query.filter(col == int(val))
                else:
                    query = query.filter(col.like(f"%{val}%"))
        elif key.endswith("s") and key[:-1] in filterable and val not in (None, ""):
            # Handle comma-separated list like role_names -> roles_name IN (list)
            actual_key = key[:-1]
            if hasattr(model, actual_key) or hasattr(model, key):
                db_col_name = key if hasattr(model, key) else actual_key
                col = getattr(model, db_col_name)
                val_list = [v.strip() for v in val.split(",")]
                query = query.filter(col.in_(val_list))
    return apply_operator_filters(query, model, request, filterable)


def apply_sort(query, model, sort_by: str | None, sort_dir: str = "asc", default=None):
    """Sắp xếp phía server theo cột — CHỈ nhận cột thật của bảng (whitelist chống SQL injection).

    - sort_by: tên cột (khớp cột model). Không hợp lệ -> bỏ qua, dùng `default`.
    - sort_dir: 'asc' / 'desc' (mặc định asc).
    - default: mệnh đề order_by mặc định (vd Model.id.desc()); None -> id desc.
    """
    col = getattr(model, sort_by, None) if sort_by else None
    # chỉ cho phép cột vật lý trong bảng, tránh sort theo relationship/hybrid/method
    valid = col is not None and sort_by in model.__table__.columns.keys()
    if valid:
        is_desc = str(sort_dir).lower() == "desc"
        return query.order_by(col.desc() if is_desc else col.asc())
    if default is not None:
        return query.order_by(default)
    return query.order_by(model.id.desc())


def apply_sort_from_request(query, model, request: Request, default=None, allow: dict | None = None):
    """Như apply_sort nhưng đọc `sort_by`/`sort_dir` trực tiếp từ query params của request.

    - allow: map tùy chọn {key_FE: cột SQLAlchemy} cho cột KHÔNG trùng tên DB (vd cột join/computed).
      Nếu key nằm trong allow -> dùng cột đó; ngược lại thử cột thật của model.
    Tiện để gắn vào các controller tự viết mà không phải đổi chữ ký hàm.
    """
    sort_by = (request.query_params.get("sort_by") or "").strip()
    sort_dir = (request.query_params.get("sort_dir") or "asc").strip()
    if sort_by and allow and sort_by in allow:
        col = allow[sort_by]
        is_desc = str(sort_dir).lower() == "desc"
        return query.order_by(col.desc() if is_desc else col.asc())
    return apply_sort(query, model, sort_by, sort_dir, default=default)


def apply_range_filters(query, model, request: Request, fields: list[str]):
    """Lọc khoảng cho cột (ngày YYYY-MM-DD lưu dạng String, so sánh chuỗi vẫn đúng thứ tự).
    Mỗi field đọc 2 param: `<field>_from` (>=) và `<field>_to` (<=). Bỏ trống -> không lọc."""
    for field in fields:
        col = getattr(model, field, None)
        if col is None:
            continue
        v_from = (request.query_params.get(f"{field}_from") or "").strip()
        v_to = (request.query_params.get(f"{field}_to") or "").strip()
        if v_from:
            query = query.filter(col != "", col >= v_from)
        if v_to:
            query = query.filter(col != "", col <= v_to)
    return query


def apply_equals(query, model, request: Request, fields: list[str], cast=int):
    """Lọc bằng (=) cho cột số/khóa ngoại (vd company_id). Bỏ trống -> không lọc."""
    for field in fields:
        col = getattr(model, field, None)
        raw = (request.query_params.get(field) or "").strip()
        if col is not None and raw:
            try:
                query = query.filter(col == cast(raw))
            except (ValueError, TypeError):
                pass
    return query
