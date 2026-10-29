"""Chiều «Xem theo Vị trí» của báo cáo A4 (duoc-CR-690, phase 24): định biên kế hoạch theo vị trí so với người đang giữ vị trí đó.

Đơn vị so sánh (chỉ kế hoạch `top`, nên không cộng đôi): kế hoạch «Toàn pháp nhân» so với MỌI người của pháp nhân, kế hoạch
phòng so với người của phòng. Trong một đơn vị:
- mỗi dòng vị trí (`position_id > 0`) so với người có đúng vị trí đó;
- dòng «Không theo vị trí» (`position_id = 0`) so với những người ở vị trí KHÔNG được liệt kê trong kế hoạch (kể cả người chưa
  gắn vị trí); không có dòng đó mà vẫn có người ngoài danh sách → dòng định biên 0, người đó tính «Vượt».
Phòng chưa có kế hoạch: mỗi vị trí một dòng `has_plan=False` (khớp KPI «Đang làm ở phòng chưa có kế hoạch»).
`PositionUnits.key_of_person` cho danh sách `/rows` cùng khóa nhóm với bảng → bấm số nào ra đúng người đó.
"""
from __future__ import annotations

from collections import Counter, defaultdict

from sqlalchemy.orm import Session

from app.modules.employee.headcount_plan_report_data import Person, PlanRow
from app.modules.employee.position_model import JobPosition
from app.modules.headcount_plan.effective import EffectiveEntry


class PositionUnits:
    """Các đơn vị so sánh của kế hoạch `top` và cách xếp một người vào vị trí của đơn vị đó."""

    def __init__(self, entries: list[EffectiveEntry]):
        self.tops = [e for e in entries if e.top]
        self.company_scoped = {e.company_id for e in self.tops if not e.department_id}
        self.listed = {(e.company_id, e.department_id): {p for p in e.by_position if p} for e in self.tops}

    def scope_of(self, company_id: int, department_id: int) -> tuple[int, int]:
        return (company_id, 0) if company_id in self.company_scoped else (company_id, department_id)

    def position_of(self, company_id: int, department_id: int, position_id: int) -> int:
        """Vị trí dùng để gom: vị trí của chính người đó nếu kế hoạch liệt kê nó (hoặc đơn vị chưa có kế hoạch), không thì 0."""
        listed = self.listed.get(self.scope_of(company_id, department_id))
        return position_id if listed is None or position_id in listed else 0

    def key_of_person(self, p: Person) -> int:
        return self.position_of(p.company_id, p.department_id, p.position_id)

    def build_rows(self, position_counts: Counter) -> list[PlanRow]:
        by_scope: dict[tuple[int, int], Counter] = defaultdict(Counter)
        for (co, dept, pos), n in position_counts.items():
            by_scope[self.scope_of(co, dept)][self.position_of(co, dept, pos)] += n
        rows: list[PlanRow] = []
        for e in self.tops:
            scope = (e.company_id, e.department_id)
            level = "dept" if e.department_id else "company"
            have = by_scope.get(scope, Counter())
            for pos in sorted({*e.by_position, *have}):
                planned, actual = e.by_position.get(pos, 0), have.get(pos, 0)
                if planned or actual or pos in e.by_position:
                    rows.append(PlanRow(e.company_id, e.department_id, level, planned, actual, True, True, pos))
        planned_scopes = set(self.listed)
        for scope, have in sorted(by_scope.items()):
            if scope in planned_scopes:
                continue
            for pos, n in sorted(have.items()):
                if n > 0:
                    rows.append(PlanRow(scope[0], scope[1], "dept", 0, n, False, True, pos))
        return rows


def load_position_names(db: Session, group_by: str | None, always: bool = False) -> dict[int, str]:
    if not (always or group_by == "position"):
        return {}
    return {p.id: p.name for p in db.query(JobPosition.id, JobPosition.name).all()}
