"""Loại trừ email — đọc/ghi danh sách chặn + lọc người nhận trước khi gửi.

Mỗi luật có thể áp cho MỌI mẫu (`event == ""`) hoặc RIÊNG một mẫu email (một event
cụ thể, vd `dx_approved_dispatcher`). Lọc theo hồ sơ nhân sự (cá nhân / phòng ban /
công ty). CHỈ chặn email — chuông vẫn gửi.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from .email_exclusion_model import EmailExclusion

VALID_SCOPES = ("employee", "department", "company")
SCOPE_LABELS = {"employee": "Cá nhân", "department": "Phòng ban", "company": "Công ty"}


def _to_dict(r: EmailExclusion) -> dict:
    from .email_template_service import event_display

    return {
        "id": r.id, "scope": r.scope, "scope_label": SCOPE_LABELS.get(r.scope, r.scope),
        "ref_id": r.ref_id, "label": r.label,
        "event": r.event or "", "event_label": event_display(r.event or ""),
    }


def list_all(db: Session) -> list[dict]:
    rows = (db.query(EmailExclusion)
            .order_by(EmailExclusion.event.asc(), EmailExclusion.scope.asc(), EmailExclusion.id.asc())
            .all())
    return [_to_dict(r) for r in rows]


def add(db: Session, scope: str, ref_id: int, label: str, event: str, user) -> dict:
    from fastapi import HTTPException

    if scope not in VALID_SCOPES:
        raise HTTPException(400, f"Mức loại trừ không hợp lệ: {scope}")
    if not ref_id:
        raise HTTPException(400, "Thiếu đối tượng loại trừ")
    event = (event or "").strip()
    row = (db.query(EmailExclusion)
           .filter(EmailExclusion.scope == scope, EmailExclusion.ref_id == ref_id,
                   EmailExclusion.event == event).first())
    if row is None:
        row = EmailExclusion(scope=scope, ref_id=ref_id, event=event, created_by=getattr(user, "id", 0))
        db.add(row)
    row.label = (label or "").strip()
    row.updated_by = getattr(user, "id", 0)
    db.commit()
    return _to_dict(row)


def remove(db: Session, exclusion_id: int) -> None:
    row = db.get(EmailExclusion, exclusion_id)
    if row is not None:
        db.delete(row)
        db.commit()


def _excluded_sets(db: Session, event: str) -> tuple[set[int], set[int], set[int]]:
    """Tập id bị loại cho MỘT event = luật áp mọi mẫu ("") + luật riêng event đó."""
    emp: set[int] = set()
    dept: set[int] = set()
    comp: set[int] = set()
    rows = (db.query(EmailExclusion)
            .filter(EmailExclusion.event.in_(("", event))).all())
    for r in rows:
        if r.scope == "employee":
            emp.add(r.ref_id)
        elif r.scope == "department":
            dept.add(r.ref_id)
        elif r.scope == "company":
            comp.add(r.ref_id)
    return emp, dept, comp


def filter_recipients(db: Session, recipients: list, event: str = "") -> list:
    """Bỏ khỏi danh sách nhận EMAIL những người bị loại trừ cho `event` này.

    Gồm luật áp mọi mẫu + luật riêng event. Không có luật nào → trả nguyên danh sách.
    """
    emp_ids, dept_ids, comp_ids = _excluded_sets(db, event)
    if not (emp_ids or dept_ids or comp_ids):
        return recipients

    from app.modules.employee.model import Employee

    rec_emp_ids = {getattr(r, "employee_id", 0) for r in recipients if getattr(r, "employee_id", 0)}
    emp_map = (
        {e.id: e for e in db.query(Employee).filter(Employee.id.in_(rec_emp_ids)).all()}
        if rec_emp_ids else {}
    )
    keep = []
    for r in recipients:
        eid = getattr(r, "employee_id", 0)
        if eid and eid in emp_ids:
            continue
        emp = emp_map.get(eid)
        if emp is not None and (emp.department_id in dept_ids or emp.company_id in comp_ids):
            continue
        keep.append(r)
    return keep
