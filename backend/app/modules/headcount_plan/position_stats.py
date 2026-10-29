"""`GET /position-stats` — số người ĐANG LÀM theo vị trí của một pháp nhân × phòng và lương / phụ cấp bình quân trên HĐLĐ
đang hiệu lực (gợi ý để nhập kế hoạch có căn cứ). Hai cột tiền chỉ trả khi `can_see_payroll` (luật che tiền)."""
from collections import defaultdict
from datetime import date

from sqlalchemy.orm import Session

from app.core.scoping import apply_scope
from app.core.vn_time import vn_today
from app.modules.employee.model import Employee
from app.modules.employee.position_model import JobPosition
from app.modules.employee.report_headcount_events import as_of_filtered
from app.modules.labor_contract.lookup import names_map
from app.modules.labor_contract.payroll_report_data import rows_at

from .contract_records import scoped_contract_records
from .serializer import can_see_payroll

NO_POSITION_LABEL = "Không theo vị trí"


def _people(db: Session, user, profile: dict, company_id: int, department_id: int, as_of: date) -> list[tuple[int, int]]:
    """[(employee_id, position_id)] đang làm tại `as_of`, trong phạm vi `headcount_plan` của người xem."""
    base = apply_scope(db.query(Employee), Employee, "headcount_plan", user, profile).filter(Employee.company_id == company_id)
    if department_id:   # 0 = kế hoạch «Toàn pháp nhân» → đếm CẢ pháp nhân, không phải người chưa gắn phòng
        base = base.filter(Employee.department_id == department_id)
    out = []
    for q in as_of_filtered(base, as_of):
        out += [(eid, pid or 0) for eid, pid in q.with_entities(Employee.id, Employee.position_id).all()]
    return out


def get_position_stats(db: Session, user, profile: dict, company_id: int, department_id: int, as_of: date) -> list[dict]:
    people = _people(db, user, profile, company_id, department_id, as_of)
    counts: dict[int, int] = defaultdict(int)
    for _, pid in people:
        counts[pid] += 1
    show_money = can_see_payroll(profile, company_id, department_id)
    base_by, allow_by = defaultdict(list), defaultdict(list)
    if show_money and people:
        position_of = dict(people)
        #  Cùng đường nạp và cùng luật «HĐ còn hiệu lực tại ngày» với chi tiết kế hoạch / báo cáo A5: qua phạm vi
        #  labor_contract, chỉ HĐ của CHÍNH pháp nhân này, bỏ HĐ xóa mềm, gồm HĐ chấm dứt sau `as_of`.
        records = scoped_contract_records(db, user, profile, as_of, as_of, vn_today(), company_id)
        for r in rows_at(records, as_of):
            if r.employee_id in position_of:
                base_by[position_of[r.employee_id]].append(r.base_salary)
                allow_by[position_of[r.employee_id]].append(r.allowance)
    names = names_map(db, JobPosition, set(counts))
    rows = []
    for pid in sorted(counts, key=lambda p: (p == 0, names.get(p, ""))):
        rows.append({
            "position_id": pid, "position_name": names.get(pid, "") if pid else NO_POSITION_LABEL,
            "current_count": counts[pid],
            "avg_base_salary": round(sum(base_by[pid]) / len(base_by[pid])) if show_money and base_by[pid] else None,
            "avg_allowance": round(sum(allow_by[pid]) / len(allow_by[pid])) if show_money and allow_by[pid] else None,
        })
    return rows
