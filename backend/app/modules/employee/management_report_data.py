"""Nạp dữ liệu báo cáo A3 «Cơ cấu quản lý» (khóa 23, duoc-CR-688): nhân sự ĐANG LÀM tại mốc
`as_of` + người nghỉ việc trong kỳ, dựng thành ba loại hàng để cộng bằng khung Haravan.

Ba loại hàng (`SpanRow.kind`):
- `p` — mỗi nhân sự đang làm (đếm `staff`, cờ «chưa gán quản lý», cờ «quản lý đã nghỉ»);
- `m` — mỗi người có cấp dưới TRONG tập đang xem (đếm `managers`, `direct_reports`, cờ span);
- `d` — mỗi người nghỉ việc trong kỳ (đếm `departures_under`, gom theo quản lý HIỆN TẠI).

Phạm vi: `scoped_employee_query` (apply_scope + lọc công ty/phòng, chỉ thu hẹp). Người có `manager_id` trỏ tới nhân sự ĐÃ NGHỈ / ngừng hoạt động (`manager_gone`) KHÔNG được tính là «đã gán»:
không cộng vào số cấp dưới của ai, không vào nhóm quản lý đó, có chỉ số riêng `manager_resigned`. Quản lý nằm NGOÀI tập
đang xem không sinh hàng `m` (không nở rộng phạm vi); chỉ tra tên/tình trạng để gán nhãn nhóm.
Số truy vấn CỐ ĐỊNH: 2 (đang làm) + 1 (nghỉ việc) + tối đa 1 mỗi 900 mã quản lý ngoài tập.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from app.core.report_period import range_filter
from app.core.scoping import apply_scope
from app.modules.employee.model import Employee
from app.modules.employee.report_headcount_events import as_of_filtered
from app.modules.employee.service import STATUS_RESIGNED

_COLS = (Employee.id, Employee.code, Employee.full_name, Employee.company_id, Employee.department_id,
         Employee.position, Employee.job_level, Employee.manager_id, Employee.status,
         Employee.resign_date, Employee.is_active)
_CHUNK = 900
SPAN_WIDE_OVER = 10   # «Quản lý trên 10 cấp dưới»


@dataclass(frozen=True)
class SpanRow:
    kind: str                 # "p" | "m" | "d"
    employee_id: int
    code: str
    name: str
    position: str
    company_id: int
    department_id: int
    job_level: int
    manager_id: int           # 0 = chưa gán (hoặc mã không tồn tại)
    reports: int = 0          # chỉ hàng "m"
    manager_gone: bool = False   # quản lý trực tiếp đã nghỉ / ngừng hoạt động (chỉ hàng "p")
    resign_date: date | None = None


def _person(row, kind: str, manager_id: int, reports: int = 0, manager_gone: bool = False) -> SpanRow:
    return SpanRow(kind, row.id, row.code or "", row.full_name or "", row.position or "",
                   row.company_id or 0, row.department_id or 0, row.job_level or 0, manager_id,
                   reports, manager_gone, row.resign_date if kind == "d" else None)


def _is_gone(status, is_active) -> bool:
    return status == STATUS_RESIGNED or not is_active


def load_rows(db: Session, user, prof: dict, as_of: date, d_from: date, d_to: date,
              company_id: int | None, department_id: int | None,
              action: str = "read") -> tuple[list[SpanRow], dict[int, str]]:
    """(hàng, {id quản lý: tên}). Nhãn CHỈ là tên — quản lý ngoài phạm vi không lộ thêm tình trạng nào."""
    #  Phạm vi theo `action` (đường xuất tệp dùng phạm vi `export`); công ty/phòng chỉ thu hẹp thêm.
    base = apply_scope(db.query(Employee), Employee, "employee", user, prof, action)
    if company_id is not None:
        base = base.filter(Employee.company_id == company_id)
    if department_id is not None:
        base = base.filter(Employee.department_id == department_id)
    with_date, fallback = as_of_filtered(base, as_of)
    active = list(with_date.with_entities(*_COLS).all()) + list(fallback.with_entities(*_COLS).all())
    left = (base.filter(Employee.status == STATUS_RESIGNED, Employee.resign_date.isnot(None))
            .filter(range_filter(Employee.resign_date, "date", d_from, d_to))
            .with_entities(*_COLS).all())

    by_id = {r.id: r for r in active}
    wanted = {r.manager_id for r in [*active, *left] if r.manager_id and r.manager_id != r.id}
    info = {i: (r.full_name or "", _is_gone(r.status, r.is_active)) for i, r in by_id.items() if i in wanted}
    missing = sorted(wanted - set(info))
    for i in range(0, len(missing), _CHUNK):
        for m in db.query(Employee.id, Employee.full_name, Employee.status, Employee.is_active).filter(
                Employee.id.in_(missing[i:i + _CHUNK])).all():
            info[m.id] = (m.full_name or "", _is_gone(m.status, m.is_active))
    labels = {i: n for i, (n, _) in info.items()}

    def mgr_of(r) -> int:   # mã không tồn tại / tự trỏ chính mình = chưa gán
        return r.manager_id if r.manager_id in info and r.manager_id != r.id else 0

    def gone(r) -> bool:
        return bool(mgr_of(r)) and info[mgr_of(r)][1]

    counts = Counter(mgr_of(r) for r in active if mgr_of(r) and not gone(r))
    rows = [_person(r, "p", mgr_of(r), manager_gone=gone(r)) for r in active]
    rows += [_person(by_id[mid], "m", mgr_of(by_id[mid]), reports=n)
             for mid, n in counts.items() if mid in by_id]
    rows += [_person(r, "d", mgr_of(r)) for r in left]
    return rows, labels
