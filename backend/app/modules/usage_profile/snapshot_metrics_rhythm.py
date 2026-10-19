"""Chỉ số nhịp làm việc, API, an toàn tài khoản — tính từ `tab_usage_daily` của một người (duoc-CR-641, phase 04)."""
from app.core.usage_codes import UnmeasuredReason as Why

from .metric_partial import Partial
from .metric_stats import median, percentile, ratio

MIN_WRITES_FOR_RATE = 20


def _active_days(rows):
    return [r for r in rows if r.active]


def rhythm_metrics(rows: list) -> Partial:
    p = Partial()
    nets = [(r, max(0.0, r.work_capacity - r.leave_days)) for r in rows if r.is_workday]
    workdays_net = sum(n for _, n in nets)
    credit = sum(n for r, n in nets if r.active)
    proxied = sum(n for r, n in nets if not r.active and r.on_behalf_received > 0)
    active = _active_days(rows)
    p.put("workdays_net", workdays_net)
    p.put("active_workdays", sum(1 for r, _ in nets if r.active))
    p.put("active_ratio", min(1.0, credit / workdays_net) if workdays_net else None)
    p.put("proxied_days_ratio", min(1.0, proxied / workdays_net) if workdays_net else None)
    p.put("first_seen_p50_min", median([r.first_seen_min for r in active if r.first_seen_min is not None]))
    p.put("last_action_p50_min", median([r.last_action_min for r in active if r.last_action_min is not None]))
    p.put("bursts_per_day", ratio(sum(r.work_bursts for r in active), len(active)))
    p.put("active_minutes_p50", median([r.active_minutes for r in active]))
    p.put("logins", sum(r.logins for r in rows))

    writes = sum(r.api_writes for r in rows)
    approvals = sum(r.approvals for r in rows)
    p.put("offhours_write_share", ratio(sum(r.writes_offhours for r in rows), writes))
    p.put("mobile_write_share", ratio(sum(r.writes_mobile for r in rows), writes))
    p.put("mobile_approve_share", ratio(sum(r.approvals_mobile for r in rows), approvals))
    p.put("http_403", sum(r.http_403 for r in rows))
    p.put("http_422_per_100_writes",
          100.0 * sum(r.http_422 for r in rows) / writes if writes >= MIN_WRITES_FOR_RATE else None,
          Why.BELOW_THRESHOLD if writes else Why.NOT_APPLICABLE)
    p.put("new_ip_logins", sum(r.new_ip_logins for r in rows))
    p.put("new_device_logins", sum(r.new_device_logins for r in rows))
    p.put("max_parallel_ips", max((r.max_parallel_ips for r in rows), default=0))
    p.put("max_deletes_10min", max((r.max_deletes_10min for r in rows), default=0))
    p.put("active_after_resign", 1 if any(r.active_after_resign for r in rows) else 0)
    p.put("exports", sum(r.exports for r in rows))
    p.put("on_behalf_received", sum(r.on_behalf_received for r in rows))
    p.put("on_behalf_done", sum(r.on_behalf_done for r in rows))

    grid = [[0] * 24 for _ in range(7)]
    for r in rows:
        for h, n in enumerate(r.hourly or []):
            grid[r.day.weekday()][h] += n
    flat = sorted((n for row in grid for n in row), reverse=True)
    p.put("heatmap_top3_share", ratio(sum(flat[:3]), sum(flat)))
    p.lists["heatmap"] = grid
    p.counts.update({
        "active_days": len(active), "api_calls": sum(r.api_reads + r.api_writes for r in rows),
        "api_writes": writes, "decisions": approvals, "forbidden": sum(r.http_403 for r in rows),
    })
    return p


def export_spike(current_rows: list, old_rows: list, window_lo, last_week_start) -> tuple[float | None, int]:
    """`(1.0/0.0 hoặc None, số dòng lịch sử)` — tuần cuối của W có xuất > 3 × p95 tuần của chính người đó
    12 tuần trước, và ≥ 1.000 dòng. Không có lịch sử → None (không kết luận)."""
    if not old_rows:
        return None, 0
    weekly: dict[int, int] = {}
    for _uid, day, export_rows, _docs in old_rows:
        idx = (window_lo - day).days // 7   # 0 = tuần ngay trước cửa sổ
        weekly[idx] = weekly.get(idx, 0) + int(export_rows or 0)
    history = [weekly.get(i, 0) for i in range(12)]
    cur = sum(r.export_rows for r in current_rows if r.day >= last_week_start)
    p95 = percentile(history, 0.95) or 0
    return (1.0 if cur >= 1000 and cur > 3 * p95 else 0.0), len(old_rows)
