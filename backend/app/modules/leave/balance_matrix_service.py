""""Tổng hợp theo người" của Quỹ phép (duoc-CR-717) — ma trận NHÂN VIÊN × LOẠI NGHỈ = còn lại (kiểu ERPNext
Employee Leave Balance Summary). `GET /api/leave-balances/matrix` (+ `/matrix/export`).

Số ô = `available_days` (trừ phần chưa tới tháng của loại cộng dần) — cùng số với màn Quỹ phép / form đơn.
Cột = loại `counts_balance` có ít nhất một dòng quỹ trong KẾT QUẢ (cả trang khác, để cột không nhảy khi lật trang).
Số truy vấn CỐ ĐỊNH: đếm người + trang người + loại (cột) + quỹ của trang + (loại + ngày vào làm của
`available_days_map`) + tên phòng + 2 câu chính sách đang áp (duoc-CR-745); cộng 1 câu loại khi có dòng mang sang cần thu hồi quá hạn.
"""
from __future__ import annotations

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.scoping import apply_scope
from app.modules.department.model import Department
from app.modules.employee.model import Employee

from . import balance_matrix_sort, balance_service, carryover_service
from .balance_model import LeaveBalance
from .balance_report_spec import employee_conds
from .catalog_model import LeaveType
from .policy_balance_links import policy_names_for_year

ENTITY = "leave_balance"
EXPORT_LIMIT = 5000


def build_matrix(db: Session, user, prof: dict, action: str, year: int, company_id: int | None,
                 department_id: int | None, status: str, search: str | None, offset: int, limit: int,
                 sort_by: str = "", sort_dir: str = "asc") -> dict:
    q = apply_scope(db.query(LeaveBalance), LeaveBalance, ENTITY, user, prof, action).filter(LeaveBalance.year == year)
    if company_id is not None:
        q = q.filter(LeaveBalance.company_id == company_id)       # chỉ THU HẸP, sau apply_scope
    conds = employee_conds(status, department_id)
    if conds:
        q = q.filter(LeaveBalance.employee_id.in_(db.query(Employee.id).filter(*conds)))

    people = db.query(Employee).filter(Employee.id.in_(q.with_entities(LeaveBalance.employee_id)))
    needle = (search or "").strip()
    if needle:
        people = people.filter(or_(Employee.code.contains(needle, autoescape=True),
                                   Employee.full_name.contains(needle, autoescape=True)))
    total = people.with_entities(func.count(Employee.id)).scalar() or 0
    page = (people.with_entities(Employee.id, Employee.code, Employee.full_name, Employee.department_id)
            .order_by(*balance_matrix_sort.build_order_by(sort_by, sort_dir)).offset(offset).limit(limit).all())

    types = (q.join(LeaveType, LeaveType.id == LeaveBalance.leave_type_id)
             .filter(LeaveType.counts_balance.is_(True))
             .with_entities(LeaveType.id, LeaveType.name, LeaveType.sort_order).distinct().all())
    types.sort(key=lambda t: (t.sort_order or 0, t.id))
    columns = [{"leave_type_id": t.id, "name": t.name} for t in types]
    type_ids = {t.id for t in types}

    cells: dict[int, dict[int, float]] = {}
    if page and type_ids:
        rows = q.filter(LeaveBalance.employee_id.in_([p.id for p in page]),
                        LeaveBalance.leave_type_id.in_(type_ids)).all()
        if carryover_service.expire_rows(db, rows):    # như màn Quỹ phép: không trưng số của phép mang sang đã quá hạn
            db.commit()
        avail = balance_service.available_days_map(db, rows)
        for r in rows:
            cells.setdefault(r.employee_id, {})[r.leave_type_id] = avail[r.id]

    dept_name = ({d.id: d.name for d in db.query(Department.id, Department.name)
                  .filter(Department.id.in_({p.department_id for p in page if p.department_id})).all()}
                 if page else {})
    policy_name = policy_names_for_year(db, [p.id for p in page], year) if page else {}
    items = [{"employee_id": p.id, "code": p.code, "name": p.full_name,
              "department_name": dept_name.get(p.department_id, ""),
              "policy_name": policy_name.get(p.id, ""),
              "cells": {str(t): v for t, v in cells.get(p.id, {}).items()},
              "total": round(sum(cells.get(p.id, {}).values()), 2)} for p in page]
    return {"year": year, "columns": columns, "items": items, "total": total}
