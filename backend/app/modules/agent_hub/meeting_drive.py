"""Thư mục «Họp» trên Google Drive → biên bản (ai-CR-116, phase 10 bước 10.4).

Đại ca 08/10/2026: *"họp xong, anh đưa file mới nhất lên thư mục họp trên Drive, thì em nhận thông tin và hỏi anh, hoặc anh
nói cần report cuộc họp mới nhất, em tìm và trả cho anh, kèm thông tin công việc trích xuất từ recap đó"*.

  - Vòng nền 5 phút (`agent.meeting_drive_scan`): với mỗi người đã nối Google + có chat riêng với bot, tìm tệp ghi âm /
    video MỚI trong thư mục tên «Họp» (scope drive.readonly). Lần đầu chỉ đặt mốc «từ bây giờ», không lôi tệp cũ ra hỏi.
  - Có tệp mới → HỎI (không tự chạy — tốn khóa AI của chính họ): «làm biên bản» (gộp mọi tệp thành MỘT cuộc họp, nối theo
    giờ tạo — họp ghi thành nhiều phần), «làm tệp 2» (chọn một / vài tệp — vd hai điện thoại cùng ghi một buổi thì chọn
    tệp rõ nhất), kèm tên mẫu nếu muốn («làm biên bản chính thức»), hoặc «bỏ qua».
  - «Report cuộc họp mới nhất» (tool `latest_meeting_report`): thư mục «Họp» có tệp mới hơn cuộc họp đã làm → làm luôn;
    không thì gửi lại biên bản + Word + thẻ việc / lịch của cuộc họp gần nhất.
"""
from __future__ import annotations

import json
import logging
import re
import time
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import chat_link, telegram
from .model import AgentChatLink, AgentCursor, AgentGoogleLink, AgentMeeting, AgentMessage
from .timeutil import to_local

log = logging.getLogger("app.agent_hub.meeting_drive")

FOLDER_NAME = "Họp"
DRIVE_URL = "https://www.googleapis.com/drive/v3/files"
FOLDER_MIME = "application/vnd.google-apps.folder"
CURSOR_PREFIX = "drive_hop:"
ACT_ASK = "hop_moi_cho"            # thẻ «có tệp họp mới» đang chờ trả lời
ACT_ASK_DONE = "hop_moi_lam"
ACT_ASK_DROPPED = "hop_moi_bo"
ASK_WINDOW = timedelta(hours=48)
MAX_FILES = 8
_FOLDER_CACHE: dict[int, tuple[float, list[str]]] = {}
FOLDER_TTL = 600


# ---------------------------------------------------------------------------
# Drive
# ---------------------------------------------------------------------------
def folder_ids(db: Session, link: AgentGoogleLink) -> list[str]:
    """Id các thư mục tên «Họp» (không phân biệt hoa thường do Drive so khớp chính xác tên → thử hai dạng)."""
    from . import google_link

    hit = _FOLDER_CACHE.get(int(link.id or 0))
    if hit and time.monotonic() - hit[0] < FOLDER_TTL:
        return hit[1]
    ids: list[str] = []
    for name in (FOLDER_NAME, FOLDER_NAME.upper(), FOLDER_NAME.lower()):
        data = google_link.api_get(db, link, DRIVE_URL, {
            "q": f"name = '{name}' and mimeType = '{FOLDER_MIME}' and trashed = false",
            "fields": "files(id)", "pageSize": 10, "supportsAllDrives": "true", "includeItemsFromAllDrives": "true"})
        ids += [str(f["id"]) for f in data.get("files") or [] if f.get("id") and str(f["id"]) not in ids]
    _FOLDER_CACHE[int(link.id or 0)] = (time.monotonic(), ids)
    return ids


#  ai-CR-116 (đại ca 08/10 thả một tệp PDF vào «Họp» rồi chờ — bot chỉ nhìn ghi âm nên im lặng): tài liệu trong thư mục
#  «Họp» (tài liệu họp, báo cáo) cũng được báo, kèm lựa chọn «tóm tắt tệp n».
DOC_MIMES = (
    "application/pdf", "application/msword", "text/plain",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.google-apps.document", "application/vnd.google-apps.spreadsheet",
    "application/vnd.google-apps.presentation",
)
MAX_DOCS = 3


def is_media(f: dict) -> bool:
    return str(f.get("mimeType") or f.get("mime") or "").startswith(("audio/", "video/"))


def media_files(db: Session, link: AgentGoogleLink, *, since: datetime | None = None, limit: int = 20,
                with_docs: bool = False) -> list[dict]:
    """Tệp ghi âm / video (và tài liệu khi `with_docs`) trong thư mục «Họp», mới nhất trước. `since` (UTC) = chỉ tệp tạo
    SAU mốc đó."""
    from . import google_link

    folders = folder_ids(db, link)
    if not folders:
        return []
    parents = " or ".join(f"'{f}' in parents" for f in folders)
    kinds = ["mimeType contains 'audio/'", "mimeType contains 'video/'"]
    if with_docs:
        kinds += [f"mimeType = '{m}'" for m in DOC_MIMES]
    q = f"({parents}) and trashed = false and ({' or '.join(kinds)})"
    if since is not None:
        q += f" and createdTime > '{since.strftime('%Y-%m-%dT%H:%M:%S')}'"
    data = google_link.api_get(db, link, DRIVE_URL, {
        "q": q, "orderBy": "createdTime desc", "pageSize": limit, "supportsAllDrives": "true",
        "includeItemsFromAllDrives": "true",
        "fields": "files(id,name,mimeType,size,createdTime,videoMediaMetadata(durationMillis))"})
    return [f for f in data.get("files") or [] if f.get("id")]


def _created(f: dict) -> datetime | None:
    try:
        return datetime.fromisoformat(str(f.get("createdTime") or "").replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def _minutes(f: dict) -> int:
    ms = int(((f.get("videoMediaMetadata") or {}).get("durationMillis")) or 0)
    return ms // 60000


def processed_ids(db: Session, user_id: int) -> set[str]:
    out: set[str] = set()
    for ref in db.scalars(select(AgentMeeting.source_ref).where(AgentMeeting.user_id == int(user_id),
                                                               AgentMeeting.source_kind == 2)):
        out.update(x.strip() for x in str(ref or "").split(",") if x.strip())
    return out


# ---------------------------------------------------------------------------
# Hỏi khi có tệp mới
# ---------------------------------------------------------------------------
def private_chat(db: Session, user_id: int) -> str:
    """Chat riêng đang đăng nhập của tài khoản (Telegram trước, rồi tới kênh khác)."""
    rows = list(db.scalars(select(AgentChatLink.chat_id).where(AgentChatLink.user_id == int(user_id),
                                                               AgentChatLink.revoked_at.is_(None))))
    rows.sort(key=lambda c: (not str(c).isdigit(), str(c)))
    return str(rows[0]) if rows else ""


def _fmt_file(i: int, f: dict) -> str:
    created = _created(f)
    bits = []
    if _minutes(f):
        bits.append(f"{_minutes(f)} phút")
    if created:
        bits.append(f"{to_local(created):%H:%M %d/%m}")
    return f"{i}) {telegram.esc(str(f.get('name') or 'tệp'))}" + (f" ({', '.join(bits)})" if bits else "")


def ask(db: Session, chat_id: str, files: list[dict], *, intro: str = "") -> None:
    from . import service

    #  Một dãy số chung: ghi âm / video trước (theo giờ tạo), tài liệu sau.
    media = sorted([f for f in files if is_media(f)], key=lambda f: str(f.get("createdTime") or ""))[:MAX_FILES]
    docs = sorted([f for f in files if not is_media(f)], key=lambda f: str(f.get("createdTime") or ""))[:MAX_FILES]
    files = media + docs
    lines = [intro or f"Có {len(files)} tệp mới trong thư mục «{FOLDER_NAME}» trên Drive:"]
    if media and docs:
        lines.append("<b>Ghi âm / video</b>")
    lines += [_fmt_file(i, f) for i, f in enumerate(media, 1)]
    if docs:
        lines.append("<b>Tài liệu</b>")
        lines += [_fmt_file(i, f) for i, f in enumerate(docs, len(media) + 1)]
    lines.append("")
    if len(media) > 1:
        lines.append("Nhắn «làm biên bản» để em gộp các ghi âm thành MỘT cuộc họp (nối theo giờ tạo), hoặc «làm tệp 1» nếu "
                     "chỉ cần một tệp (vd hai máy cùng ghi một buổi thì chọn tệp rõ nhất).")
    elif media:
        lines.append("Nhắn «làm biên bản» để em làm biên bản (thêm tên mẫu nếu muốn, vd «làm biên bản chính thức»).")
    if docs:
        first_doc = len(media) + 1
        lines.append(f"Tài liệu: nhắn «tóm tắt tệp {first_doc}», hoặc hỏi thẳng «phân tích tệp {first_doc} …».")
    lines.append("«bỏ qua» nếu không cần.")
    for old in db.scalars(select(AgentMessage).where(AgentMessage.chat_id == chat_id, AgentMessage.action == ACT_ASK)):
        old.action = ACT_ASK_DROPPED
    db.commit()
    service.reply(db, chat_id, "\n".join(lines))
    service.log_message(db, service.DIR_OUT, chat_id, 0,
                        json.dumps({"files": [{"id": f["id"], "name": f.get("name", ""), "mime": f.get("mimeType", "")}
                                              for f in files]},
                                   ensure_ascii=False), action=ACT_ASK)
    db.commit()


def _cursor(db: Session, user_id: int) -> AgentCursor:
    name = f"{CURSOR_PREFIX}{int(user_id)}"
    row = db.scalar(select(AgentCursor).where(AgentCursor.name == name))
    if row is None:
        row = AgentCursor(name=name, value=0)
        db.add(row)
        db.flush()
    return row


def scan(db: Session, *, now: datetime | None = None) -> int:
    """Một vòng quét mọi người đã nối Google. Trả số thẻ hỏi đã gửi."""
    from . import google_link

    now = now or datetime.utcnow()
    asked = 0
    for link in db.scalars(select(AgentGoogleLink).where(AgentGoogleLink.revoked_at.is_(None))):
        chat = private_chat(db, link.user_id)
        if not chat:
            continue
        cur = _cursor(db, link.user_id)
        if not cur.value:
            cur.value = int(now.timestamp())           # lần đầu: chỉ theo dõi từ bây giờ
            db.commit()
            continue
        try:
            files = media_files(db, link, since=datetime.utcfromtimestamp(cur.value), with_docs=True)
        except google_link.GoogleError as e:
            log.info("agent_hub: quét thư mục Họp của user %s hỏng: %s", link.user_id, e)
            continue
        done = processed_ids(db, link.user_id)
        fresh = [f for f in files if f["id"] not in done]
        newest = max((_created(f) for f in files if _created(f)), default=None)
        if newest is not None:
            cur.value = max(cur.value, int(newest.timestamp()) + 1)
        db.commit()
        if fresh:
            ask(db, chat, fresh)
            asked += 1
    return asked


# ---------------------------------------------------------------------------
# Trả lời thẻ
# ---------------------------------------------------------------------------
_YES = re.compile(r"^\s*(?:(?:ok|[uừ]|[dđ][uư][oợ]c|c[oó])[,!]?\s+)?"
                  r"(l[aà]m|g[oộ]p|t[oó]m\s*t[aắ]t|[dđ][oọ]c|ph[aâ]n\s*t[ií]ch)\b(.*)$", re.I | re.S)
#  Động từ hỏi về TÀI LIỆU, tra theo dạng không dấu (`fold`).
_DOC_VERBS = {"tom tat": "tóm tắt", "doc": "đọc", "phan tich": "phân tích"}
#  Sau «làm / gộp» chỉ nhận các chữ này đứng đầu — «làm sao để…», «làm ơn tra giá…» không phải trả lời thẻ.
_YES_NEXT = ("bien", "recap", "tep", "di", "luon", "het", "nhe", "giup", "ca", "theo", "mau", "bao", "ngay")
_NO = re.compile(r"^\s*(b[oỏ]\s+qua|b[oỏ]|kh[oô]ng\s+c[aầ]n|kh[oô]ng|th[oô]i)(\s+(nh[eé]|[dđ]i|h[eế]t))?\s*[.!]?\s*$", re.I)
_FILLER = re.compile(r"(?<!\w)(bi[eê]n\s+b[aả]n|recap|t[eệ]p|[dđ]i|lu[oô]n|nh[eé]|gi[uú]p(\s+em)?|h[eế]t|c[aả]|ngay)(?!\w)", re.I)
_PICK = re.compile(r"t[eệ]p\s+((?:\d+\s*(?:,|v[aà]|\s)\s*)*\d+)", re.I)


def pending_ask(db: Session, chat_id: str, before_id: int) -> AgentMessage | None:
    row = db.scalar(select(AgentMessage).where(AgentMessage.chat_id == chat_id, AgentMessage.action == ACT_ASK,
                                               AgentMessage.id < before_id).order_by(AgentMessage.id.desc()).limit(1))
    if row is None or (row.created_at and datetime.now() - row.created_at > ASK_WINDOW):
        return None
    #  Thẻ khác cùng chữ «làm / tạo / bỏ» mới hơn (nháp phiếu, thẻ việc biên bản) thì nhường.
    from .meeting_actions import ACT_CARD
    from .service import ACT_DRAFT_WAIT

    newer = db.scalar(select(AgentMessage.id).where(AgentMessage.chat_id == chat_id,
                                                    AgentMessage.action.in_((ACT_DRAFT_WAIT, ACT_CARD)),
                                                    AgentMessage.id > row.id).limit(1))
    return None if newer else row


def parse_reply(text: str, n_files: int) -> tuple[str, list[int], str] | None:
    """(«yes»|«doc»|«no», số tệp chọn (rỗng = tất cả), phần chữ còn lại — tên mẫu, hoặc câu hỏi về tài liệu).
    Không phải trả lời thẻ → None. «tóm tắt / đọc / phân tích» = hỏi về TÀI LIỆU."""
    low = " ".join((text or "").split())
    if _NO.match(low):
        return "no", [], ""
    m = _YES.match(low)
    if not m:
        return None
    from app.modules.assistant.glossary import fold

    verb = fold(m.group(1))
    rest = m.group(2) or ""
    first = fold(rest.strip().split(" ")[0]) if rest.strip() else ""
    if first and first not in _YES_NEXT:
        return None
    picks = []
    pm = _PICK.search(rest)
    if pm:
        picks = sorted({int(x) for x in re.findall(r"\d+", pm.group(1)) if 1 <= int(x) <= n_files})
        if not picks:
            return None
        rest = rest[:pm.start()] + rest[pm.end():]
    #  Bỏ chữ đệm còn sót («tệp», «đi», «luôn», «giúp em»…) để phần còn lại chỉ là tên mẫu hoặc câu hỏi.
    rest = " ".join(_FILLER.sub(" ", rest).split())
    if verb in _DOC_VERBS:
        return "doc", picks, (f"{_DOC_VERBS[verb]} {rest.strip()}".strip() if rest.strip() else "")
    return "yes", picks, rest.strip()


def handle_text(db: Session, chat_id: str, msg_row: AgentMessage, text: str) -> bool:
    from . import meetings, service

    if meetings.retry_by_text(db, chat_id, msg_row, text):     # ai-CR-162: «thử lại biên bản»
        return True
    if meetings.speakers_by_text(db, chat_id, msg_row, text):  # ai-CR-164: «Người 1 = Ngân, Người 3 = Phú»
        return True
    card = pending_ask(db, chat_id, msg_row.id)
    if card is None:
        return False
    try:
        files = list(json.loads(card.body or "{}").get("files") or [])
    except ValueError:
        files = []
    parsed = parse_reply(text, len(files))
    if parsed is None or not files:
        return False
    msg_row.action = service.ACT_COMMAND
    verdict, picks, rest = parsed
    if verdict == "no":
        card.action = ACT_ASK_DROPPED
        db.commit()
        service.reply(db, chat_id, "Dạ, em bỏ qua tệp họp này.")
        return True
    link = chat_link.get_active_link(db, chat_id)
    if link is None:
        card.action = ACT_ASK_DROPPED
        db.commit()
        service.reply(db, chat_id, "Chat này đã đăng xuất ERP, em không làm biên bản.")
        return True
    chosen = [files[i - 1] for i in picks] if picks else files
    if verdict == "doc":
        docs = [f for f in chosen if not is_media(f)]
        if not docs:
            db.commit()
            service.reply(db, chat_id, "Tệp đó là ghi âm / video — nhắn «làm biên bản» để em làm biên bản.")
            return True
        db.commit()
        read_docs(db, int(link.user_id), chat_id, docs[:MAX_DOCS], rest)
        return True
    media = [f for f in chosen if is_media(f)]
    if not media:
        db.commit()
        service.reply(db, chat_id, "Không có tệp ghi âm / video nào để làm biên bản — tài liệu thì nhắn «tóm tắt tệp n».")
        return True
    card.action = ACT_ASK_DONE
    db.commit()
    start(db, int(link.user_id), chat_id, media, rest)
    return True


def read_docs(db: Session, user_id: int, chat_id: str, docs: list[dict], question: str = "") -> None:
    """Đọc tài liệu trong thư mục «Họp» (pdf / Word / Excel / Google Docs) rồi trả lời — mặc định tóm tắt."""
    from . import google_link, service

    link = google_link.get_link(db, user_id)
    if link is None:
        service.reply(db, chat_id, "Chat này chưa nối Google nên em chưa mở được tệp trên Drive.")
        return
    q = question.strip() or service.DOC_DEFAULT_QUESTION
    for f in docs:
        name = str(f.get("name") or "tệp")
        try:
            text = google_link.export_text(db, link, str(f["id"]), str(f.get("mime") or f.get("mimeType") or ""),
                                           max_chars=60_000)
        except google_link.GoogleError as e:
            service.reply(db, chat_id, f"Em chưa đọc được «{telegram.esc(name)}»: {telegram.esc(str(e))}")
            continue
        row = service.log_message(db, service.DIR_IN, chat_id, 0, f"[Drive «{name}»] {q}"[:4000], action=service.ACT_ASKED)
        db.commit()
        service.answer_question(db, chat_id, f"{q}\n\n{service.DOC_GUIDE}\n\nNỘI DUNG TỆP «{name}»:\n{text}",
                                before_id=row.id, kind="document")


def start(db: Session, user_id: int, chat_id: str, files: list[dict], text: str = "") -> AgentMeeting:
    """Tạo một phiên biên bản từ các tệp Drive (nối theo thứ tự đưa vào) và giao chạy nền."""
    from . import meetings, service

    tpl = meetings.resolve_template(db, user_id, text)
    ref = ",".join(str(f["id"]) for f in files[:meetings.MAX_PARTS])
    title = re.sub(r"\.[A-Za-z0-9]{2,4}$", "", str(files[0].get("name") or "Cuộc họp"))[:200]
    row = meetings.create(db, user_id=user_id, chat_id=chat_id, kind=meetings.SourceKind.DRIVE, ref=ref, title=title,
                          template=tpl)
    db.commit()
    more = f", gộp {len(files)} tệp" if len(files) > 1 else ""
    service.reply(db, chat_id, f"Em nhận rồi, đang làm biên bản «{telegram.esc(title)}» ({tpl.label.lower()}{more}). "
                               "Họp một giờ mất khoảng 3–5 phút; xong em gửi biên bản, tệp Word và thẻ việc / lịch.")
    db.commit()
    try:
        meetings.dispatch(row.id)
    except Exception:  # noqa: BLE001 — broker hỏng thì chạy tại chỗ còn hơn mất việc
        log.exception("agent_hub: giao biên bản Drive hỏng, chạy tại chỗ")
        meetings.process(db, row.id)
    return row


# ---------------------------------------------------------------------------
# «Report cuộc họp mới nhất»
# ---------------------------------------------------------------------------
def latest_report(db: Session, user_id: int, chat_id: str, text: str = "") -> dict:
    """Tệp mới nhất trong «Họp» chưa làm → làm luôn; không thì gửi lại cuộc họp gần nhất đã làm."""
    from . import google_link, meetings

    last = next(iter(meetings.recent(db, user_id, 1)), None)
    link = google_link.get_link(db, user_id)
    newest = None
    if link is not None:
        try:
            files = media_files(db, link, limit=5)
        except google_link.GoogleError as e:
            files = []
            log.info("agent_hub: đọc thư mục Họp hỏng: %s", e)
        done = processed_ids(db, user_id)
        newest = next((f for f in files if f["id"] not in done), None)
        created = _created(newest) if newest is not None else None
        if created is not None and last is not None and last.created_at and to_local(created) < last.created_at:
            newest = None                                 # tệp chưa làm nhưng CŨ hơn cuộc họp gần nhất đã làm
    if newest is not None:
        row = start(db, user_id, chat_id, [newest], text)
        return {"started": True, "meeting": row.title,
                "message": f"Thư mục «{FOLDER_NAME}» có tệp mới «{row.title}», em đang làm biên bản, xong gửi kèm Word và "
                           "thẻ việc / lịch."}
    if last is None:
        hint = ("Chưa nối Google — nối ở ERP → Trang cá nhân → «Nối Google» để em đọc thư mục «Họp»." if link is None
                else f"Thư mục «{FOLDER_NAME}» trên Drive chưa có tệp ghi âm / video nào.")
        return {"error": "chưa có cuộc họp nào", "hint": hint}
    if last.status != int(meetings.MeetingStatus.DONE):
        return {"started": True, "meeting": last.title,
                "message": f"Biên bản «{last.title}» đang được làm, xong em gửi ngay."}
    meetings.resend(db, last)
    return {"sent": True, "meeting": last.title,
            "message": "Đã gửi lại biên bản, tệp Word và thẻ việc / lịch (nếu còn mục chờ) vào chat riêng. Chỉ cần báo "
                       "ngắn là đã gửi, KHÔNG chép lại nội dung biên bản."}
