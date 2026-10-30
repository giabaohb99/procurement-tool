"""Đề xuất kế hoạch AI chờ duyệt (kh-AI1-3, doc/erp/tai-lieu-ai/22 §5.2) — lưu, sửa, duyệt, từ chối.

AI chỉ đề xuất, người quyết (A1 chốt 22/10): người duyệt là CHÍNH người hỏi AI; đề xuất của người khác coi như không tồn
tại. Duyệt mới dựng bảng Dự án, bằng đúng `work/plan_service.build` mà bao-CR-616 đang dùng. Bản AI (`plan_ai`) không bao
giờ sửa; bản người (`plan_final`) và `diff` để vòng học so lại.

Khuôn kế hoạch: xem doc 22 §5.2. `normalize` dùng chung cho bản AI lúc lưu và bản người lúc sửa / duyệt — mọi ô đều
có trần, người theo `employee_id` phải còn làm, loại việc phải còn dùng.
"""
from __future__ import annotations

import json
import logging
import re
from datetime import date, datetime

from sqlalchemy.orm import Session

from app.core import app_settings
from app.core.ai_plan_codes import AI_PLAN_STATUS_LABELS, AiPlanStatus
from app.core.logging_codes import AI_CHANNEL_LABELS
from app.modules.ai_plan.model import AiPlanProposal

log = logging.getLogger("app.ai_plan")

MAX_PHASES, MAX_TASKS, MAX_SUBS, MAX_CRITERIA, MAX_ASSIGNEES = 12, 30, 7, 3, 10
MAX_PLAN_BYTES = 200_000
PRIORITIES = ("Gấp", "Ưu tiên", "Thường")
REVIEW_PATH = "/project/ai-plans/{id}"
LIST_PATH = "/project/lists/{id}"
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_KEY = re.compile(r"^[a-z0-9]{1,20}$")


class PlanInvalid(ValueError):
    """Khuôn kế hoạch sai, trả 422. Mỗi lỗi `{phase, task, subtask, key, field, message}` — `phase` / `task` / `subtask`
    là vị trí (đếm từ 0, None = cấp kế hoạch) để màn duyệt tô đúng ô; `key` rỗng với dòng người mới thêm."""

    def __init__(self, problems: list[dict]):
        super().__init__("; ".join(p["message"] for p in problems))
        self.problems = problems

    @property
    def messages(self) -> list[str]:
        return [p["message"] for p in self.problems]


def _problem(message: str, field: str = "", where: dict | None = None) -> dict:
    w = where or {}
    return {"phase": w.get("phase"), "task": w.get("task"), "subtask": w.get("subtask"), "key": w.get("key", ""),
            "field": field, "message": message}


class NotPending(ValueError):
    """Đề xuất không còn ở trạng thái Chờ duyệt — trả 409."""


def review_enabled() -> bool:
    return bool(app_settings.get("ai_plan_review_enabled"))


# ── chuẩn hóa khuôn ─────────────────────────────────────────────────────────────────────────────────────────────

def _text(v, limit: int) -> str:
    return " ".join(str(v or "").split())[:limit]


def _load_people(db: Session, ids: set[int]) -> dict[int, tuple[str, str]]:
    from app.modules.employee.model import Employee

    if not ids:
        return {}
    rows = db.query(Employee.id, Employee.code, Employee.full_name, Employee.status, Employee.is_active) \
        .filter(Employee.id.in_(sorted(ids))).all()
    return {int(r.id): (r.code or "", r.full_name or "") for r in rows
            if r.status != "resigned" and r.is_active is not False}


def _load_task_types(db: Session, ids: set[int]) -> dict[int, str]:
    from app.modules.work.task_type_model import WorkTaskType

    if not ids:
        return {}
    rows = db.query(WorkTaskType.id, WorkTaskType.name).filter(WorkTaskType.id.in_(sorted(ids)),
                                                              WorkTaskType.is_active.is_(True)).all()
    return {int(r.id): r.name or "" for r in rows}


def _iter_tasks(phases: list) -> list[dict]:
    out = []
    for ph in phases:
        for t in ph.get("tasks") or []:
            out.append(t)
            out.extend(t.get("subtasks") or [])
    return out


def _collect_ids(phases_raw: list) -> tuple[set[int], set[int]]:
    people, types = set(), set()
    for ph in phases_raw:
        if not isinstance(ph, dict):
            continue
        for t in (ph.get("tasks") or [])[:MAX_TASKS]:
            if not isinstance(t, dict):
                continue
            for item in [t] + [s for s in (t.get("subtasks") or [])[:MAX_SUBS] if isinstance(s, dict)]:
                for a in (item.get("assignees") or [])[:MAX_ASSIGNEES]:
                    try:
                        people.add(int(a.get("employee_id") if isinstance(a, dict) else 0))
                    except (TypeError, ValueError):
                        pass
                tt = item.get("task_type")
                if isinstance(tt, dict):
                    try:
                        types.add(int(tt.get("id") or 0))
                    except (TypeError, ValueError):
                        pass
    return people - {0}, types - {0}


def _normalize_task(raw: dict, people: dict, types: dict, problems: list[dict], where: dict, allow_sub: bool) -> dict | None:
    title = _text(raw.get("title"), 500)
    where = {**where, "key": str(raw.get("key") or "").strip().lower()[:20]}
    if not title:
        #  Báo lỗi, không bỏ lặng: sửa qua cổng MCP / bot không có giao diện chặn trước (A3 góp ý 22/10).
        problems.append(_problem("dòng việc chưa có tên", "title", where))
        return None
    assignees = []
    for a in (raw.get("assignees") or [])[:MAX_ASSIGNEES]:
        try:
            eid = int(a.get("employee_id") if isinstance(a, dict) else 0)
        except (TypeError, ValueError):
            eid = 0
        if eid in people:
            assignees.append({"employee_id": eid, "code": people[eid][0], "name": people[eid][1]})
        else:
            problems.append(_problem(f"\"{title}\": người được giao #{eid} không có hoặc đã nghỉ việc", "assignees", where))
    start, due = str(raw.get("start_date") or "").strip()[:10], str(raw.get("due_date") or "").strip()[:10]
    for field, name, val in (("start_date", "ngày bắt đầu", start), ("due_date", "hạn", due)):
        if val:
            try:
                if not _DATE.match(val):
                    raise ValueError
                date.fromisoformat(val)
            except ValueError:
                problems.append(_problem(f"\"{title}\": {name} phải dạng YYYY-MM-DD", field, where))
    if start and due and _DATE.match(start) and _DATE.match(due) and due < start:
        problems.append(_problem(f"\"{title}\": hạn trước ngày bắt đầu", "due_date", where))
    hours = raw.get("estimate_hours")
    if hours in (None, ""):
        hours = None
    else:
        try:
            hours = round(float(hours), 2)
            if not 0 < hours <= 999:
                raise ValueError
        except (TypeError, ValueError):
            problems.append(_problem(f"\"{title}\": giờ ước lượng phải lớn hơn 0 và không quá 999", "estimate_hours", where))
            hours = None
    task_type = None
    tt = raw.get("task_type")
    if isinstance(tt, dict) and tt.get("id"):
        try:
            tid = int(tt.get("id"))
        except (TypeError, ValueError):
            tid = 0
        if tid in types:
            task_type = {"id": tid, "name": types[tid]}
        else:
            problems.append(_problem(f"\"{title}\": loại việc #{tt.get('id')} không có hoặc đã ngừng dùng", "task_type", where))
    priority = str(raw.get("priority") or "").strip()
    key = str(raw.get("key") or "").strip().lower()
    out = {"key": key if _KEY.match(key) else "", "title": title, "description": str(raw.get("description") or "")[:2000],
           "assignees": assignees, "start_date": start, "due_date": due,
           "priority": priority if priority in PRIORITIES else "Thường",
           "criteria": [_text(c, 300) for c in (raw.get("criteria") or []) if _text(c, 300)][:MAX_CRITERIA],
           "estimate_hours": hours, "task_type": task_type,
           "assignee_reason": _text(raw.get("assignee_reason"), 300)}
    if allow_sub:
        subs = []
        for k, s in enumerate((raw.get("subtasks") or [])[:MAX_SUBS]):
            if isinstance(s, dict):
                sub = _normalize_task(s, people, types, problems, {**where, "subtask": k}, allow_sub=False)
                if sub:
                    subs.append(sub)
        out["subtasks"] = subs
    return out


def normalize(db: Session, plan, *, assign_keys: bool = False) -> dict:
    """Khuôn sạch hoặc ném `PlanInvalid`. `assign_keys` = đặt lại `key` theo vị trí (bản AI lúc lưu); không thì giữ `key`
    cũ, dòng mới / key trùng được đặt `n1`, `n2`…"""
    if not isinstance(plan, dict):
        raise PlanInvalid([_problem("kế hoạch phải là một đối tượng")])
    if len(json.dumps(plan, ensure_ascii=False, default=str)) > MAX_PLAN_BYTES:
        raise PlanInvalid([_problem(f"kế hoạch quá lớn (tối đa {MAX_PLAN_BYTES // 1000} nghìn ký tự)")])
    problems: list[dict] = []
    title = _text(plan.get("title"), 200)
    if not title:
        problems.append(_problem("kế hoạch phải có tên", "title"))
    deadline = str(plan.get("deadline") or "").strip()[:10]
    if deadline and not _DATE.match(deadline):
        problems.append(_problem("hạn chót phải dạng YYYY-MM-DD", "deadline"))
    phases_raw = [p for p in (plan.get("phases") or []) if isinstance(p, dict)] if isinstance(plan.get("phases"), list) else []
    if len(phases_raw) > MAX_PHASES:
        problems.append(_problem(f"tối đa {MAX_PHASES} giai đoạn", "phases"))
    phases_raw = phases_raw[:MAX_PHASES]
    people_ids, type_ids = _collect_ids(phases_raw)
    people, types = _load_people(db, people_ids), _load_task_types(db, type_ids)
    phases = []
    for i, ph in enumerate(phases_raw):
        tasks_raw = [t for t in (ph.get("tasks") or []) if isinstance(t, dict)]
        if len(tasks_raw) > MAX_TASKS:
            problems.append(_problem(f"giai đoạn {i + 1}: tối đa {MAX_TASKS} việc", "tasks", {"phase": i}))
        tasks = [t for t in (_normalize_task(r, people, types, problems, {"phase": i, "task": j}, allow_sub=True)
                             for j, r in enumerate(tasks_raw[:MAX_TASKS])) if t]
        if tasks:
            phases.append({"name": _text(ph.get("name"), 100) or f"Giai đoạn {i + 1}", "tasks": tasks})
    if not phases:
        problems.append(_problem("kế hoạch chưa có việc nào có tên", "phases"))
    if problems:
        raise PlanInvalid(problems[:20])
    _set_keys(phases, assign_keys)
    n_tasks = sum(len(p["tasks"]) for p in phases)
    n_subs = sum(len(t.get("subtasks") or []) for p in phases for t in p["tasks"])
    return {"title": title, "description": str(plan.get("description") or "")[:2000], "deadline": deadline,
            "phases": phases, "assumptions": [_text(a, 300) for a in (plan.get("assumptions") or []) if _text(a, 300)][:10],
            "counts": {"phases": len(phases), "tasks": n_tasks, "subtasks": n_subs}}


def _set_keys(phases: list, by_position: bool) -> None:
    seen: set[str] = set()
    fresh = 0
    for i, ph in enumerate(phases, 1):
        for j, t in enumerate(ph["tasks"], 1):
            items = [(t, f"p{i}t{j}")] + [(s, f"p{i}t{j}s{k}") for k, s in enumerate(t.get("subtasks") or [], 1)]
            for item, pos in items:
                key = pos if by_position else item["key"]
                if not key or key in seen:
                    fresh += 1
                    key = f"n{fresh}"
                    while key in seen:
                        fresh += 1
                        key = f"n{fresh}"
                item["key"] = key
                seen.add(key)


# ── so bản AI với bản người ─────────────────────────────────────────────────────────────────────────────────────

def compute_diff(ai: dict, final: dict | None) -> dict:
    """Đếm khác nhau theo `key`: thêm / bỏ / đổi người / đổi giờ / đổi hạn / đổi tên / giữ nguyên."""
    a = {t["key"]: t for t in _iter_tasks(ai.get("phases") or [])}
    b = {t["key"]: t for t in _iter_tasks((final or ai).get("phases") or [])}
    same = set(a) & set(b)
    who = lambda t: sorted(p["employee_id"] for p in t.get("assignees") or [])   # noqa: E731
    out = {"added": len(set(b) - set(a)), "removed": len(set(a) - set(b)),
           "assignee_changed": sum(1 for k in same if who(a[k]) != who(b[k])),
           "hours_changed": sum(1 for k in same if a[k].get("estimate_hours") != b[k].get("estimate_hours")),
           "due_changed": sum(1 for k in same if a[k].get("due_date") != b[k].get("due_date")),
           "title_changed": sum(1 for k in same if a[k].get("title") != b[k].get("title"))}
    out["unchanged"] = sum(1 for k in same if a[k] == b[k])
    return out


def _to_build_draft(plan: dict) -> dict:
    """Khuôn đề xuất → khuôn `plan_service.build` (loại việc đi bằng `task_type_id`). Chịu được bản nháp thô từ cổng MCP:
    phần sai hình dạng bị bỏ, để `build` tự báo lỗi đọc được như trước."""
    def conv(t: dict) -> dict:
        item = {k: v for k, v in t.items() if k not in ("task_type", "subtasks", "key", "assignee_reason")}
        tt = t.get("task_type")
        item["task_type_id"] = (tt.get("id") if isinstance(tt, dict) else 0) or t.get("task_type_id") or 0
        if isinstance(t.get("subtasks"), list):
            item["subtasks"] = [conv(s) for s in t["subtasks"] if isinstance(s, dict)]
        return item
    phases = [p for p in (plan.get("phases") or []) if isinstance(p, dict)] if isinstance(plan.get("phases"), list) else []
    return {"title": plan.get("title") or "", "description": plan.get("description") or "",
            "deadline": plan.get("deadline") or "",
            "phases": [{"name": p.get("name") or "", "tasks": [conv(t) for t in (p.get("tasks") or []) if isinstance(t, dict)]}
                       for p in phases]}


# ── vòng đời ────────────────────────────────────────────────────────────────────────────────────────────────────

def record(db: Session, user, draft: dict, *, status: AiPlanStatus, list_id: int = 0, goal: str = "") -> AiPlanProposal:
    """Lưu bản AI soạn (đã qua `draft_work_plan`). Không commit — bên gọi commit."""
    from app.core.request_context import current_ai_channel
    from app.modules.employee.model import Employee

    plan = normalize(db, draft, assign_keys=True)
    emp_id = int(getattr(user, "employee_id", 0) or 0)
    dept = int(db.query(Employee.department_id).filter(Employee.id == emp_id).scalar() or 0) if emp_id else 0
    row = AiPlanProposal(status=int(status), owner_user_id=int(user.id), owner_employee_id=emp_id, department_id=dept,
                         channel=current_ai_channel(), title=plan["title"],
                         goal=str(goal or draft.get("description") or "")[:4000],
                         deadline=date.fromisoformat(plan["deadline"]) if plan["deadline"] else None,
                         plan_ai=plan, list_id=int(list_id or 0), created_by=int(user.id), updated_by=int(user.id))
    if status == AiPlanStatus.DIRECT:
        row.decided_at, row.decided_by = datetime.utcnow(), int(user.id)
    db.add(row)
    db.flush()
    return row


def get_mine(db: Session, user, proposal_id: int) -> AiPlanProposal | None:
    """Chỉ chủ đề xuất thấy — của người khác trả None như không tồn tại."""
    return db.query(AiPlanProposal).filter(AiPlanProposal.id == int(proposal_id),
                                           AiPlanProposal.owner_user_id == int(user.id)).first()


def list_mine(db: Session, user, *, status: int | None = None, page: int = 1, page_size: int = 20) -> dict:
    q = db.query(AiPlanProposal).filter(AiPlanProposal.owner_user_id == int(user.id))
    if status:
        q = q.filter(AiPlanProposal.status == int(status))
    total = q.count()
    rows = q.order_by(AiPlanProposal.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": [serialize(r) for r in rows], "total": total, "page": page, "page_size": page_size,
            "has_more": page * page_size < total}


def _require_pending(row: AiPlanProposal) -> None:
    if int(row.status) != int(AiPlanStatus.PENDING):
        raise NotPending(f"Đề xuất đang ở trạng thái \"{AI_PLAN_STATUS_LABELS[AiPlanStatus(row.status)]}\", không sửa được nữa.")


def save_edit(db: Session, user, row: AiPlanProposal, plan: dict) -> AiPlanProposal:
    _require_pending(row)
    final = normalize(db, plan)
    row.plan_final = final
    row.title = final["title"]
    row.deadline = date.fromisoformat(final["deadline"]) if final["deadline"] else None
    row.updated_by = int(user.id)
    db.commit()
    return row


def approve(db: Session, user, row: AiPlanProposal, plan: dict | None = None) -> AiPlanProposal:
    """Duyệt: (lưu bản người nếu có) → dựng bảng Dự án như bao-CR-616 → Đã duyệt. Hỏng dựng thì không đổi trạng thái."""
    from app.modules.work import plan_service

    _require_pending(row)
    if plan is not None:
        row.plan_final = normalize(db, plan)
    final = row.plan_final or row.plan_ai
    _code, list_id = plan_service.build(db, user, _to_build_draft(final))     # build tự commit khi xong
    row.status = int(AiPlanStatus.APPROVED)
    row.list_id = int(list_id)
    row.diff = compute_diff(row.plan_ai, row.plan_final)
    row.decided_at, row.decided_by, row.updated_by = datetime.utcnow(), int(user.id), int(user.id)
    db.commit()
    log.info("ai_plan: duyệt đề xuất #%s → kế hoạch #%s (%s)", row.id, list_id, row.diff)
    return row


def reject(db: Session, user, row: AiPlanProposal, reason: str) -> AiPlanProposal:
    _require_pending(row)
    row.status = int(AiPlanStatus.REJECTED)
    row.reject_reason = str(reason or "")[:500]
    row.decided_at, row.decided_by, row.updated_by = datetime.utcnow(), int(user.id), int(user.id)
    db.commit()
    return row


def serialize(row: AiPlanProposal, *, detail: bool = False) -> dict:
    plan = row.plan_final or row.plan_ai or {}
    out = {"id": row.id, "status": int(row.status), "status_label": AI_PLAN_STATUS_LABELS[AiPlanStatus(row.status)],
           "title": row.title, "deadline": row.deadline.isoformat() if row.deadline else None,
           "channel": int(row.channel or 0), "channel_label": AI_CHANNEL_LABELS.get(int(row.channel or 0), ""),
           "counts": plan.get("counts") or {}, "created_at": row.created_at.isoformat() if row.created_at else None,
           "list_id": int(row.list_id or 0), "review_url": REVIEW_PATH.format(id=row.id),
           "list_url": LIST_PATH.format(id=row.list_id) if row.list_id else None}
    if detail:
        out.update(goal=row.goal or "", plan=plan, plan_ai=row.plan_ai, plan_final=row.plan_final, diff=row.diff,
                   reject_reason=row.reject_reason or "",
                   decided_at=row.decided_at.isoformat() if row.decided_at else None)
    return out


# ── nối với lớp nháp dùng chung (draft_create, nhánh work_plan) ─────────────────────────────────────────────────

def submit_for_review(db: Session, user, draft: dict) -> AiPlanProposal:
    """Công tắc duyệt BẬT: xác nhận bản nháp (Telegram "tạo", MCP `confirm_draft`) chỉ lưu đề xuất Chờ duyệt, CHƯA tạo
    việc. Khuôn sai → `PlanInvalid`."""
    row = record(db, user, draft, status=AiPlanStatus.PENDING)
    db.commit()
    return row


def create_direct(db: Session, user, draft: dict) -> tuple[str, int]:
    """Công tắc duyệt TẮT: dựng bảng ngay như bao-CR-616 rồi ghi đề xuất "Tạo thẳng" để có dữ liệu học. Ghi sổ hỏng thì
    chỉ mất dữ liệu học, không mất bảng đã tạo."""
    from app.modules.work import plan_service

    code, list_id = plan_service.build(db, user, _to_build_draft(draft))   # loại việc đi bằng task_type_id
    try:
        record(db, user, draft, status=AiPlanStatus.DIRECT, list_id=list_id)
        db.commit()
    except Exception:  # noqa: BLE001
        db.rollback()
        log.exception("ai_plan: ghi đề xuất \"tạo thẳng\" cho kế hoạch #%s hỏng", list_id)
    return code, list_id
