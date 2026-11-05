"""Duyệt mọi đường API thật của app hay router (bao-CR-725).

FastAPI 0.137 trở đi (`Refactor internals to preserve APIRouter and APIRoute instances`) KHÔNG trải phẳng
`include_router` nữa: `app.routes` chỉ còn các `_IncludedRouter` bọc router gốc, đường thật nằm ở
`original_router.routes` (lồng nhiều tầng). Mã nào soi `app.routes` để tìm `APIRoute` (bảng khóa báo cáo
`usage_profile/report_route_keys.py`, các bài kiểm quét đường) đều đi qua đây để không phụ thuộc cách FastAPI xếp.

Giữ ĐÚNG thứ tự đăng ký như bản trải phẳng cũ (đường tĩnh khai trước đường động vẫn đứng trước). Cả hệ
`include_router` không truyền `prefix` / `dependencies` nên `path` và `dependencies` của đường gốc đã đầy đủ.
Mount (tệp tĩnh) không phải đường API nên bỏ qua, như `isinstance(r, APIRoute)` trước đây.
"""
from collections.abc import Iterator

from fastapi.routing import APIRoute


def iter_api_routes(target) -> Iterator[APIRoute]:
    """`target` là app hay router (có `.routes`). Trả lần lượt từng `APIRoute`, lồng bao nhiêu tầng cũng tới."""
    for route in getattr(target, "routes", ()):
        if isinstance(route, APIRoute):
            yield route
        elif getattr(route, "original_router", None) is not None:   # fastapi >= 0.137: _IncludedRouter
            yield from iter_api_routes(route.original_router)


def api_routes(target) -> list[APIRoute]:
    return list(iter_api_routes(target))
