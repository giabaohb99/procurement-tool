"""Danh sách hồ sơ theo người (duoc-CR-641, phase 05) — SỐ TRUY VẤN CỐ ĐỊNH ≤ 5 bất kể số người:
(1) tuần nhãn mới nhất + «dữ liệu từ ngày» · (2) đếm · (3) trang GROUP BY trên `tab_usage_daily` ⨝ người/phòng ban ·
(4) nhóm so sánh của người trong trang (tên vai trò/pháp nhân JOIN sẵn) · (5) nhãn của trang.
Chỉ đọc `tab_usage_daily` + snapshot + nhãn — KHÔNG đọc request_log / ui_event lúc mở màn (nhanh, và đúng §7.7).
"""
from datetime import date

from sqlalchemy import and_, case, exists, func, literal, or_, select
from sqlalchemy.orm import Session

from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.role.model import Role
from app.modules.user.model import User, UserRole

from .metric_stats import rnd
from .model import UsageDaily, UserUsageLabel, UserUsageSnapshot
from .schema import ListFilters, parse_sort


def _escape_like(text: str) -> str:
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def cohort_name_columns():
    """(JOIN Role/Company) cho tên nhóm so sánh — dùng lại ở danh sách, hồ sơ, nhóm."""
    return func.coalesce(Role.name, Company.name)


def _base_filters(f: ListFilters, label_week: date | None) -> list:
    conds = [UsageDaily.day >= f.date_from, UsageDaily.day <= f.date_to]
    if f.company_id:
        conds.append(Employee.company_id == f.company_id)
    if f.department_id:
        conds.append(Employee.department_id == f.department_id)
    if f.role_id:
        conds.append(exists().where(UserRole.user_id == UsageDaily.user_id, UserRole.role_id == f.role_id))
    if f.q:
        like = f"%{_escape_like(f.q.strip())}%"
        conds.append(or_(Employee.full_name.like(like, escape="\\"), Employee.code.like(like, escape="\\")))
    if f.labels:
        if label_week is None:
            conds.append(literal(False))
        else:
            conds.append(exists().where(UserUsageLabel.user_id == UsageDaily.user_id,
                                        UserUsageLabel.period_start == label_week,
                                        UserUsageLabel.label.in_(f.labels)))
    return conds


def _joined(stmt):
    return (stmt.select_from(UsageDaily)
            .join(User, User.id == UsageDaily.user_id)
            .outerjoin(Employee, Employee.id == User.employee_id)
            .outerjoin(Department, Department.id == Employee.department_id)
            .outerjoin(Company, Company.id == Employee.company_id))


def latest_label_week_and_since(db: Session, date_to: date):
    """Query 1: tuần snapshot mới nhất ≤ `date_to` và ngày đầu tiên có dữ liệu."""
    row = db.execute(select(
        select(func.max(UserUsageSnapshot.period_start)).where(UserUsageSnapshot.period_start <= date_to)
        .scalar_subquery(),
        select(func.min(UsageDaily.day)).scalar_subquery())).one()
    return row[0], row[1]


def fetch_rows(db: Session, f: ListFilters, label_week: date | None, offset: int = 0, limit: int | None = None):
    net = case((UsageDaily.is_workday.is_(True), UsageDaily.work_capacity - UsageDaily.leave_days), else_=0.0)
    credit = case((and_(UsageDaily.is_workday.is_(True), UsageDaily.active.is_(True)),
                   UsageDaily.work_capacity - UsageDaily.leave_days), else_=0.0)
    cols = {
        "active_days": func.sum(case((and_(UsageDaily.is_workday.is_(True), UsageDaily.active.is_(True)), 1), else_=0)),
        "workdays_net": func.sum(net),
        "active_credit": func.sum(credit),
        "api_writes": func.sum(UsageDaily.api_writes),
        "docs_created": func.sum(UsageDaily.docs_created),
        "approvals": func.sum(UsageDaily.approvals),
        "exports": func.sum(UsageDaily.exports),
        "http_422": func.sum(UsageDaily.http_422),
        "last_active_day": func.max(case((UsageDaily.active.is_(True), UsageDaily.day), else_=None)),
    }
    active_ratio = cols["active_credit"] / func.nullif(cols["workdays_net"], 0)
    per100 = cols["http_422"] * 100.0 / func.nullif(cols["api_writes"], 0)
    sortable = {**cols, "active_ratio": active_ratio, "http_422_per_100_writes": per100,
                "full_name": func.coalesce(Employee.full_name, User.email), "emp_code": Employee.code}
    key, desc = parse_sort(f.sort)
    stmt = _joined(select(
        UsageDaily.user_id, Employee.id.label("employee_id"), Employee.full_name, User.email,
        Employee.code.label("emp_code"),
        Department.name.label("department_name"), Company.name.label("company_name"),
        *[c.label(k) for k, c in cols.items()]))
    stmt = (stmt.where(*_base_filters(f, label_week))
            .group_by(UsageDaily.user_id, Employee.id, Employee.full_name, User.email, Employee.code, Department.name,
                      Company.name)
            .order_by(sortable[key].desc() if desc else sortable[key].asc(), UsageDaily.user_id))
    if limit is not None:
        stmt = stmt.offset(offset).limit(limit)
    return db.execute(stmt).all()


def count_users(db: Session, f: ListFilters, label_week: date | None) -> int:
    stmt = _joined(select(func.count(func.distinct(UsageDaily.user_id)))).where(*_base_filters(f, label_week))
    return int(db.execute(stmt).scalar() or 0)


def decorate(db: Session, rows, label_week: date | None) -> list[dict]:
    """Queries 4–5: nhóm so sánh + nhãn của các người trong trang; dựng JSON dòng."""
    uids = [r.user_id for r in rows]
    cohorts, labels = {}, {}
    if uids and label_week:
        for sid, uid, kind, key, size, name in db.execute(
                select(UserUsageSnapshot.id, UserUsageSnapshot.user_id, UserUsageSnapshot.cohort_kind,
                       UserUsageSnapshot.cohort_key, UserUsageSnapshot.cohort_size, cohort_name_columns())
                .select_from(UserUsageSnapshot)
                .outerjoin(Role, and_(UserUsageSnapshot.cohort_kind == 1, Role.id == UserUsageSnapshot.cohort_key))
                .outerjoin(Company, and_(UserUsageSnapshot.cohort_kind == 2, Company.id == UserUsageSnapshot.cohort_key))
                .where(UserUsageSnapshot.period_start == label_week, UserUsageSnapshot.user_id.in_(uids))).all():
            cohorts[uid] = {"kind": kind, "key": key, "size": size, "name": name or ""}
        for uid, code, score in db.execute(
                select(UserUsageLabel.user_id, UserUsageLabel.label, UserUsageLabel.score)
                .where(UserUsageLabel.period_start == label_week, UserUsageLabel.user_id.in_(uids))
                .order_by(UserUsageLabel.score.desc(), UserUsageLabel.label)).all():
            labels.setdefault(uid, []).append({"code": code, "score": rnd(score, 3)})
    out = []
    for r in rows:
        #  MySQL trả SUM() dạng Decimal (SQLite trả float) — đổi hết sang số thường trước khi tính.
        net, credit, writes = float(r.workdays_net or 0), float(r.active_credit or 0), int(r.api_writes or 0)
        out.append({
            "user_id": r.user_id, "full_name": r.full_name or r.email or "", "emp_code": r.emp_code or "",
            "department_name": r.department_name or "", "company_name": r.company_name or "",
            "cohort": cohorts.get(r.user_id),
            "active_days": int(r.active_days or 0), "workdays_net": rnd(net, 2),
            "active_ratio": rnd(min(1.0, credit / net)) if net else None,
            "api_writes": writes, "docs_created": int(r.docs_created or 0),
            "approvals": int(r.approvals or 0), "exports": int(r.exports or 0),
            "http_422_per_100_writes": rnd(int(r.http_422 or 0) * 100.0 / writes, 2) if writes else None,
            "labels": labels.get(r.user_id, []),
            "last_active_day": r.last_active_day.isoformat() if r.last_active_day else None,
        })
    return out


def summary(db: Session, f: ListFilters, page: int, page_size: int) -> dict:
    label_week, since = latest_label_week_and_since(db, f.date_to)
    total = count_users(db, f, label_week)
    rows = fetch_rows(db, f, label_week, (page - 1) * page_size, page_size) if total else []
    return {"items": decorate(db, rows, label_week), "total": total, "page": page, "page_size": page_size,
            "period": {"date_from": f.date_from.isoformat(), "date_to": f.date_to.isoformat()},
            "label_week": label_week.isoformat() if label_week else None,
            "data_since": since.isoformat() if since else None}
