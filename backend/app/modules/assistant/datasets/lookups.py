"""Tra nhãn sau truy vấn cho các chiều mang id (pháp nhân, phòng ban) — một truy vấn cho cả trang kết quả."""
from __future__ import annotations


def company_names(db, ids: set) -> dict:
    from app.modules.company.model import Company

    keys = {int(i) for i in ids if i}
    if not keys:
        return {}
    return {c.id: c.name for c in db.query(Company.id, Company.name).filter(Company.id.in_(keys)).all()}


def department_names(db, ids: set) -> dict:
    from app.modules.department.model import Department

    keys = {int(i) for i in ids if i}
    if not keys:
        return {}
    return {d.id: d.name for d in db.query(Department.id, Department.name).filter(Department.id.in_(keys)).all()}
