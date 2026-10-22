"""Cấu hình cổng MCP do quản trị chỉnh trên màn G7 (ai-CR-216, doc/erp/21 §6.2 G7 + §5.2).

- BẬT / TẮT NHÓM tool ERP qua MCP. Mỗi tool thuộc ĐÚNG MỘT nhóm (bài kiểm canh: tool mới quên xếp nhóm là đỏ). Mặc
  định theo Q4 (doc 21 §9): «đợt đầu chỉ nhóm tra cứu của chính mình + nghỉ phép + danh bạ; nhóm công nợ / tài chính
  tắt» — cộng thêm báo cáo gom sẵn + Kho skill (Agent 1 chốt 17/10). Nhóm khác TẮT sẵn, quản trị bật trên màn.
- Trần tần suất, ngân sách dòng, số ngày giữ nhật ký, câu dặn thêm cho AI (nối sau INSTRUCTIONS).

Lưu MỘT dòng JSON ở `tab_setting` của ERP (khóa `SETTING_KEY`) qua `erp.setting_raw_get/put` — chạy được cả chế độ nhúng
lẫn tách dịch vụ (cổng B). Đọc có bộ đệm `CACHE_SEC` giây trong tiến trình; ghi xong xóa bộ đệm. Trường chưa lưu lấy theo
biến môi trường `AGENT_MCP_*` (mặc định cũ), nên bỏ trống cấu hình = hành vi như trước, trừ phần nhóm tool.
"""
from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass

from app.core.config import settings

log = logging.getLogger("app.agent_hub.mcp_settings")

SETTING_KEY = "agent_mcp_settings"
CACHE_SEC = 60
EXTRA_MAX_LEN = 1000
#  Tool riêng của cổng — luôn mở (báo lỗi ai cũng được; xác nhận nháp tự gác bằng mức khóa + nhóm của tool draft_*).
ALWAYS_ON = frozenset({"report_issue", "confirm_draft"})


@dataclass(frozen=True)
class ToolGroup:
    key: str
    label: str
    default_on: bool
    tools: frozenset[str]


GROUPS: tuple[ToolGroup, ...] = (
    ToolGroup("mine", "Tra cứu phiếu và việc của chính mình", True, frozenset({
        "my_approval_tasks", "my_requests_status", "my_procurement_requests", "my_documents", "my_tickets",
        "my_work_tasks", "pending_procurement_approvals", "search_chat_history"})),
    ToolGroup("leave", "Nghỉ phép", True, frozenset({"my_leave_summary", "draft_leave_request"})),
    ToolGroup("directory", "Danh bạ, thuật ngữ, hướng dẫn sử dụng", True, frozenset({
        "employee_lookup", "glossary_lookup", "search_docs"})),
    ToolGroup("reports", "Báo cáo gom sẵn và bảng số tổng hợp", True, frozenset({"report_summary", "dataset_query"})),
    ToolGroup("skills", "Kho skill AI (cẩm nang công ty)", True, frozenset({"list_skills", "read_skill", "read_skill_file"})),
    ToolGroup("purchase", "Thu mua: chứng từ, sản phẩm, nhà cung cấp, hợp đồng", False, frozenset({
        "procurement_doc_read", "recent_purchase_orders", "recent_purchases", "product_search", "product_best_price",
        "product_purchase_history", "supplier_search", "suppliers_for_product", "supplier_contracts", "supplier_scorecard",
        "contract_count_by_status", "contract_list_by_expiry", "analytics_query", "purchase_report",
        "top_suppliers_by_purchase", "market_price_search", "erp_read", "draft_purchase_request", "draft_survey_request"})),
    ToolGroup("finance", "Công nợ và thanh toán", False, frozenset({
        "payable_lookup", "payment_request_read", "draft_payment_request"})),
    ToolGroup("document", "Văn thư", False, frozenset({"document_read", "document_search", "approval_flow_lookup"})),
    ToolGroup("work", "Công việc và dự án (soạn việc, kế hoạch, năng lực đội)", False, frozenset({
        "draft_work_task", "draft_work_plan", "team_capacity", "task_type_stats"})),
    ToolGroup("customs", "Tra cứu thị trường (tờ khai hải quan)", False, frozenset({
        "customs_price_stats", "customs_buy_timing", "customs_market", "customs_legal_check"})),
    ToolGroup("google", "Lịch và Drive Google cá nhân", False, frozenset({
        "my_calendar_events", "create_calendar_event", "update_calendar_event", "delete_calendar_event", "drive_read",
        "drive_search"})),
    ToolGroup("personal", "Sổ nhớ, ghi chú, nhóm chat, biên bản họp", False, frozenset({
        "add_personal_item", "list_personal_items", "mark_personal_item", "save_note", "search_notes", "remember_fact",
        "forget_fact", "manage_briefs", "list_my_groups", "read_group_messages", "read_group_file", "list_my_meetings",
        "latest_meeting_report", "rewrite_meeting_minutes", "save_meeting_template"})),
    ToolGroup("ticket", "Tạo phiếu hỗ trợ", False, frozenset({"ticket_create"})),
    ToolGroup("research", "Nghiên cứu sâu nhiều nguồn (tốn phí công ty)", False, frozenset({"deep_research"})),
    ToolGroup("export", "Xuất tệp Excel / Word mẫu công ty", False, frozenset({"export_report_file", "export_excel_file"})),
    #  bao-CR-634 (K9): quản trị bằng lời — bật sẵn vì đã gác kép (khóa được ghi + quyền ai_skill / ai_mcp_key_admin).
    ToolGroup("admin", "Quản trị Kho skill và khóa AI bằng lời (khóa được ghi, đúng quyền)", True, frozenset({
        "draft_skill", "draft_skill_publish", "draft_skill_access", "draft_key_issue", "draft_key_revoke"})),
)
GROUP_OF = {tool: g for g in GROUPS for tool in g.tools}
#  Bộ dữ liệu của dataset_query thuộc nhóm Công nợ — nhóm đó tắt thì hai bộ này cũng tắt dù nhóm Báo cáo đang bật.
FINANCE_DATASETS = frozenset({"payable", "payment_request"})

#  (khóa, nhãn, biến môi trường mặc định, nhỏ nhất, lớn nhất) — 0 ở trần tần suất / ngân sách = không chặn.
LIMITS = (
    ("rate_per_key", "Lượt / phút / khóa", "AGENT_MCP_RATE_PER_KEY", 10, 2000),
    ("rate_per_ip", "Lượt / phút / IP", "AGENT_MCP_RATE_PER_IP", 0, 20000),
    ("bad_key_per_ip", "Khóa sai / phút / IP", "AGENT_MCP_BAD_KEY_PER_IP", 5, 1000),
    ("row_budget_per_min", "Dòng dữ liệu / phút / khóa (erp_read)", "AGENT_MCP_ROW_BUDGET_PER_MIN", 0, 100000),
    ("log_retention_days", "Số ngày giữ nhật ký chi tiết", "AGENT_MCP_LOG_RETENTION_DAYS", 30, 730),
)

_cache: tuple[float, dict] | None = None


def clear_cache() -> None:
    global _cache
    _cache = None


def _stored(db) -> dict:
    global _cache
    if _cache is not None and time.monotonic() - _cache[0] < CACHE_SEC:
        return _cache[1]
    from . import erp

    try:
        raw = erp.setting_raw_get(db, SETTING_KEY)
        data = json.loads(raw) if raw else {}
    except Exception:  # noqa: BLE001 — ERP không trả lời / JSON hỏng: chạy theo mặc định, không làm sập cổng
        log.warning("mcp_settings: không đọc được cấu hình, dùng mặc định", exc_info=True)
        data = {}
    if not isinstance(data, dict):
        data = {}
    _cache = (time.monotonic(), data)
    return data


def current(db) -> dict:
    """Cấu hình đang hiệu lực: phần đã lưu đè lên mặc định."""
    data = _stored(db)
    saved_groups = data.get("groups") if isinstance(data.get("groups"), dict) else {}
    groups = {g.key: bool(saved_groups.get(g.key, g.default_on)) for g in GROUPS}
    out: dict = {"groups": groups}
    for key, _label, env, lo, hi in LIMITS:
        default = int(getattr(settings, env))
        if key not in data:
            out[key] = default                    # chưa lưu: đúng biến môi trường (kể cả 0 = không chặn)
            continue
        try:
            out[key] = max(lo, min(int(data[key]), hi))
        except (TypeError, ValueError):
            out[key] = default
    out["extra_instructions"] = str(data.get("extra_instructions") or "")[:EXTRA_MAX_LEN]
    return out


def save(db, payload: dict, user_id: int) -> dict:
    """Kiểm + lưu. Trả cấu hình hiệu lực sau khi lưu. Sai kiểu / ngoài dải → ValueError (controller trả 400)."""
    from . import erp

    data = dict(_stored(db))
    if "groups" in payload:
        groups = payload["groups"]
        if not isinstance(groups, dict):
            raise ValueError("groups phải là {mã nhóm: true/false}.")
        unknown = sorted(set(groups) - {g.key for g in GROUPS})
        if unknown:
            raise ValueError(f"Không có nhóm: {', '.join(unknown)}.")
        data["groups"] = {**(data.get("groups") or {}), **{k: bool(v) for k, v in groups.items()}}
    for key, label, _env, lo, hi in LIMITS:
        if key in payload:
            try:
                value = int(payload[key])
            except (TypeError, ValueError):
                raise ValueError(f"{label} phải là số nguyên.") from None
            if not lo <= value <= hi:
                raise ValueError(f"{label} chỉ nhận từ {lo} tới {hi}.")
            data[key] = value
    if "extra_instructions" in payload:
        text = str(payload["extra_instructions"] or "").strip()
        if len(text) > EXTRA_MAX_LEN:
            raise ValueError(f"Câu dặn thêm tối đa {EXTRA_MAX_LEN} ký tự.")
        data["extra_instructions"] = text
    erp.setting_raw_put(db, SETTING_KEY, json.dumps(data, ensure_ascii=False), user_id)
    clear_cache()
    return current(db)


def describe(db) -> dict:
    """Bản cho màn G7: nhóm kèm nhãn / mặc định / danh sách tool, trần kèm nhãn / dải / mặc định."""
    cur = current(db)
    return {
        "groups": [{"key": g.key, "label": g.label, "enabled": cur["groups"][g.key], "default": g.default_on,
                    "tools": sorted(g.tools)} for g in GROUPS],
        "limits": [{"key": key, "label": label, "value": cur[key], "default": int(getattr(settings, env)), "min": lo,
                    "max": hi} for key, label, env, lo, hi in LIMITS],
        "extra_instructions": cur["extra_instructions"], "extra_max_len": EXTRA_MAX_LEN,
    }


def tool_blocked(db, name: str, args: dict | None = None) -> str | None:
    """Câu từ chối nếu tool (hoặc bộ dữ liệu của dataset_query) thuộc nhóm đang tắt qua MCP; None = được gọi."""
    if name in ALWAYS_ON:
        return None
    cur = current(db)["groups"]
    group = GROUP_OF.get(name)
    if group is None:
        return f"Công cụ '{name}' chưa được xếp nhóm nên chưa mở qua MCP."
    if not cur[group.key]:
        return (f'Nhóm "{group.label}" đang tắt qua MCP — nhờ quản trị bật ở Kho skill AI → Cấu hình nếu cần. '
                "Đừng thử công cụ khác để lấy cùng dữ liệu.")
    if name == "dataset_query" and str((args or {}).get("dataset") or "").strip().lower() in FINANCE_DATASETS \
            and not cur["finance"]:
        finance = next(g for g in GROUPS if g.key == "finance")
        return f'Bộ dữ liệu này thuộc nhóm "{finance.label}" đang tắt qua MCP — nhờ quản trị bật ở Kho skill AI → Cấu hình.'
    return None


def tool_listed(db, name: str) -> bool:
    return name in ALWAYS_ON or (name in GROUP_OF and current(db)["groups"][GROUP_OF[name].key])
