"""Dựng JSON + tra tên + điều kiện tìm kiếm cho danh sách phân bổ chính sách (duoc-CR-717) — tách khỏi controller."""
from datetime import date

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.modules.employee.model import Employee

from .policy_assignment_plan import assignment_state
from .policy_model import LeavePolicy, LeavePolicyAssignment


def dump_assignment(a: LeavePolicyAssignment, emps: dict, policies: dict, today: date) -> dict:
    emp = emps.get(a.employee_id)
    return {
        "id": a.id, "employee_id": a.employee_id, "company_id": a.company_id, "policy_id": a.policy_id,
        "effective_from": a.effective_from, "effective_to": a.effective_to, "note": a.note,
        "employee_name": emp[1] if emp else "", "employee_code": emp[0] if emp else "",
        "policy_name": policies.get(a.policy_id, ""), "state": assignment_state(a, today),
        "updated_at": a.updated_at,
    }


def lookup_names(db: Session, rows: list[LeavePolicyAssignment]) -> tuple[dict, dict]:
    emps = {i: (c, n) for i, c, n in db.query(Employee.id, Employee.code, Employee.full_name).filter(
        Employee.id.in_({r.employee_id for r in rows} or {0})).all()}
    policies = {i: n for i, n in db.query(LeavePolicy.id, LeavePolicy.name).filter(
        LeavePolicy.id.in_({r.policy_id for r in rows} or {0})).all()}
    return emps, policies


def search_condition(keyword: str):
    """Tên / mã nhân sự chứa `keyword`, so khớp NGAY TRONG SQL (không nạp cả bảng nhân sự). Dấu `%` `_` người gõ
    được coi là chữ thường. Chữ hoa/thường + dấu theo collation `_ci` của MySQL."""
    escaped = keyword.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    like = f"%{escaped}%"
    return LeavePolicyAssignment.employee_id.in_(select(Employee.id).where(
        or_(Employee.full_name.ilike(like, escape="\\"), Employee.code.ilike(like, escape="\\"))))
