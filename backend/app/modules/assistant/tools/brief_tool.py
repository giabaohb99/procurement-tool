"""Tool BẢN TIN (ai-CR-140) — người dùng bật / tắt / hẹn bản tin bằng câu tự nhiên trong chat.

«sáng thứ hai gửi anh công nợ quá hạn của DEGO lúc 8h», «tắt bản tin công nợ», «bản tin sáng đổi sang 6h45 ngày thường».
Câu ngắn kiểu «bật bản tin» / «tắt bản tin» bot đã bắt bằng lệnh chữ trước khi tới Trợ lý (`service._brief_by_text`).
`user_id` luôn là người đang hỏi — model không chọn được người khác. Chạy trong dịch vụ AI (bảng ở DB bot).
"""
from __future__ import annotations

from app.modules.agent_hub import brief_subs as bs

from .base import ToolContext, ToolSpec


def _uid(ctx: ToolContext) -> int:
    return int(getattr(ctx.user, "id", 0) or 0)


def _manage_briefs(ctx: ToolContext, args: dict) -> dict:
    uid = _uid(ctx)
    if uid <= 0:
        return {"error": "chưa đăng nhập"}
    action = str(args.get("action") or "list").strip()
    when = bs.parse_time(str(args.get("time") or "")) if args.get("time") else None
    if args.get("time") and when is None:
        return {"error": "giờ không đọc được, dùng dạng 7h30 / 07:30"}
    days = bs.parse_days(args.get("days")) if args.get("days") else None
    try:
        if action == "enable_daily":
            bs.set_daily(ctx.db, uid, enabled=True, hour=when[0] if when else None, minute=when[1] if when else None,
                         days=days)
        elif action == "disable_daily":
            bs.set_daily(ctx.db, uid, enabled=False)
        elif action == "add_topic":
            hour, minute = when or (bs.DEFAULT_HOUR, bs.DEFAULT_MINUTE)
            bs.add_topic(ctx.db, uid, str(args.get("question") or ""), hour=hour, minute=minute,
                         days=days if days is not None else bs.ALL_DAYS)
        elif action in ("disable", "enable", "remove"):
            sid = int(args.get("id") or 0)
            ok = bs.remove(ctx.db, uid, sid) if action == "remove" else bs.set_enabled(ctx.db, uid, sid,
                                                                                      action == "enable")
            if not ok:
                return {"error": f"không có bản tin id {sid} của người hỏi"}
        elif action == "disable_all":
            bs.disable_all(ctx.db, uid)
        elif action != "list":
            return {"error": f"action lạ: {action}"}
    except ValueError as e:
        return {"error": str(e)}
    return {"ok": True, "briefs": bs.list_for(ctx.db, uid),
            "note": "Báo lại ngắn gọn bản tin nào đang bật, giờ nào, thứ nào. Bot chỉ gửi bản tin người dùng đã bật."}


MANAGE_BRIEFS_SPEC = ToolSpec(
    name="manage_briefs",
    description=("Xem / bật / tắt / hẹn BẢN TIN tự gửi của chính người hỏi. Bản tin sáng (lịch, việc riêng, việc Dự án tới "
                 "hạn, phiếu chờ duyệt) dùng enable_daily / disable_daily. Bản tin CHỦ ĐỀ là một câu hỏi bot tự hỏi hộ "
                 "theo lịch ('sáng thứ hai gửi anh công nợ quá hạn của DEGO') dùng add_topic với question viết như người "
                 "dùng tự hỏi. Tắt / bật / xóa một bản tin theo id lấy từ action list."),
    parameters={"type": "object", "properties": {
        "action": {"type": "string", "enum": ["list", "enable_daily", "disable_daily", "add_topic", "enable", "disable",
                                              "remove", "disable_all"]},
        "question": {"type": "string", "description": "add_topic: câu hỏi bot sẽ tự hỏi hộ, vd 'công nợ quá hạn của DEGO'."},
        "time": {"type": "string", "description": "Giờ gửi, vd '7h30' (giờ VN). Bỏ trống = 07:30."},
        "days": {"type": "array", "items": {"type": "string"},
                 "description": "Thứ gửi: 'thứ hai'…'chủ nhật', 'ngày thường', 'mọi ngày'. Bỏ trống = mọi ngày."},
        "id": {"type": "integer", "description": "enable / disable / remove: id bản tin lấy từ action list."}},
        "required": ["action"]},
    handler=_manage_briefs,
)
