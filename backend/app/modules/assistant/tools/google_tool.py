"""Tool Lịch + Drive của CHÍNH người hỏi (ai-CR-064, M-06 · T-11 · R-03 của `doc/agent-hub/04`).

Chạy bằng token Google cá nhân đã nối ở Trang cá nhân (`agent_hub/google_link`). Chưa nối thì trả lời rõ,
không đoán. Cùng một bộ tool cho Trợ lý web, bot Telegram và cổng MCP.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from app.modules.agent_hub import google_link as gl
from app.modules.agent_hub.timeutil import LOCAL_OFFSET, now_local

from .base import ToolContext, ToolSpec

TZ = "Asia/Ho_Chi_Minh"
MAX_EVENTS = 30
MAX_FILES = 20


def _link_or_error(ctx: ToolContext):
    link = gl.get_link(ctx.db, ctx.user.id)
    if link is None:
        return None, {"error": "Bạn chưa nối Google. Vào Trang cá nhân → Khóa AI → «Nối Google» rồi hỏi lại."}
    return link, None


def _day_range(date_from: str, date_to: str) -> tuple[str, str]:
    today = now_local().date()
    start = datetime.fromisoformat(date_from).date() if date_from else today
    end = datetime.fromisoformat(date_to).date() if date_to else start
    s = datetime.combine(start, datetime.min.time()) - LOCAL_OFFSET
    e = datetime.combine(end + timedelta(days=1), datetime.min.time()) - LOCAL_OFFSET
    return s.isoformat() + "Z", e.isoformat() + "Z"


def _event_row(ev: dict) -> dict:
    start = ev.get("start") or {}
    end = ev.get("end") or {}
    return {"id": ev.get("id"), "title": ev.get("summary") or "(không tên)",
            "start": start.get("dateTime") or start.get("date"), "end": end.get("dateTime") or end.get("date"),
            "all_day": "date" in start, "location": ev.get("location") or "",
            "attendees": [a.get("email") for a in (ev.get("attendees") or []) if a.get("email")][:10],
            "meet": ev.get("hangoutLink") or "", "url": ev.get("htmlLink") or ""}


def list_events(db, link, date_from: str = "", date_to: str = "", limit: int = MAX_EVENTS) -> list[dict]:
    t_min, t_max = _day_range(date_from, date_to)
    out = gl.api_get(db, link, f"{gl.CALENDAR_URL}/calendars/primary/events",
                     {"timeMin": t_min, "timeMax": t_max, "singleEvents": "true", "orderBy": "startTime",
                      "maxResults": min(max(int(limit or MAX_EVENTS), 1), MAX_EVENTS), "timeZone": TZ})
    return [_event_row(e) for e in out.get("items") or []]


def _my_calendar_events(ctx: ToolContext, args: dict) -> dict:
    link, err = _link_or_error(ctx)
    if err:
        return err
    try:
        items = list_events(ctx.db, link, str(args.get("date_from") or ""), str(args.get("date_to") or ""), args.get("limit") or MAX_EVENTS)
    except (gl.GoogleError, ValueError) as e:
        return {"error": str(e)}
    return {"count": len(items), "items": items, "timezone": TZ}


def _create_calendar_event(ctx: ToolContext, args: dict) -> dict:
    link, err = _link_or_error(ctx)
    if err:
        return err
    title = str(args.get("title") or "").strip()
    start = str(args.get("start") or "").strip()
    if not title or not start:
        return {"error": "Cần title và start (ISO, ví dụ 2026-09-26T14:00:00)."}
    try:
        st = datetime.fromisoformat(start)
        minutes = int(args.get("duration_minutes") or 60)
        en = datetime.fromisoformat(str(args["end"])) if args.get("end") else st + timedelta(minutes=minutes)
    except ValueError:
        return {"error": "Giờ không đúng dạng ISO (2026-09-26T14:00:00)."}
    body = {"summary": title, "start": {"dateTime": st.isoformat(), "timeZone": TZ}, "end": {"dateTime": en.isoformat(), "timeZone": TZ}}
    if args.get("description"):
        body["description"] = str(args["description"])[:2000]
    if args.get("location"):
        body["location"] = str(args["location"])[:255]
    attendees = [str(a).strip() for a in (args.get("attendees") or []) if str(a).strip()][:20]
    if attendees:
        body["attendees"] = [{"email": a} for a in attendees]
    try:
        ev = gl.api_post(ctx.db, link, f"{gl.CALENDAR_URL}/calendars/primary/events", body)
    except gl.GoogleError as e:
        return {"error": str(e)}
    return {"ok": True, "event": _event_row(ev)}


def _find_event(ctx: ToolContext, link, args: dict) -> tuple[dict | None, dict | None]:
    """Tìm ĐÚNG MỘT sự kiện: theo `event_id`, hoặc theo tên (khớp một phần, không dấu) trong ngày `date`."""
    eid = str(args.get("event_id") or "").strip()
    if eid:
        try:
            return gl.api_get(ctx.db, link, f"{gl.CALENDAR_URL}/calendars/primary/events/{eid}"), None
        except gl.GoogleError as e:
            return None, {"error": str(e)}
    from app.modules.assistant.glossary import fold

    title = fold(str(args.get("title") or ""))
    day = str(args.get("date") or "").strip()
    if not title:
        return None, {"error": "Cần event_id, hoặc title (+ date YYYY-MM-DD) của sự kiện cần sửa / hủy."}
    try:
        rows = list_events(ctx.db, link, day, day) if day else list_events(ctx.db, link, "", "")
    except gl.GoogleError as e:
        return None, {"error": str(e)}
    hits = [r for r in rows if title in fold(r["title"])]
    if len(hits) != 1:
        return None, {"need_choice": "event", "candidates": hits[:8] or rows[:8],
                      "note": ("Không thấy sự kiện khớp" if not hits else "Nhiều sự kiện khớp")
                              + " — hỏi người dùng MỘT câu kèm lựa chọn đánh số, rồi gọi lại với event_id."}
    try:
        return gl.api_get(ctx.db, link, f"{gl.CALENDAR_URL}/calendars/primary/events/{hits[0]['id']}"), None
    except gl.GoogleError as e:
        return None, {"error": str(e)}


def _update_calendar_event(ctx: ToolContext, args: dict) -> dict:
    """ai-CR-084: DỜI / đổi tên một sự kiện ĐÃ CÓ (PATCH) — trước đây Trợ lý «dời» bằng cách tạo thêm, đẻ ra bản trùng."""
    link, err = _link_or_error(ctx)
    if err:
        return err
    ev, err = _find_event(ctx, link, args)
    if err:
        return err
    body: dict = {}
    new_start = str(args.get("new_start") or "").strip()
    if new_start:
        try:
            st = datetime.fromisoformat(new_start)
            old_st = (ev.get("start") or {}).get("dateTime")
            old_en = (ev.get("end") or {}).get("dateTime")
            if args.get("duration_minutes"):
                dur = timedelta(minutes=int(args["duration_minutes"]))
            elif old_st and old_en:
                dur = datetime.fromisoformat(old_en) - datetime.fromisoformat(old_st)
            else:
                dur = timedelta(minutes=60)
        except ValueError:
            return {"error": "Giờ không đúng dạng ISO (2026-10-06T09:00:00)."}
        body["start"] = {"dateTime": st.isoformat(), "timeZone": TZ}
        body["end"] = {"dateTime": (st + dur).isoformat(), "timeZone": TZ}
    if args.get("new_title"):
        body["summary"] = str(args["new_title"])[:255]
    if args.get("new_location"):
        body["location"] = str(args["new_location"])[:255]
    if not body:
        return {"error": "Không có gì để đổi (cần new_start, new_title hoặc new_location)."}
    try:
        out = gl.api_patch(ctx.db, link, f"{gl.CALENDAR_URL}/calendars/primary/events/{ev['id']}", body)
    except gl.GoogleError as e:
        return {"error": str(e)}
    return {"ok": True, "before": _event_row(ev), "event": _event_row(out),
            "note": "Đã sửa ĐÚNG sự kiện cũ (không tạo thêm)."}


def _delete_calendar_event(ctx: ToolContext, args: dict) -> dict:
    """AI-0003: HỦY một sự kiện ĐÃ CÓ. Tìm như `update_calendar_event` — khớp không đúng một thì trả lựa chọn,
    KHÔNG xóa. Lịch lặp lại: danh sách đã bung từng buổi (`singleEvents`), nên tìm theo tên + ngày chỉ hủy buổi đó.
    Có khách mời thì Google gửi thư báo hủy (`sendUpdates=all`)."""
    link, err = _link_or_error(ctx)
    if err:
        return err
    ev, err = _find_event(ctx, link, args)
    if err:
        return err
    row = _event_row(ev)
    params = {"sendUpdates": "all" if row["attendees"] else "none"}
    try:
        gl.api_delete(ctx.db, link, f"{gl.CALENDAR_URL}/calendars/primary/events/{ev['id']}", params)
    except gl.GoogleError as e:
        return {"error": str(e)}
    organizer = ev.get("organizer") or {}
    note = "Đã hủy ĐÚNG sự kiện này."
    if organizer and not organizer.get("self"):
        note = "Bạn là khách mời: đã gỡ sự kiện khỏi lịch của bạn, lịch của người tổ chức không đổi."
    elif row["attendees"]:
        note += " Google đã gửi thư báo hủy cho khách mời."
    return {"ok": True, "cancelled": row, "note": note}


def _drive_search(ctx: ToolContext, args: dict) -> dict:
    link, err = _link_or_error(ctx)
    if err:
        return err
    q = str(args.get("q") or "").strip().replace("'", "\\'")
    if not q:
        return {"error": "Cần từ khóa q."}
    query = f"(name contains '{q}' or fullText contains '{q}') and trashed = false"
    try:
        out = gl.api_get(ctx.db, link, f"{gl.DRIVE_URL}/files",
                         {"q": query, "pageSize": min(max(int(args.get("limit") or MAX_FILES), 1), MAX_FILES),
                          "fields": "files(id,name,mimeType,modifiedTime,webViewLink,owners(emailAddress))",
                          "orderBy": "modifiedTime desc"})
    except gl.GoogleError as e:
        return {"error": str(e)}
    files = [{"id": f.get("id"), "name": f.get("name"), "mime": f.get("mimeType"), "modified": f.get("modifiedTime"),
              "url": f.get("webViewLink")} for f in out.get("files") or []]
    return {"count": len(files), "items": files}


def _drive_read(ctx: ToolContext, args: dict) -> dict:
    link, err = _link_or_error(ctx)
    if err:
        return err
    fid = str(args.get("file_id") or "").strip()
    if not fid:
        return {"error": "Cần file_id (lấy từ drive_search)."}
    try:
        meta = gl.api_get(ctx.db, link, f"{gl.DRIVE_URL}/files/{fid}", {"fields": "id,name,mimeType,webViewLink"})
        text = gl.export_text(ctx.db, link, fid, str(meta.get("mimeType") or ""))
    except gl.GoogleError as e:
        return {"error": str(e)}
    return {"name": meta.get("name"), "mime": meta.get("mimeType"), "url": meta.get("webViewLink"), "text": text}


MY_CALENDAR_EVENTS_SPEC = ToolSpec(
    name="my_calendar_events",
    description=("LỊCH Google của CHÍNH người hỏi: các sự kiện trong một ngày hoặc khoảng ngày (mặc định hôm nay). Gọi khi "
                 "hỏi 'hôm nay tôi có họp gì', 'lịch tuần này', 'mai mấy giờ họp'. Trả giờ theo Asia/Ho_Chi_Minh."),
    parameters={"type": "object", "properties": {
        "date_from": {"type": "string", "description": "Ngày đầu YYYY-MM-DD (bỏ trống = hôm nay)."},
        "date_to": {"type": "string", "description": "Ngày cuối YYYY-MM-DD (bỏ trống = bằng date_from)."},
        "limit": {"type": "integer"}}},
    handler=_my_calendar_events,
)
CREATE_CALENDAR_EVENT_SPEC = ToolSpec(
    name="create_calendar_event",
    description=("TẠO một sự kiện MỚI trên lịch Google của CHÍNH người hỏi ('đặt lịch họp NCC X 14h mai 1 tiếng', 'thêm lịch…'). "
                 "Chỉ gọi khi người dùng nói rõ muốn tạo; ghi giờ ISO theo Asia/Ho_Chi_Minh; mặc định 60 phút. KHÔNG dùng "
                 "để DỜI / đổi giờ / đổi tên lịch đã có — việc đó là update_calendar_event (tạo thêm sẽ đẻ bản trùng)."),
    parameters={"type": "object", "properties": {
        "title": {"type": "string"}, "start": {"type": "string", "description": "ISO 2026-09-26T14:00:00"},
        "end": {"type": "string"}, "duration_minutes": {"type": "integer"},
        "description": {"type": "string"}, "location": {"type": "string"},
        "attendees": {"type": "array", "items": {"type": "string"}, "description": "Email người mời."}},
        "required": ["title", "start"]},
    handler=_create_calendar_event,
)
DRIVE_SEARCH_SPEC = ToolSpec(
    name="drive_search",
    description=("TÌM tệp trên Google Drive của CHÍNH người hỏi theo tên hoặc nội dung ('tìm trên Drive hợp đồng ABC', "
                 "'file báo giá tháng 8 của tôi'). Trả tên, loại, ngày sửa, link mở."),
    parameters={"type": "object", "properties": {"q": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["q"]},
    handler=_drive_search,
)
DRIVE_READ_SPEC = ToolSpec(
    name="drive_read",
    description=("ĐỌC nội dung chữ của một tệp trên Drive của người hỏi (Google Docs/Sheets, hoặc tệp chữ) để tóm tắt hay "
                 "trả lời câu hỏi về tệp đó. Lấy file_id từ drive_search."),
    parameters={"type": "object", "properties": {"file_id": {"type": "string"}}, "required": ["file_id"]},
    handler=_drive_read,
)
UPDATE_CALENDAR_EVENT_SPEC = ToolSpec(
    name="update_calendar_event",
    description=("DỜI / ĐỔI GIỜ / ĐỔI TÊN một sự kiện ĐÃ CÓ trên lịch Google của chính người hỏi ('dời lịch mua thuốc qua mai', "
                 "'đổi họp NCC sang 3h chiều'). Tìm theo event_id (lấy từ my_calendar_events) hoặc theo tên + ngày. Dời ngày mà "
                 "không nói giờ thì GIỮ giờ cũ; giữ nguyên thời lượng nếu không nói. Không chắc sự kiện nào → tool trả lựa chọn, "
                 "hỏi MỘT câu. Chỉ báo «đã dời» khi tool trả ok."),
    parameters={"type": "object", "properties": {
        "event_id": {"type": "string"}, "title": {"type": "string", "description": "Tên (một phần) để tìm."},
        "date": {"type": "string", "description": "Ngày đang có sự kiện, YYYY-MM-DD (giúp tìm đúng)."},
        "new_start": {"type": "string", "description": "Giờ bắt đầu MỚI, ISO 2026-10-06T18:00:00."},
        "duration_minutes": {"type": "integer"}, "new_title": {"type": "string"}, "new_location": {"type": "string"}}},
    handler=_update_calendar_event,
)
DELETE_CALENDAR_EVENT_SPEC = ToolSpec(
    name="delete_calendar_event",
    description=("HỦY / XÓA một sự kiện ĐÃ CÓ trên lịch Google của chính người hỏi ('hủy lịch họp NCC chiều nay', "
                 "'xóa lịch mua thuốc mai'). Chỉ gọi khi người dùng nói rõ muốn hủy; KHÔNG dùng để dời giờ (việc đó là "
                 "update_calendar_event). Tìm theo event_id (lấy từ my_calendar_events) hoặc theo tên + ngày; lịch lặp lại "
                 "thì chỉ hủy buổi của ngày đó. Không chắc sự kiện nào → tool trả lựa chọn, hỏi MỘT câu, không tự chọn. "
                 "Chỉ báo «đã hủy» khi tool trả ok, kèm tên + giờ sự kiện vừa hủy."),
    parameters={"type": "object", "properties": {
        "event_id": {"type": "string"}, "title": {"type": "string", "description": "Tên (một phần) để tìm."},
        "date": {"type": "string", "description": "Ngày đang có sự kiện, YYYY-MM-DD (giúp tìm đúng)."}}},
    handler=_delete_calendar_event,
)
GOOGLE_SPECS = [MY_CALENDAR_EVENTS_SPEC, CREATE_CALENDAR_EVENT_SPEC, UPDATE_CALENDAR_EVENT_SPEC,
                DELETE_CALENDAR_EVENT_SPEC, DRIVE_SEARCH_SPEC, DRIVE_READ_SPEC]
