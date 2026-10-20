"""Đọc báo cáo «Mức dùng chức năng» (duoc-CR-655, D0c) — số truy vấn CỐ ĐỊNH, gom bằng SQL trên `tab_feature_usage_daily`.

KHÔNG có `user_id` / tên người trong kết quả: chỉ có «bao nhiêu người khác nhau» và phân rã theo phòng ban.
`/summary` = 3 truy vấn (gom theo chức năng · mẫu số người hoạt động · mốc bắt đầu thu). `/breakdown` = 2 truy vấn.
«Chức năng không ai dùng» lấy từ danh mục mã (UiAction / UiForm) trừ đi mã đã thấy; màn hình chưa ai mở do giao diện so với menu.
"""
from dataclasses import dataclass
from datetime import date

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.ui_action_codes import UiAction
from app.core.usage_codes import FeatureKind as K
from app.core.usage_codes import UiForm
from app.modules.department.model import Department
from app.modules.usage_profile.model import UsageDaily

from .model import FeatureUsageDaily as F

MAX_ROWS_PER_KIND = 300   # trần danh sách mỗi loại (route mẫu có hạn, trần để chặn thân phình)


@dataclass(frozen=True)
class Filters:
    date_from: date
    date_to: date
    company_id: int | None = None
    department_id: int | None = None


def _where(model, f: Filters) -> list:
    conds = [model.day >= f.date_from, model.day <= f.date_to]
    if f.company_id:
        conds.append(model.company_id == f.company_id)
    if f.department_id:
        conds.append(model.department_id == f.department_id)
    return conds


def _aggs():
    return (func.count(func.distinct(F.user_id)), func.sum(F.uses), func.sum(F.completes), func.sum(F.abandons),
            func.sum(F.fails), func.sum(F.duration_ms))


def _row(kind: int, code: int, route: str, a: tuple) -> dict:
    users, uses, completes, abandons, fails, duration = a
    return {"kind": int(kind), "code": int(code), "route": route, "users": int(users or 0), "uses": int(uses or 0),
            "completes": int(completes or 0), "abandons": int(abandons or 0), "fails": int(fails or 0),
            "duration_ms": int(duration or 0)}


def summary(db: Session, f: Filters) -> dict:
    rows = db.execute(select(F.kind, F.code, F.route, *_aggs()).where(*_where(F, f))
                      .group_by(F.kind, F.code, F.route)).all()
    active_users = db.execute(select(func.count(func.distinct(UsageDaily.user_id)))
                              .where(UsageDaily.active.is_(True), *_where(UsageDaily, f))).scalar() or 0
    tracking_since = db.execute(select(func.min(F.day))).scalar()

    items = [_row(r[0], r[1], r[2], r[3:]) for r in rows]
    by_kind = {k: sorted((i for i in items if i["kind"] == int(k)), key=lambda i: (-i["users"], -i["uses"], i["route"]))
               [:MAX_ROWS_PER_KIND] for k in K}
    seen_actions = {i["code"] for i in items if i["kind"] == int(K.ACTION)}
    seen_forms = {i["code"] for i in items if i["kind"] == int(K.FORM)}
    return {
        "period": {"date_from": f.date_from.isoformat(), "date_to": f.date_to.isoformat()},
        "tracking_since": tracking_since.isoformat() if tracking_since else None,
        "has_data": bool(items),
        "active_users": int(active_users),
        "actions": by_kind[K.ACTION], "forms": by_kind[K.FORM], "screens": by_kind[K.SCREEN],
        "searches": by_kind[K.SEARCH], "errors": by_kind[K.CLIENT_ERROR],
        "unused_actions": sorted(int(a) for a in UiAction if int(a) not in seen_actions),
        "unused_forms": sorted(int(x) for x in UiForm if int(x) not in seen_forms),
    }


def breakdown(db: Session, f: Filters, kind: int, code: int, route: str) -> dict:
    """Một chức năng theo phòng ban (bắt buộc) và theo màn (chỉ hữu ích cho ACTION dùng ở nhiều màn)."""
    try:
        K(kind)
    except ValueError:
        raise HTTPException(422, f"Loại chức năng không hợp lệ: {kind}")
    feat = [F.kind == kind, F.code == code]
    if kind in (int(K.SCREEN), int(K.SEARCH), int(K.CLIENT_ERROR)):
        feat.append(F.route == route)
    by_dept = db.execute(
        select(F.department_id, func.max(Department.name), *_aggs())
        .select_from(F).outerjoin(Department, Department.id == F.department_id)
        .where(*_where(F, f), *feat).group_by(F.department_id)).all()
    by_route = db.execute(select(F.route, *_aggs()).where(*_where(F, f), *feat).group_by(F.route)).all() \
        if kind == int(K.ACTION) else []
    return {
        "kind": kind, "code": code, "route": route,
        "by_department": sorted((dict(_row(kind, code, route, r[2:]), department_id=int(r[0] or 0),
                                      department_name=r[1] or "") for r in by_dept),
                                key=lambda i: (-i["users"], -i["uses"])),
        "by_route": sorted((_row(kind, code, r[0], r[1:]) for r in by_route), key=lambda i: (-i["users"], -i["uses"])),
    }
