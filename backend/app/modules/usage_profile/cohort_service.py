"""`GET /cohorts` — các nhóm so sánh của một tuần và trung vị đã lưu (duoc-CR-641, phase 05). ≤ 3 truy vấn:
(1) tuần (mặc định = tuần snapshot mới nhất) · (2) nhóm + id snapshot đại diện + tên · (3) `metrics` của các snapshot đại diện."""
from datetime import date

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.core.usage_codes import PeriodKind
from app.modules.company.model import Company
from app.modules.role.model import Role

from .model import UserUsageSnapshot


def list_cohorts(db: Session, week: date | None) -> dict:
    S = UserUsageSnapshot
    if week is None:
        week = db.execute(select(func.max(S.period_start)).where(S.period_kind == int(PeriodKind.WEEK))).scalar()
    if week is None:
        return {"week": None, "cohorts": []}
    groups = db.execute(
        select(S.cohort_kind, S.cohort_key, func.max(S.cohort_size), func.min(S.id), func.min(Role.name),
               func.min(Company.name))
        .select_from(S)
        .outerjoin(Role, and_(S.cohort_kind == 1, Role.id == S.cohort_key))
        .outerjoin(Company, and_(S.cohort_kind == 2, Company.id == S.cohort_key))
        .where(S.period_kind == int(PeriodKind.WEEK), S.period_start == week)
        .group_by(S.cohort_kind, S.cohort_key).order_by(S.cohort_kind, S.cohort_key)).all()
    metrics_by_id = {sid: m for sid, m in db.execute(
        select(S.id, S.metrics).where(S.id.in_([g[3] for g in groups]))).all()} if groups else {}
    cohorts = []
    for kind, key, size, sid, role_name, company_name in groups:
        medians = {k: v.get("med") for k, v in (metrics_by_id.get(sid) or {}).get("metrics", {}).items()
                   if v.get("med") is not None}
        cohorts.append({"cohort_kind": kind, "cohort_key": key, "name": role_name or company_name or "",
                        "size": size, "medians": medians})
    return {"week": week.isoformat(), "cohorts": cohorts}
