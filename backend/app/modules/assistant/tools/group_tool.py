"""Ba tool đọc NHÓM Telegram mà bot đang ở (ai-CR-105) — trợ lý cá nhân tóm tắt nhóm hộ người hỏi.

Quyền: chủ nhóm (người đã thêm bot) hoặc người Telegram xác nhận đang là thành viên — `groups.can_read`. Không có tham
số chọn người; người hỏi là `ctx.user`. Không phải dữ liệu ERP nên không qua `apply_scope`.
"""
from __future__ import annotations

from app.modules.agent_hub import doc_text, groups

from .base import ToolContext, ToolSpec

FILE_MAX_BYTES = 20 * 1024 * 1024


def _uid(ctx: ToolContext) -> int:
    return int(getattr(ctx.user, "id", 0) or 0)


def _group(ctx: ToolContext, args: dict):
    g = groups.find(ctx.db, _uid(ctx), str(args.get("group") or ""))
    if g is None:
        mine = groups.groups_for(ctx.db, _uid(ctx))
        return None, {"error": "không thấy nhóm này trong các nhóm bạn đọc được",
                      "groups": [{"no": i + 1, "title": x.title} for i, x in enumerate(mine)]}
    return g, None


def _list_my_groups(ctx: ToolContext, args: dict) -> dict:
    mine = groups.groups_for(ctx.db, _uid(ctx))
    return {"count": len(mine), "groups": [{"no": i + 1, "title": g.title, "owner": bool(g.owner_user_id == _uid(ctx))}
                                           for i, g in enumerate(mine)],
            "hint": "" if mine else ("Chưa có nhóm nào. Thêm bot vào nhóm Telegram (bot cần được tắt chế độ riêng tư "
                                     "hoặc làm quản trị nhóm), từ lúc đó bot mới đọc được tin của nhóm.")}


def _read_group_messages(ctx: ToolContext, args: dict) -> dict:
    g, err = _group(ctx, args)
    if err:
        return err
    return groups.read(ctx.db, g, hours=int(args.get("hours") or 24))


def _read_group_file(ctx: ToolContext, args: dict) -> dict:
    from app.modules.agent_hub import meetings, telegram

    g, err = _group(ctx, args)
    if err:
        return err
    row = groups.file_by_ref(ctx.db, g, int(args.get("file_ref") or 0))
    if row is None:
        return {"error": "không thấy tệp này trong nhóm (hoặc đã quá hạn giữ)"}
    f = row.file or {}
    kind, mime, name = str(f.get("kind")), str(f.get("mime") or ""), str(f.get("name") or "tệp")
    if kind in ("audio", "video", "voice", "video_note") or mime.startswith(("audio/", "video/")):
        chat = groups.private_chat_of(ctx.db, _uid(ctx))
        if not chat:
            return {"error": "cần nhắn riêng với bot để nhận biên bản"}
        m = meetings.create(ctx.db, user_id=_uid(ctx), chat_id=chat, kind=meetings.SourceKind.TELEGRAM,
                            ref=str(f.get("file_id")), title=f"{name} (nhóm {g.title})", mime=mime)
        ctx.db.commit()
        meetings.dispatch(m.id)
        return {"started": True, "message": "Tệp là ghi âm / video: em đang chép lời và viết biên bản, xong gửi riêng."}
    if not doc_text.readable(name, mime):
        return {"error": f"chưa đọc được loại tệp này ({mime or name})"}
    if int(f.get("size") or 0) > FILE_MAX_BYTES:
        return {"error": "tệp lớn hơn 20 MB, bot Telegram không tải được"}
    try:
        data, _ = telegram.download_file(str(f.get("file_id")), max_bytes=FILE_MAX_BYTES)
        text = doc_text.extract(name, mime, data)
    except (telegram.TelegramError, doc_text.DocTextError) as e:
        return {"error": f"không đọc được tệp: {e}"}
    return {"file": name, "from": row.from_name, "text": text}


LIST_MY_GROUPS_SPEC = ToolSpec(
    name="list_my_groups",
    description=("Liệt kê các NHÓM Telegram mà bot đang ở và người hỏi đọc được (người đã thêm bot vào, hoặc đang là thành "
                 "viên). Gọi khi người dùng hỏi «nhóm nào», «bot đang ở nhóm nào», hoặc nói tên nhóm chưa rõ."),
    parameters={"type": "object", "properties": {}},
    handler=_list_my_groups,
)
READ_GROUP_MESSAGES_SPEC = ToolSpec(
    name="read_group_messages",
    description=("ĐỌC tin nhắn của một nhóm Telegram bot đang ở để TÓM TẮT / tổng hợp / viết báo cáo cho người hỏi. `group` = "
                 "tên nhóm (khớp một phần) hoặc số thứ tự từ list_my_groups; `hours` = bao nhiêu giờ gần nhất (mặc định 24, "
                 "«hôm nay» ≈ số giờ từ 0h, «tuần này» = 168). Tóm tắt xong: liệt kê các tệp trong nhóm kèm số thứ tự và gợi ý "
                 "«tóm tắt tệp số n»; giữ `file_ref` của từng tệp để gọi read_group_file."),
    parameters={"type": "object", "properties": {"group": {"type": "string"},
                                                 "hours": {"type": "integer", "minimum": 1, "maximum": 720}},
                "required": ["group"]},
    handler=_read_group_messages,
)
READ_GROUP_FILE_SPEC = ToolSpec(
    name="read_group_file",
    description=("ĐỌC một tệp gửi trong nhóm (pdf, Word, Excel, văn bản) để tóm tắt; ghi âm / video thì tự chuyển sang làm "
                 "biên bản họp và gửi riêng. `file_ref` lấy từ danh sách tệp của read_group_messages."),
    parameters={"type": "object", "properties": {"group": {"type": "string"}, "file_ref": {"type": "integer"}},
                "required": ["group", "file_ref"]},
    handler=_read_group_file,
)
GROUP_SPECS = [LIST_MY_GROUPS_SPEC, READ_GROUP_MESSAGES_SPEC, READ_GROUP_FILE_SPEC]
