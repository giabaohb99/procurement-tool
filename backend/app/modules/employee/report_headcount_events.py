"""Sự kiện VÀO/NGHỈ + định biên tại một thời điểm — tách khỏi `report_service.py`
để giữ tệp đó dưới 200 dòng (phase 04).

Mỗi nhân sự trong phạm vi sinh ra 1-2 "sự kiện" (`HeadcountEvent`): một sự
kiện VÀO (ngày hiệu lực = `hire_date`, hoặc `created_at` khi hồ sơ cũ thiếu
`hire_date` — Q4.2) và một sự kiện NGHỈ (chỉ sinh khi `status=resigned` VÀ có
`resign_date` — thiếu `resign_date` thì KHÔNG tính, chỉ đếm riêng để báo vào
`notes`, Q4.3/key-insight của phase-04).

⚠️ Review 01/10/2026 (M3): "đang làm" = `status ≠ resigned` (Q4.3) — hồ sơ
`status=resigned` mà THIẾU `resign_date` trước đây bị tính nhầm là đang làm
(nhánh `resign_date IS NULL` của `OR` cũ luôn đúng). `_not_resigned_cond` sửa
lại: thiếu `resign_date` thì KHÔNG coi là đang làm nữa, ở MỌI mốc `as_of`.

`employees_as_of` (mới, phục vụ "Xem theo" cơ cấu — xem `report_service.py`)
trả nguyên nhân sự ĐANG LÀM tại một mốc dưới dạng `HeadcountEvent(kind="snapshot")`
để tái dùng ĐÚNG các `DimensionSpec.key_of` đã khai cho sự kiện vào/nghỉ — không
viết lại luật gom nhóm lần hai. Thâm niên tính TẠI NGÀY SNAPSHOT (`as_of`), không
phải "hôm nay" — một nhân sự "đang làm tại 2024" có thâm niên tính tới 2024.

Hiệu năng: MỌI lọc (ngày qua `range_filter`, trạng thái, phạm vi, CÔNG TY) nằm
trong SQL WHERE; `with_entities` chỉ nạp đúng cột cần. `company_id` lọc SAU
`apply_scope` ở mọi hàm (chỉ thu hẹp thêm, không mở rộng phạm vi).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.core.export_xlsx import VN_OFFSET
from app.core.report_period import range_filter, to_local_date
from app.core.scoping import apply_scope
from app.modules.employee.model import Employee
from app.modules.employee.service import STATUS_RESIGNED

#  (trần số năm — nửa mở, trần cuối = None nghĩa "trở lên", nhãn hiển thị)
_SENIORITY_BUCKETS = ((1, "Dưới 1 năm"), (3, "1-3 năm"), (5, "3-5 năm"), (None, "Trên 5 năm"))
#  Cột chiều DÙNG CHUNG cho mọi truy vấn sự kiện — `with_entities` chỉ nạp đúng 8 cột này,
#  không nạp cả dòng Employee (~40 cột, có cột JSON `extra_fields`).
_DIM_COLS = (Employee.company_id, Employee.department_id, Employee.job_level,
            Employee.employment_type, Employee.gender, Employee.position_id, Employee.position,
            Employee.status)


def vn_today() -> date:
    """"Hôm nay" theo giờ VN — container chạy UTC, cùng quy ước `report_period.parse_period`."""
    return (datetime.utcnow() + VN_OFFSET).date()


def effective_hire_date(hire_date, created_at) -> date | None:
    """Hồ sơ thiếu `hire_date` (dữ liệu cũ) → coi như có mặt từ lúc TẠO hồ sơ (Q4.2)."""
    return hire_date or to_local_date(created_at)


def seniority_bucket(hire_date: date | None, as_of: date) -> tuple[str, str]:
    """Thâm niên TÍNH TẠI `as_of` — sự kiện nghỉ dùng `resign_date`, snapshot dùng ngày mốc,
    sự kiện vào/tổng quan "hôm nay" dùng `vn_today()`. KHÔNG phải lúc nào cũng là "hôm nay"."""
    if hire_date is None or hire_date > as_of:
        return "", "(Chưa gắn)"
    years = (as_of - hire_date).days / 365.25
    for cap, label in _SENIORITY_BUCKETS:
        if cap is None or years < cap:
            return label, label
    return _SENIORITY_BUCKETS[-1][1], _SENIORITY_BUCKETS[-1][1]


@dataclass(frozen=True)
class HeadcountEvent:
    """Một sự kiện VÀO/NGHỈ/ẢNH CHỤP của một nhân sự — hàng nạp cho `build_report` hoặc để
    gom nhóm bằng `report_compute.bucket_rows` (snapshot "cơ cấu")."""

    kind: str  # "hire" | "resign" | "snapshot"
    event_date: date
    company_id: int
    department_id: int
    job_level: int
    employment_type: int
    gender: int
    position_id: int
    position_name: str
    status: str
    seniority_key: str
    seniority_label: str


def scoped_employee_query(db: Session, user, prof: dict, company_id: int | None = None):
    """H1: `company_id` lọc SAU `apply_scope` — chỉ THU HẸP thêm phạm vi đã có, không mở rộng."""
    q = apply_scope(db.query(Employee), Employee, "employee", user, prof)
    if company_id is not None:
        q = q.filter(Employee.company_id == company_id)
    return q


def _row_common(row) -> dict:
    return dict(company_id=row.company_id or 0, department_id=row.department_id or 0,
               job_level=row.job_level or 0, employment_type=row.employment_type or 0,
               gender=row.gender or 0, position_id=row.position_id or 0,
               position_name=row.position or "", status=row.status or "")


def _not_resigned_cond(as_of: date):
    """M3 (Q4.3): "đang làm" = `status ≠ resigned`. `status=resigned` mà THIẾU `resign_date`
    KHÔNG được coi là đang làm nữa (trước đây `resign_date IS NULL` luôn đúng → tính nhầm)."""
    return or_(Employee.status != STATUS_RESIGNED,
              and_(Employee.resign_date.isnot(None), Employee.resign_date > as_of))


def hire_events(db: Session, user, prof: dict, d_from: date, d_to: date, today: date,
                company_id: int | None = None) -> list[HeadcountEvent]:
    """`range_filter` lọc NGAY TRONG SQL — hai nhánh (có `hire_date`/lùi về `created_at`) vì
    hai cột khác kiểu (`Date`/`DateTime UTC`), không gộp được bằng một điều kiện cột đơn."""
    base = scoped_employee_query(db, user, prof, company_id)
    out: list[HeadcountEvent] = []
    for row in (base.filter(Employee.hire_date.isnot(None))
               .filter(range_filter(Employee.hire_date, "date", d_from, d_to))
               .with_entities(*_DIM_COLS, Employee.hire_date).all()):
        sen_key, sen_label = seniority_bucket(row.hire_date, today)
        out.append(HeadcountEvent(kind="hire", event_date=row.hire_date, seniority_key=sen_key,
                                  seniority_label=sen_label, **_row_common(row)))
    for row in (base.filter(Employee.hire_date.is_(None))
               .filter(range_filter(Employee.created_at, "datetime_utc", d_from, d_to))
               .with_entities(*_DIM_COLS, Employee.created_at).all()):
        eff = to_local_date(row.created_at)
        sen_key, sen_label = seniority_bucket(eff, today)
        out.append(HeadcountEvent(kind="hire", event_date=eff, seniority_key=sen_key,
                                  seniority_label=sen_label, **_row_common(row)))
    return out


def resign_events(db: Session, user, prof: dict, d_from: date, d_to: date,
                  company_id: int | None = None) -> list[HeadcountEvent]:
    """Thâm niên tính TẠI `resign_date` (lúc rời đi), KHÔNG tính tới hôm nay — người nghỉ 5 năm
    trước không thể "tích thêm thâm niên" sau khi đã thôi việc."""
    base = scoped_employee_query(db, user, prof, company_id)
    rows = (base.filter(Employee.status == STATUS_RESIGNED, Employee.resign_date.isnot(None))
           .filter(range_filter(Employee.resign_date, "date", d_from, d_to))
           .with_entities(*_DIM_COLS, Employee.hire_date, Employee.created_at,
                          Employee.resign_date).all())
    out = []
    for row in rows:
        eff_hire = effective_hire_date(row.hire_date, row.created_at)
        sen_key, sen_label = seniority_bucket(eff_hire, row.resign_date)
        out.append(HeadcountEvent(kind="resign", event_date=row.resign_date, seniority_key=sen_key,
                                  seniority_label=sen_label, **_row_common(row)))
    return out


def _as_of_filtered(base, as_of: date):
    """Hai nhánh (có/không `hire_date`) ĐÃ VÀO ≤ `as_of` VÀ ĐANG LÀM tại `as_of` — dùng chung
    cho `employees_as_of`/`headcount_as_of`."""
    not_resigned = _not_resigned_cond(as_of)
    as_of_next = as_of + timedelta(days=1)
    utc_cutoff = datetime.combine(as_of_next, time.min) - VN_OFFSET
    with_date = base.filter(Employee.hire_date.isnot(None), Employee.hire_date < as_of_next,
                            not_resigned)
    fallback = base.filter(Employee.hire_date.is_(None), Employee.created_at < utc_cutoff,
                           not_resigned)
    return with_date, fallback


def employees_as_of(db: Session, user, prof: dict, as_of: date,
                    company_id: int | None = None) -> list[HeadcountEvent]:
    """Toàn bộ nhân sự ĐANG LÀM tại `as_of`, dạng `HeadcountEvent(kind="snapshot")` để gom
    nhóm lại bằng `DimensionSpec.key_of` CÓ SẴN (xem `report_service._merge_group_headcount`).
    Đúng 2 câu SQL, KHÔNG tăng theo số nhân sự."""
    base = scoped_employee_query(db, user, prof, company_id)
    with_date, fallback = _as_of_filtered(base, as_of)
    out = []
    for row in with_date.with_entities(*_DIM_COLS, Employee.hire_date).all():
        sen_key, sen_label = seniority_bucket(row.hire_date, as_of)
        out.append(HeadcountEvent(kind="snapshot", event_date=as_of, seniority_key=sen_key,
                                  seniority_label=sen_label, **_row_common(row)))
    for row in fallback.with_entities(*_DIM_COLS, Employee.created_at).all():
        eff = to_local_date(row.created_at)
        sen_key, sen_label = seniority_bucket(eff, as_of)
        out.append(HeadcountEvent(kind="snapshot", event_date=as_of, seniority_key=sen_key,
                                  seniority_label=sen_label, **_row_common(row)))
    return out


def missing_resign_count(db: Session, user, prof: dict, company_id: int | None = None) -> int:
    return scoped_employee_query(db, user, prof, company_id).filter(
        Employee.status == STATUS_RESIGNED, Employee.resign_date.is_(None)).count()
