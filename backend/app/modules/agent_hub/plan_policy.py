"""Bộ luật lập kế hoạch cho bot điều phối việc (bao-CR-616, phase 24.1 — `doc/agent-hub/18` §4).

Luật là DỮ LIỆU, không phải mã: bản nháp nằm ở `DEFAULTS`, bản chính thức sếp sửa ở màn Cấu hình hệ thống (khóa
`agent_plan_policy`, chuỗi JSON). Khóa nào sếp không khai thì lấy mặc định — một ô cấu hình gõ sai không được phép làm
bot ngừng lập kế hoạch, nên JSON hỏng cũng rơi về mặc định (và ghi log).

Ba mức ưu tiên của kế hoạch ánh xạ sang trường tùy biến «Độ ưu tiên» có sẵn của phân hệ Dự án (P1…P4):
Gấp → P1 · Ưu tiên → P2 · Thường → P3.
"""
from __future__ import annotations

import json
import logging

log = logging.getLogger("app.agent_hub.plan_policy")

SETTING_KEY = "agent_plan_policy"

PRIORITY_URGENT, PRIORITY_HIGH, PRIORITY_NORMAL = "Gấp", "Ưu tiên", "Thường"
PRIORITY_LEVELS = (PRIORITY_URGENT, PRIORITY_HIGH, PRIORITY_NORMAL)
#  Tên mức → tên giá trị trong trường «Độ ưu tiên» (`list_config_service.PRIORITY_OPTIONS`).
PRIORITY_TO_OPTION = {PRIORITY_URGENT: "P1", PRIORITY_HIGH: "P2", PRIORITY_NORMAL: "P3"}

DEFAULTS: dict = {
    "max_subtasks": 7,              # mỗi việc cha tối đa chừng này việc con
    "max_task_days": 2,             # việc con dài hơn chừng này ngày công thì nên chia tiếp (chỉ cảnh báo)
    "default_priority": PRIORITY_NORMAL,
    "no_sunday": True,              # không xếp hạn vào Chủ nhật (chỉ cảnh báo, không tự dời)
    "accept_reply_hours": 4,        # người nhận trả lời trong chừng này giờ làm việc
    "progress_ask_hour": 15,        # giờ hỏi tiến độ đúng ngày hạn
    "overdue_ask_hour": 8,          # giờ hỏi lại ngày sau hạn
    "self_shift_days": {PRIORITY_NORMAL: 3, PRIORITY_HIGH: 1, PRIORITY_URGENT: 0},   # ngưỡng bot tự dời
    "contact_retries": 2,           # nhắn không được: thử chừng này lần
    "contact_retry_hours": 2,
    "brief_hour": 8, "brief_minute": 30,
    "default_criteria": "Hoàn thành đúng hạn và được người giao xác nhận",
}


def current() -> dict:
    """Luật đang có hiệu lực = mặc định đè bởi JSON sếp khai (chỉ các khóa hợp lệ)."""
    from app.core import app_settings

    out = json.loads(json.dumps(DEFAULTS))     # bản sao sâu
    raw = ""
    try:
        raw = str(app_settings.get(SETTING_KEY) or "").strip()
    except Exception:  # noqa: BLE001 — chưa có bảng cấu hình (test) thì dùng mặc định
        raw = ""
    if not raw:
        return out
    try:
        data = json.loads(raw)
    except ValueError:
        log.warning("agent_plan_policy không phải JSON, dùng mặc định")
        return out
    if not isinstance(data, dict):
        return out
    for k, v in data.items():
        if k not in DEFAULTS:
            continue
        if k == "self_shift_days" and isinstance(v, dict):
            out[k].update({kk: int(vv) for kk, vv in v.items() if kk in PRIORITY_LEVELS and str(vv).lstrip("-").isdigit()})
        elif k == "default_priority":
            if v in PRIORITY_LEVELS:
                out[k] = v
        elif isinstance(DEFAULTS[k], bool):
            out[k] = bool(v)
        elif isinstance(DEFAULTS[k], int):
            try:
                out[k] = int(v)
            except (TypeError, ValueError):
                pass
        elif isinstance(DEFAULTS[k], str):
            out[k] = str(v)[:300]
    return out


def describe(policy: dict | None = None) -> str:
    """Luật viết thành câu ngắn để Trợ lý đọc trước khi lập kế hoạch (nhét vào kết quả tool, không phải mã)."""
    p = policy or current()
    return (f"Ưu tiên 3 mức: {PRIORITY_URGENT} (trong ngày) · {PRIORITY_HIGH} (trong 3 ngày) · {PRIORITY_NORMAL} "
            f"(theo kế hoạch), mặc định {p['default_priority']}. Mỗi việc cha tối đa {p['max_subtasks']} việc con; "
            f"việc con tối đa {p['max_task_days']} ngày công, dài hơn thì chia tiếp. Mỗi việc con 1–3 tiêu chí đo được, "
            f"thiếu thì dùng: {p['default_criteria']}. "
            + ("Không xếp hạn vào Chủ nhật. " if p.get("no_sunday") else "")
            + "Chọn người theo phòng ban, chức vụ; không rõ ai thì để trống và hỏi.")
