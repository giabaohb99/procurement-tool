"""Đọc sổ việc chạy ngầm (bao-CR-703): danh sách việc theo lịch beat + lần chạy gần nhất + số 7 ngày; lịch sử một việc;
dọn sổ quá hạn giữ.
"""
from datetime import datetime, timedelta

from sqlalchemy import case, delete, func, select
from sqlalchemy.orm import Session

from app.core import app_settings
from app.core.job_run_codes import JOB_GROUP_LABELS, JOB_RUN_STATUS_LABELS, JobRunStatus
from app.core.logging_policy import CLEANUP_BATCH_SIZE, CLEANUP_MAX_BATCHES
from app.core.text_fold import fold

from .model import JobRun
from .registry import JOBS

SUMMARY_LIST_CHARS = 300
WEEKDAYS = {0: "Chủ nhật", 1: "thứ Hai", 2: "thứ Ba", 3: "thứ Tư", 4: "thứ Năm", 5: "thứ Sáu", 6: "thứ Bảy"}


# ── Lịch dạng dễ đọc ─────────────────────────────────────────────────────────────────────────────────────────────────
def _field(sched, name: str) -> str:
    return str(getattr(sched, f"_orig_{name}", "*"))


def _join_vi(items: list[str]) -> str:
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " và " + items[-1]


def schedule_label(sched) -> str:
    """crontab / số giây → chữ: "mỗi phút", "mỗi 15 phút", "02:45 mỗi ngày", "03:30 ngày 1 và 16", "05:15 thứ Hai"."""
    if isinstance(sched, (int, float)):
        return f"mỗi {int(sched)} giây"
    if isinstance(sched, timedelta):
        return f"mỗi {int(sched.total_seconds())} giây"
    if not hasattr(sched, "_orig_minute"):
        return str(sched)
    minute, hour = _field(sched, "minute"), _field(sched, "hour")
    dom, dow = _field(sched, "day_of_month"), _field(sched, "day_of_week")
    if hour == "*":
        if minute == "*":
            return "mỗi phút"
        if minute.startswith("*/"):
            return f"mỗi {minute[2:]} phút"
        return f"phút {_join_vi(minute.split(','))} mỗi giờ"
    hours = hour.split(",")
    mm = int(minute) if minute.isdigit() else 0
    at = _join_vi([f"{int(h):02d}:{mm:02d}" for h in hours if h.isdigit()]) or f"{hour}:{minute}"
    if dom != "*":
        return f"{at} ngày {_join_vi(dom.split(','))} hằng tháng"
    if dow != "*":
        days = [WEEKDAYS.get(int(d) % 7, d) for d in dow.split(",") if d.isdigit()]
        return f"{at} {_join_vi(days)} hằng tuần"
    return f"{at} mỗi ngày"


def next_run(sched, now: datetime | None = None) -> datetime | None:
    """Lần chạy kế (giờ VN, không múi): crontab tính bằng chính Celery (múi giờ của app); số giây thì now + số đó."""
    try:
        if isinstance(sched, (int, float)):
            return (now or datetime.now()) + timedelta(seconds=float(sched))
        if hasattr(sched, "remaining_estimate"):
            base = sched.now()
            nxt = base + sched.remaining_estimate(base) + timedelta(seconds=30)    # làm tròn về đúng phút
            return nxt.replace(tzinfo=None, second=0, microsecond=0)
    except Exception:  # noqa: BLE001 — lịch lạ thì bỏ trống, không làm hỏng danh sách
        return None
    return None


# ── Danh sách việc ───────────────────────────────────────────────────────────────────────────────────────────────────
def beat_jobs() -> dict[str, list]:
    """Tên task → các lịch beat của nó (một task có thể có nhiều mục, vd sao lưu sáng + chiều)."""
    from app.core.celery_app import celery_app

    out: dict[str, list] = {}
    for entry in (celery_app.conf.beat_schedule or {}).values():
        out.setdefault(entry["task"], []).append(entry["schedule"])
    return out


def _iso(d: datetime | None) -> str | None:
    return d.isoformat(timespec="seconds") if d else None


def serialize_run(r: JobRun, summary_chars: int = 0) -> dict:
    status = int(r.status or 0)
    summary = r.result_summary or ""
    return {"id": r.id, "job_code": r.task_name, "started_at": _iso(r.started_at), "finished_at": _iso(r.finished_at),
            "duration_ms": r.duration_ms, "status": status,
            "status_label": JOB_RUN_STATUS_LABELS.get(JobRunStatus(status), "") if status in (1, 2, 3, 4) else "",
            "summary": summary[:summary_chars] if summary_chars else summary, "error": r.error or ""}


def _last_runs(db: Session, codes: list[str]) -> dict[str, JobRun]:
    if not codes:
        return {}
    latest = (select(JobRun.task_name, func.max(JobRun.started_at).label("at")).where(JobRun.task_name.in_(codes))
              .group_by(JobRun.task_name).subquery())
    rows = db.scalars(select(JobRun).join(latest, (JobRun.task_name == latest.c.task_name)
                                          & (JobRun.started_at == latest.c.at)).order_by(JobRun.id))
    return {r.task_name: r for r in rows}       # cùng giây hai dòng thì dòng sau (id lớn) thắng


def _week_stats(db: Session, codes: list[str], now: datetime) -> dict[str, tuple]:
    if not codes:
        return {}
    ok = int(JobRunStatus.SUCCESS)
    rows = db.execute(
        select(JobRun.task_name, func.count(JobRun.id),
               func.sum(case((JobRun.status == int(JobRunStatus.FAILED), 1), else_=0)),
               func.avg(case((JobRun.status == ok, JobRun.duration_ms), else_=None)))
        .where(JobRun.task_name.in_(codes), JobRun.started_at >= now - timedelta(days=7))
        .group_by(JobRun.task_name))
    return {name: (int(n or 0), int(failed or 0), int(avg) if avg is not None else None) for name, n, failed, avg in rows}


def list_jobs(db: Session, *, group: str = "", status: int | None = None, q: str = "",
              now: datetime | None = None) -> dict:
    """Mọi việc có lịch beat + việc chạy theo yêu cầu có lần chạy trong 7 ngày. `status` lọc theo lần chạy GẦN NHẤT,
    0 = chưa chạy lần nào."""
    now = now or datetime.now()
    beats = beat_jobs()
    recent = {n for (n,) in db.execute(select(JobRun.task_name).where(JobRun.started_at >= now - timedelta(days=7))
                                       .distinct())}
    codes = sorted(set(beats) | recent)
    last, week = _last_runs(db, codes), _week_stats(db, codes, now)
    needle = fold(q.strip())
    items = []
    for code in codes:
        info = JOBS.get(code)
        name, purpose, grp = (info.name, info.purpose, info.group) if info else (code, "", "")
        if group and grp != group:
            continue
        if needle and needle not in fold(f"{name} {code} {purpose}"):
            continue
        run = last.get(code)
        if status is not None and (int(run.status) if run else 0) != int(status):
            continue
        scheds = beats.get(code, [])
        nexts = [n for n in (next_run(s, now) for s in scheds) if n]
        enabled = bool(app_settings.get(info.switch)) if info and info.switch else True
        runs, failed, avg = week.get(code, (0, 0, None))
        items.append({"code": code, "name": name, "purpose": purpose, "group": grp,
                      "group_label": JOB_GROUP_LABELS.get(grp, ""),
                      "schedule_label": "; ".join(dict.fromkeys(schedule_label(s) for s in scheds)) or "chạy theo yêu cầu",
                      "enabled": enabled, "next_run_at": _iso(min(nexts)) if nexts else None,
                      "last_run": serialize_run(run, SUMMARY_LIST_CHARS) if run else None,
                      "avg_duration_ms_7d": avg, "runs_7d": runs, "failed_7d": failed})
    items.sort(key=lambda x: (x["group"], x["name"]))
    return {"items": items,
            "groups": [{"code": k, "label": v} for k, v in JOB_GROUP_LABELS.items()],
            "statuses": [{"code": 0, "label": "Chưa chạy"}]
                        + [{"code": int(k), "label": v} for k, v in JOB_RUN_STATUS_LABELS.items()]}


def list_runs(db: Session, code: str, *, status: int | None = None, page: int = 1, page_size: int = 20) -> dict:
    base = select(JobRun).where(JobRun.task_name == code)
    if status:
        base = base.where(JobRun.status == int(status))
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    rows = db.scalars(base.order_by(JobRun.started_at.desc(), JobRun.id.desc()).offset((page - 1) * page_size).limit(page_size))
    return {"items": [serialize_run(r) for r in rows], "total": int(total), "page": page, "page_size": page_size}


# ── Dọn sổ ───────────────────────────────────────────────────────────────────────────────────────────────────────────
def keep_days() -> int:
    return max(0, int(app_settings.get("job_run_keep_days") or 0))


def cleanup(db: Session, *, now: datetime | None = None, days: int | None = None,
            max_batches: int = CLEANUP_MAX_BATCHES) -> dict:
    """Xóa dòng sổ cũ hơn N ngày (job_run_keep_days, mặc định 90; 0 = tắt), theo lô nhỏ như các việc dọn khác."""
    days = keep_days() if days is None else max(0, int(days))
    if not days:
        return {"status": "disabled", "deleted": 0}
    cutoff = (now or datetime.now()) - timedelta(days=days)
    deleted = batches = 0
    while batches < max_batches:
        ids = list(db.scalars(select(JobRun.id).where(JobRun.started_at < cutoff).order_by(JobRun.id)
                              .limit(CLEANUP_BATCH_SIZE)))
        if not ids:
            break
        db.execute(delete(JobRun).where(JobRun.id.in_(ids)))
        db.commit()
        deleted += len(ids)
        batches += 1
    return {"status": "partial" if batches >= max_batches else "success", "deleted": deleted, "keep_days": days,
            "cutoff": cutoff.isoformat(timespec="seconds")}
