"""Kế hoạch việc do bot lập — LỚP ERP (bao-CR-616, phase 24.1, `doc/agent-hub/18`).

Tệp này chạy TRONG ERP (cùng DB với bảng Dự án). Phía bot (`agent_hub/work_plan.py`) chạy ở dịch vụ AI tách, DB riêng,
nên KHÔNG import tệp này; bot gọi qua `agent_hub/erp.py` (`plan_overview` / `plan_reply`) → cổng B
`/api/agent-gw/plan/*` → đây. Tách khỏi `agent_hub/work_plan.py` ngày 13/10/2026 sau khi bài canh ranh giới
`test_agent_hub_ranh_gioi_erp.py` bắt lỗi import thẳng bảng Dự án từ phía bot.

  * `build`: dựng một bảng Dự án (kế hoạch) → mỗi giai đoạn một cột kanban → việc cha → việc con, bằng đúng các hàm
    service của web (kiểm quyền thành viên như web). Các ô của kế hoạch là TRƯỜNG TÙY BIẾN của bảng (không cột cứng,
    không migration): «Độ ưu tiên» có sẵn (P1/P2/P3), «Tiêu chí», «Nhận việc», «Tiến độ %», «Tự chấm (1-10)»,
    «Ghi nhận». Sếp sửa ngay trên màn Dự án.
  * `overview`: cây việc + người làm + tài khoản của họ (để bot tìm chat); chỉ thành viên thấy bảng mới đọc được.
  * `reply`: ghi câu trả lời của người làm (nhận / giờ khác / từ chối / ghi chú / xong / tiến độ) vào việc.
Tên trường, nhãn «Nhận việc» và mã hành động dùng chung nằm ở `agent_hub/plan_policy.py`.
"""
from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy.orm import Session

from app.modules.agent_hub.plan_policy import (A_ACCEPT, A_DECLINE, A_DONE, A_LATER, A_NOTE, A_PROGRESS,
                                               A_UNREACHABLE, ACCEPT_LATER, ACCEPT_NO, ACCEPT_NOT_ASKED,
                                               ACCEPT_OPTIONS, ACCEPT_UNREACHABLE, ACCEPT_YES, FIELD_ACCEPT,
                                               FIELD_CRITERIA, FIELD_NOTE, FIELD_PROGRESS, FIELD_SCORE, PLAN_MARK,
                                               PRIORITY_TO_OPTION)

log = logging.getLogger("app.work.plan_service")


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
