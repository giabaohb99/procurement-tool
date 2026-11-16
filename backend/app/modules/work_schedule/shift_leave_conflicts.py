"""CHỐT ĐƠN NGHỈ ĐANG GIỮ NGÀY (duoc-CR-761, chủ dự án chốt 16/11/2026) — không đổi / gỡ ca của ngày đã có đơn nghỉ.

Đơn nghỉ CHỜ DUYỆT hoặc ĐÃ DUYỆT phủ ngày nào thì ca của ngày đó không được đổi, vì số ngày nghỉ của đơn đã tính trên ca
cũ (đơn đã duyệt đã trừ quỹ phép): sửa ca xong là số trừ lệch. Muốn xếp lại phải sửa / hủy đơn trước.

"Phủ ngày nào" đọc qua `leave/period_spans` (từng KHOẢNG của đơn, không phải bao ngoài ở đầu đơn — ngày khe giữa hai
khoảng không nghỉ nên vẫn xếp được). Đơn nghỉ theo giờ cũng giữ ngày của nó. Số truy vấn cố định: một truy vấn đơn + khoảng
(`periods_by_request`: 1, +1 nếu có đơn chưa có dòng khoảng), + một truy vấn phạm vi `leave_request` — bất kể bao nhiêu ô.

Thấy ô bị giữ không có nghĩa là thấy được đơn: mã đơn + trạng thái chỉ lộ cho người xem được đơn đó theo phạm vi
`leave_request.read` (như lớp nghỉ phép của "Ai làm / ai nghỉ"); người khác chỉ biết "ngày này đã có đơn nghỉ" (mã đơn rỗng).
"""
from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.core.scoping import apply_scope
from app.modules.leave.constants import HOLDING_STATUSES, LR_APPROVED
from app.modules.leave.period_spans import periods_by_request
from app.modules.leave.request_model import LeaveRequest

STATUS_LABELS = {LR_APPROVED: "đã duyệt"}   # còn lại trong `HOLDING_STATUSES` là chờ duyệt
PENDING_LABEL = "chờ duyệt"


@dataclass(frozen=True)
class LeaveConflict:
    """Đơn nghỉ đang giữ một ô người × ngày."""

    request_id: int
    request_code: str     # RỖNG khi người hỏi không xem được đơn theo phạm vi `leave_request`
    status: int
    visible: bool = True

    @property
    def status_label(self) -> str:
        if not self.visible:
            return ""
        return STATUS_LABELS.get(self.status, PENDING_LABEL)


def _visible_request_ids(db: Session, request_ids, user, profile) -> set[int]:
    """Trong `request_ids`, những đơn nằm trong phạm vi `leave_request.read` của người hỏi (1 truy vấn)."""
    query = apply_scope(db.query(LeaveRequest.id).filter(LeaveRequest.id.in_(list(request_ids))),
                        LeaveRequest, "leave_request", user, profile)
    return {row.id for row in query.all()}


def _holding_requests(db: Session, employee_ids, lo: date, hi: date):
    """`(đơn chờ duyệt / đã duyệt chạm [lo, hi], {id đơn: [khoảng]})` — nền chung của `find_leave_conflicts` (chốt ghi ca)
    và `held_days` (cờ `leave_hold` của lưới Xem lịch), để hai nơi KHÔNG thể lệch luật "đơn nào giữ ngày nào"."""
    requests = (db.query(LeaveRequest.id, LeaveRequest.code, LeaveRequest.status, LeaveRequest.employee_id)
                .filter(LeaveRequest.employee_id.in_(list(employee_ids)), LeaveRequest.is_deleted.is_(False),
                        LeaveRequest.status.in_(HOLDING_STATUSES),
                        LeaveRequest.from_date <= hi, LeaveRequest.to_date >= lo).all())
    return requests, (periods_by_request(db, [r.id for r in requests]) if requests else {})


def held_days(db: Session, employee_ids, from_date: date, to_date: date) -> set[tuple[int, date]]:
    """`{(employee_id, ngày)}` trong `[from_date, to_date]` đang bị đơn nghỉ chờ duyệt / đã duyệt giữ — CÙNG luật với
    `find_leave_conflicts` (từng khoảng thật của đơn; ngày lễ / ngày nghỉ / nửa ngày / theo giờ đều tính là giữ) nhưng
    KHÔNG lọc theo phạm vi `leave_request` và KHÔNG lộ mã / trạng thái đơn: chỉ để lưới báo "ô này không xếp ca được".
    Số truy vấn cố định: đơn (1) + khoảng (1, +1 nếu có đơn chưa có dòng khoảng).
    """
    ids = {int(i) for i in employee_ids if i}
    if not ids:
        return set()
    requests, periods = _holding_requests(db, ids, from_date, to_date)
    out: set[tuple[int, date]] = set()
    for req in requests:
        for p in periods.get(req.id, []):
            day, last = max(p.from_date, from_date), min(p.to_date, to_date)
            while day <= last:
                out.add((req.employee_id, day))
                day += timedelta(days=1)
    return out


def find_leave_conflicts(db: Session, cells, user, profile) -> dict[tuple[int, date], LeaveConflict]:
    """`{(employee_id, ngày): LeaveConflict}` cho các ô `cells` đang bị đơn nghỉ chờ duyệt / đã duyệt phủ.

    `user` + `profile` quyết định đơn nào được lộ mã (xem đầu tệp); đơn ngoài phạm vi vẫn tính là giữ ngày nhưng
    `request_code` rỗng và `visible = False`.

    Một ô có nhiều đơn: lấy đơn ĐÃ DUYỆT trước, rồi id nhỏ nhất (kết quả ổn định cho câu báo lỗi).
    """
    cells = list(dict.fromkeys(cells))
    if not cells:
        return {}
    requests, periods = _holding_requests(db, {emp for emp, _ in cells}, min(day for _, day in cells),
                                          max(day for _, day in cells))
    if not requests:
        return {}
    seen = _visible_request_ids(db, [r.id for r in requests], user, profile)
    out: dict[tuple[int, date], LeaveConflict] = {}
    for req in sorted(requests, key=lambda r: (r.status != LR_APPROVED, r.id)):
        spans = periods.get(req.id, [])
        for emp, day in cells:
            key = (emp, day)
            if emp == req.employee_id and key not in out and any(p.from_date <= day <= p.to_date for p in spans):
                out[key] = (LeaveConflict(req.id, req.code, req.status) if req.id in seen
                            else LeaveConflict(req.id, "", req.status, visible=False))
    return out
