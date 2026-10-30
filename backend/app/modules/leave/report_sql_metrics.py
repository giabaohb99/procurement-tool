"""Gom CỘNG ở SQL cho `/api/leave-requests/summary` — thay máy Python
`report_aggregate.aggregate()` (gói B, review hiệu năng 01/10/2026).

Vì sao KHÔNG tái dùng `build_report()/aggregate()` như khung chung của các báo cáo khác: báo
cáo này rơi đúng vào ca mà khung chung cộng chậm — `group_by=employee` có thể ra tới hàng
nghìn NHÓM gần như DUY NHẤT (một nhân sự hiếm khi trùng cả ngày/trạng thái/loại nghỉ với
người khác), nên gộp hàng theo (ngày, loại, trạng thái, nhân sự) ở SQL KHÔNG thu hẹp được số
dòng — ở quy mô 60 nghìn đơn/3 năm, đo được `group_by=employee` tốn 1,9–22,9s, 79% là vòng lặp
Python `compute_metrics`/`bucket_rows` (xem báo cáo load-test gói B). Cách đúng là để DATABASE
tính SUM/COUNT/COUNT DISTINCT theo ĐÚNG MỘT chiều cần (nhân sự/phòng ban/công ty/loại/trạng
thái) — khi đó số NHÓM trả về bị chặn bởi số giá trị PHÂN BIỆT của chiều đó (vài nghìn nhân sự
tối đa), không phải bởi số đơn/số dòng.

Hai bảng nguồn, hai hàm gom riêng (JOIN qua `report_rows.header_subquery`):
  - `header_aggregate` — trên `LeaveRequest`: 5 chỉ số KHÔNG cần biết loại nghỉ của từng DÒNG
    (requests · requests_reject_return · people_on_leave · turnaround_hours_sum/count).
  - `line_aggregate` — JOIN `LeaveRequestLine`: `days_approved`/`days_pending`, CỘNG theo loại
    nghỉ CỦA TỪNG DÒNG (khác loại CHÍNH của đơn khi đơn khai nhiều loại).

`DERIVED` là nguồn DUY NHẤT cho công thức `reject_return_rate`/`avg_turnaround_hours` — dùng
lại ở cả `report_service._build_spec()` (để `meta_of()` ra đúng nhãn/kind) lẫn mọi nơi tính
giá trị thật trong gói tệp `report_sql_*`, tránh hai công thức lệch nhau.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import and_, case, cast, Float, func, literal_column
from sqlalchemy.orm import Session

from app.core.report_aggregate import DerivedSpec
from app.modules.leave.catalog_model import LeaveType
from app.modules.leave.constants import LR_APPROVED, LR_PENDING, LR_REJECTED, LR_RETURNED
from app.modules.leave.report_sql_merge import ZERO_METRICS, merge_dim_rows, totals_dict  # noqa: F401 (tái xuất)
from app.modules.leave.request_model import LeaveRequest, LeaveRequestLine

#  Đơn chờ duyệt quá bấy nhiêu giờ kể từ lúc nộp thì tính là "chờ quá 3 ngày".
PENDING_OVERDUE_HOURS = 72

DERIVED = [
    DerivedSpec("reject_return_rate", "Tỷ lệ từ chối/trả về", num="requests_reject_return",
               den="requests", good="down"),
    #  `scale=1`: TRUNG BÌNH giờ, không phải tỷ lệ % (mặc định ×100 của DerivedSpec).
    DerivedSpec("avg_turnaround_hours", "Thời gian duyệt TB", num="turnaround_hours_sum",
               den="turnaround_hours_count", kind="hours", good="down", scale=1),
    #  Ngày nghỉ đã duyệt BÌNH QUÂN mỗi người nghỉ (không phải %, nên scale=1).
    DerivedSpec("avg_days_per_person", "Ngày nghỉ TB/người", num="days_approved",
               den="people_on_leave", kind="days", scale=1, ndigits=2),
]

#  Cột GOM theo CHIỀU, phía header (copy sẵn trên `LeaveRequest`) — `leave_type` KHÔNG nằm ở
#  đây vì nó LỆCH giữa header/dòng, xem `dim_columns`.
_HEADER_DIM_COLS = {"company": LeaveRequest.company_id, "department": LeaveRequest.department_id,
                    "employee": LeaveRequest.employee_id, "status": LeaveRequest.status}


def turnaround_hours_expr(db: Session):
    """Biểu thức SỐ GIỜ xử lý (`decided_at − submitted_at`), tính PORTABLE SQLite/MySQL.

    ⚠️ `julianday()` của SQLite KHÔNG đủ chính xác cho phép trừ này: số ngày Julius của năm
    2026 cần ~17 chữ số có nghĩa, vượt độ chính xác an toàn của `double` (~15-17 chữ số) — đo
    tay ra MỘT GIỜ chênh lệch (không hề có phần lẻ giây ở input) tính thành `26.49999999627`
    thay vì `26.5`. Đổi sang HIỆU HAI MỐC GIÂY TUYỆT ĐỐI (epoch, ~1,7 tỷ — nằm gọn trong 2^53
    của `double`) thì phép trừ CHÍNH XÁC TUYỆT ĐỐI ở độ phân giải GIÂY.

    MySQL thật: cột `DateTime` không khai `fsp` nên MySQL đã CẮT phần lẻ giây ngay lúc LƯU —
    `TIMESTAMPDIFF(SECOND,...)` vì vậy không mất gì so với giá trị đã lưu, khớp tuyệt đối với
    `(decided_at-submitted_at).total_seconds()` của bản Python cũ (cũng đọc từ giá trị đã bị
    MySQL cắt sẵn). SQLite (bộ test) giữ nguyên micro-giây nếu ai gán — khác biệt CHỈ lộ ra
    khi test tự gán micro-giây, nên bài kiểm so khớp dùng mốc giờ TRÒN GIÂY (nghiệp vụ thật
    không gán micro-giây tay).
    """
    a, b = LeaveRequest.submitted_at, LeaveRequest.decided_at
    if db.bind is not None and db.bind.dialect.name == "mysql":
        diff_seconds = func.timestampdiff(literal_column("SECOND"), a, b)
    else:
        diff_seconds = cast(func.strftime("%s", b), Float) - cast(func.strftime("%s", a), Float)
    return diff_seconds / 3600.0


def header_aggregate(db: Session, scoped_query, group_col=None, with_first_date: bool = False):
    """5 chỉ số GOM trên `LeaveRequest`. `group_col=None` → TỔNG một dòng (`.one()`, luôn ĐÚNG
    MỘT dòng dù 0 hay nhiều đơn khớp — luật SQL chuẩn của hàm gộp không `GROUP BY`).

    `with_first_date=True` (CHỈ dùng khi `group_col` khác None — `groups_for_dim`/breakdown)
    thêm `MIN(from_date)` — KHÔNG phải một chỉ số nghiệp vụ, mà là CHÌA KHÓA sắp lại thứ tự
    HÒA ĐIỂM đúng như bản cũ, xem docstring `merge_dim_rows`."""
    expr = turnaround_hours_expr(db)
    #  Mốc 72 giờ trước, so với CÙNG loại đồng hồ đã ghi `submitted_at`: tiến trình ghi bằng
    #  `datetime.now()` (giờ máy), nên dùng `now()` chứ không `utcnow()` để khỏi lệch khi
    #  container không chạy UTC.
    overdue_cutoff = datetime.now() - timedelta(hours=PENDING_OVERDUE_HOURS)
    cols = [
        func.count(case((and_(LeaveRequest.status == LR_PENDING,
                              LeaveRequest.submitted_at < overdue_cutoff), 1))
                  ).label("requests_pending_over_3d"),
        func.count().label("requests"),
        func.count(case((LeaveRequest.status.in_((LR_REJECTED, LR_RETURNED)), 1))
                  ).label("requests_reject_return"),
        func.count(func.distinct(case(
            (and_(LeaveRequest.status == LR_APPROVED, LeaveRequest.employee_id != 0),
             LeaveRequest.employee_id)))).label("people_on_leave"),
        func.sum(expr).label("turnaround_hours_sum"),
        func.count(expr).label("turnaround_hours_count"),
    ]
    if with_first_date:
        cols.append(func.min(LeaveRequest.from_date).label("first_date"))
    if group_col is None:
        return scoped_query.with_entities(*cols).one()
    return scoped_query.with_entities(group_col.label("key"), *cols).group_by(group_col).all()


def line_aggregate(db: Session, header_subq, group_col=None, with_first_date: bool = False,
                   extra_filter=None):
    """3 chỉ số NGÀY (đã duyệt/chờ/không lương), GOM trên `LeaveRequestLine` JOIN `header_subq` (trạng thái/ngày/chiều
    lấy từ ĐƠN — bảng dòng không tự có các cột này). `with_first_date` — xem `header_aggregate`.
    `extra_filter` — lọc THÊM (vd `cap_groups` tính lại tổng của phần "(Các nhóm khác)"); không
    có ở `header_aggregate` vì caller tự `.filter()` thẳng lên `scoped_query` composable sẵn."""
    days_approved = func.sum(case((header_subq.c.status == LR_APPROVED, LeaveRequestLine.days),
                                  else_=0.0)).label("days_approved")
    days_pending = func.sum(case((header_subq.c.status == LR_PENDING, LeaveRequestLine.days),
                                 else_=0.0)).label("days_pending")
    #  Ngày KHÔNG LƯƠNG: dòng đã duyệt của loại nghỉ `is_paid = False` (JOIN loại — 1 khóa/dòng,
    #  không nhân hàng, số truy vấn không đổi).
    days_unpaid = func.sum(case((and_(header_subq.c.status == LR_APPROVED, LeaveType.is_paid.is_(False)),
                                 LeaveRequestLine.days), else_=0.0)).label("days_unpaid")
    cols = [days_approved, days_pending, days_unpaid]
    if with_first_date:
        cols.append(func.min(header_subq.c.from_date).label("first_date"))
    q = (db.query(LeaveRequestLine).join(header_subq, LeaveRequestLine.request_id == header_subq.c.id)
         .outerjoin(LeaveType, LeaveType.id == LeaveRequestLine.leave_type_id))
    if extra_filter is not None:
        q = q.filter(extra_filter)
    if group_col is None:
        return q.with_entities(*cols).one()
    return q.with_entities(group_col.label("key"), *cols).group_by(group_col).all()


def dim_columns(dim: str, header_subq):
    """(cột GOM phía header, cột GOM phía dòng) cho một CHIỀU. `leave_type` LỆCH có chủ đích:
    header dùng loại CHÍNH của đơn (`LeaveRequest.leave_type_id`), dòng dùng loại CỦA TỪNG
    DÒNG (`LeaveRequestLine.leave_type_id`) — một đơn khai nhiều loại thì hai giá trị này
    KHÁC NHAU trên cùng một đơn, đúng ý "đơn nhiều loại nghỉ góp mặt ở mọi loại có dòng"."""
    if dim == "leave_type":
        return LeaveRequest.leave_type_id, LeaveRequestLine.leave_type_id
    return _HEADER_DIM_COLS[dim], getattr(header_subq.c, _HEADER_DIM_COLS[dim].key)
