"""Bot trong NHÓM Telegram (ai-CR-105) — trợ lý cá nhân đọc nhóm hộ chủ (đại ca chốt 07/10/2026).

Định hướng: mỗi người coi bot là trợ lý riêng; ai thêm bot vào nhóm nào thì nhắn RIÊNG cho bot «tóm tắt nhóm X hôm nay»,
«nhóm Y có tệp gì», «tóm tắt tệp 2» — không cần gọi @bot trong nhóm, bot không nói gì trong nhóm. Không liên quan bot IDA.

  - Bot phải được TẮT chế độ riêng tư (BotFather → /setprivacy → Disable) hoặc làm quản trị nhóm mới thấy mọi tin.
  - Bot chỉ thấy tin TỪ LÚC vào nhóm (Bot API không đọc tin cũ).
  - Nhóm ghi nhận chủ = người đã thêm bot (update `my_chat_member`, `from.id` → chat riêng đã đăng nhập ERP). Người khác
    đã đăng nhập ERP đọc được nhóm khi Telegram xác nhận họ đang là thành viên (`getChatMember`).
  - Tin nhóm giữ GROUP_RETENTION_DAYS ngày rồi dọn (vòng nền hằng ngày) — 90 ngày từ ai-CR-122.
  - ai-CR-122: nhóm Zalo của tài khoản công ty (`zg:`) — tiến trình `zalo-listener` báo tên + danh sách thành viên;
    người đọc được = tài khoản Zalo đã đăng nhập ERP (`zu:<uid>`) có trong danh sách đó.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta

from sqlalchemy import select
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


def by_id(db: Session, group_id: int) -> AgentGroup | None:
    return db.get(AgentGroup, int(group_id or 0)) if group_id else None


def get_group(db: Session, chat_id: str) -> AgentGroup | None:
    return db.scalar(select(AgentGroup).where(AgentGroup.chat_id == str(chat_id)))


def _ensure(db: Session, chat: dict) -> AgentGroup:
    row = get_group(db, str(chat.get("id")))
    if row is None:
        default = "nhóm Zalo" if channels.is_zalo_account(chat.get("id")) else "nhóm"
        row = AgentGroup(chat_id=str(chat.get("id")), title=str(chat.get("title") or default)[:200], active=True,
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
    if row.paused:
        return                      # ai-CR-123: người quản lý bot AI đã tắt ghi nhóm này
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


def _zalo_uids_of(db: Session, user_id: int) -> set[str]:
    return {channels.raw_id(c) for c in db.scalars(
        select(AgentChatLink.chat_id).where(AgentChatLink.user_id == int(user_id), AgentChatLink.revoked_at.is_(None)))
        if str(c or "").startswith(channels.ZALO_USER_PREFIX)}


def _zalo_account_member(db: Session, user_id: int, group: AgentGroup) -> bool:
    members = {str(m) for m in (group.members or [])}
    return bool(members & _zalo_uids_of(db, user_id))


#  ai-CR-123: màn «Nhóm chat» hỏi quyền cho cả danh sách nhóm mỗi lần mở — nhớ câu trả lời của Telegram vài phút
#  thay vì gọi `getChatMember` N lần mỗi lượt.
_MEMBER_CACHE: dict[tuple[str, int], tuple[float, bool]] = {}
MEMBER_CACHE_SEC = 300


def is_member(group: AgentGroup, tg_id: int) -> bool:
    import time

    if not channels.is_telegram(group.chat_id):
        return False
    key = (str(group.chat_id), int(tg_id))
    hit = _MEMBER_CACHE.get(key)
    if hit and time.monotonic() - hit[0] < MEMBER_CACHE_SEC:
        return hit[1]
    try:
        info = telegram._call("getChatMember", {"chat_id": group.chat_id, "user_id": tg_id})
    except telegram.TelegramError:
        return False
    ok = str(info.get("status") or "") in MEMBER_STATUSES
    _MEMBER_CACHE[key] = (time.monotonic(), ok)
    return ok


def can_read(db: Session, user_id: int, group: AgentGroup) -> bool:
    if not user_id:
        return False
    if group.owner_user_id and int(group.owner_user_id) == int(user_id):
        return True
    if channels.is_zalo_account(group.chat_id):
        return _zalo_account_member(db, user_id, group)
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
    from .purge import delete_in_batches

    days = int(days or settings.AGENT_GROUP_RETENTION_DAYS)
    #  ai-CR-139: xóa theo lô — một phát vài trăm nghìn dòng khóa bảng tin nhóm lâu.
    return delete_in_batches(db, AgentGroupMessage, AgentGroupMessage.sent_at < now_utc() - timedelta(days=days))


def private_chat_of(db: Session, user_id: int) -> str:
    """Chat riêng đang đăng nhập của một tài khoản ERP (để gửi kết quả riêng, không vào nhóm). Telegram trước, không có
    thì chat riêng Zalo của tài khoản công ty (ai-CR-122)."""
    ids = _tg_ids_of(db, user_id)
    if ids:
        return str(ids[0])
    uids = sorted(_zalo_uids_of(db, user_id))
    return channels.zalo_user_chat(uids[0]) if uids else ""


# ---------------------------------------------------------------------------
# Màn «Nhóm chat» trên ERP v2 (ai-CR-123)
# ---------------------------------------------------------------------------
CHANNEL_TELEGRAM = "telegram"
CHANNEL_ZALO_ACCOUNT = "zalo_account"
CHANNEL_ZALO_BOT = "zalo_bot"
CHANNEL_LABELS = {CHANNEL_TELEGRAM: "Telegram", CHANNEL_ZALO_ACCOUNT: "Zalo (tài khoản công ty)",
                  CHANNEL_ZALO_BOT: "Zalo (bot chính thức)"}
SOURCE_ASK = 1          # bản tóm tắt sinh ra khi người dùng hỏi bot / Trợ lý web
SOURCE_BUTTON = 2       # nút «Tóm tắt» trên màn nhóm
SUMMARY_TOOL = "read_group_messages"
PAGE_MAX = 200


def channel_of(group: AgentGroup) -> str:
    if channels.is_zalo_account(group.chat_id):
        return CHANNEL_ZALO_ACCOUNT
    if channels.is_zalo(group.chat_id):
        return CHANNEL_ZALO_BOT
    return CHANNEL_TELEGRAM


def is_viewer(db: Session, user_id: int, group: AgentGroup, *, manager: bool) -> bool:
    """Xem được nội dung nhóm trên web: thành viên (luật của bot) hoặc người có `agent_group.read`."""
    return bool(manager) or can_read(db, user_id, group)


def record_view(db: Session, group: AgentGroup, user_id: int, what: str, *, manager: bool) -> None:
    """Người quản lý mở nội dung nhóm mà họ KHÔNG phải thành viên → ghi một dòng nhật ký (đại ca chốt 08/10)."""
    from .model import AgentGroupView

    if manager and not can_read(db, user_id, group):
        db.add(AgentGroupView(group_id=group.id, user_id=int(user_id), what=str(what)[:40], created_by=int(user_id)))
        db.flush()


def _counts(db: Session, ids: list[int]) -> dict[int, tuple[int, int, datetime | None]]:
    """(số tin, số tệp, tin cuối) cho từng nhóm — một truy vấn."""
    from sqlalchemy import func

    if not ids:
        return {}
    rows = db.execute(select(AgentGroupMessage.group_id, func.count(AgentGroupMessage.id),
                             func.count(AgentGroupMessage.file), func.max(AgentGroupMessage.sent_at))
                      .where(AgentGroupMessage.group_id.in_(ids)).group_by(AgentGroupMessage.group_id)).all()
    return {int(g): (int(n or 0), int(f or 0), last) for g, n, f, last in rows}


def list_for_web(db: Session, user_id: int, *, manager: bool, scope: str = "mine", channel: str = "",
                 category: int | None = None, q: str = "", include_inactive: bool = False) -> list[dict]:
    """Danh sách nhóm cho màn web. `scope=all` chỉ có nghĩa với người quản lý; người thường luôn là nhóm của mình."""
    from .constants import GROUP_CATEGORY_LABELS

    stmt = select(AgentGroup).order_by(AgentGroup.id.desc())
    if not include_inactive:
        stmt = stmt.where(AgentGroup.active.is_(True))
    see_all = manager and scope == "all"
    key = fold(q or "")
    picked = []
    for g in db.scalars(stmt):
        if channel and channel_of(g) != channel:
            continue
        if category is not None and int(g.category or 0) != int(category):
            continue
        if key and key not in fold(g.title):
            continue
        member = can_read(db, user_id, g)
        if member or see_all:
            picked.append((g, member))
    counts = _counts(db, [g.id for g, _ in picked])
    out = []
    for g, member in picked:
        n, nf, last = counts.get(g.id, (0, 0, None))
        ch = channel_of(g)
        out.append({
            "id": g.id, "title": g.title, "channel": ch, "channel_label": CHANNEL_LABELS[ch],
            "category": int(g.category or 0), "category_label": GROUP_CATEGORY_LABELS.get(int(g.category or 0), "?"),
            "active": bool(g.active), "paused": bool(g.paused), "is_member": member,
            "is_owner": bool(g.owner_user_id and int(g.owner_user_id) == int(user_id)),
            "owner_user_id": int(g.owner_user_id or 0),
            "members_count": len(g.members) if g.members is not None else None,
            "message_count": n, "file_count": nf,
            "last_message_at": last.isoformat() if last else None,
            "joined_at": g.joined_at.isoformat() if g.joined_at else None,
        })
    return out


def _message_dict(r: AgentGroupMessage) -> dict:
    #  Màn web nhận giờ UTC trần (giao diện tự đổi sang giờ VN, `shared/utils/format-date.ts`) — đổi ở đây là lệch 7
    #  tiếng hai lần (gặp 08/10: tin 16:37 hiện 23:37).
    f = r.file or None
    return {"id": r.id, "from_name": r.from_name, "text": r.text,
            "sent_at": r.sent_at.isoformat() if r.sent_at else None,
            "file": ({"name": f.get("name"), "kind": f.get("kind"), "mime": f.get("mime") or "",
                      "size": int(f.get("size") or 0)} if f else None)}


def messages_page(db: Session, group: AgentGroup, *, before_id: int = 0, limit: int = 100, q: str = "",
                  files_only: bool = False) -> dict:
    """Tin của một nhóm, mới nhất trước, phân trang bằng `before_id`."""
    limit = max(1, min(int(limit or 100), PAGE_MAX))
    stmt = select(AgentGroupMessage).where(AgentGroupMessage.group_id == group.id)
    if before_id:
        stmt = stmt.where(AgentGroupMessage.id < int(before_id))
    if files_only:
        stmt = stmt.where(AgentGroupMessage.file.is_not(None))
    if q:
        stmt = stmt.where(AgentGroupMessage.text.contains(str(q)[:100]))
    rows = list(db.scalars(stmt.order_by(AgentGroupMessage.id.desc()).limit(limit + 1)))
    more = len(rows) > limit
    rows = rows[:limit]
    return {"items": [_message_dict(r) for r in rows], "has_more": more,
            "next_before_id": rows[-1].id if more and rows else None}


def save_summary(db: Session, group: AgentGroup, user_id: int, *, question: str, text: str, hours: int,
                 source: int) -> None:
    from .model import AgentGroupSummary

    if not (text or "").strip():
        return
    db.add(AgentGroupSummary(group_id=group.id, user_id=int(user_id or 0), source=int(source), hours=int(hours or 24),
                             question=str(question or "")[:500], text=str(text), created_by=int(user_id or 0)))
    db.flush()


def summaries(db: Session, group: AgentGroup, *, limit: int = 50) -> list[dict]:
    from .model import AgentGroupSummary

    rows = db.scalars(select(AgentGroupSummary).where(AgentGroupSummary.group_id == group.id)
                      .order_by(AgentGroupSummary.id.desc()).limit(max(1, min(int(limit), 200))))
    out = []
    for r in rows:
        when = r.created_at
        out.append({"id": r.id, "user_id": int(r.user_id or 0), "source": int(r.source or 1),
                    "hours": int(r.hours or 24), "question": r.question, "text": r.text,
                    "created_at": when.isoformat() if when else None})
    return out


def views(db: Session, group: AgentGroup, *, limit: int = 100) -> list[dict]:
    from .model import AgentGroupView

    rows = db.scalars(select(AgentGroupView).where(AgentGroupView.group_id == group.id)
                      .order_by(AgentGroupView.id.desc()).limit(max(1, min(int(limit), 500))))
    out = []
    for r in rows:
        when = r.created_at
        out.append({"id": r.id, "user_id": int(r.user_id or 0), "what": r.what,
                    "at": when.isoformat() if when else None})
    return out


def record_answers(db: Session, user, question: str, tool_calls: list[dict] | None, text: str) -> int:
    """Câu trả lời của bot / Trợ lý web có đọc nhóm (`read_group_messages`) → lưu làm bản tóm tắt của nhóm đó.
    Lỗi ở đây không bao giờ làm hỏng câu trả lời. Trả số bản đã lưu."""
    uid = int(getattr(user, "id", 0) or 0)
    if not uid or not (text or "").strip():
        return 0
    saved = 0
    seen: set[int] = set()
    for call in tool_calls or []:
        if not isinstance(call, dict) or call.get("name") != SUMMARY_TOOL:
            continue
        args = call.get("args") or {}
        try:
            g = find(db, uid, str(args.get("group") or ""))
            if g is None or g.id in seen:
                continue
            seen.add(g.id)
            save_summary(db, g, uid, question=question, text=text, hours=int(args.get("hours") or 24),
                         source=SOURCE_ASK)
            saved += 1
        except Exception:  # noqa: BLE001
            log.exception("agent_hub: không lưu được bản tóm tắt nhóm")
    return saved


SUMMARY_PROMPT = (
    "Dưới đây là tin nhắn của nhóm chat «{title}» trong {hours} giờ qua (mỗi dòng: [giờ] người gửi: nội dung). "
    "Viết bản tóm tắt tiếng Việt cho người bận: (1) các chủ đề chính, (2) việc / quyết định đã chốt, (3) ai hứa làm "
    "gì, hạn khi nào, (4) việc còn treo hoặc câu hỏi chưa ai trả lời, (5) tệp đáng chú ý. Ngắn gọn, gạch đầu dòng, "
    "chỉ dựa vào tin bên dưới, không bịa.\n\n{messages}{files}"
)


def summarize_now(db: Session, group: AgentGroup, user, *, hours: int = 24) -> dict:
    """Nút «Tóm tắt» trên màn nhóm: đọc tin trong `hours` giờ, nhờ model viết, lưu lại. Không qua công cụ (người quản
    lý không phải thành viên vẫn tóm tắt được nhóm họ được quyền xem)."""
    from app.modules.assistant import service as assistant_service

    data = read(db, group, hours=hours)
    if not data["messages"]:
        return {"text": "", "empty": True, "count": 0}
    files = ""
    if data["files"]:
        files = "\n\nTệp trong nhóm:\n" + "\n".join(f"- {f['name']} ({f['from']}, {f['at']})" for f in data["files"])
    prompt = SUMMARY_PROMPT.format(title=group.title, hours=hours, messages="\n".join(data["messages"]), files=files)
    result = assistant_service.ask(prompt)
    text = str(result.get("text") or "").strip()
    save_summary(db, group, int(getattr(user, "id", 0) or 0), question=f"Tóm tắt {hours} giờ qua (nút trên web)",
                 text=text, hours=hours, source=SOURCE_BUTTON)
    return {"text": text, "empty": False, "count": data["count"]}
