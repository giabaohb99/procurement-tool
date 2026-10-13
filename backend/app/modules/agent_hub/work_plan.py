"""Bot điều phối việc theo kế hoạch — phase 24.1 (bao-CR-616, `doc/agent-hub/18`).

Đợt 1 CHỈ ghi nhận việc trong phân hệ Dự án, chưa nối phân hệ nào khác. Tệp này có HAI LỚP, vì dịch vụ AI chạy tách
(phase 11) với DB riêng, không đọc thẳng bảng Dự án:

  * **Lớp ERP** (chạy trong ERP, mở qua cổng B `/api/agent-gw/plan/*`, gọi từ bot bằng `erp.plan_overview` /
    `erp.plan_reply`): `build` dựng một bảng Dự án (kế hoạch) → mỗi giai đoạn một cột kanban → việc cha → việc con,
    bằng đúng các hàm service của web (kiểm quyền thành viên như web); `overview` trả cây việc + người làm + tài khoản
    của họ; `reply` ghi câu trả lời của người làm (nhận / giờ khác / từ chối / xong / tiến độ) vào việc.
    Các ô của kế hoạch là TRƯỜNG TÙY BIẾN của bảng (không cột cứng, không migration): «Độ ưu tiên» có sẵn (P1/P2/P3),
    «Tiêu chí», «Nhận việc», «Tiến độ %», «Tự chấm (1-10)», «Ghi nhận». Sếp sửa ngay trên màn Dự án.
  * **Lớp bot** (chạy ở dịch vụ AI, chỉ đụng bảng của bot `AgentChatLink` / `AgentMessage` + Telegram):
    `ask_assignees` nhắn riêng từng người làm đã liên kết, mỗi việc một tin NHÂN DANH chủ kế hoạch, ba nút
    Nhận · Giờ khác · Từ chối; người chưa liên kết → ô «Nhận việc» = «Nhắn không được» và báo chủ.
    `handle_callback` / `handle_text` nhận nút / câu chữ, gọi `erp.plan_reply`, báo lại chủ kế hoạch.

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

log = logging.getLogger("app.agent_hub.work_plan")

FIELD_ACCEPT = "Nhận việc"
ACCEPT_NOT_ASKED, ACCEPT_YES, ACCEPT_LATER, ACCEPT_NO, ACCEPT_UNREACHABLE = (
    "Chưa hỏi", "Nhận", "Nhận giờ khác", "Từ chối", "Nhắn không được")
ACCEPT_OPTIONS = ((ACCEPT_NOT_ASKED, "slate"), (ACCEPT_YES, "green"), (ACCEPT_LATER, "orange"),
                  (ACCEPT_NO, "red"), (ACCEPT_UNREACHABLE, "slate"))
FIELD_CRITERIA, FIELD_PROGRESS, FIELD_SCORE, FIELD_NOTE = "Tiêu chí", "Tiến độ %", "Tự chấm (1-10)", "Ghi nhận"
PLAN_MARK = "[kế hoạch do bot lập]"       # đuôi mô tả bảng — để nhận ra bảng là kế hoạch

CB_YES, CB_LATER, CB_NO = "kh_ok", "kh_khac", "kh_tc"
CALLBACK_ACTIONS = frozenset({CB_YES, CB_LATER, CB_NO})
#  Hành động của `reply` (lớp ERP). Nút → hành động: kh_ok → accept, kh_khac → later, kh_tc → decline.
A_ACCEPT, A_LATER, A_DECLINE, A_NOTE, A_DONE, A_PROGRESS, A_UNREACHABLE = (
    "accept", "later", "decline", "note", "done", "progress", "unreachable")
_CB_TO_ACTION = {CB_YES: A_ACCEPT, CB_LATER: A_LATER, CB_NO: A_DECLINE}
MAX_ASK_PER_PERSON = 10
REPLY_WINDOW = timedelta(hours=48)


# ===========================================================================
# LỚP ERP — chạy trong ERP (embedded hoặc qua cổng B)
# ===========================================================================
def _fields(db: Session, list_id: int) -> dict:
    from app.modules.work.label_model import WorkLabelField

    return {f.name: f for f in db.query(WorkLabelField).filter(WorkLabelField.list_id == int(list_id))}


def ensure_fields(db: Session, actor, list_id: int) -> dict:
    """Tạo các trường của kế hoạch nếu bảng chưa có; trả {tên: WorkLabelField}."""
    from app.modules.work import list_config_service as cfg
    from app.modules.work.model import WorkLabelFieldType
    from app.modules.work.schema import LabelFieldIn, LabelOptionIn

    have = _fields(db, list_id)
    wanted = [(FIELD_ACCEPT, WorkLabelFieldType.SINGLE), (FIELD_CRITERIA, WorkLabelFieldType.TEXT),
              (FIELD_PROGRESS, WorkLabelFieldType.NUMBER), (FIELD_SCORE, WorkLabelFieldType.NUMBER),
              (FIELD_NOTE, WorkLabelFieldType.TEXT)]
    for i, (name, kind) in enumerate(wanted):
        if name in have:
            continue
        out = cfg.create_label_field(db, actor, list_id, LabelFieldIn(name=name, sort_order=10 + i, field_type=int(kind)))
        if name == FIELD_ACCEPT:
            for j, (opt, color) in enumerate(ACCEPT_OPTIONS):
                cfg.create_label_option(db, actor, int(out["id"]), LabelOptionIn(name=opt, color=color, sort_order=j))
    return _fields(db, list_id)


def _priority_field(fields: dict):
    return next((f for f in fields.values() if getattr(f, "system_key", "") == "priority"), None)


def _option(db: Session, field, name: str):
    """Giá trị của trường chọn theo tên (so khớp đầu chuỗi: «P1» khớp «P1 — Khẩn»)."""
    from app.modules.work.label_model import WorkLabelOption

    rows = db.query(WorkLabelOption).filter(WorkLabelOption.field_id == field.id).order_by(WorkLabelOption.sort_order).all()
    for o in rows:
        if o.name == name or o.name.startswith(name):
            return o
    return None


def _set(db: Session, field, task_id: int, value, user_id: int) -> None:
    from app.modules.work.label_value_service import write_value

    if field is None:
        return
    write_value(db, field, int(task_id), value, int(user_id))


def _set_option(db: Session, field, task_id: int, name: str, user_id: int) -> None:
    opt = _option(db, field, name) if field is not None else None
    if opt is not None:
        _set(db, field, task_id, opt.id, user_id)


def _label_text(db: Session, field, task_id: int) -> str:
    from app.modules.work.label_model import WorkLabelOption, WorkTaskLabel

    if field is None:
        return ""
    row = db.query(WorkTaskLabel).filter(WorkTaskLabel.task_id == int(task_id), WorkTaskLabel.field_id == field.id).first()
    if row is None:
        return ""
    if row.option_id:
        opt = db.get(WorkLabelOption, row.option_id)
        return opt.name if opt else ""
    if row.value_number is not None:
        s = format(row.value_number, "f")
        return s.rstrip("0").rstrip(".") if "." in s else s
    return row.value_text or ""


def build(db: Session, user, draft: dict) -> tuple[str, int]:
    """Tạo bảng + cột + việc cha / con + trường + thành viên. Trả (mã, id bảng). Ném HTTPException / ValueError như
    các hàm web (`draft_create.create` đổi thành DraftError)."""
    from app.modules.work import list_config_service as cfg
    from app.modules.work import list_service, task_service
    from app.modules.work.membership_service import require_employee, resolve_actor
    from app.modules.work.model import WorkListMember, WorkMemberRole
    from app.modules.work.schema import ListCreate, MemberIn, SectionIn, TaskCreate
    from app.modules.work.task_model import WorkSection
    from .plan_policy import PRIORITY_TO_OPTION

    actor = resolve_actor(db, user)
    require_employee(actor)
    title = " ".join(str(draft.get("title") or "").split())
    if not title:
        raise ValueError("kế hoạch phải có tên")
    phases = [p for p in (draft.get("phases") or []) if isinstance(p, dict) and p.get("tasks")]
    if not phases:
        raise ValueError("kế hoạch chưa có việc nào")
    desc = str(draft.get("description") or "").strip()
    if draft.get("deadline"):
        desc = (desc + f"\nHạn chót: {draft['deadline']}").strip()
    lst = list_service.create_list(db, actor, ListCreate(name=title[:200], description=(desc + "\n" + PLAN_MARK).strip()))
    list_id = int(lst["id"])

    #  Cột kanban = giai đoạn: đổi tên các cột mặc định, thiếu thì thêm, thừa thì bỏ.
    sections = (db.query(WorkSection).filter(WorkSection.list_id == list_id)
                .order_by(WorkSection.sort_order, WorkSection.id).all())
    section_ids: list[int] = []
    for i, ph in enumerate(phases):
        name = " ".join(str(ph.get("name") or "").split())[:100] or f"Giai đoạn {i + 1}"
        if i < len(sections):
            cfg.update_section(db, actor, sections[i].id, SectionIn(name=name, sort_order=i))
            section_ids.append(int(sections[i].id))
        else:
            out = cfg.create_section(db, actor, list_id, SectionIn(name=name, sort_order=i))
            section_ids.append(int(out["id"]))
    for extra in sections[len(phases):]:
        cfg.delete_section(db, actor, extra.id, None)

    fields = ensure_fields(db, actor, list_id)
    priority_field = _priority_field(fields)
    members = {m.employee_id for m in db.query(WorkListMember).filter(WorkListMember.list_id == list_id)}

    def _invite(people: list[dict]) -> list[int]:
        ids = []
        for p in people or []:
            eid = int(p.get("employee_id") or 0)
            if not eid:
                continue
            ids.append(eid)
            if eid not in members:
                list_service.add_member(db, actor, list_id, MemberIn(employee_id=eid, role=int(WorkMemberRole.MEMBER)))
                members.add(eid)
        return ids

    def _one(item: dict, section_id: int | None, parent_id: int | None) -> int:
        data = TaskCreate(list_id=list_id, section_id=section_id, parent_id=parent_id,
                          title=str(item.get("title") or "")[:500], description=str(item.get("description") or ""),
                          start_date=str(item.get("start_date") or "")[:10], due_date=str(item.get("due_date") or "")[:10],
                          assignee_ids=_invite(item.get("assignees") or []))
        tid = int(task_service.create_task(db, actor, data)["id"])
        _set_option(db, priority_field, tid, PRIORITY_TO_OPTION.get(str(item.get("priority") or ""), "P3"), actor.user_id)
        _set(db, fields.get(FIELD_CRITERIA), tid, "; ".join(str(c) for c in (item.get("criteria") or []))[:500], actor.user_id)
        _set_option(db, fields.get(FIELD_ACCEPT), tid, ACCEPT_NOT_ASKED, actor.user_id)
        return tid

    n_tasks = n_subs = 0
    for ph, sid in zip(phases, section_ids):
        for t in ph.get("tasks") or []:
            tid = _one(t, sid, None)
            n_tasks += 1
            for s in t.get("subtasks") or []:
                _one(s, None, tid)
                n_subs += 1
    db.commit()
    log.info("work_plan: tạo kế hoạch #%s «%s»: %s giai đoạn, %s việc, %s việc con", list_id, title, len(phases),
             n_tasks, n_subs)
    return f"kế hoạch #{list_id}", list_id


def details(db: Session, list_id: int) -> list[str]:
    """Dòng tóm tắt đọc lại từ DB cho tin «Đã tạo» (cùng khuôn `draft_create.created_details`)."""
    from app.modules.employee.model import Employee
    from app.modules.work.model import WorkList
    from app.modules.work.task_model import WorkSection, WorkTask, WorkTaskAssignee

    lst = db.get(WorkList, int(list_id))
    if lst is None:
        return []
    tasks = db.query(WorkTask).filter(WorkTask.list_id == lst.id, WorkTask.deleted_at.is_(None)).all()
    parents = [t for t in tasks if t.parent_id is None]
    sections = (db.query(WorkSection).filter(WorkSection.list_id == lst.id)
                .order_by(WorkSection.sort_order, WorkSection.id).all())
    people = {e for (e,) in db.query(WorkTaskAssignee.employee_id)
              .filter(WorkTaskAssignee.task_id.in_([t.id for t in tasks] or [-1])).distinct()}
    names = [e.full_name for e in db.query(Employee).filter(Employee.id.in_(people or [-1])).order_by(Employee.full_name)]
    return [f"Kế hoạch: {lst.name}", f"Giai đoạn: {' → '.join(s.name for s in sections)}",
            f"Việc: {len(parents)} việc cha, {len(tasks) - len(parents)} việc con",
            f"Người làm: {', '.join(names) or '(chưa giao ai)'}"]


def _users_of_employees(db: Session, employee_ids: set[int]) -> dict[int, list[int]]:
    from app.modules.user.model import User

    out: dict[int, list[int]] = {}
    if not employee_ids:
        return out
    for u in db.query(User).filter(User.employee_id.in_(employee_ids), User.is_active == True):  # noqa: E712
        out.setdefault(int(u.employee_id), []).append(int(u.id))
    return out


def _owner_member(db: Session, list_id: int):
    from app.modules.work.model import WorkListMember, WorkMemberRole

    return db.query(WorkListMember).filter(WorkListMember.list_id == int(list_id),
                                           WorkListMember.role == int(WorkMemberRole.OWNER)).first()


def overview(db: Session, user, list_id: int) -> dict:
    """Cây việc của kế hoạch cho lớp bot: bảng, chủ, từng việc kèm nhãn và người làm (có id tài khoản để tìm chat).
    Chỉ thành viên thấy bảng mới đọc được; ngoài ra trả `error`."""
    from app.modules.employee.model import Employee
    from app.modules.work.membership_service import resolve_actor, visible_list_ids
    from app.modules.work.model import WorkList
    from app.modules.work.task_model import WorkTask, WorkTaskAssignee

    lst = db.get(WorkList, int(list_id))
    if lst is None:
        return {"error": "không thấy kế hoạch"}
    actor = resolve_actor(db, user)
    if not actor.employee_id or lst.id not in visible_list_ids(db, actor.employee_id):
        return {"error": "anh/chị không ở trong bảng kế hoạch này"}
    fields = _fields(db, lst.id)
    pr = _priority_field(fields)
    tasks = (db.query(WorkTask).filter(WorkTask.list_id == lst.id, WorkTask.deleted_at.is_(None))
             .order_by(WorkTask.parent_id.is_(None).desc(), WorkTask.id).all())
    assign: dict[int, list[int]] = {}
    for a in db.query(WorkTaskAssignee).filter(WorkTaskAssignee.task_id.in_([t.id for t in tasks] or [-1])):
        assign.setdefault(int(a.task_id), []).append(int(a.employee_id))
    emp_ids = {e for v in assign.values() for e in v}
    owner = _owner_member(db, lst.id)
    if owner:
        emp_ids.add(int(owner.employee_id))
    names = {e.id: e.full_name for e in db.query(Employee).filter(Employee.id.in_(emp_ids or [-1]))}
    users = _users_of_employees(db, emp_ids)
    out_tasks = []
    for t in tasks:
        out_tasks.append({
            "id": t.id, "title": t.title, "parent_id": t.parent_id, "status": int(t.status),
            "start_date": t.start_date or "", "due_date": t.due_date or "", "description": (t.description or "")[:300],
            "priority": _label_text(db, pr, t.id), "criteria": _label_text(db, fields.get(FIELD_CRITERIA), t.id),
            "accept": _label_text(db, fields.get(FIELD_ACCEPT), t.id),
            "assignees": [{"employee_id": e, "name": names.get(e, f"#{e}"), "user_ids": users.get(e, [])}
                          for e in assign.get(t.id, [])]})
    oe = int(owner.employee_id) if owner else 0
    return {"id": lst.id, "name": lst.name,
            "owner": {"employee_id": oe, "name": names.get(oe, "chủ kế hoạch"), "user_ids": users.get(oe, [])},
            "tasks": out_tasks}


def reply(db: Session, user, task_id: int, action: str, text: str = "", pct: int | None = None,
          score: int | None = None) -> dict:
    """Ghi câu trả lời của người làm vào việc. `action` ∈ A_*. Người gọi phải là người được giao việc đó (hoặc chủ
    bảng với `unreachable`). Trả thông tin để lớp bot soạn tin; lỗi thì `error`."""
    from app.modules.employee.model import Employee
    from app.modules.work import task_service
    from app.modules.work.membership_service import resolve_actor
    from app.modules.work.model import WorkList, WorkTaskStatus
    from app.modules.work.schema import TaskUpdate
    from app.modules.work.task_model import WorkTask, WorkTaskAssignee

    t = db.get(WorkTask, int(task_id or 0)) if task_id else None
    if t is None or t.deleted_at is not None:
        return {"error": "không thấy việc"}
    eid = int(getattr(user, "employee_id", 0) or 0)
    owner = _owner_member(db, t.list_id)
    is_owner = owner is not None and int(owner.employee_id) == eid
    assigned = bool(db.query(WorkTaskAssignee).filter(WorkTaskAssignee.task_id == t.id,
                                                      WorkTaskAssignee.employee_id == eid).first())
    if action == A_UNREACHABLE:
        if not is_owner:
            return {"error": "chỉ chủ kế hoạch mới đánh dấu được"}
    elif not assigned:
        return {"error": "việc này không giao cho anh/chị"}
    lst = db.get(WorkList, t.list_id)
    fields = _fields(db, t.list_id)
    me = db.get(Employee, eid)
    oe = int(owner.employee_id) if owner else 0
    out = {"ok": True, "task_id": t.id, "title": t.title, "list_id": t.list_id, "list_name": lst.name if lst else "",
           "person": me.full_name if me else "Người làm", "kind": "",
           "owner_user_ids": _users_of_employees(db, {oe}).get(oe, []) if oe else []}
    uid = int(getattr(user, "id", 0) or 0)
    if action in (A_ACCEPT, A_LATER, A_DECLINE, A_UNREACHABLE):
        label = {A_ACCEPT: ACCEPT_YES, A_LATER: ACCEPT_LATER, A_DECLINE: ACCEPT_NO, A_UNREACHABLE: ACCEPT_UNREACHABLE}[action]
        _set_option(db, fields.get(FIELD_ACCEPT), t.id, label, uid)
        out["kind"] = label
    elif action == A_NOTE:
        _set(db, fields.get(FIELD_NOTE), t.id, f"{text}".strip()[:500], uid)
        out["kind"] = _label_text(db, fields.get(FIELD_ACCEPT), t.id)
    elif action == A_DONE:
        if t.status == int(WorkTaskStatus.DONE):
            return {**out, "already_done": True}
        task_service.update_task(db, resolve_actor(db, user), t.id, TaskUpdate(status=int(WorkTaskStatus.DONE)))
        _set(db, fields.get(FIELD_PROGRESS), t.id, 100, uid)
        if score is not None:
            _set(db, fields.get(FIELD_SCORE), t.id, max(0, min(int(score), 10)), uid)
        if text.strip():
            _set(db, fields.get(FIELD_NOTE), t.id, text.strip()[:500], uid)
        out["when"] = datetime.now().strftime("%H:%M %d/%m")
    elif action == A_PROGRESS:
        if pct is not None:
            out["pct"] = max(0, min(int(pct), 100))
            _set(db, fields.get(FIELD_PROGRESS), t.id, out["pct"], uid)
        if score is not None:
            out["score"] = max(0, min(int(score), 10))
            _set(db, fields.get(FIELD_SCORE), t.id, out["score"], uid)
        if text.strip():
            _set(db, fields.get(FIELD_NOTE), t.id, text.strip()[:500], uid)
    else:
        return {"error": f"hành động lạ: {action}"}
    db.commit()
    return out


# ===========================================================================
# LỚP BOT — chạy ở dịch vụ AI, chỉ đụng bảng của bot + Telegram, gọi ERP qua `erp`
# ===========================================================================
def summary_lines(draft: dict) -> list[str]:
    """Dòng tóm tắt bản nháp cho thẻ «BẢN NHÁP» trên Telegram (tối đa 8 việc cha, mỗi việc kèm số việc con)."""
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
            subs = f", {len(t.get('subtasks') or [])} việc con" if t.get("subtasks") else ""
            out.append(f"- {t.get('title', '')} ({who}{', ' + span if span else ''}, {t.get('priority', '')}{subs})")
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
    lines = [f"<b>Theo kế hoạch «{esc(plan_name)}» của {esc(owner)}</b>",
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
            _send(db, chat_id, f"… và {len(items) - MAX_ASK_PER_PERSON} việc nữa trong kế hoạch «{ov.get('name', '')}», "
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
        _reply(db, chat_id, f"Đã ghi: anh/chị <b>nhận</b> việc «{esc(title)}». Xong thì nhắn <code>xong việc {out['task_id']}</code>.")
        _notify_owner(db, out, f"{esc(out.get('person', ''))} đã <b>nhận</b> việc «{esc(title)}» "
                      f"(kế hoạch «{esc(out.get('list_name', ''))}»).", except_user=user.id)
        return
    telegram.answer_callback(cb_id, "Đã ghi, chờ anh/chị nhắn thêm")
    ask = ("Anh/chị làm được lúc nào? Nhắn giờ hoặc ngày (ví dụ «chiều mai», «15/10 sáng»)."
           if action == CB_LATER else "Lý do từ chối là gì? Nhắn một câu để em báo lại.")
    _send(db, chat_id, f"Đã ghi: <b>{esc(label)}</b> việc «{esc(title)}». {ask}", action=ACT_PLAN_ASK_WAIT,
          body={"task_id": out["task_id"], "list_id": out.get("list_id"), "kind": label, "user_id": user.id})


_DONE = re.compile(r"^(?:da |em |toi )?(?:lam )?(?:xong|hoan thanh|hoan tat)(?: roi)?(?: viec)?\s*#?(?P<id>\d+)\s*(?P<rest>.*)$")
_PROGRESS = re.compile(r"^(?:viec|task)\s*#?(?P<id>\d+)\b(?P<rest>.*)$")
_PCT = re.compile(r"(\d{1,3})\s*%")
_SCORE = re.compile(r"(\d{1,2})\s*(?:diem|/10)")


def handle_text(db: Session, chat_id: str, row: AgentMessage, text: str) -> bool:
    """Tin chữ của người làm: (1) giờ khác / lý do sau khi bấm nút · (2) «xong việc N …» · (3) «việc N 80% 7 điểm …»."""
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
                _reply(db, chat_id, f"Đã ghi lại cho việc «{esc(out['title'])}»: {esc(text.strip()[:200])}. Em báo chủ kế hoạch.")
                _notify_owner(db, out, f"{esc(out.get('person', ''))} — việc «{esc(out['title'])}»: "
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
            _reply(db, chat_id, f"Việc «{esc(out['title'])}» đã ghi xong từ trước rồi.")
            return True
        row.action = ACT_PLAN_REPLY
        db.commit()
        tail = f", tự chấm {sc.group(1)}/10" if sc else ""
        _reply(db, chat_id, f"Đã ghi <b>xong</b> việc «{esc(out['title'])}» lúc {out.get('when', '')}{tail}.")
        _notify_owner(db, out, f"{esc(out.get('person', ''))} đã <b>xong</b> việc «{esc(out['title'])}» lúc "
                      f"{out.get('when', '')}{tail}.", except_user=user.id)
        return True
    m = _PROGRESS.match(f)
    #  `fold` bỏ cả dấu % nên phần trăm bắt trên CÂU GỐC; «điểm» bắt trên bản bỏ dấu.
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
        _reply(db, chat_id, f"Đã ghi tiến độ việc «{esc(out['title'])}»: {esc(', '.join(bits))}.")
        _notify_owner(db, out, f"{esc(out.get('person', ''))} — việc «{esc(out['title'])}»: {esc(', '.join(bits))}"
                      + (f" — {esc(m.group('rest').strip()[:200])}" if m.group("rest").strip() else ""), except_user=user.id)
        return True
    return False
