"""Ba tool BIÊN BẢN HỌP (ai-CR-112, phase 10 bước 10.2) — trợ lý cá nhân viết lại biên bản theo mẫu khác, quản lý mẫu riêng.

Chỉ phiên họp / mẫu của CHÍNH người hỏi (`tab_agent_meeting.user_id`, sổ ghi nhớ riêng) — không có tham số chọn người,
không phải dữ liệu ERP nên không qua `apply_scope`. Viết lại chạy nền (không chép lời lại), xong bot gửi vào chat riêng.
"""
from __future__ import annotations

from app.modules.agent_hub import meetings

from .base import ToolContext, ToolSpec


def _uid(ctx: ToolContext) -> int:
    return int(getattr(ctx.user, "id", 0) or 0)


def _list_my_meetings(ctx: ToolContext, args: dict) -> dict:
    rows = meetings.recent(ctx.db, _uid(ctx), 10)
    return {"count": len(rows),
            "meetings": [{"no": i + 1, **meetings.describe(r),
                          "date": f"{r.finished_at or r.created_at:%d/%m/%Y %H:%M}" if (r.finished_at or r.created_at) else ""}
                         for i, r in enumerate(rows)],
            "templates": meetings.list_templates(ctx.db, _uid(ctx)),
            "hint": "" if rows else "Chưa có cuộc họp nào. Gửi tệp ghi âm / video (hoặc link Drive kèm chữ «họp») vào chat "
                                    "riêng với bot để làm biên bản."}


def _rewrite_meeting_minutes(ctx: ToolContext, args: dict) -> dict:
    row = meetings.find(ctx.db, _uid(ctx), str(args.get("meeting") or ""))
    if row is None:
        return {"error": "không thấy cuộc họp này trong các cuộc họp của bạn",
                "meetings": [{"no": i + 1, "title": r.title} for i, r in enumerate(meetings.recent(ctx.db, _uid(ctx), 10))]}
    if not row.transcript:
        return {"error": "cuộc họp này chưa chép lời xong (hoặc hỏng ở bước chép lời) — gửi lại tệp giúp em"}
    if row.status in (int(meetings.MeetingStatus.TRANSCRIBING), int(meetings.MeetingStatus.WRITING),
                      int(meetings.MeetingStatus.QUEUED)):
        return {"error": "biên bản cuộc họp này đang được viết, chờ xong rồi hẵng viết lại"}
    tpl = meetings.resolve_template(ctx.db, _uid(ctx), str(args.get("template") or ""))
    meetings.rewrite(ctx.db, row, tpl)
    return {"started": True, "meeting": row.title, "template": tpl.label,
            "message": f"Đang viết lại biên bản «{row.title}» theo mẫu «{tpl.label}», xong em gửi kèm tệp Word."}


def _save_meeting_template(ctx: ToolContext, args: dict) -> dict:
    return meetings.save_personal_template(ctx.db, _uid(ctx), str(args.get("name") or ""),
                                           str(args.get("instruction") or ""))


LIST_MY_MEETINGS_SPEC = ToolSpec(
    name="list_my_meetings",
    description=("Liệt kê 10 cuộc họp gần nhất mà người hỏi đã gửi cho bot làm biên bản (số thứ tự, tên, ngày, số phút, mẫu, "
                 "trạng thái) và các mẫu biên bản họ dùng được (mẫu sẵn + mẫu riêng). Gọi khi hỏi «các cuộc họp của tôi», "
                 "«có những mẫu biên bản nào», hoặc trước khi viết lại mà chưa rõ cuộc họp nào."),
    parameters={"type": "object", "properties": {}},
    handler=_list_my_meetings,
)
REWRITE_MEETING_MINUTES_SPEC = ToolSpec(
    name="rewrite_meeting_minutes",
    description=("VIẾT LẠI biên bản một cuộc họp đã chép lời theo MẪU KHÁC (không chép lời lại), chạy nền rồi gửi chữ + Word. "
                 "`meeting` = số thứ tự từ list_my_meetings (1 = mới nhất), một phần tên, hoặc để trống = cuộc họp mới nhất. "
                 "`template` = tên mẫu («chính thức», «danh sách việc», «theo giờ», «tóm tắt nhanh», hoặc tên mẫu riêng), "
                 "hoặc lời dặn tự do dạng «mẫu: <cách viết>»."),
    parameters={"type": "object", "properties": {"meeting": {"type": "string"}, "template": {"type": "string"}},
                "required": ["template"]},
    handler=_rewrite_meeting_minutes,
)
SAVE_MEETING_TEMPLATE_SPEC = ToolSpec(
    name="save_meeting_template",
    description=("LƯU một mẫu biên bản RIÊNG của người hỏi để dùng lại («lưu mẫu biên bản Giao ban: chỉ ghi số liệu và việc "
                 "của từng phòng»). Trùng tên thì thay mẫu cũ. Dùng sau đó bằng cách nhắc tên mẫu khi gửi tệp họp hoặc khi "
                 "nhờ viết lại. `name` ≤ 40 ký tự; `instruction` = cách viết."),
    parameters={"type": "object", "properties": {"name": {"type": "string", "maxLength": 40},
                                                 "instruction": {"type": "string", "maxLength": 250}},
                "required": ["name", "instruction"]},
    handler=_save_meeting_template,
)
MEETING_SPECS = [LIST_MY_MEETINGS_SPEC, REWRITE_MEETING_MINUTES_SPEC, SAVE_MEETING_TEMPLATE_SPEC]
