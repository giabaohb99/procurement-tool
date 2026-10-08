"""Việc + lịch rút từ biên bản họp → MỘT thẻ duyệt → việc ERP / thẻ cá nhân / lịch Google (ai-CR-114, phase 10 bước 10.3).

Đại ca chốt 07/10/2026: không tự tạo khi chưa duyệt; việc rút ra thì bot hỏi MỘT câu kèm danh sách dự án (Q9).

  1. Biên bản viết xong (`meetings._write`) → một lượt model đọc bản chép + biên bản, trả JSON việc (tên · người làm · hạn)
     và lịch hẹn (tên · giờ bắt đầu · độ dài · nơi). Ngày tương đối («thứ sáu», «tuần sau») tính theo ngày xử lý.
  2. Lưu vào `tab_agent_meeting.actions`, gửi một thẻ đánh số. Người gửi nhắn «tạo hết» / «tạo 1 3» (kèm «dự án 2» khi
     có nhiều dự án) hoặc «bỏ».
  3. Việc → phân hệ Dự án qua ĐÚNG đường «tạo» của nháp việc (`draft_create`, kiểm quyền work_task.create, báo chuông người
     được giao); người làm khớp đúng MỘT nhân sự thì gán, không thì ghi tên vào mô tả. Không có quyền / không ở dự án nào
     → thẻ cá nhân. Lịch → Google Calendar nếu đã nối Google, không thì thẻ cá nhân.
"""
from __future__ import annotations

import json
import logging
import re
from datetime import date, datetime, timedelta
from enum import IntEnum

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.assistant.provider.base import ChatMessage

from . import telegram
from .model import AgentMeeting, AgentMessage
from .timeutil import now_local

log = logging.getLogger("app.agent_hub.meeting_actions")

ACT_CARD = "bb_cho_tao"           # thẻ việc / lịch đang chờ người gửi duyệt
ACT_CARD_DONE = "bb_da_tao"
ACT_CARD_DROPPED = "bb_bo"
CARD_WINDOW = timedelta(hours=48)
MAX_TASKS = 15
MAX_EVENTS = 5
TITLE_MAX = 300
WEEKDAYS = ("thứ hai", "thứ ba", "thứ tư", "thứ năm", "thứ sáu", "thứ bảy", "chủ nhật")


class ActionState(IntEnum):
    PENDING = 1
    CREATED = 2
    SKIPPED = 3
    FAILED = 4


EXTRACT_SYSTEM = (
    "Bạn rút VIỆC CẦN LÀM và LỊCH HẸN từ một cuộc họp. Chỉ lấy điều có trong bản chép / biên bản, không bịa. Trả về DUY "
    "NHẤT một JSON: {\"tasks\": [{\"title\": \"việc, bắt đầu bằng động từ\", \"owner\": \"tên người làm như trong họp, "
    "không rõ thì rỗng\", \"due\": \"YYYY-MM-DD hoặc rỗng\"}], \"events\": [{\"title\": \"tên cuộc hẹn\", \"start\": "
    "\"YYYY-MM-DDTHH:MM\", \"minutes\": 60, \"location\": \"nơi hoặc rỗng\"}]}. Ngày tương đối («thứ sáu», «ngày mai», "
    "«tuần sau») tính theo NGÀY HỌP cho sẵn; không suy ra được ngày cụ thể thì để rỗng. Lịch hẹn chỉ lấy cuộc gặp / cuộc "
    "họp có ngày giờ rõ ràng; không có thì mảng rỗng."
)


# ---------------------------------------------------------------------------
# Rút việc + lịch
# ---------------------------------------------------------------------------
def _clean_date(value) -> str:
    s = str(value or "").strip()[:10]
    try:
        return date.fromisoformat(s).isoformat()
    except ValueError:
        return ""


def _clean_start(value) -> str:
    s = str(value or "").strip()[:16]
    try:
        return datetime.fromisoformat(s).strftime("%Y-%m-%dT%H:%M")
    except ValueError:
        return ""


def normalize(data: dict) -> list[dict]:
    """JSON của model → danh sách mục đánh số (việc trước, lịch sau). Bỏ mục thiếu tên / lịch thiếu giờ."""
    items: list[dict] = []
    for t in (data.get("tasks") or [])[:MAX_TASKS]:
        if not isinstance(t, dict):
            continue
        title = " ".join(str(t.get("title") or "").split())[:TITLE_MAX]
        if title:
            items.append({"kind": "task", "title": title, "owner": " ".join(str(t.get("owner") or "").split())[:80],
                          "due": _clean_date(t.get("due")), "state": int(ActionState.PENDING)})
    for e in (data.get("events") or [])[:MAX_EVENTS]:
        if not isinstance(e, dict):
            continue
        title, start = " ".join(str(e.get("title") or "").split())[:TITLE_MAX], _clean_start(e.get("start"))
        if title and start:
            try:
                minutes = max(15, min(int(e.get("minutes") or 60), 600))
            except (TypeError, ValueError):
                minutes = 60
            items.append({"kind": "event", "title": title, "start": start, "minutes": minutes,
                          "location": " ".join(str(e.get("location") or "").split())[:200],
                          "state": int(ActionState.PENDING)})
    for i, it in enumerate(items, 1):
        it["no"] = i
    return items


def extract(db: Session, row: AgentMeeting, *, today: date | None = None) -> list[dict]:
    """Một lượt model (bộ định tuyến khóa của người gửi). Hỏng thì [] — biên bản đã gửi, không chặn gì."""
    from . import manager

    day = today or (row.finished_at or now_local().replace(tzinfo=None)).date()
    content = (f"NGÀY HỌP: {WEEKDAYS[day.weekday()]} {day.isoformat()}\n\nBIÊN BẢN:\n{row.recap[:20000]}\n\n"
               f"BẢN CHÉP LỜI:\n{row.transcript[:60000]}")
    try:
        result = manager.get_provider().ask([ChatMessage(role="user", content=content)], system=EXTRACT_SYSTEM,
                                            max_tokens=8000, temperature=0.0)
        return normalize(manager.parse_json(result.text or ""))
    except Exception as e:  # noqa: BLE001 — rút việc hỏng không được làm hỏng phiên biên bản
        log.warning("agent_hub: rút việc từ biên bản %s hỏng: %s", row.id, str(e)[:200])
        return []


# ---------------------------------------------------------------------------
# Dự án + người làm
# ---------------------------------------------------------------------------
def projects_for(db: Session, user) -> list:
    """Dự án (danh sách việc) người gửi tạo việc được. Không quyền work_task.create / không ở dự án nào → []."""
    from app.core.auth import user_has_permission
    from app.modules.work.membership_service import resolve_actor, visible_list_ids
    from app.modules.work.model import WorkList

    if user is None or not user_has_permission(db, user, "work_task", "create"):
        return []
    actor = resolve_actor(db, user)
    if not actor.employee_id:
        return []
    ids = visible_list_ids(db, actor.employee_id)
    if not ids:
        return []
    return list(db.query(WorkList).filter(WorkList.id.in_(ids), WorkList.is_archived == 0).order_by(WorkList.name))


def match_employee(db: Session, name: str) -> dict | None:
    """Đúng MỘT nhân sự đang làm khớp tên / mã thì trả {employee_id, name, code}; mơ hồ hay không thấy → None."""
    from sqlalchemy import or_

    from app.modules.employee.model import Employee

    raw = " ".join((name or "").split())
    raw = re.sub(r"^(anh|chị|chi|em|cô|chú|bác|ông|bà|bạn|mr\.?|ms\.?)\s+", "", raw, flags=re.I)
    if len(raw) < 2:
        return None
    rows = db.query(Employee).filter(Employee.code == raw).all() or db.query(Employee).filter(
        or_(Employee.full_name.ilike(f"% {raw}"), Employee.full_name.ilike(raw))).limit(3).all()
    rows = [e for e in rows if getattr(e, "is_active", True) is not False]
    if len(rows) != 1:
        return None
    return {"employee_id": rows[0].id, "name": rows[0].full_name, "code": rows[0].code}


# ---------------------------------------------------------------------------
# Thẻ duyệt
# ---------------------------------------------------------------------------
def _fmt_day(iso: str) -> str:
    d = date.fromisoformat(iso[:10])
    return f"{WEEKDAYS[d.weekday()]} {d:%d/%m}"


def item_line(it: dict) -> str:
    done = " <i>(đã tạo)</i>" if it.get("state") == int(ActionState.CREATED) else ""
    return _item_line(it) + done


def _item_line(it: dict) -> str:
    esc = telegram.esc
    if it["kind"] == "task":
        bits = [esc(it["title"])]
        if it.get("owner"):
            bits.append(esc(it["owner"]))
        bits.append(f"hạn {_fmt_day(it['due'])}" if it.get("due") else "chưa có hạn")
        return f"{it['no']}. " + " — ".join(bits)
    st = datetime.fromisoformat(it["start"])
    where = f" — {esc(it['location'])}" if it.get("location") else ""
    return f"{it['no']}. {esc(it['title'])} — {st:%H:%M} {_fmt_day(it['start'])}{where}"


def card_text(row: AgentMeeting, items: list[dict], projects: list, google: bool) -> str:
    esc = telegram.esc
    tasks = [it for it in items if it["kind"] == "task"]
    events = [it for it in items if it["kind"] == "event"]
    lines = [f"<b>Việc và lịch rút từ biên bản «{esc(row.title)}»</b>"]
    if tasks:
        lines += ["", "<b>Việc</b>"] + [item_line(it) for it in tasks]
    if events:
        lines += ["", "<b>Lịch hẹn</b>"] + [item_line(it) for it in events]
    lines.append("")
    if tasks:
        if not projects:
            lines.append("Việc sẽ ghi vào thẻ cá nhân (tài khoản chưa tạo việc được ở phân hệ Dự án).")
        elif len(projects) == 1:
            lines.append(f"Việc sẽ vào dự án «{esc(projects[0].name)}».")
        else:
            opts = " · ".join(f"{i}) {esc(p.name)}" for i, p in enumerate(projects[:8], 1))
            lines.append(f"Việc vào dự án nào? {opts}")
    if events:
        lines.append("Lịch sẽ vào lịch Google của anh/chị." if google
                     else "Lịch sẽ ghi vào thẻ cá nhân (chưa nối Google: ERP → Trang cá nhân → «Nối Google»).")
    example = "«tạo hết dự án 1»" if tasks and len(projects) > 1 else "«tạo hết»"
    lines.append(f"Nhắn {example}, hoặc chọn mục «tạo 1 3», hoặc «bỏ» để thôi. Ngày tính theo hôm xử lý tệp.")
    return "\n".join(lines)


def offer(db: Session, row: AgentMeeting) -> int:
    """Rút việc + lịch rồi gửi thẻ duyệt. Trả số mục. Không có mục nào thì im lặng."""
    from app.modules.user.model import User

    from . import google_link, service

    existing = [dict(it) for it in (row.actions or [])]
    if existing:
        #  Đã rút rồi (gửi lại / viết lại theo mẫu khác): dùng lại, không tốn lượt model; hết mục chờ thì thôi.
        if not any(it.get("state") == int(ActionState.PENDING) for it in existing):
            return 0
        items = existing
    else:
        items = extract(db, row)
        if not items:
            return 0
        row.actions = items
    user = db.get(User, int(row.user_id or 0))
    projects = projects_for(db, user)
    google = google_link.get_link(db, row.user_id) is not None
    #  Thẻ mới thay thẻ cũ còn treo của chat này: «tạo hết» luôn nói về biên bản vừa nhận.
    for old in db.scalars(select(AgentMessage).where(AgentMessage.chat_id == row.chat_id, AgentMessage.action == ACT_CARD)):
        old.action = ACT_CARD_DROPPED
    db.commit()
    service.reply(db, row.chat_id, card_text(row, items, projects, google))
    service.log_message(db, service.DIR_OUT, row.chat_id, 0, json.dumps({"meeting_id": row.id}), action=ACT_CARD)
    db.commit()
    return len(items)


# ---------------------------------------------------------------------------
# Trả lời thẻ bằng chữ
# ---------------------------------------------------------------------------
#  ai-CR-118: nhận cả có dấu lẫn không dấu («tao het du an 2»).
_YES = re.compile(r"^\s*(?:(?:ok|[uừ]|[dđ][uư][oợ]c)[,!]?\s+)?(t[aạ]o|l[aà]m)\s*"
                  r"(h[eế]t|t[aấ]t\s*c[aả]|c[aả]|c[aá]c\s*m[uụ]c|lu[oô]n)?\b(.*)$", re.I | re.S)
_NO = re.compile(r"^\s*(b[oỏ]|kh[oô]ng\s+t[aạ]o|kh[oỏ]i\s+t[aạ]o|th[oô]i)(\s+(h[eế]t|[dđ]i|nh[eé]|c[aá]c\s*m[uụ]c))?\s*[.!]?\s*$",
                 re.I)
_PROJECT = re.compile(r"(?:d[uự]\s*[aá]n|project)\s*(?:s[oố]\s*)?(.+)$", re.I)


def pending_card(db: Session, chat_id: str, before_id: int) -> AgentMessage | None:
    """Thẻ việc / lịch đang chờ của chat — chỉ khi nó MỚI HƠN mọi nháp phiếu đang chờ (cùng chữ «tạo»)."""
    from .service import ACT_DRAFT_WAIT

    card = db.scalar(select(AgentMessage).where(AgentMessage.chat_id == chat_id, AgentMessage.action == ACT_CARD,
                                                AgentMessage.id < before_id).order_by(AgentMessage.id.desc()).limit(1))
    if card is None or (card.created_at and datetime.now() - card.created_at > CARD_WINDOW):
        return None
    draft = db.scalar(select(AgentMessage.id).where(AgentMessage.chat_id == chat_id, AgentMessage.action == ACT_DRAFT_WAIT,
                                                    AgentMessage.id > card.id).limit(1))
    return None if draft else card


def parse_reply(text: str, n_items: int) -> tuple[str, list[int], str] | None:
    """«tạo hết dự án 2» → ("yes", [1..n], "2"); «tạo 1 3» → ("yes", [1, 3], ""); «bỏ» → ("no", [], ""). Khác → None."""
    low = " ".join((text or "").split())
    if _NO.match(low):
        return "no", [], ""
    m = _YES.match(low)
    if not m:
        return None
    rest = m.group(3) or ""
    project = ""
    pm = _PROJECT.search(rest)
    if pm:
        project = pm.group(1).strip(" .,«»\"")
        rest = rest[:pm.start()]
    nums = sorted({int(x) for x in re.findall(r"\d+", rest) if 1 <= int(x) <= n_items})
    if re.sub(r"[\d,;.\s]|v[aà]|m[uụ]c|s[oố]", "", rest, flags=re.I).strip():
        return None                      # còn chữ lạ («tạo phiếu mua hàng…») → không phải trả lời thẻ
    if not nums and (m.group(2) or not rest.strip()):
        nums = list(range(1, n_items + 1))
    return ("yes", nums, project) if nums else None


def _pick_project(projects: list, want: str):
    if len(projects) == 1:
        return projects[0]
    if not want:
        return None
    if want.isdigit() and 1 <= int(want) <= min(len(projects), 8):
        return projects[int(want) - 1]
    hits = [p for p in projects if want.lower() in (p.name or "").lower()]
    return hits[0] if len(hits) == 1 else None


def handle_text(db: Session, chat_id: str, msg_row: AgentMessage, text: str) -> bool:
    from . import service

    card = pending_card(db, chat_id, msg_row.id)
    if card is None:
        return False
    try:
        meeting = db.get(AgentMeeting, int(json.loads(card.body or "{}").get("meeting_id") or 0))
    except ValueError:
        meeting = None
    items = list(meeting.actions or []) if meeting is not None else []
    parsed = parse_reply(text, len(items))
    if parsed is None:
        return False
    msg_row.action = service.ACT_COMMAND
    verdict, nums, want = parsed
    if verdict == "no":
        card.action = ACT_CARD_DROPPED
        db.commit()
        service.reply(db, chat_id, "Dạ, em không tạo việc / lịch nào từ biên bản này.")
        return True
    user = service._assistant_user(db, chat_id)
    if user is None or meeting is None or int(user.id) != int(meeting.user_id):
        card.action = ACT_CARD_DROPPED
        db.commit()
        service.reply(db, chat_id, "Tài khoản của chat này đã đổi so với lúc làm biên bản, em không tạo.")
        return True
    chosen = [it for it in items if it["no"] in nums and it.get("state") == int(ActionState.PENDING)]
    projects = projects_for(db, user)
    project = None
    if any(it["kind"] == "task" for it in chosen) and projects:
        project = _pick_project(projects, want)
        if project is None:
            opts = " · ".join(f"{i}) {telegram.esc(p.name)}" for i, p in enumerate(projects[:8], 1))
            db.commit()
            service.reply(db, chat_id, f"Việc vào dự án nào? {opts} — nhắn lại kèm «dự án số», vd «tạo hết dự án 1».")
            return True
    #  Chốt dấu TRƯỚC khi ghi: một lỗi giữa chừng không được để «tạo» lần hai tạo trùng.
    card.action = ACT_CARD_DONE
    db.commit()
    lines = create_items(db, user, meeting, chosen, project)
    meeting.actions = [dict(it) for it in items]       # gán lại để SQLAlchemy thấy JSON đổi
    db.commit()
    service.reply(db, chat_id, "\n".join(lines) if lines else "Không còn mục nào chờ tạo.")
    return True


# ---------------------------------------------------------------------------
# Tạo
# ---------------------------------------------------------------------------
def _when(iso: str, hour: int = 9) -> datetime | None:
    if not iso:
        return None
    try:
        dt = datetime.fromisoformat(iso)
    except ValueError:
        return None
    return dt if len(iso) > 10 else dt.replace(hour=hour)


def create_items(db: Session, user, meeting: AgentMeeting, chosen: list[dict], project) -> list[str]:
    from . import draft_create, google_link, personal_items

    esc = telegram.esc
    out: list[str] = []
    link = google_link.get_link(db, meeting.user_id)
    note = f"Từ biên bản họp «{meeting.title}» ({(meeting.finished_at or datetime.now()):%d/%m/%Y})."
    for it in chosen:
        try:
            if it["kind"] == "task" and project is not None:
                person = match_employee(db, it.get("owner") or "")
                desc = note + (f" Người làm nêu trong họp: {it['owner']}." if it.get("owner") and not person else "")
                draft = {"list_id": project.id, "list_name": project.name, "title": it["title"], "description": desc,
                         "due_date": it.get("due") or "", "start_date": "", "assignees": [person] if person else []}
                code, oid = draft_create.create(db, user, "work_task", draft)
                it["ref"] = {"type": "work_task", "id": oid}
                who = f" — giao {esc(person['name'])}" if person else ""
                out.append(f"{it['no']}. Đã tạo {esc(code)} ở dự án «{esc(project.name)}»{who}.")
            elif it["kind"] == "event" and link is not None:
                st = datetime.fromisoformat(it["start"])
                body = {"summary": it["title"], "description": note,
                        "start": {"dateTime": st.isoformat(), "timeZone": "Asia/Ho_Chi_Minh"},
                        "end": {"dateTime": (st + timedelta(minutes=int(it.get("minutes") or 60))).isoformat(),
                                "timeZone": "Asia/Ho_Chi_Minh"}}
                if it.get("location"):
                    body["location"] = it["location"]
                ev = google_link.api_post(db, link, f"{google_link.CALENDAR_URL}/calendars/primary/events", body)
                it["ref"] = {"type": "calendar", "id": str(ev.get("id") or "")}
                out.append(f"{it['no']}. Đã thêm vào lịch Google: {esc(it['title'])} {st:%H:%M %d/%m}.")
            else:
                title = it["title"] + (f" — {it['owner']}" if it.get("owner") else "")
                when = _when(it.get("start") or it.get("due") or "")
                res = personal_items.add(db, meeting.user_id, personal_items.ItemKind.SCHEDULE, title, when=when, note=note)
                if not res.get("ok", True):
                    raise ValueError(res.get("message") or "không ghi được thẻ")
                it["ref"] = {"type": "personal_item", "id": int(res.get("id") or res.get("item_id") or 0)}
                out.append(f"{it['no']}. Đã ghi thẻ cá nhân: {esc(title)}"
                           + (f" ({when:%H:%M %d/%m})." if when else "."))
            it["state"] = int(ActionState.CREATED)
            db.commit()
        except Exception as e:  # noqa: BLE001 — một mục hỏng không chặn các mục còn lại
            db.rollback()
            it["state"] = int(ActionState.FAILED)
            reason = str(e)[:200]
            log.warning("agent_hub: tạo mục %s từ biên bản %s hỏng: %s", it.get("no"), meeting.id, reason)
            out.append(f"{it['no']}. Chưa tạo được: {esc(reason)}")
    return out
