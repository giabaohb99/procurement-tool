"""Danh mục KHÓA chỉ số (duoc-CR-641) — nguồn duy nhất: snapshot, API và pha 4 (AI) cùng đọc khóa ở đây.

⚠️ Khóa là ĐỊNH DANH CỐ ĐỊNH: đổi tên là gãy snapshot cũ + pha 4. Thêm khóa mới thì thêm dòng; không tái dùng tên.
Bảng định nghĩa/nguồn/công thức từng chỉ số: `plans/261019-1450-tracking-ho-so-lam-viec-cr641/metric-definitions.md`.

Mỗi dòng: khóa → (đơn vị, mục §3, pha, hướng). Pha: 1 = gom từ bảng có sẵn · 2 = cần sự kiện giao diện / `read_at` · 3 = cần số dùng AI (`tab_ai_usage_daily`).
Hướng: +1 càng cao càng tốt · -1 càng thấp càng tốt · 0 trung tính (chỉ mô tả).
Đơn vị: ratio (0..1) · count · min · h · ms · per100 · minute_of_day · flag.
"""
from typing import NamedTuple


class MetricMeta(NamedTuple):
    unit: str
    section: str
    phase: int
    direction: int


METRIC_CATALOG: dict[str, MetricMeta] = {
    #  3.1 Nhịp làm việc
    "first_seen_p50_min": MetricMeta("minute_of_day", "3.1", 1, 0),
    "last_action_p50_min": MetricMeta("minute_of_day", "3.1", 1, 0),
    "workdays_net": MetricMeta("count", "3.1", 1, 0),
    "active_workdays": MetricMeta("count", "3.1", 1, 1),
    "active_ratio": MetricMeta("ratio", "3.1", 1, 1),
    "proxied_days_ratio": MetricMeta("ratio", "3.1", 1, 0),
    "bursts_per_day": MetricMeta("count", "3.1", 1, 0),
    "active_minutes_p50": MetricMeta("min", "3.1", 1, 0),
    "logins": MetricMeta("count", "3.1", 1, 0),
    "offhours_write_share": MetricMeta("ratio", "3.1", 1, -1),
    "mobile_write_share": MetricMeta("ratio", "3.1", 1, 0),
    "mobile_approve_share": MetricMeta("ratio", "3.1", 1, 0),
    "heatmap_top3_share": MetricMeta("ratio", "3.1", 1, 0),
    #  3.2 Trang truy cập
    "page_views": MetricMeta("count", "3.2", 2, 0),
    "screen_dwell_avg": MetricMeta("ms", "3.2", 2, 0),
    "distinct_screens_30d": MetricMeta("count", "3.2", 2, 1),
    "loop_share": MetricMeta("ratio", "3.2", 2, -1),
    "reports_opened": MetricMeta("count", "3.2", 1, 0),
    "http_403": MetricMeta("count", "3.2", 1, -1),
    #  3.3 Cách làm task
    "docs_created": MetricMeta("count", "3.3", 1, 0),
    "docs_submitted": MetricMeta("count", "3.3", 1, 0),
    "form_submit_p50_ms": MetricMeta("ms", "3.3", 2, -1),
    "drafts_before_submit_p50": MetricMeta("count", "3.3", 1, 0),
    "edits_after_submit_share": MetricMeta("ratio", "3.3", 1, -1),
    "returned_rate": MetricMeta("ratio", "3.3", 1, -1),
    "form_abandon_rate": MetricMeta("ratio", "3.3", 2, -1),
    "approval_wait_p50_h": MetricMeta("h", "3.3", 1, -1),
    "approval_wait_p90_h": MetricMeta("h", "3.3", 1, -1),
    "pending_now": MetricMeta("count", "3.3", 1, -1),
    "batch_approval_share": MetricMeta("ratio", "3.3", 1, 0),
    "month_end_create_share": MetricMeta("ratio", "3.3", 1, 0),
    "on_behalf_received": MetricMeta("count", "3.3", 1, 0),
    "on_behalf_done": MetricMeta("count", "3.3", 1, 0),
    "proxy_share": MetricMeta("ratio", "3.3", 1, 0),
    "imports": MetricMeta("count", "3.3", 1, 0),
    "import_error_rate": MetricMeta("ratio", "3.3", 1, -1),
    "work_on_time_rate": MetricMeta("ratio", "3.3", 1, 1),
    "work_overdue_open": MetricMeta("count", "3.3", 1, -1),
    #  3.4 Phản hồi và phối hợp
    "notif_read_rate": MetricMeta("ratio", "3.4", 1, 1),
    "notif_read_p50_min": MetricMeta("min", "3.4", 2, -1),
    "mention_reply_p50_h": MetricMeta("h", "3.4", 1, -1),
    "comments": MetricMeta("count", "3.4", 1, 0),
    "assistant_questions": MetricMeta("count", "3.4", 1, 0),
    "assistant_changes": MetricMeta("count", "3.4", 1, 0),
    #  3.5 Mức thành thạo
    "saved_prefs": MetricMeta("count", "3.5", 1, 1),
    "http_422_per_100_writes": MetricMeta("per100", "3.5", 1, -1),
    "search_empty_rate": MetricMeta("ratio", "3.5", 2, -1),
    "help_views": MetricMeta("count", "3.5", 2, 0),
    "tickets": MetricMeta("count", "3.5", 1, 0),
    "exports": MetricMeta("count", "3.5", 1, 0),
    "export_per_list_view": MetricMeta("ratio", "3.5", 2, 0),
    "export_entity_weeks_max": MetricMeta("count", "3.5", 1, 0),
    #  3.6 An toàn tài khoản
    "new_ip_logins": MetricMeta("count", "3.6", 1, -1),
    "new_device_logins": MetricMeta("count", "3.6", 1, -1),
    "max_parallel_ips": MetricMeta("count", "3.6", 1, -1),
    "export_rows_spike": MetricMeta("flag", "3.6", 1, -1),
    "max_deletes_10min": MetricMeta("count", "3.6", 1, -1),
    "active_after_resign": MetricMeta("flag", "3.6", 1, -1),
    #  3.8 Dùng AI (duoc-CR-655) — nguồn `tab_ai_usage_daily` (ai-CR-230) + `tab_audit_log.ai_channel`; chưa thu = NOT_COLLECTED.
    #  Kênh/ứng dụng/nhóm công cụ chính là MÃ nên nằm ở `lists` của snapshot (ai_channels, ai_clients, ai_tool_groups).
    "ai_uses": MetricMeta("count", "3.8", 3, 0),
    "ai_active_days": MetricMeta("count", "3.8", 3, 0),
    "ai_mcp_share": MetricMeta("ratio", "3.8", 3, 0),
    "ai_tool_groups_used": MetricMeta("count", "3.8", 3, 0),
    "ai_denied": MetricMeta("count", "3.8", 3, -1),
    "ai_drafts_confirmed": MetricMeta("count", "3.8", 3, 0),
    "ai_docs_drafted": MetricMeta("count", "3.8", 3, 0),
    "ai_docs_share": MetricMeta("ratio", "3.8", 3, 0),
}

#  Chỉ số HOÃN / BỎ (ghi để API và tài liệu không hứa thứ chưa có) — xem metric-definitions.md.
DEFERRED_METRICS = {
    "approval_wait_ycmh_dmh": "Duyệt YCMH/ĐMH ngoài bộ máy duyệt: không có mốc \"tới lượt\" tin được",
    "comments_own_vs_other": "Tách bình luận phiếu mình/người khác: cần tra chủ phiếu từng entity",
    "http_422_per_field": "Lỗi 422 theo trường: phải bóc response_body.details",
    "unused_permissions_90d": "Quyền 90 ngày không dùng: lượt đọc (GET) không ánh xạ được route → entity",
    "assistant_topics": "Chủ đề hay hỏi trợ lý AI: văn bản tự do, trái nguyên tắc §7.4",
}
