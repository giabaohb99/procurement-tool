"""Dựng `tab_work_cycle` — GIA TĂNG mỗi đêm + dựng lại toàn bộ (duoc-CR-656, D1a).

Giữ "mốc đã chạm tới" (watermark) ở `tab_setting` khóa `capability_cycle_watermark`. Mỗi lượt lấy lại
`since = watermark - 1 ngày` cho chắc (phiếu sửa đúng lúc job chạy). Số truy vấn mỗi lô cố định
(`cycle_sources`), ghi bằng: xóa dòng cũ của lô + chèn nhiều dòng — lặp lại không nhân đôi.
"""
import logging
from datetime import datetime, timedelta

from sqlalchemy import delete, insert, select
from sqlalchemy.orm import Session

from app.core.base_model import Base
from app.core.vn_time import vn_today
from app.modules.capability import cycle_sources as src
from app.modules.capability.cycle_compute import compute_cycles
from app.modules.capability.cycle_specs import SPECS, CycleSpec
from app.modules.capability.model import WorkCycle

log = logging.getLogger("app.capability.cycles")

WATERMARK_KEY = "capability_cycle_watermark"
OVERLAP = timedelta(days=1)


def _employee_info(db: Session, emp_ids: set[int]) -> dict[int, tuple[int, int]]:
    if not emp_ids:
        return {}
    e = Base.metadata.tables["tab_employee"]
    return {i: (int(c or 0), int(d or 0)) for i, c, d in db.execute(
        select(e.c.id, e.c.company_id, e.c.department_id).where(e.c.id.in_(sorted(emp_ids))))}


def rebuild_batch(db: Session, spec: CycleSpec, ids: list[int], now: datetime) -> int:
    """Tính lại một lô id (≤ BATCH) và ghi. Trả số dòng chèn. Phiếu đã xóa mềm bị gỡ khỏi bảng."""
    facts = src.build_facts(db, spec, ids)
    today = vn_today()
    rows: list[dict] = []
    for f in facts:
        rows.extend(compute_cycles(spec, f, now, today))
    info = _employee_info(db, {r["employee_id"] for r in rows})
    for r in rows:
        company, dept = info.get(r["employee_id"], (0, 0))
        r["department_id"] = dept
        r["company_id"] = company or r["company_id"]
    db.execute(delete(WorkCycle).where(WorkCycle.kind == int(spec.kind), WorkCycle.entity_id.in_(ids)))
    if rows:
        db.execute(insert(WorkCycle), rows)
    db.commit()
    return len(rows)


def build_all(db: Session, since: datetime | None, now: datetime | None = None, kinds: set[int] | None = None) -> dict:
    """Dựng cho mọi loại. `since=None` = toàn bộ (backfill). Trả `{kind: số dòng}`."""
    now = now or datetime.utcnow()
    result: dict[int, int] = {}
    for spec in SPECS:
        if kinds and int(spec.kind) not in kinds:
            continue
        ids = src.touched_ids(db, spec, since)
        n = 0
        for i in range(0, len(ids), src.BATCH):
            n += rebuild_batch(db, spec, ids[i:i + src.BATCH], now)
        result[int(spec.kind)] = n
    return result


def _get_watermark(db: Session) -> datetime | None:
    from app.modules.setting.model import Setting

    row = db.query(Setting).filter(Setting.skey == WATERMARK_KEY).first()
    try:
        return datetime.fromisoformat(row.svalue) if row and row.svalue else None
    except ValueError:
        return None


def _set_watermark(db: Session, value: datetime) -> None:
    from app.modules.setting.model import Setting

    row = db.query(Setting).filter(Setting.skey == WATERMARK_KEY).first()
    if row:
        row.svalue = value.isoformat()
    else:
        db.add(Setting(skey=WATERMARK_KEY, svalue=value.isoformat()))
    db.commit()


def run_incremental(db: Session, now: datetime | None = None) -> dict:
    """Lượt đêm: tính lại phiếu chạm tới từ `watermark - 1 ngày`; chưa có watermark → dựng toàn bộ.

    Watermark chỉ tiến SAU khi mọi loại dựng xong; một loại lỗi thì lượt sau tự thử lại từ mốc cũ.
    """
    now = now or datetime.utcnow()
    mark = _get_watermark(db)
    since = (mark - OVERLAP) if mark else None
    result = build_all(db, since, now)
    _set_watermark(db, now)
    log.info("Dựng vòng đời phiếu (since=%s): %s", since, result)
    return {"since": since.isoformat() if since else None, "rows": result}
