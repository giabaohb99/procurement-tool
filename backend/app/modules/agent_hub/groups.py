"""Bot trong NHÓM Telegram (ai-CR-105) — trợ lý cá nhân đọc nhóm hộ chủ (đại ca chốt 07/10/2026).

Định hướng: mỗi người coi bot là trợ lý riêng; ai thêm bot vào nhóm nào thì nhắn RIÊNG cho bot «tóm tắt nhóm X hôm nay»,
«nhóm Y có tệp gì», «tóm tắt tệp 2» — không cần gọi @bot trong nhóm, bot không nói gì trong nhóm. Không liên quan bot IDA.

  - Bot phải được TẮT chế độ riêng tư (BotFather → /setprivacy → Disable) hoặc làm quản trị nhóm mới thấy mọi tin.
  - Bot chỉ thấy tin TỪ LÚC vào nhóm (Bot API không đọc tin cũ).
  - Nhóm ghi nhận chủ = người đã thêm bot (update `my_chat_member`, `from.id` → chat riêng đã đăng nhập ERP). Người khác
    đã đăng nhập ERP đọc được nhóm khi Telegram xác nhận họ đang là thành viên (`getChatMember`).
  - Tin nhóm giữ GROUP_RETENTION_DAYS ngày rồi dọn (vòng nền hằng ngày).
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.assistant.glossary import fold

from . import channels, chat_link, telegram
from .model import AgentChatLink, AgentGroup, AgentGroupMessage
from .timeutil import now_utc, to_local

log = logging.getLogger("app.agent_hub.groups")

GROUP_TYPES = ("group", "supergroup")
TEXT_MAX = 4000
READ_MAX = 400                 # tin tối đa đưa cho model một lượt
READ_CHARS = 60_000
MEMBER_STATUSES = ("creator", "administrator", "member", "restricted")


def is_group(msg: dict) -> bool:
    return str((msg.get("chat") or {}).get("type") or "") in GROUP_TYPES


def _sender(msg: dict) -> tuple[int, str]:
    f = msg.get("from") or {}
    name = " ".join(x for x in (f.get("first_name"), f.get("last_name")) if x) or f.get("username") or "ẩn danh"
    return int(f.get("id") or 0), str(name)[:120]


def file_of(msg: dict) -> dict | None:
    """Tệp đính kèm của một tin nhóm (chưa tải — chỉ ghi lại để đọc khi được nhờ)."""
    for key in ("document", "audio", "video", "voice", "video_note"):
        m = msg.get(key) or {}
        if m.get("file_id"):
            return {"kind": key, "file_id": str(m["file_id"]), "name": str(m.get("file_name") or m.get("title") or key),
                    "mime": str(m.get("mime_type") or ""), "size": int(m.get("file_size") or 0),
                    "duration": int(m.get("duration") or 0)}
    photos = msg.get("photo") or []
    if photos:
        return {"kind": "photo", "file_id": str(photos[-1].get("file_id") or ""), "name": "ảnh", "mime": "image/jpeg",
                "size": int(photos[-1].get("file_size") or 0), "duration": 0}
    return None


def _user_of_tg(db: Session, tg_id: int) -> int:
    """Tài khoản ERP của một người Telegram: chat riêng của họ có id = id người dùng Telegram."""
    if not tg_id:
        return 0
    link = chat_link.get_active_link(db, str(tg_id))
    return int(link.user_id) if link is not None else 0


def get_group(db: Session, chat_id: str) -> AgentGroup | None:
    return db.scalar(select(AgentGroup).where(AgentGroup.chat_id == str(chat_id)))


def _ensure(db: Session, chat: dict) -> AgentGroup:
    row = get_group(db, str(chat.get("id")))
    if row is None:
        row = AgentGroup(chat_id=str(chat.get("id")), title=str(chat.get("title") or "nhóm")[:200], active=True,
                         joined_at=datetime.now())
        db.add(row)
        db.flush()
    elif chat.get("title") and row.title != chat["title"]:
        row.title = str(chat["title"])[:200]
    return row


def on_member_update(db: Session, upd: dict) -> None:
    """`my_chat_member`: bot được thêm vào / bị mời ra khỏi nhóm. Người thêm là CHỦ nhóm đối với bot."""
    chat = upd.get("chat") or {}
    if str(chat.get("type") or "") not in GROUP_TYPES:
        return
    status = str(((upd.get("new_chat_member") or {}).get("status")) or "")
    row = _ensure(db, chat)
    if status in ("member", "administrator"):
        row.active = True
        row.left_at = None
        adder_tg = int((upd.get("from") or {}).get("id") or 0)
        if adder_tg and not row.owner_user_id:
            row.owner_tg_id = adder_tg
            row.owner_user_id = _user_of_tg(db, adder_tg)
    elif status in ("left", "kicked"):
        row.active = False
        row.left_at = datetime.now()
    db.flush()


def capture(db: Session, msg: dict) -> None:
    """Ghi lặng một tin nhóm. Bot không trả lời gì trong nhóm."""
    row = _ensure(db, msg.get("chat") or {})
    if not row.active:
        row.active = True
    text = str(msg.get("text") or msg.get("caption") or "")[:TEXT_MAX]
    f = file_of(msg)
    if not text and not f:
        return
    from_id, name = _sender(msg)
    if channels.is_zalo(row.chat_id) and not row.owner_user_id:
        #  ai-CR-111: Zalo không báo «ai thêm bot vào nhóm» — người đã đăng nhập ERP nói câu đầu tiên trong nhóm là chủ.
        zid = str((msg.get("from") or {}).get("zalo_id") or "")
        link = chat_link.get_active_link(db, channels.zalo_chat(zid)) if zid else None
        if link is not None:
            row.owner_user_id = int(link.user_id)
            row.owner_tg_id = from_id
    db.add(AgentGroupMessage(group_id=row.id, tg_message_id=int(msg.get("message_id") or 0), from_tg_id=from_id,
                             from_name=name, text=text, file=f,
                             sent_at=datetime.utcfromtimestamp(int(msg.get("date") or 0)) if msg.get("date") else now_utc()))
    db.flush()


# ---------------------------------------------------------------------------
# Quyền đọc nhóm
# ---------------------------------------------------------------------------
def _tg_ids_of(db: Session, user_id: int) -> list[int]:
    ids = []
    for c in db.scalars(select(AgentChatLink.chat_id).where(AgentChatLink.user_id == int(user_id),
                                                            AgentChatLink.revoked_at.is_(None))):
        if c and str(c).isdigit():
            ids.append(int(c))
    return ids


def _zalo_member(db: Session, user_id: int, group: AgentGroup) -> bool:
    """Nhóm Zalo không có API hỏi thành viên: người từng nhắn trong nhóm (bằng tài khoản Zalo đã đăng nhập ERP) mới đọc
    được nhóm đó."""
    ids = [channels.number_of(channels.raw_id(c)) for c in db.scalars(
        select(AgentChatLink.chat_id).where(AgentChatLink.user_id == int(user_id), AgentChatLink.revoked_at.is_(None)))
        if channels.is_zalo(c)]
    if not ids:
        return False
    return db.scalar(select(AgentGroupMessage.id).where(AgentGroupMessage.group_id == group.id,
                                                        AgentGroupMessage.from_tg_id.in_(ids)).limit(1)) is not None


def is_member(group: AgentGroup, tg_id: int) -> bool:
    if channels.is_zalo(group.chat_id):
        return False
    try:
        info = telegram._call("getChatMember", {"chat_id": group.chat_id, "user_id": tg_id})
    except telegram.TelegramError:
        return False
    return str(info.get("status") or "") in MEMBER_STATUSES


def can_read(db: Session, user_id: int, group: AgentGroup) -> bool:
    if not user_id:
        return False
    if group.owner_user_id and int(group.owner_user_id) == int(user_id):
        return True
    if channels.is_zalo(group.chat_id):
        return _zalo_member(db, user_id, group)
    return any(is_member(group, tg) for tg in _tg_ids_of(db, user_id))


def groups_for(db: Session, user_id: int) -> list[AgentGroup]:
    rows = list(db.scalars(select(AgentGroup).where(AgentGroup.active.is_(True)).order_by(AgentGroup.id)))
    return [g for g in rows if can_read(db, user_id, g)]


def find(db: Session, user_id: int, name: str) -> AgentGroup | None:
    """Nhóm theo tên (khớp một phần, không dấu) hoặc số thứ tự trong danh sách. Không quyền = None."""
    mine = groups_for(db, user_id)
    key = fold(name)
    if key.isdigit() and 1 <= int(key) <= len(mine):
        return mine[int(key) - 1]
    hits = [g for g in mine if key and key in fold(g.title)]
    if not hits and len(mine) == 1 and not key:
        return mine[0]
    return hits[0] if len(hits) == 1 else None


# ---------------------------------------------------------------------------
# Đọc tin + tệp
# ---------------------------------------------------------------------------
def read(db: Session, group: AgentGroup, *, hours: int = 24, limit: int = READ_MAX) -> dict:
    since = now_utc() - timedelta(hours=max(1, min(int(hours or 24), 24 * settings.AGENT_GROUP_RETENTION_DAYS)))
    rows = list(db.scalars(select(AgentGroupMessage).where(AgentGroupMessage.group_id == group.id,
                                                           AgentGroupMessage.sent_at >= since)
                           .order_by(AgentGroupMessage.id.desc()).limit(min(limit, READ_MAX))))
    rows.reverse()
    lines, files, total = [], [], 0
    for r in rows:
        when = to_local(r.sent_at)
        extra = ""
        if r.file:
            files.append({"no": len(files) + 1, "file_ref": r.id, "name": r.file.get("name"), "kind": r.file.get("kind"),
                          "from": r.from_name, "at": f"{when:%d/%m %H:%M}" if when else ""})
            extra = f" [tệp {len(files)}: {r.file.get('name')}]"
        line = f"[{when:%d/%m %H:%M}] {r.from_name}: {r.text}{extra}" if when else f"{r.from_name}: {r.text}{extra}"
        total += len(line)
        if total > READ_CHARS:
            lines.append("[… còn tin cũ hơn, em chỉ đọc phần mới nhất]")
            break
        lines.append(line)
    return {"group": group.title, "hours": hours, "count": len(rows), "messages": lines, "files": files}


def file_by_ref(db: Session, group: AgentGroup, ref: int) -> AgentGroupMessage | None:
    """Tin có tệp theo `file_ref` (id dòng tin) mà `read` đã trả — đúng nhóm, còn trong thời hạn giữ."""
    row = db.get(AgentGroupMessage, int(ref or 0))
    return row if row is not None and row.group_id == group.id and row.file else None


def purge(db: Session, *, days: int | None = None) -> int:
    days = int(days or settings.AGENT_GROUP_RETENTION_DAYS)
    res = db.execute(delete(AgentGroupMessage).where(AgentGroupMessage.sent_at < now_utc() - timedelta(days=days)))
    db.commit()
    return int(res.rowcount or 0)


def private_chat_of(db: Session, user_id: int) -> str:
    """Chat riêng đang đăng nhập của một tài khoản ERP (để gửi kết quả riêng, không vào nhóm)."""
    ids = _tg_ids_of(db, user_id)
    return str(ids[0]) if ids else ""

