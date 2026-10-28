"""Nạp dữ liệu báo cáo A4 «Định biên kế hoạch so với thực tế» (khóa 25, duoc-CR-689).

Hai nguồn: dòng kế hoạch của năm (`tab_headcount_plan`, phạm vi `headcount_plan`) và người ĐANG LÀM tại mốc
`as_of` (luật A1: `as_of_filtered`, phạm vi `employee`). Số truy vấn CỐ ĐỊNH: 1 (kế hoạch) + 2 (đếm người,
GROUP BY) hoặc 2 (danh sách người, cho `/rows`).

Dựng `PlanRow` — một hàng = một «đơn vị so sánh»:
- dòng kế hoạch của CẢ pháp nhân (`department_id = 0`, `level="company"`) so với TỔNG người của pháp nhân;
- dòng kế hoạch của một phòng (`level="dept"`) so với người của phòng;
- phòng CÓ NGƯỜI mà không có dòng kế hoạch (`has_plan=False`) — hiện «chưa có kế hoạch».
Cờ `top` chống cộng đôi: pháp nhân có dòng «toàn pháp nhân» thì CHỈ dòng đó tính vào Tổng / nhóm Pháp nhân
(các dòng phòng của nó chỉ hiện ở «Xem theo Phòng ban»); pháp nhân không có thì các dòng phòng là `top`.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.scoping import apply_scope
from app.modules.employee.model import Employee
from app.modules.employee.report_headcount_events import as_of_filtered, effective_hire_date
from app.modules.headcount_plan.model import HeadcountPlan


@dataclass(frozen=True)
class PlanRow:
    company_id: int
    department_id: int          # 0 với dòng «toàn pháp nhân» và với người chưa gắn phòng
    level: str                  # "company" | "dept"
    planned: int
    actual: int
    has_plan: bool
    top: bool                   # tính vào Tổng + nhóm Pháp nhân

    @property
    def vacancies(self) -> int:
        return max(0, self.planned - self.actual) if self.has_plan else 0

    @property
    def over(self) -> int:
        return max(0, self.actual - self.planned) if self.has_plan else 0

    @property
    def filled(self) -> int:
        return min(self.actual, self.planned) if self.has_plan else 0

    @property
    def unplanned(self) -> int:
        return 0 if self.has_plan else self.actual


@dataclass(frozen=True)
class Person:
    employee_id: int
    code: str
    name: str
    company_id: int
    department_id: int
    position: str
    hire_date: date | None
    level: str = "person"


_COLS = (Employee.id, Employee.code, Employee.full_name, Employee.company_id, Employee.department_id,
         Employee.position)


def _employee_base(db: Session, user, prof: dict, company_id: int | None, department_id: int | None,
                   action: str = "read", also_employee_scope: bool = False):
    """Người được ĐẾM theo phạm vi của khóa `headcount_plan` (cùng cột pháp nhân + phòng với `Employee`): chỉ là con
    số theo đơn vị tổ chức mà người xem đã được xem kế hoạch, không lộ danh tính. Danh sách người (`/rows`) bắt
    thêm phạm vi `employee` (`also_employee_scope`)."""
    q = apply_scope(db.query(Employee), Employee, "headcount_plan", user, prof, action)
    if also_employee_scope:
        q = apply_scope(q, Employee, "employee", user, prof)
    if company_id is not None:
        q = q.filter(Employee.company_id == company_id)
    if department_id is not None:
        q = q.filter(Employee.department_id == department_id)
    return q


def load_plans(db: Session, user, prof: dict, year: int, company_id: int | None, department_id: int | None,
               action: str = "read") -> list[HeadcountPlan]:
    q = apply_scope(db.query(HeadcountPlan), HeadcountPlan, "headcount_plan", user, prof, action)
    q = q.filter(HeadcountPlan.year == year)
    if company_id is not None:
        q = q.filter(HeadcountPlan.company_id == company_id)
    if department_id is not None:
        q = q.filter(HeadcountPlan.department_id == department_id)   # chỉ dòng của phòng đó
    return q.order_by(HeadcountPlan.company_id, HeadcountPlan.department_id).all()


def load_counts(db: Session, user, prof: dict, as_of: date, company_id: int | None,
                department_id: int | None, action: str = "read") -> Counter:
    """{(pháp nhân, phòng): số người đang làm tại `as_of`} — hai câu GROUP BY, không theo số nhân sự."""
    counts: Counter = Counter()
    for q in as_of_filtered(_employee_base(db, user, prof, company_id, department_id, action), as_of):
        rows = (q.with_entities(Employee.company_id, Employee.department_id, func.count(Employee.id))
                .group_by(Employee.company_id, Employee.department_id).all())
        for co, dept, n in rows:
            counts[(co or 0, dept or 0)] += n
    return counts


def load_people(db: Session, user, prof: dict, as_of: date, company_id: int | None,
                department_id: int | None) -> list[Person]:
    with_date, fallback = as_of_filtered(_employee_base(db, user, prof, company_id, department_id, "read", True), as_of)
    out = []
    for r in with_date.with_entities(*_COLS, Employee.hire_date).all():
        out.append(Person(r.id, r.code or "", r.full_name or "", r.company_id or 0, r.department_id or 0,
                          r.position or "", r.hire_date))
    for r in fallback.with_entities(*_COLS, Employee.created_at).all():
        out.append(Person(r.id, r.code or "", r.full_name or "", r.company_id or 0, r.department_id or 0,
                          r.position or "", effective_hire_date(None, r.created_at)))
    return out


def counts_of(people: list[Person]) -> Counter:
    return Counter((p.company_id, p.department_id) for p in people)


def build_plan_rows(plans: list[HeadcountPlan], counts: Counter) -> list[PlanRow]:
    company_total: Counter = Counter()
    for (co, _), n in counts.items():
        company_total[co] += n
    company_level = {p.company_id for p in plans if not p.department_id}
    planned_depts = {(p.company_id, p.department_id) for p in plans if p.department_id}
    rows = []
    for p in plans:
        if not p.department_id:
            rows.append(PlanRow(p.company_id, 0, "company", int(p.planned_headcount or 0),
                                company_total[p.company_id], True, True))
        else:
            rows.append(PlanRow(p.company_id, p.department_id, "dept", int(p.planned_headcount or 0),
                                counts[(p.company_id, p.department_id)], True, p.company_id not in company_level))
    for (co, dept), n in sorted(counts.items()):
        if n > 0 and (co, dept) not in planned_depts:
            rows.append(PlanRow(co, dept, "dept", 0, n, False, co not in company_level))
    return rows
