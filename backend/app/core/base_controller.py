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
    for key, val in request.query_params.items():
        if key in filterable and val not in (None, ""):
            col = getattr(model, key, None)
            if col is not None:
                if key == 'is_active':
                    is_true = val.lower() in ('true', '1', 'yes')
                    query = query.filter(col == is_true)
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
