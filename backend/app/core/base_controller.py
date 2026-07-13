from fastapi import Query, Request


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

    Trường text -> LIKE %val%; có thể mở rộng so sánh khác sau.
    """
    for key, raw in request.query_params.items():
        val = raw.strip() if isinstance(raw, str) else raw   # cắt space thừa để LIKE khớp
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
    return query


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
