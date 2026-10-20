"""Tính vòng đời MỘT phiếu từ dữ kiện đã gom — HÀM THUẦN, không đụng DB (duoc-CR-656, D1a).

Phần lớn bài kiểm của D1a nằm ở đây. `cycle_sources` lo đọc, `cycle_builder` lo ghi.

Quy ước:
- Mọi mốc là UTC naive như cột `DateTime` của hệ. Ngày hạn so theo NGÀY VN.
- Hai nguồn sự kiện (nhật ký thay đổi + audit) có thể kể CÙNG một chuyện hai lần → gộp các sự kiện
  cùng loại cách nhau ≤ `DEDUP_SECONDS` làm một (nếu không, một lần trả về thành hai lần làm lại).
- Thời gian trọn vòng theo NGÀY LỊCH (Q12), lưu bằng giờ; giao diện đổi sang ngày.
"""
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo

from app.core.capability_codes import CycleOutcome, CycleRole
from app.modules.capability.cycle_specs import CycleSpec, Ev

DEDUP_SECONDS = 120
_VN = ZoneInfo("Asia/Ho_Chi_Minh")


@dataclass
class Facts:
    """Dữ kiện đã gom của MỘT phiếu (do `cycle_sources` dựng)."""

    entity_id: int
    status: str
    created_at: datetime
    updated_at: datetime | None = None
    company_id: int = 0
    creator_id: int = 0                                           # employee_id người lập, 0 = không rõ
    handlers: list = field(default_factory=list)                  # [(employee_id, started_at | None)]
    events: list = field(default_factory=list)                    # [(at, Ev)] — đã chuẩn hóa, chưa khử trùng
    done_ts: datetime | None = None                               # cột mốc dự phòng của chính bảng
    due_date: str = ""
    task_type_id: int = 0
    estimate_hours: Decimal | None = None
    actual_hours: Decimal | None = None
    review_outcome: int = 0


def _dedupe(events: list, kinds: tuple) -> list[datetime]:
    """Mốc của các sự kiện thuộc `kinds`, gộp những mốc sát nhau thành một."""
    times = sorted(at for at, ev in events if ev in kinds)
    out: list[datetime] = []
    for at in times:
        if not out or (at - out[-1]).total_seconds() > DEDUP_SECONDS:
            out.append(at)
    return out


def _vn_date(dt: datetime) -> date:
    return dt.replace(tzinfo=timezone.utc).astimezone(_VN).date()


def _outcome(spec: CycleSpec, f: Facts, has_done_event: bool, events: list) -> CycleOutcome:
    cur = str(f.status)
    if cur in spec.done or (spec.sticky_done and has_done_event):
        return CycleOutcome.DONE
    if cur in spec.cancelled:
        return CycleOutcome.CANCELLED
    if cur in spec.ambiguous_reject:
        #  YCMH: `rejected` là «từ chối» hay «trả về»? Sự kiện sau cùng trong hai loại ấy quyết định.
        last = max(((at, ev) for at, ev in events if ev in (Ev.REJECT, Ev.RETURN)), default=None)
        return CycleOutcome.OPEN if last and last[1] == Ev.RETURN else CycleOutcome.REJECTED
    if cur in spec.rejected:
        return CycleOutcome.REJECTED
    return CycleOutcome.OPEN


def compute_cycles(spec: CycleSpec, f: Facts, now: datetime, today_vn: date | None = None) -> list[dict]:
    """Các dòng `tab_work_cycle` của một phiếu: 1 dòng người lập + 1 dòng mỗi người xử lý."""
    done_times = _dedupe(f.events, (Ev.DONE,))
    outcome = _outcome(spec, f, bool(done_times), f.events)

    done_at, estimated = None, False
    if outcome == CycleOutcome.DONE:
        if done_times:
            done_at = done_times[-1] if spec.done_pick == "last" else done_times[0]
        else:
            #  Không có dấu vết trong nhật ký (phiếu cũ trước ngày bật nhật ký, hoặc nhập từ hệ khác).
            done_at, estimated = (f.done_ts or f.updated_at or f.created_at), True

    rework = len(_dedupe(f.events, (Ev.RETURN, Ev.REOPEN)))
    due = _parse_date(f.due_date)
    is_late = _is_late(due, done_at, outcome, today_vn)

    people: list[tuple[int, int, datetime]] = []
    if f.creator_id:
        people.append((CycleRole.CREATOR, f.creator_id, f.created_at))
    seen: set[int] = set()
    for emp_id, start in f.handlers:
        if emp_id and emp_id not in seen:
            seen.add(emp_id)
            people.append((CycleRole.HANDLER, emp_id, start or f.created_at))

    rows = []
    for role, emp_id, start in people:
        hours = None
        if done_at is not None and done_at >= start:
            hours = round((done_at - start).total_seconds() / 3600.0, 2)
        rows.append({
            "kind": int(spec.kind), "entity_id": f.entity_id, "role": int(role), "employee_id": int(emp_id),
            "company_id": f.company_id, "department_id": 0, "task_type_id": f.task_type_id,
            "started_at": start, "done_at": done_at, "outcome": int(outcome), "cycle_hours": hours,
            "rework_count": min(rework, 32000), "is_estimated": estimated,
            "due_date": due, "is_late": is_late,
            "estimate_hours": f.estimate_hours, "actual_hours": f.actual_hours,
            "review_outcome": f.review_outcome, "computed_at": now,
        })
    return rows


def _parse_date(text: str) -> date | None:
    try:
        return date.fromisoformat((text or "")[:10]) if text else None
    except ValueError:
        return None


def _is_late(due: date | None, done_at: datetime | None, outcome: CycleOutcome, today_vn: date | None) -> bool | None:
    """Trễ hạn: đã xong thì so ngày xong (VN) với hạn; còn mở thì so hôm nay; hủy/từ chối: không tính."""
    if due is None or outcome in (CycleOutcome.CANCELLED, CycleOutcome.REJECTED):
        return None
    if outcome == CycleOutcome.DONE and done_at is not None:
        return _vn_date(done_at) > due
    return bool(today_vn and today_vn > due)


def to_vn_date(dt: datetime) -> date:
    """Cho nơi khác cần đổi mốc UTC naive sang ngày VN."""
    return _vn_date(dt)


__all__ = ["Facts", "compute_cycles", "to_vn_date"]
