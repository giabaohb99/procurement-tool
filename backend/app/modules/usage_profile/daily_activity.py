"""Nhịp làm việc + truy vấn API của MỘT người trong MỘT ngày (thuần) — duoc-CR-641, phase 02.

Phiên làm việc (`work_bursts`) = chuỗi lượt (request ∪ sự kiện giao diện) ngắt khi nghỉ > 30 phút; KHÔNG dùng phiên
đăng nhập vì nó sống 7 ngày. Lượt `/api/auth/*` (đăng nhập, gia hạn) không tính là «làm việc».
"""
from collections import Counter
from datetime import datetime, timedelta

from .daily_window import minute_of_day, referer_to_pattern, vn_hour
from .daily_workday import DayCalendar, is_offhours

BURST_GAP = timedelta(minutes=30)
PARALLEL_WINDOW = timedelta(minutes=10)
WRITE_METHODS = ("POST", "PUT", "PATCH", "DELETE")
#  DANH SÁCH LOẠI TRỪ DUY NHẤT: các đường ghi KHÔNG phải thao tác nghiệp vụ (đánh dấu đã đọc thông báo, lưu tùy chỉnh
#  cá nhân, chat trợ lý AI, thu sự kiện giao diện). Không tính vào api_writes và các chỉ số dẫn xuất (ghi ngoài giờ /
#  trên điện thoại / 422 mỗi 100 lượt ghi). `/api/auth/*` đã bị loại riêng bởi `is_auth_route` (đăng nhập, gia hạn, đăng xuất).
#  Khớp theo TIỀN TỐ của `route` (mẫu đường dẫn trong request_log).
NON_BUSINESS_WRITE_PREFIXES = ("/api/notifications", "/api/me/preferences", "/api/assistant", "/api/telemetry")
MOBILE = 2   # login_session.constants.DeviceType.MOBILE
MAX_FORBIDDEN_ROUTES = 5


def is_auth_route(route: str) -> bool:
    return (route or "").startswith("/api/auth/")


def is_non_business_write(method: str, route: str) -> bool:
    return method in WRITE_METHODS and (route or "").startswith(NON_BUSINESS_WRITE_PREFIXES)


def sliding_max(stamps: list[datetime], window: timedelta) -> int:
    """Số lớn nhất các mốc rơi vào một khung `window` trượt (stamps đã sắp xếp)."""
    best, left = 0, 0
    for right, ts in enumerate(stamps):
        while ts - stamps[left] > window:
            left += 1
        best = max(best, right - left + 1)
    return best


def max_distinct_in_window(items: list[tuple[datetime, str]], window: timedelta) -> int:
    """Số giá trị KHÁC NHAU lớn nhất trong một khung trượt; items = [(mốc, giá trị)] đã sắp xếp theo mốc."""
    best, left, counts = 0, 0, Counter()
    for right, (ts, val) in enumerate(items):
        counts[val] += 1
        while ts - items[left][0] > window:
            old = items[left][1]
            counts[old] -= 1
            if not counts[old]:
                del counts[old]
            left += 1
        best = max(best, len(counts))
    return best


def bursts(stamps: list[datetime]) -> tuple[int, int]:
    """`(số phiên làm việc, tổng phút hoạt động)`; mỗi phiên tính tối thiểu 1 phút."""
    if not stamps:
        return 0, 0
    n, minutes, start, prev = 1, 0, stamps[0], stamps[0]
    for ts in stamps[1:]:
        if ts - prev > BURST_GAP:
            minutes += max(1, round((prev - start).total_seconds() / 60))
            n, start = n + 1, ts
        prev = ts
    minutes += max(1, round((prev - start).total_seconds() / 60))
    return n, minutes


def activity_columns(requests: list, ui_stamps: list[datetime], sessions: dict, cal: DayCalendar,
                     report_map: dict[str, int]) -> dict:
    """requests: [(created_at, method, http_status, session_id, route, referer, ip)] của một người."""
    work = [r for r in requests if not is_auth_route(r[4])]
    stamps = sorted([r[0] for r in work] + list(ui_stamps))
    n_bursts, minutes = bursts(stamps)
    #  Lượt ghi không phải nghiệp vụ vẫn là hoạt động (stamps, hourly) nhưng KHÔNG tính vào api_writes lẫn api_reads.
    n_non_business = sum(1 for r in work if is_non_business_write(r[1], r[4]))
    writes = [r for r in work if r[1] in WRITE_METHODS and not is_non_business_write(r[1], r[4])]
    hourly = [0] * 24
    for r in work:
        hourly[vn_hour(r[0])] += 1
    forbidden = Counter(r[4] for r in requests if r[2] == 403)
    reports: Counter = Counter()
    screens: dict[str, list[int]] = {}
    for created, method, status, _sid, route, referer, _ip in work:
        if method == "GET" and status == 200 and route in report_map:
            reports[str(report_map[route])] += 1
        pattern = referer_to_pattern(referer)
        if pattern:
            screens.setdefault(pattern, [0, 0, 0])[2] += 1
    ip_items = sorted((r[0], r[6]) for r in work if r[6])
    return {
        "active": bool(stamps),
        "first_seen_min": minute_of_day(stamps[0]) if stamps else None,
        "last_action_min": minute_of_day(stamps[-1]) if stamps else None,
        "work_bursts": n_bursts,
        "active_minutes": min(minutes, 1440),
        "api_reads": len(work) - len(writes) - n_non_business,
        "api_writes": len(writes),
        "writes_offhours": sum(1 for r in writes if is_offhours(cal, r[0])),
        "writes_mobile": sum(1 for r in writes if sessions.get(r[3], (0, 0, 0))[2] == MOBILE),
        "http_403": sum(1 for r in requests if r[2] == 403),
        "http_422": sum(1 for r in requests if r[2] == 422 and not is_non_business_write(r[1], r[4])),
        "http_5xx": sum(1 for r in requests if r[2] >= 500),
        "max_parallel_ips": max_distinct_in_window(ip_items, PARALLEL_WINDOW),
        "hourly": hourly,
        "reports": dict(reports),
        "forbidden_routes": dict(forbidden.most_common(MAX_FORBIDDEN_ROUTES)),
        "_screens_api": screens,
    }
