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
MIN_SUBTASKS = 2                     # mỗi việc cha phải chia ít nhất chừng này việc con (tool bắt soạn lại nếu thiếu)

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
            f"(theo kế hoạch), mặc định {p['default_priority']}. MỖI việc cha PHẢI tự chia thành {MIN_SUBTASKS}–"
            f"{p['max_subtasks']} việc con (các bước làm cụ thể, kể cả khi người dùng chỉ ghi một dòng); việc con tối đa "
            f"{p['max_task_days']} ngày công, dài hơn thì chia tiếp. MỖI việc cha và việc con PHẢI có 1–3 tiêu chí đo được "
            f"do bot tự đặt (kết quả nhìn thấy được: tệp / tin nhắn / số lượng / mốc giờ), không chép lại tên việc; "
            f"người dùng không nêu thì tự đặt, chỉ khi không nghĩ ra mới dùng: {p['default_criteria']}. "
            + ("Không xếp hạn vào Chủ nhật. " if p.get("no_sunday") else "")
            + "Chọn người theo phòng ban, chức vụ; không rõ ai thì để trống và hỏi.")


# ---------------------------------------------------------------------------------------------------------------------
#  Hằng dùng chung cho HAI phía của kế hoạch (bao-CR-616): phía ERP (`modules/work/plan_service.py`) và phía bot
#  (`agent_hub/work_plan.py`). Để ở đây vì tệp này thuần luật, không đụng bảng — phía bot import được mà không vi phạm
#  ranh giới bot / ERP (`test_agent_hub_ranh_gioi_erp.py`).
# ---------------------------------------------------------------------------------------------------------------------
FIELD_ACCEPT = "Nhận việc"
ACCEPT_NOT_ASKED, ACCEPT_YES, ACCEPT_LATER, ACCEPT_NO, ACCEPT_UNREACHABLE = (
    "Chưa hỏi", "Nhận", "Nhận giờ khác", "Từ chối", "Nhắn không được")
ACCEPT_OPTIONS = ((ACCEPT_NOT_ASKED, "slate"), (ACCEPT_YES, "green"), (ACCEPT_LATER, "orange"),
                  (ACCEPT_NO, "red"), (ACCEPT_UNREACHABLE, "slate"))
FIELD_CRITERIA, FIELD_PROGRESS, FIELD_SCORE, FIELD_NOTE = "Tiêu chí", "Tiến độ %", "Tự chấm (1-10)", "Ghi nhận"
PLAN_MARK = "[kế hoạch do bot lập]"       # đuôi mô tả bảng — để nhận ra bảng là kế hoạch

#  Hành động của `plan_service.reply`. Nút Telegram → hành động: kh_ok → accept, kh_khac → later, kh_tc → decline.
A_ACCEPT, A_LATER, A_DECLINE, A_NOTE, A_DONE, A_PROGRESS, A_UNREACHABLE = (
    "accept", "later", "decline", "note", "done", "progress", "unreachable")
