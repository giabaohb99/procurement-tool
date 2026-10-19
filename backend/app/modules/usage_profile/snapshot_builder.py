"""Dựng snapshot tuần cho cả công ty và ghi idempotent (duoc-CR-641, phase 04).

Khuôn `metrics` (schema_version = 1) chỉ chứa SỐ và MÃ — không tên người, không bình luận, không từ khóa. Chuỗi chỉ xuất
hiện ở: khóa chỉ số (định danh trong `metric_catalog`), route mẫu, tên entity. Sẵn cho pha 4 (AI đọc hồ sơ).
Chỉ số không đo được nằm ở `unmeasured` kèm mã lý do (`UnmeasuredReason`), KHÔNG bao giờ ghi 0 thay thế.
"""
from collections import defaultdict
from datetime import date, datetime, timedelta

from sqlalchemy import delete, insert, select
from sqlalchemy.orm import Session

from app.core.usage_codes import PeriodKind, UnmeasuredReason
from app.core.vn_time import vn_today

from .cohort import assign_cohorts, cohort_stats
from .label_rules import LabelContext, evaluate_labels
from .metric_catalog import METRIC_CATALOG
from .metric_partial import Partial
from .metric_stats import rnd
from .model import UserUsageLabel, UserUsageSnapshot
from .snapshot_metrics_flow import (approval_metrics, batch_approval_share, chain_metrics,
                                    notification_metrics, work_task_metrics)
from .snapshot_metrics_misc import export_entity_weeks, misc_metrics
from .snapshot_metrics_rhythm import rhythm_metrics
from .snapshot_metrics_screens import docs_forms_metrics, screens_metrics
from .snapshot_paths import path_metrics
from .snapshot_sources import SnapshotSources, load_snapshot_sources

SCHEMA_VERSION = 1


def monday_of(day: date) -> date:
    return day - timedelta(days=day.weekday())


def last_full_week_start(today: date | None = None) -> date:
    """Thứ Hai của tuần ĐÃ KẾT THÚC gần nhất (chạy thứ Hai 05:15 → tuần vừa qua)."""
    return monday_of(today or vn_today()) - timedelta(days=7)


def _group(rows, idx=None):
    out = defaultdict(list)
    for r in rows:
        out[r.user_id if idx is None else r[idx]].append(r)
    return out


def _user_partials(src: SnapshotSources, uid: int, emp: int, rows: list, old: list, ui_ok: bool,
                   shared: dict[str, dict], export_weeks: dict[int, int]) -> Partial:
    p = Partial()
    p.merge(rhythm_metrics(rows)).merge(screens_metrics(rows, ui_ok)).merge(docs_forms_metrics(rows, old, ui_ok))
    p.merge(misc_metrics(src, uid, emp, rows, old))
    for part in shared.values():
        if uid in part:
            p.merge(part[uid])
    p.put("export_entity_weeks_max", export_weeks.get(uid, 0))
    return p


def _fill_unmeasured(p: Partial, ui_ok: bool) -> None:
    for key, meta in METRIC_CATALOG.items():
        if key not in p.values and key not in p.unmeasured:
            p.unmeasured[key] = int(UnmeasuredReason.NOT_COLLECTED if (meta.phase == 2 and not ui_ok)
                                    else UnmeasuredReason.NOT_APPLICABLE)


def build_snapshots(db: Session, week_start: date, now: datetime | None = None) -> int:
    """Dựng và ghi snapshot + nhãn cho tuần `week_start` (thứ Hai). Trả số snapshot đã ghi."""
    week_start = monday_of(week_start)
    src = load_snapshot_sources(db, week_start)
    win = src.window
    users = {u[0]: u for u in src.users}
    emp_user = {u[2]: u[0] for u in src.users if u[2]}
    daily = _group(src.daily)
    old = _group(src.daily_old, 0)
    measured = {uid: (users[uid][3] or 0) for uid in daily if uid in users and users[uid][1]}
    ui_ok = src.tracking_since is not None and src.tracking_since < win.hi
    notif = notification_metrics(src.notifications, src.mentions, src.replies)
    shared = {
        "chains": chain_metrics(src.chain_audits, win.utc_lo, win.utc_hi),
        "approvals": approval_metrics(src.tasks, src.siblings, src.instances, emp_user, win.utc_lo, win.utc_hi),
        "batch": batch_approval_share(src.decisions),
        "notif": notif,
        "paths": path_metrics(src.pageviews) if ui_ok else {},
        "work": work_task_metrics(src.work_tasks, emp_user, win.hi),
    }
    export_weeks = export_entity_weeks(src)
    partials: dict[int, Partial] = {}
    for uid in measured:
        partials[uid] = _user_partials(src, uid, users[uid][2] or 0, daily[uid], old.get(uid, []), ui_ok, shared,
                                       export_weeks)
        _fill_unmeasured(partials[uid], ui_ok)

    cohorts = assign_cohorts(measured, src.user_roles, src.roles)
    stats = cohort_stats(cohorts, {uid: p.values for uid, p in partials.items()})
    prev = {(u, ps): m for u, ps, m in src.prev_snapshots}
    prev_starts = [week_start - timedelta(weeks=i) for i in (3, 2, 1)]

    now = now or datetime.utcnow()
    rows, labels_by_user = [], {}
    for uid, p in partials.items():
        c = cohorts[uid]
        st = stats[(c.kind, c.key)]
        metrics = {}
        for key, val in p.values.items():
            hist = [((prev.get((uid, ps)) or {}).get("metrics", {}).get(key) or {}).get("v") for ps in prev_starts]
            metrics[key] = {"v": val, "med": rnd(st.get(key, (None, None))[0]),
                            "p75": rnd(st.get(key, (None, None))[1]), "trend": [*hist, val]}
        hire = users[uid][4]
        tenure = (week_start + timedelta(days=6) - hire).days if hire else None
        ctx = LabelContext(v=p.values, med={k: m["med"] for k, m in metrics.items() if m["med"] is not None},
                           p75={k: m["p75"] for k, m in metrics.items() if m["p75"] is not None},
                           counts=p.counts, tenure_days=tenure)
        labels = evaluate_labels(ctx)
        labels_by_user[uid] = labels
        drows = daily[uid]
        rows.append({
            "user_id": uid, "period_kind": int(PeriodKind.WEEK), "period_start": week_start,
            "window_weeks": 4, "schema_version": SCHEMA_VERSION, "cohort_kind": c.kind,
            "cohort_key": c.key, "cohort_size": c.size, "computed_at": now,
            "metrics": {
                "period": {"start": win.lo.isoformat(), "end": (week_start + timedelta(days=6)).isoformat(),
                           "window_weeks": 4},
                "subject": {"tenure_days": tenure, "cohort_role_id": c.key if c.kind == 1 else None},
                "context": {"workdays_net": p.values.get("workdays_net"),
                            "leave_days": rnd(sum(r.leave_days for r in drows)),
                            "holidays": sum(1 for r in drows if r.is_holiday),
                            "on_behalf_received": p.values.get("on_behalf_received", 0),
                            "tracking_since": src.tracking_since.isoformat() if src.tracking_since else None},
                "metrics": metrics, "lists": p.lists, "counts": p.counts, "unmeasured": p.unmeasured,
                "labels": labels,
            },
        })
    return _write(db, week_start, rows, labels_by_user)


def _write(db: Session, week_start: date, rows: list[dict], labels_by_user: dict) -> int:
    """Xóa nhãn rồi snapshot của tuần, INSERT lại — chạy lại không nhân đôi."""
    snap_ids = select(UserUsageSnapshot.id).where(UserUsageSnapshot.period_kind == int(PeriodKind.WEEK),
                                                  UserUsageSnapshot.period_start == week_start)
    db.execute(delete(UserUsageLabel).where(UserUsageLabel.snapshot_id.in_(snap_ids)))
    db.execute(delete(UserUsageSnapshot).where(UserUsageSnapshot.period_kind == int(PeriodKind.WEEK),
                                               UserUsageSnapshot.period_start == week_start))
    if rows:
        db.execute(insert(UserUsageSnapshot.__table__), rows)
        id_of = {uid: sid for sid, uid in db.execute(
            select(UserUsageSnapshot.id, UserUsageSnapshot.user_id).where(
                UserUsageSnapshot.period_kind == int(PeriodKind.WEEK), UserUsageSnapshot.period_start == week_start))}
        label_rows = [{"snapshot_id": id_of[uid], "user_id": uid, "period_start": week_start, "label": l["code"],
                       "score": l["score"], "evidence": l["evidence"]}
                      for uid, labels in labels_by_user.items() for l in labels]
        if label_rows:
            db.execute(insert(UserUsageLabel.__table__), label_rows)
    db.commit()
    return len(rows)
