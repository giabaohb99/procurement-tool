"""Đọc dữ kiện để dựng vòng đời phiếu — SỐ TRUY VẤN CỐ ĐỊNH theo (loại × lô), không theo số phiếu (duoc-CR-656, D1a).

Một lô ≤ `BATCH` id. Mỗi lô tốn: 1 (dòng phiếu) + 0–1 (người xử lý) + 1 (nhật ký thay đổi) + 0–1 (audit)
+ 2–3 (bảng tra nhân sự). Dùng Core + `Base.metadata.tables` thay vì lớp ORM để một bảng đổi tên lớp không làm gãy đây.

Chọn tập phiếu «chạm tới»: `updated_at >= since` (cột này được cập nhật cả ở UPDATE hàng loạt) cộng bảng con
(dòng hàng YCMH, dòng YCBG, người phụ trách task) — nhờ vậy cả phiếu nhập từ hệ khác không qua nhật ký vẫn được tính.
"""
from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.base_model import Base
from app.core.capability_codes import CycleKind
from app.modules.capability.cycle_compute import Facts
from app.modules.capability.cycle_specs import SPEC_BY_KIND, CycleSpec, Ev, event_from_status_change

BATCH = 1000


def _t(name: str):
    return Base.metadata.tables[name]


def vn_midnight_utc(text: str) -> datetime | None:
    """«YYYY-MM-DD» (ngày VN) → 00:00 giờ VN dạng UTC naive. Rỗng / sai → None."""
    try:
        return datetime.combine(date.fromisoformat((text or "")[:10]), datetime.min.time()) - timedelta(hours=7)
    except ValueError:
        return None


def as_datetime(value) -> datetime | None:
    """Cột mốc có bảng lưu `DateTime`, có bảng lưu chuỗi ISO (Đặt xe, Duyệt dấu: `approved_at`, `completed_at`).

    Chuỗi ISO do `datetime.now()` ghi trong container UTC nên coi là UTC naive, giống cột `DateTime`.
    """
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(value) if value else None
    except (TypeError, ValueError):
        return None


def touched_ids(db: Session, spec: CycleSpec, since: datetime | None) -> list[int]:
    """Id phiếu cần tính lại. `since=None` = TẤT CẢ (backfill)."""
    table = _t(spec.table)
    q = select(table.c.id)
    if since is not None:
        q = q.where(table.c.updated_at >= since)
    ids = {r[0] for r in db.execute(q)}
    child = _CHILD.get(spec.kind)
    if child:
        child_table, fk = child
        cq = select(_t(child_table).c[fk])
        if since is not None:
            cq = cq.where(_t(child_table).c.updated_at >= since)
        ids |= {r[0] for r in db.execute(cq)}
    return sorted(ids)


#  Bảng con quyết định «ai xử lý»: đổi dòng con không chạm `updated_at` của phiếu cha.
_CHILD = {
    CycleKind.PURCHASE_REQUEST: ("tab_purchase_request_item", "pr_id"),
    CycleKind.SURVEY_REQUEST: ("tab_survey_request_line", "survey_request_id"),
    CycleKind.WORK_TASK: ("tab_work_task_assignee", "task_id"),
}

#  (cột người lập, cách đọc): `emp` = đã là employee_id; `user` = là user_id → đổi sang employee_id.
_CREATOR = {
    CycleKind.PURCHASE_REQUEST: ("requester_id", "emp"),
    CycleKind.SURVEY_REQUEST: ("requester_id", "emp"),
    CycleKind.PURCHASE_ORDER: ("created_by", "user"),
    CycleKind.PAYMENT_REQUEST: ("created_by", "user"),
    CycleKind.DOCUMENT: ("drafter_employee_id", "emp"),
    CycleKind.VEHICLE_BOOKING: ("requester_id", "emp"),
    CycleKind.SEAL_REQUEST: ("requester_id", "emp"),
    CycleKind.ROOM_BOOKING: ("requester_employee_id", "emp"),
    CycleKind.LEAVE_REQUEST: ("employee_id", "emp"),
    CycleKind.WORK_TASK: ("creator_employee_id", "emp"),
}


def build_facts(db: Session, spec: CycleSpec, ids: list[int]) -> list[Facts]:
    """Dựng `Facts` cho một lô id (≤ BATCH). Phiếu đã xóa mềm bị bỏ qua (nơi gọi sẽ xóa dòng cũ)."""
    if not ids:
        return []
    table = _t(spec.table)
    rows = db.execute(select(table).where(table.c.id.in_(ids))).mappings().all()
    rows = [r for r in rows if not _is_deleted(r)]
    if not rows:
        return []
    row_ids = [r["id"] for r in rows]

    events = _status_events(db, spec, row_ids)
    handlers = _handlers(db, spec, rows)
    users = _user_employees(db, [r[_CREATOR[spec.kind][0]] for r in rows] +
                            ([r["completed_by"] for r in rows] if spec.kind == CycleKind.SEAL_REQUEST else []))
    out = []
    for r in rows:
        col, mode = _CREATOR[spec.kind]
        creator = int(r[col] or 0) if mode == "emp" else users.get(int(r[col] or 0), 0)
        hs = handlers.get(r["id"], [])
        if spec.kind == CycleKind.SEAL_REQUEST and r["completed_by"]:
            emp = users.get(int(r["completed_by"]), 0)
            if emp:
                hs = [(emp, as_datetime(r.get("approved_at")) or r["created_at"])]
        f = Facts(entity_id=r["id"], status=str(r["status"]), created_at=r["created_at"],
                  updated_at=r["updated_at"], company_id=int(r.get("company_id") or 0), creator_id=creator,
                  handlers=hs, events=events.get(r["id"], []))
        if spec.done_ts_col:
            f.done_ts = as_datetime(r.get(spec.done_ts_col))
        if spec.kind == CycleKind.WORK_TASK:
            f.due_date, f.task_type_id = r["due_date"] or "", int(r["task_type_id"] or 0)
            f.estimate_hours, f.actual_hours, f.review_outcome = r["estimate_hours"], r["actual_hours"], int(r["outcome"] or 0)
        out.append(f)
    return out


def _is_deleted(r) -> bool:
    if r.get("is_deleted"):
        return True
    return r.get("deleted_at") is not None and "is_deleted" not in r


def _status_events(db: Session, spec: CycleSpec, ids: list[int]) -> dict[int, list]:
    """Sự kiện chuẩn hóa từ nhật ký thay đổi (mọi loại) + audit (4 chứng từ Thu mua)."""
    out: dict[int, list] = {}
    cl = _t("tab_change_log")
    for rid, before, after, at in db.execute(
            select(cl.c.row_id, cl.c.before_value, cl.c.after_value, cl.c.created_at)
            .where(cl.c.table_name == spec.table, cl.c.field == "status", cl.c.op == 2, cl.c.row_id.in_(ids))):
        ev = event_from_status_change(spec, before, after)
        if ev is not None:
            out.setdefault(rid, []).append((at, ev))
    if spec.audit_entity:
        al = _t("tab_audit_log")
        for rid, action, at in db.execute(
                select(al.c.entity_id, al.c.action, al.c.created_at)
                .where(al.c.entity == spec.audit_entity, al.c.entity_id.in_(ids),
                       al.c.action.in_(list(spec.audit_map)))):
            out.setdefault(rid, []).append((at, spec.audit_map[action]))
    return out


def _user_employees(db: Session, user_ids: list) -> dict[int, int]:
    wanted = sorted({int(u) for u in user_ids if u})
    if not wanted:
        return {}
    u = _t("tab_user")
    return {i: int(e or 0) for i, e in db.execute(select(u.c.id, u.c.employee_id).where(u.c.id.in_(wanted)))}


def _codes_to_ids(db: Session, codes: set[str]) -> dict[str, int]:
    if not codes:
        return {}
    e = _t("tab_employee")
    return {c: i for i, c in db.execute(select(e.c.id, e.c.code).where(e.c.code.in_(sorted(codes))))}


def _handlers(db: Session, spec: CycleSpec, rows) -> dict[int, list]:
    """`{phiếu: [(employee_id, mốc bắt đầu)]}` — mỗi người một mục, lấy mốc SỚM nhất."""
    ids = [r["id"] for r in rows]
    if spec.kind == CycleKind.WORK_TASK:
        a = _t("tab_work_task_assignee")
        pairs = [(tid, int(emp), at) for tid, emp, at in db.execute(
            select(a.c.task_id, a.c.employee_id, a.c.created_at).where(a.c.task_id.in_(ids), a.c.kind == 1))]
    elif spec.kind == CycleKind.PURCHASE_REQUEST:
        it = _t("tab_purchase_request_item")
        recv = {r["id"]: vn_midnight_utc(r.get("received_date")) for r in rows}
        raw = [(pid, code, recv.get(pid)) for pid, code in db.execute(
            select(it.c.pr_id, it.c.assignee).where(it.c.pr_id.in_(ids), it.c.assignee != ""))]
        pairs = _by_code(db, raw)
        pairs += [(r["id"], int(r["assignee_id"]), recv.get(r["id"])) for r in rows if r.get("assignee_id")]
    elif spec.kind == CycleKind.SURVEY_REQUEST:
        ln = _t("tab_survey_request_line")
        raw = [(sid, code, vn_midnight_utc(rd)) for sid, code, rd in db.execute(
            select(ln.c.survey_request_id, ln.c.assignee, ln.c.received_date)
            .where(ln.c.survey_request_id.in_(ids), ln.c.assignee != ""))]
        pairs = _by_code(db, raw)
    elif spec.kind == CycleKind.PURCHASE_ORDER:
        pairs = [(r["id"], int(r["nspt_id"]), None) for r in rows if r.get("nspt_id")]
    else:
        return {}
    out: dict[int, dict[int, datetime | None]] = {}
    for rid, emp, at in pairs:
        cur = out.setdefault(rid, {})
        if emp not in cur or (at is not None and (cur[emp] is None or at < cur[emp])):
            cur[emp] = at
    return {rid: list(d.items()) for rid, d in out.items()}


def _by_code(db: Session, raw: list) -> list:
    ids = _codes_to_ids(db, {c for _, c, _ in raw})
    return [(rid, ids[c], at) for rid, c, at in raw if c in ids]


__all__ = ["BATCH", "SPEC_BY_KIND", "Ev", "as_datetime", "build_facts", "touched_ids", "vn_midnight_utc"]
