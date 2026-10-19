"""`{đường dẫn route: ReportKey}` của MỌI đường `/summary` đang gác khóa báo cáo (duoc-CR-641).

Dựng MỘT lần từ `app.routes` (dependency mang thuộc tính `report_key` do `require_report` gắn) — DRY với
gác quyền, thêm báo cáo mới không phải sửa bảng ở đây. Chỉ lấy `/summary` (không lấy `/summary/export`).
"""
import logging

log = logging.getLogger("app.usage_profile.report_route_keys")


_cache: dict[str, int] | None = None


def report_route_keys() -> dict[str, int]:
    """Kết quả KHÔNG rỗng được nhớ cả vòng đời worker; rỗng (nạp app lỗi / chưa có đường) thì lần sau thử lại."""
    global _cache
    if _cache:
        return _cache
    try:
        from fastapi.routing import APIRoute

        from app.main import app
    except Exception:  # noqa: BLE001 — worker không nạp được app thì chỉ mất chỉ số «báo cáo hay mở»
        log.warning("Không nạp được app để dựng bảng báo cáo — chỉ số «báo cáo hay mở» tạm rỗng, sẽ thử lại", exc_info=True)
        return {}
    out: dict[str, int] = {}
    for route in app.routes:
        if not isinstance(route, APIRoute) or not route.path.endswith("/summary"):
            continue
        for dep in route.dependencies:
            key = getattr(dep.dependency, "report_key", None)
            if key is not None:
                out[route.path] = int(key)
    if out:
        _cache = out
    else:
        log.warning("Bảng báo cáo rỗng — sẽ dựng lại ở lần gọi sau")
    return out
