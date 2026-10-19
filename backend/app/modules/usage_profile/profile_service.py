"""Hồ sơ một người (duoc-CR-641, phase 05) — SỐ TRUY VẤN CỐ ĐỊNH ≤ 6 bất kể `weeks`:
(1) người + nhân sự + phòng/pháp nhân · (2) snapshot N tuần (kèm tên nhóm so sánh) · (3) nhãn N tuần ·
(4) `tab_usage_daily` `weeks × 7` ngày gần nhất · (5) vai trò của người · (6) ngày bắt đầu có dữ liệu / thu thập UI.
Chỉ đọc số gom + snapshot; trường văn bản duy nhất trả ra là họ tên, mã NV, phòng ban, pháp nhân, chức vụ, tên vai trò."""
from collections import defaultdict

from fastapi import HTTPException
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.core.usage_codes import PeriodKind
from app.core.vn_time import vn_today
from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.role.model import Role
from app.modules.user.model import User, UserRole

from .metric_catalog import DEFERRED_METRICS, METRIC_CATALOG
from .metric_stats import rnd
from .model import UsageDaily, UserUsageLabel, UserUsageSnapshot

SCREENS_SOURCE_UI, SCREENS_SOURCE_API = 1, 2
TOP_SCREENS = 20


def _daily_json(r) -> dict:
    return {"day": r.day.isoformat(), "active": bool(r.active), "is_workday": bool(r.is_workday),
            "is_holiday": bool(r.is_holiday), "work_capacity": r.work_capacity, "leave_days": r.leave_days,
            "first_seen_min": r.first_seen_min, "last_action_min": r.last_action_min,
            "work_bursts": r.work_bursts, "active_minutes": r.active_minutes,
            "api_reads": r.api_reads, "api_writes": r.api_writes, "writes_offhours": r.writes_offhours,
            "approvals": r.approvals, "exports": r.exports, "http_403": r.http_403, "http_422": r.http_422,
            "page_views": r.page_views, "on_behalf_received": r.on_behalf_received}


def _aggregate_screens(rows) -> tuple[list[dict], int]:
    agg: dict[str, list[int]] = defaultdict(lambda: [0, 0, 0])
    for r in rows:
        for route, (v, d, a) in (r.screens or {}).items():
            slot = agg[route]
            slot[0] += v
            slot[1] += d
            slot[2] += a
    use_ui = any(r.page_views > 0 for r in rows)
    order = sorted(agg.items(), key=lambda kv: (kv[1][0], kv[1][2]) if use_ui else (kv[1][2], kv[1][0]), reverse=True)
    return ([{"route": k, "views": v[0], "dwell_ms": v[1], "api_calls": v[2]} for k, v in order[:TOP_SCREENS]],
            SCREENS_SOURCE_UI if use_ui else SCREENS_SOURCE_API)


def get_profile(db: Session, user_id: int, weeks: int) -> dict:
    head = db.execute(
        select(User.id, Employee.id, func.coalesce(Employee.full_name, User.email), Employee.code, Employee.position, Employee.hire_date,
               Department.name, Company.name)
        .select_from(User).outerjoin(Employee, Employee.id == User.employee_id)
        .outerjoin(Department, Department.id == Employee.department_id)
        .outerjoin(Company, Company.id == Employee.company_id).where(User.id == user_id)).first()
    if head is None:
        raise HTTPException(404, "Không tìm thấy người dùng")
    _uid, _emp, full_name, code, position, hire, dept_name, company_name = head

    S = UserUsageSnapshot
    today = vn_today()
    #  «N tuần gần nhất CÓ DỮ LIỆU» (sắp giảm dần + LIMIT) chứ không tính ngược từ hôm nay: job tuần trễ vài ngày thì
    #  hồ sơ vẫn thấy snapshot mới nhất, không rỗng.
    snaps = list(reversed(db.execute(
        select(S.id, S.period_start, S.cohort_kind, S.cohort_key, S.cohort_size, S.metrics, S.schema_version,
               func.coalesce(Role.name, Company.name))
        .select_from(S)
        .outerjoin(Role, and_(S.cohort_kind == 1, Role.id == S.cohort_key))
        .outerjoin(Company, and_(S.cohort_kind == 2, Company.id == S.cohort_key))
        .where(S.user_id == user_id, S.period_kind == int(PeriodKind.WEEK))
        .order_by(S.period_start.desc()).limit(weeks)).all()))
    labels: dict[int, list[dict]] = defaultdict(list)
    if snaps:
        for sid, code_, score, evidence in db.execute(
                select(UserUsageLabel.snapshot_id, UserUsageLabel.label, UserUsageLabel.score, UserUsageLabel.evidence)
                .where(UserUsageLabel.snapshot_id.in_([sn[0] for sn in snaps]))
                .order_by(UserUsageLabel.score.desc(), UserUsageLabel.label)).all():
            labels[sid].append({"code": code_, "score": rnd(score, 3), "evidence": evidence or []})

    daily = list(reversed(list(db.execute(
        select(UsageDaily).where(UsageDaily.user_id == user_id).order_by(UsageDaily.day.desc())
        .limit(weeks * 7)).scalars())))
    role_names = [n for (n,) in db.execute(select(Role.name).join(UserRole, UserRole.role_id == Role.id)
                                           .where(UserRole.user_id == user_id).order_by(Role.name)).all()]
    since, tracking_since = db.execute(select(func.min(UsageDaily.day),
                                              select(func.min(UsageDaily.day)).where(UsageDaily.page_views > 0)
                                              .scalar_subquery())).one()

    latest = None
    if snaps:
        sid, start, kind, key, size, metrics, version, cname = snaps[-1]
        latest = {"period_start": start.isoformat(), "schema_version": version,
                  "cohort": {"kind": kind, "key": key, "size": size, "name": cname or ""},
                  "period": metrics.get("period"), "context": metrics.get("context"),
                  "metrics": metrics.get("metrics", {}), "lists": metrics.get("lists", {}),
                  "counts": metrics.get("counts", {}), "unmeasured": metrics.get("unmeasured", {}),
                  "labels": labels.get(sid, [])}
    grid = [[0] * 24 for _ in range(7)]
    for r in daily:
        for h, n in enumerate(r.hourly or []):
            grid[r.day.weekday()][h] += n
    screens, source = _aggregate_screens(daily)
    return {
        "subject": {"user_id": user_id, "full_name": full_name or "", "emp_code": code or "",
                    "position": position or "", "department_name": dept_name or "", "company_name": company_name or "",
                    "role_names": role_names, "hire_date": hire.isoformat() if hire else None,
                    "tenure_days": (today - hire).days if hire else None},
        "latest": latest,
        "weekly": [{"period_start": s[1].isoformat(), "cohort_size": s[4],
                    "metrics": {k: v.get("v") for k, v in s[5].get("metrics", {}).items()},
                    "labels": [l["code"] for l in labels.get(s[0], [])]} for s in snaps],
        "daily": [_daily_json(r) for r in daily],
        "heatmap": grid,
        "screens": screens, "screens_source": source,
        "metric_meta": {k: {"unit": m.unit, "section": m.section, "phase": m.phase, "direction": m.direction}
                        for k, m in METRIC_CATALOG.items()},
        "deferred_metrics": list(DEFERRED_METRICS),
        "data_since": since.isoformat() if since else None,
        "tracking_since": tracking_since.isoformat() if tracking_since else None,
    }
