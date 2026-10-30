"""Bot điều phối việc theo kế hoạch — phase 24.1 (bao-CR-616, `doc/agent-hub/18`) — LỚP BOT.

Đợt 1 CHỈ ghi nhận việc trong phân hệ Dự án, chưa nối phân hệ nào khác. Dịch vụ AI chạy tách (phase 11) với DB riêng,
không có bảng Dự án, nên tệp này CHỈ đụng bảng của bot (`AgentChatLink` / `AgentMessage`) + Telegram, và gọi ERP qua
`erp.plan_overview` / `erp.plan_reply` (cổng B `/api/agent-gw/plan/*`). Lớp ERP (dựng bảng, đọc cây việc, ghi câu trả
lời) nằm ở `modules/work/plan_service.py`; hằng dùng chung ở `plan_policy.py`.

  * `ask_assignees`: nhắn riêng từng người làm đã liên kết, mỗi việc một tin NHÂN DANH chủ kế hoạch, ba nút
    Nhận · Giờ khác · Từ chối; người chưa liên kết → ô "Nhận việc" = "Nhắn không được" và báo chủ.
  * `handle_callback` / `handle_text`: nhận nút / câu chữ, gọi `erp.plan_reply`, báo lại chủ kế hoạch.

Luật nới nguyên tắc trợ lý cá nhân (doc 18 §11): tin ở đây là tin NHÂN DANH chủ kế hoạch, không phải tin hệ thống; mọi
tin gửi người khác đều ghi sổ `AgentMessage` với `action` riêng để truy vết và tránh gửi trùng.
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from .constants import (ACT_COMMAND, ACT_PLAN_ASK, ACT_PLAN_ASK_WAIT, ACT_PLAN_NOTIFY, ACT_PLAN_REPLY, DIR_OUT,
                        NOTIFY_OFF)
from .model import AgentChatLink, AgentMessage
from .plan_policy import A_ACCEPT, A_DECLINE, A_DONE, A_LATER, A_NOTE, A_PROGRESS, A_UNREACHABLE

log = logging.getLogger("app.agent_hub.work_plan")

CB_YES, CB_LATER, CB_NO = "kh_ok", "kh_khac", "kh_tc"
CALLBACK_ACTIONS = frozenset({CB_YES, CB_LATER, CB_NO})
_CB_TO_ACTION = {CB_YES: A_ACCEPT, CB_LATER: A_LATER, CB_NO: A_DECLINE}
MAX_ASK_PER_PERSON = 10
REPLY_WINDOW = timedelta(hours=48)


def _crit_text(item: dict) -> str:
    return "; ".join(str(x) for x in (item.get("criteria") or []) if str(x).strip())[:160]


def summary_lines(draft: dict) -> list[str]:
    """Dòng tóm tắt bản nháp cho thẻ "BẢN NHÁP" trên Telegram: tối đa 8 việc cha, mỗi việc kèm người, hạn, ưu tiên, rồi
    các việc con (tên · hạn) và tiêu chí — để sếp duyệt phần bot tự nghĩ ra TRƯỚC khi tạo (sau thử dev 13/10)."""
    c = draft.get("counts") or {}
    out = [f"Kế hoạch: {draft.get('title', '')}",
           f"Quy mô: {c.get('phases', 0)} giai đoạn · {c.get('tasks', 0)} việc · {c.get('subtasks', 0)} việc con"]
    if draft.get("deadline"):
        out.append(f"Hạn chót: {draft['deadline']}")
    shown = 0
    for ph in draft.get("phases") or []:
        out.append(f"{ph.get('name', '')}:")
        for t in ph.get("tasks") or []:
            if shown >= 8:
                break
            who = ", ".join(p.get("name", "?") for p in t.get("assignees") or []) or "chưa giao"
            span = " → ".join(x for x in (t.get("start_date"), t.get("due_date")) if x)
            out.append(f"- {t.get('title', '')} ({who}{', ' + span if span else ''}, {t.get('priority', '')})")
            subs = [s for s in (t.get("subtasks") or []) if isinstance(s, dict)]
            for s in subs[:7]:
                due = f" · {_vn(s['due_date'])}" if s.get("due_date") else ""
                out.append(f"    + {s.get('title', '')}{due}")
            if _crit_text(t):
                out.append(f"    Tiêu chí: {_crit_text(t)}")
            shown += 1
    total = int(c.get("tasks") or 0)
    if total > shown:
        out.append(f"… và {total - shown} việc nữa (xem đủ sau khi tạo)")
    return out


def _chat_of_users(db: Session, user_ids: list[int], now: datetime | None = None) -> tuple[str, int]:
    """(chat Telegram riêng đang liên kết, user_id) của một trong các tài khoản; ("", 0) nếu chưa nối / đã tắt chuông."""
    now = now or datetime.now()
    for uid in user_ids or []:
        link = db.scalar(select(AgentChatLink).where(
            AgentChatLink.user_id == int(uid), AgentChatLink.chat_id != "", AgentChatLink.revoked_at.is_(None),
            AgentChatLink.expires_at > now).order_by(AgentChatLink.id.desc()).limit(1))
        if link is not None and int(link.notify_mode or NOTIFY_OFF) != NOTIFY_OFF:
            return str(link.chat_id), int(uid)
    return "", 0


def _send(db: Session, chat_id: str, text: str, *, action: str, body: dict | None = None,
          buttons: list[tuple[str, str]] | None = None) -> int:
    from . import telegram

    try:
        mid = telegram.send(text, chat_id=chat_id, buttons=buttons)
    except Exception as e:  # noqa: BLE001 — gửi hỏng vẫn ghi sổ, không làm hỏng việc đã tạo
        mid, text = 0, f"[KHÔNG GỬI ĐƯỢC: {e}] {text}"
    db.add(AgentMessage(task_id=0, direction=DIR_OUT, chat_id=chat_id, tg_message_id=mid,
                        body=json.dumps(body, ensure_ascii=False, default=str) if body else text, action=action))
    db.commit()
    return mid


def _vn(iso: str) -> str:
    try:
        d = datetime.strptime(str(iso)[:10], "%Y-%m-%d")
        return f"{d:%d/%m}"
    except ValueError:
        return str(iso or "")


def _task_card(task: dict, plan_name: str, owner: str) -> str:
    from . import telegram

    esc = telegram.esc
    span = " → ".join(_vn(x) for x in (task.get("start_date"), task.get("due_date")) if x) or "chưa đặt hạn"
    lines = [f"<b>Theo kế hoạch <i>{esc(plan_name)}</i> của {esc(owner)}</b>",
             f"Việc: <b>{esc(task['title'])}</b> (#{task['id']})",
             f"Thời gian: {esc(span)}" + (f" · {esc(task['priority'])}" if task.get("priority") else "")]
    if task.get("criteria"):
        lines.append(f"Tiêu chí: {esc(task['criteria'])}")
    if task.get("description"):
        lines.append(f"Ghi chú: {esc(task['description'][:300])}")
    lines.append("Anh/chị nhận việc này không? Bấm nút, hoặc nhắn lại bằng chữ.")
    return "\n".join(lines)


def ask_assignees(db: Session, owner_user, list_id: int) -> dict:
    """Nhắn từng người làm một tin cho mỗi việc (cha + con) của kế hoạch. Trả {asked, unreachable, tasks}."""
    from . import erp

    ov = erp.plan_overview(db, owner_user, int(list_id))
    if not isinstance(ov, dict) or ov.get("error"):
        raise RuntimeError(str((ov or {}).get("error") or "không đọc được kế hoạch"))
    owner = (ov.get("owner") or {}).get("name") or "chủ kế hoạch"
    by_person: dict[int, tuple[str, list[int], list[dict]]] = {}
    for t in ov.get("tasks") or []:
        for a in t.get("assignees") or []:
            eid = int(a.get("employee_id") or 0)
            entry = by_person.setdefault(eid, (a.get("name") or f"#{eid}", list(a.get("user_ids") or []), []))
            entry[2].append(t)
    asked, unreachable, n = [], [], 0
    for eid, (name, user_ids, items) in by_person.items():
        chat_id, uid = _chat_of_users(db, user_ids)
        if not chat_id:
            for t in items:
                erp.plan_reply(db, owner_user, int(t["id"]), A_UNREACHABLE)
            unreachable.append(name)
            continue
        for t in items[:MAX_ASK_PER_PERSON]:
            _send(db, chat_id, _task_card(t, ov.get("name") or "", owner), action=ACT_PLAN_ASK,
                  body={"task_id": t["id"], "list_id": ov["id"], "employee_id": eid, "user_id": uid, "title": t["title"]},
                  buttons=[("Nhận", f"{CB_YES}:{t['id']}"), ("Nhận nhưng giờ khác", f"{CB_LATER}:{t['id']}"),
                           ("Từ chối", f"{CB_NO}:{t['id']}")])
            n += 1
        if len(items) > MAX_ASK_PER_PERSON:
            _send(db, chat_id, f"… và {len(items) - MAX_ASK_PER_PERSON} việc nữa trong kế hoạch **{ov.get('name', '')}**, "
                  "xem ở phân hệ Dự án.", action=ACT_PLAN_ASK)
        asked.append(name)
    return {"asked": asked, "unreachable": unreachable, "tasks": n}


def ask_summary_text(out: dict) -> str:
    from . import telegram

    esc = telegram.esc
    parts = []
    if out.get("asked"):
        parts.append(f"Đã nhắn hỏi nhận việc ({out.get('tasks', 0)} việc) tới: {esc(', '.join(out['asked']))}.")
    if out.get("unreachable"):
        parts.append("Nhắn không được (chưa liên kết Telegram): " + esc(", ".join(out["unreachable"]))
                     + " — em đã đánh dấu trên việc, anh/chị báo họ giúp em.")
    if not parts:
        parts.append("Kế hoạch chưa giao ai nên em chưa nhắn hỏi ai.")
    return "\n".join(parts)


def _user_of_chat(db: Session, chat_id: str):
    from . import chat_link, erp

    link = chat_link.get_active_link(db, chat_id)
    return erp.user_by_id(db, link.user_id) if link is not None else None


def _notify_owner(db: Session, out: dict, text: str, *, except_user: int = 0) -> None:
    chat_id, uid = _chat_of_users(db, list(out.get("owner_user_ids") or []))
    if chat_id and uid != int(except_user or 0):
        _send(db, chat_id, text, action=ACT_PLAN_NOTIFY)


def _reply(db: Session, chat_id: str, text: str) -> None:
    _send(db, chat_id, text, action=ACT_PLAN_REPLY)


def handle_callback(db: Session, chat_id: str, cb_id: str, action: str, task_id: int) -> None:
    """Nút trên tin hỏi nhận việc: kh_ok · kh_khac · kh_tc."""
    from . import erp, telegram

    esc = telegram.esc
    user = _user_of_chat(db, chat_id)
    if user is None or action not in _CB_TO_ACTION:
        telegram.answer_callback(cb_id, "Chat này chưa đăng nhập ERP")
        return
    out = erp.plan_reply(db, user, int(task_id or 0), _CB_TO_ACTION[action])
    if not isinstance(out, dict) or out.get("error"):
        telegram.answer_callback(cb_id, str((out or {}).get("error") or "Không ghi được"))
        return
    title, label = out.get("title", ""), out.get("kind", "")
    if action == CB_YES:
        telegram.answer_callback(cb_id, "Đã ghi nhận")
        _reply(db, chat_id, f"Đã ghi: anh/chị <b>nhận</b> việc **{esc(title)}**. Xong thì nhắn <code>xong việc {out['task_id']}</code>.")
        _notify_owner(db, out, f"{esc(out.get('person', ''))} đã <b>nhận</b> việc **{esc(title)}** "
                      f"(kế hoạch **{esc(out.get('list_name', ''))}**).", except_user=user.id)
        return
    telegram.answer_callback(cb_id, "Đã ghi, chờ anh/chị nhắn thêm")
    ask = ("Anh/chị làm được lúc nào? Nhắn giờ hoặc ngày (ví dụ **chiều mai**, **15/10 sáng**)."
           if action == CB_LATER else "Lý do từ chối là gì? Nhắn một câu để em báo lại.")
    _send(db, chat_id, f"Đã ghi: <b>{esc(label)}</b> việc **{esc(title)}**. {ask}", action=ACT_PLAN_ASK_WAIT,
          body={"task_id": out["task_id"], "list_id": out.get("list_id"), "kind": label, "user_id": user.id})


_DONE = re.compile(r"^(?:da |em |toi )?(?:lam )?(?:xong|hoan thanh|hoan tat)(?: roi)?(?: viec)?\s*#?(?P<id>\d+)\s*(?P<rest>.*)$")
_PROGRESS = re.compile(r"^(?:viec|task)\s*#?(?P<id>\d+)\b(?P<rest>.*)$")
_PCT = re.compile(r"(\d{1,3})\s*%")
_SCORE = re.compile(r"(\d{1,2})\s*(?:diem|/10)")


def handle_text(db: Session, chat_id: str, row: AgentMessage, text: str) -> bool:
    """Tin chữ của người làm: (1) giờ khác / lý do sau khi bấm nút · (2) "xong việc N …" · (3) "việc N 80% 7 điểm …"."""
    from app.modules.assistant.glossary import fold
    from . import erp, telegram

    esc = telegram.esc
    user = _user_of_chat(db, chat_id)
    if user is None:
        return False
    #  (1) đang chờ giờ khác / lý do
    pending = db.scalar(select(AgentMessage).where(
        AgentMessage.chat_id == chat_id, AgentMessage.action == ACT_PLAN_ASK_WAIT, AgentMessage.id < row.id)
        .order_by(AgentMessage.id.desc()).limit(1))
    if pending is not None and not (row.created_at and pending.created_at
                                    and row.created_at - pending.created_at > REPLY_WINDOW):
        try:
            info = json.loads(pending.body or "{}")
        except ValueError:
            info = {}
        if int(info.get("user_id") or 0) == user.id:
            out = erp.plan_reply(db, user, int(info.get("task_id") or 0), A_NOTE,
                                 text=f"{info.get('kind', '')}: {text.strip()}")
            if isinstance(out, dict) and out.get("ok"):
                pending.action = ACT_COMMAND
                row.action = ACT_PLAN_REPLY
                db.commit()
                _reply(db, chat_id, f"Đã ghi lại cho việc **{esc(out['title'])}**: {esc(text.strip()[:200])}. Em báo chủ kế hoạch.")
                _notify_owner(db, out, f"{esc(out.get('person', ''))} — việc **{esc(out['title'])}**: "
                              f"<b>{esc(info.get('kind', ''))}</b> — {esc(text.strip()[:300])}", except_user=user.id)
                return True
    f = " ".join(fold(text).split())
    m = _DONE.match(f)
    if m:
        rest = m.group("rest").strip()
        sc = _SCORE.search(rest)
        out = erp.plan_reply(db, user, int(m.group("id")), A_DONE, text=text.strip() if rest else "",
                             score=int(sc.group(1)) if sc else None)
        row.action = ACT_COMMAND
        db.commit()
        if not isinstance(out, dict) or out.get("error"):
            _reply(db, chat_id, f"Việc #{m.group('id')}: {esc(str((out or {}).get('error') or 'không ghi được'))}.")
            return True
        if out.get("already_done"):
            _reply(db, chat_id, f"Việc **{esc(out['title'])}** đã ghi xong từ trước rồi.")
            return True
        row.action = ACT_PLAN_REPLY
        db.commit()
        tail = f", tự chấm {sc.group(1)}/10" if sc else ""
        _reply(db, chat_id, f"Đã ghi <b>xong</b> việc **{esc(out['title'])}** lúc {out.get('when', '')}{tail}.")
        _notify_owner(db, out, f"{esc(out.get('person', ''))} đã <b>xong</b> việc **{esc(out['title'])}** lúc "
                      f"{out.get('when', '')}{tail}.", except_user=user.id)
        return True
    m = _PROGRESS.match(f)
    #  `fold` bỏ cả dấu % nên phần trăm bắt trên CÂU GỐC; "điểm" bắt trên bản bỏ dấu.
    pct = _PCT.search(text) if m else None
    sc = _SCORE.search(m.group("rest")) if m else None
    if m and (pct or sc):
        out = erp.plan_reply(db, user, int(m.group("id")), A_PROGRESS, text=text.strip(),
                             pct=int(pct.group(1)) if pct else None, score=int(sc.group(1)) if sc else None)
        if not isinstance(out, dict) or out.get("error"):
            return False
        bits = ([f"{out['pct']}%"] if "pct" in out else []) + ([f"tự chấm {out['score']}/10"] if "score" in out else [])
        row.action = ACT_PLAN_REPLY
        db.commit()
        _reply(db, chat_id, f"Đã ghi tiến độ việc **{esc(out['title'])}**: {esc(', '.join(bits))}.")
        _notify_owner(db, out, f"{esc(out.get('person', ''))} — việc **{esc(out['title'])}**: {esc(', '.join(bits))}"
                      + (f" — {esc(m.group('rest').strip()[:200])}" if m.group("rest").strip() else ""), except_user=user.id)
        return True
    return False
