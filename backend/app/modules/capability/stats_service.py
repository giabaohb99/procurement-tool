"""Thống kê năng lực theo loại việc từ `tab_work_cycle` (duoc-CR-657, D1d) — DÙNG CHUNG cho báo cáo quản trị và hàm của trợ lý.

`fetch_stats` tốn ĐÚNG ≤ 4 truy vấn bất kể số người / số dòng:
  Q1 các dòng ĐÃ XONG, KHÔNG ước tính (cột cần tính, đã lọc kỳ + phạm vi)  ·  Q2 đếm riêng các dòng ƯỚC TÍNH (gom SQL)
  Q3 tên nhân sự  ·  Q4 tên loại việc.

Luật diễn giải (chốt 20/10/2026):
  · dòng `is_estimated` KHÔNG BAO GIỜ trộn vào p50/p90 — chỉ được đếm riêng ở `n_estimated` (đặt xe nhập từ hệ cũ toàn là dòng này);
  · số theo nhóm chỉ hiện khi ≥ `min_samples` (mặc định 5); dưới ngưỡng trả `None` + `below_threshold`;
  · "chậm" có thể chỉ là việc khó — hàm chỉ đo, không chấm điểm.

⚠️ KHÔNG TỰ GÁC QUYỀN. Người gọi kiểm quyền (khóa báo cáo 16) và truyền phạm vi. Muốn lấy KHÔNG lọc phạm vi phải bật `unrestricted=True`
một cách tường minh (đường API quản trị đã qua `require_report`); mặc định, không truyền phạm vi nào thì trả rỗng.
"""
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.base_model import Base
from app.core.capability_codes import CYCLE_KIND_LABELS, CycleKind, CycleOutcome, CycleRole
from app.modules.capability import stats_math
from app.modules.capability.model import WorkCycle as W

MAX_FETCH = 200_000        # trần số dòng đọc vào Python; kỳ tối đa ~3 năm
MAX_PERSON_ROWS = 2000


@dataclass(frozen=True)
class StatsFilter:
    date_from: date
    date_to: date
    role: CycleRole = CycleRole.HANDLER
    kinds: tuple[int, ...] = ()
    task_type_ids: tuple[int, ...] = ()
    company_id: int | None = None
    department_ids: tuple[int, ...] = ()
    employee_ids: tuple[int, ...] = ()
    min_samples: int = stats_math.MIN_SAMPLES
    unrestricted: bool = False

    @property
    def has_scope(self) -> bool:
        return bool(self.unrestricted or self.company_id or self.department_ids or self.employee_ids)


def _where(f: StatsFilter) -> list:
    start = datetime.combine(f.date_from, datetime.min.time()) - timedelta(hours=7)          # ngày VN → UTC naive
    end = datetime.combine(f.date_to + timedelta(days=1), datetime.min.time()) - timedelta(hours=7)
    conds = [W.role == int(f.role), W.outcome == int(CycleOutcome.DONE), W.done_at >= start, W.done_at < end]
    if f.kinds:
        conds.append(W.kind.in_(list(f.kinds)))
    if f.task_type_ids:
        conds.append(W.task_type_id.in_(list(f.task_type_ids)))
    if f.company_id:
        conds.append(W.company_id == f.company_id)
    if f.department_ids:
        conds.append(W.department_id.in_(list(f.department_ids)))
    if f.employee_ids:
        conds.append(W.employee_id.in_(list(f.employee_ids)))
    return conds


def _num(v) -> float | None:
    return None if v is None else float(v)


def fetch_stats(db: Session, f: StatsFilter) -> dict:
    """`{"types": [...], "people": [...], "n_estimated": int, "min_samples": int}` — xem module docstring."""
    empty = {"types": [], "people": [], "n_estimated": 0, "min_samples": f.min_samples, "truncated": False}
    if not f.has_scope:
        return empty
    conds = _where(f)
    rows = db.execute(
        select(W.kind, W.task_type_id, W.employee_id, W.cycle_hours, W.rework_count, W.is_late, W.estimate_hours, W.actual_hours)
        .where(*conds, W.is_estimated.is_(False)).limit(MAX_FETCH + 1)).all()
    est = db.execute(
        select(W.kind, W.task_type_id, W.employee_id, func.count())
        .where(*conds, W.is_estimated.is_(True)).group_by(W.kind, W.task_type_id, W.employee_id)).all()
    truncated = len(rows) > MAX_FETCH

    by_type, by_person = defaultdict(list), defaultdict(list)
    for kind, tid, emp, hours, rework, late, est_h, act_h in rows[:MAX_FETCH]:
        s = stats_math.Sample(_num(hours), int(rework or 0), late, _num(est_h), _num(act_h))
        by_type[(kind, tid)].append(s)
        by_person[(kind, tid, emp)].append(s)
    est_type, est_person = defaultdict(int), defaultdict(int)
    for kind, tid, emp, n in est:
        est_type[(kind, tid)] += n
        est_person[(kind, tid, emp)] += n

    #  Nhóm chỉ có dòng ước tính cũng phải hiện (n_done = 0) để người xem thấy "có việc nhưng chưa đo được".
    type_keys = set(by_type) | set(est_type)
    person_keys = set(by_person) | set(est_person)
    type_names = _type_names(db, {k[1] for k in type_keys if k[1]})
    names = _employees(db, {k[2] for k in person_keys})

    types = [{"kind": k, "kind_label": CYCLE_KIND_LABELS[CycleKind(k)], "task_type_id": t,
              "task_type_name": type_names.get(t, "Chưa chọn loại việc" if k == int(CycleKind.WORK_TASK) else ""),
              **stats_math.summarize(by_type.get((k, t), []), est_type.get((k, t), 0), f.min_samples)}
             for k, t in type_keys]
    people = []
    for k, t, e in person_keys:
        emp = names.get(e)
        people.append({"kind": k, "kind_label": CYCLE_KIND_LABELS[CycleKind(k)], "task_type_id": t,
                       "task_type_name": type_names.get(t, "Chưa chọn loại việc" if k == int(CycleKind.WORK_TASK) else ""),
                       "employee_id": e, "employee_code": emp[0] if emp else "", "full_name": emp[1] if emp else f"#{e}",
                       "department_id": emp[2] if emp else 0,
                       **stats_math.summarize(by_person.get((k, t, e), []), est_person.get((k, t, e), 0), f.min_samples)})
    order = lambda r: (-r["n_done"], r["kind"], r["task_type_id"], r.get("employee_id", 0))   # noqa: E731
    return {"types": sorted(types, key=order), "people": sorted(people, key=order)[:MAX_PERSON_ROWS],
            "n_estimated": sum(est_type.values()), "min_samples": f.min_samples, "truncated": truncated}


def task_type_stats(db: Session, f: StatsFilter, *, by_person: bool = True) -> list[dict]:
    """Chữ ký gọn cho nơi chỉ cần một tầng (trợ lý, kiểm thử)."""
    return fetch_stats(db, f)["people" if by_person else "types"]


def _employees(db: Session, ids: set[int]) -> dict[int, tuple[str, str, int]]:
    if not ids:
        return {}
    e = Base.metadata.tables["tab_employee"]
    return {i: (c or "", n or "", int(d or 0)) for i, c, n, d in db.execute(
        select(e.c.id, e.c.code, e.c.full_name, e.c.department_id).where(e.c.id.in_(sorted(ids))))}


def _type_names(db: Session, ids: set[int]) -> dict[int, str]:
    if not ids:
        return {}
    t = Base.metadata.tables["tab_work_task_type"]
    return {i: n or "" for i, n in db.execute(select(t.c.id, t.c.name).where(t.c.id.in_(sorted(ids))))}
