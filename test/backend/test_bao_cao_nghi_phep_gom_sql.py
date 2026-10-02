"""Gói B (01/10/2026) — chứng minh `report_service.build_summary` MỚI (gom ở SQL) ra
ĐÚNG Y HỆT dict bản CŨ (gom bằng `report_aggregate.build_report()` trên hàng thô Python).

Bản CŨ (`_old_fetch_rows`/`_old_build_spec`/`_old_build_summary` dưới đây) là BẢN ĐÔNG CỨNG,
sao chép nguyên văn từ git history NGAY TRƯỚC khi gói B thay `report_rows.py`/`report_service.py`
— cố tình KHÔNG import gì từ 2 tệp đó, để sửa nhầm ở bản mới không vô tình kéo bài kiểm này đổi
theo (mất tác dụng đối chứng). Khung gộp kỳ so sánh (`report_aggregate.build_report`,
`report_compute.bucket_rows`) vẫn dùng bản THẬT, chưa ai đụng tới ở cả hai phía.

Một fixture "giàu" dùng chung cho mọi tổ hợp (kỳ × group_by):
  - 2 công ty, 4 phòng ban, 6 nhân sự, 3 loại nghỉ.
  - Đủ 5 trạng thái không-nháp (chờ duyệt/đã duyệt/từ chối/trả về/đã hủy).
  - 2 đơn khai NHIỀU loại nghỉ — một loại CỐ Ý chỉ nằm ở dòng PHỤ (không bao giờ là loại
    CHÍNH của đơn nào), đúng ca `TestBreakdownLoaiNghiXepTheoNgay` đã canh.
  - Một nhân sự nghỉ 2 lần KHÁC NGÀY nhưng CÙNG THÁNG (group_by=None/kỳ "month") — ca hiểm
    của `people_on_leave`: cộng thẳng số đếm DISTINCT theo từng ngày rồi gộp lên tháng sẽ ra
    2, trong khi đúng phải là 1 (cùng một người).
  - `submitted_at`/`decided_at` CỐ Ý tròn giây (không micro-giây) — xem lý do ở docstring
    `report_sql_metrics.turnaround_hours_expr`: `julianday()`/epoch-giây chỉ khớp TUYỆT ĐỐI
    với phép trừ `timedelta` của Python khi không có phần lẻ giây.

Hai kỳ, phủ cả hai độ hạt trục (`day`/`month`) và cả hai kiểu so sánh (`previous`/`year`):
  - B1: `custom 2026-01-01..2026-04-10`, so sánh `year` (độ hạt THÁNG, >92 ngày).
  - B2: `custom 2026-02-01..2026-02-28`, so sánh `previous` (độ hạt NGÀY, ≤31 ngày).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta

import pytest

from app.core.report_aggregate import (BREAKDOWN_LIMIT, DerivedSpec, DimensionSpec, MetricSpec,
                                       ReportSpec, build_report)
from app.core.report_compute import bucket_rows
from app.core.report_period import parse_period, range_filter
from app.core.scoping import apply_scope
from app.modules.leave import report_service
from app.modules.leave.constants import (LEAVE_REQUEST_STATUS_LABELS, LR_APPROVED, LR_CANCELLED,
                                         LR_DRAFT, LR_PENDING, LR_REJECTED, LR_RETURNED)
from app.modules.leave.request_model import LeaveRequest, LeaveRequestLine

# ═══════════════════════════════ BẢN CŨ — ĐÔNG CỨNG ═══════════════════════════════

_REQ_COLS = (LeaveRequest.id, LeaveRequest.company_id, LeaveRequest.department_id,
            LeaveRequest.status, LeaveRequest.employee_id, LeaveRequest.leave_type_id,
            LeaveRequest.from_date, LeaveRequest.submitted_at, LeaveRequest.decided_at)
_LINE_COLS = (LeaveRequestLine.request_id, LeaveRequestLine.leave_type_id, LeaveRequestLine.days)


@dataclass(frozen=True)
class _OldLeaveRow:
    kind: str
    from_date: date
    company_id: int
    department_id: int
    status: int
    employee_id: int
    employee_name: str
    request_id: int
    leave_type_id: int
    leave_type_name: str
    days: float = 0.0
    turnaround_hours: float | None = None


def _old_fetch_rows(db, user, prof, d_from, d_to, type_name, emp_name, company_id=None):
    q = apply_scope(db.query(LeaveRequest), LeaveRequest, "leave_request", user, prof)
    if company_id is not None:
        q = q.filter(LeaveRequest.company_id == company_id)
    requests = (q.filter(LeaveRequest.is_deleted.is_(False), LeaveRequest.status != LR_DRAFT)
               .filter(range_filter(LeaveRequest.from_date, "date", d_from, d_to))
               .with_entities(*_REQ_COLS).all())
    if not requests:
        return []
    req_ids = [r.id for r in requests]
    lines_by_request: dict[int, list] = {}
    for ln in db.query(*_LINE_COLS).filter(LeaveRequestLine.request_id.in_(req_ids)).all():
        lines_by_request.setdefault(ln.request_id, []).append(ln)

    rows: list[_OldLeaveRow] = []
    for r in requests:
        turnaround = ((r.decided_at - r.submitted_at).total_seconds() / 3600.0
                     if r.submitted_at and r.decided_at else None)
        name = emp_name.get(r.employee_id, "")
        rows.append(_OldLeaveRow(kind="request", from_date=r.from_date, company_id=r.company_id or 0,
                                 department_id=r.department_id or 0, status=r.status,
                                 employee_id=r.employee_id or 0, employee_name=name, request_id=r.id,
                                 leave_type_id=r.leave_type_id or 0,
                                 leave_type_name=type_name.get(r.leave_type_id, ""),
                                 turnaround_hours=turnaround))
        for ln in lines_by_request.get(r.id, []):
            rows.append(_OldLeaveRow(kind="line", from_date=r.from_date, company_id=r.company_id or 0,
                                     department_id=r.department_id or 0, status=r.status,
                                     employee_id=r.employee_id or 0, employee_name=name, request_id=r.id,
                                     leave_type_id=ln.leave_type_id or 0,
                                     leave_type_name=type_name.get(ln.leave_type_id, ""),
                                     days=ln.days or 0.0))
    return rows


def _old_build_spec(company_name: dict, department_name: dict) -> ReportSpec:
    metrics = [
        MetricSpec("requests", "Số đơn", kind="int",
                  distinct_of=lambda r: r.request_id if r.kind == "request" else None),
        MetricSpec("days_approved", "Ngày nghỉ đã duyệt", kind="days",
                  value_of=lambda r: r.days if r.kind == "line" and r.status == LR_APPROVED else 0),
        MetricSpec("days_pending", "Ngày đang chờ duyệt", kind="days",
                  value_of=lambda r: r.days if r.kind == "line" and r.status == LR_PENDING else 0),
        MetricSpec("people_on_leave", "Số người nghỉ", kind="int",
                  distinct_of=lambda r: (r.employee_id if r.kind == "request"
                                        and r.status == LR_APPROVED and r.employee_id else None)),
        MetricSpec("requests_reject_return", "Đơn từ chối/trả về", kind="int", helper=True,
                  distinct_of=lambda r: (r.request_id if r.kind == "request"
                                        and r.status in (LR_REJECTED, LR_RETURNED) else None)),
        MetricSpec("turnaround_hours_sum", "Tổng giờ xử lý", kind="hours", helper=True,
                  value_of=lambda r: (r.turnaround_hours if r.kind == "request"
                                     and r.turnaround_hours is not None else 0)),
        MetricSpec("turnaround_hours_count", "Số đơn có thời gian xử lý", kind="int", helper=True,
                  value_of=lambda r: (1 if r.kind == "request" and r.turnaround_hours is not None
                                     else 0)),
    ]
    derived = [
        DerivedSpec("reject_return_rate", "Tỷ lệ từ chối/trả về", num="requests_reject_return",
                   den="requests", good="down"),
        DerivedSpec("avg_turnaround_hours", "Thời gian duyệt TB", num="turnaround_hours_sum",
                   den="turnaround_hours_count", kind="hours", good="down", scale=1),
    ]
    leave_type_dim = DimensionSpec("leave_type", "Loại nghỉ", key_of=lambda r: (
        [(r.leave_type_id, r.leave_type_name)] if r.leave_type_id else []))
    status_dim = DimensionSpec("status", "Trạng thái", key_of=lambda r: (
        [(r.status, LEAVE_REQUEST_STATUS_LABELS.get(r.status, ""))] if r.status else []))
    dimensions = {
        "leave_type": leave_type_dim,
        "department": DimensionSpec("department", "Phòng ban", key_of=lambda r: (
            [(r.department_id, department_name.get(r.department_id, ""))] if r.department_id else [])),
        "company": DimensionSpec("company", "Công ty", key_of=lambda r: (
            [(r.company_id, company_name.get(r.company_id, ""))] if r.company_id else [])),
        "employee": DimensionSpec("employee", "Nhân sự", key_of=lambda r: (
            [(r.employee_id, r.employee_name)] if r.employee_id else [])),
        "status": status_dim,
    }
    return ReportSpec(date_of=lambda r: r.from_date, metrics=metrics, derived=derived,
                      dimensions=dimensions,
                      breakdowns={"leave_type": leave_type_dim, "status": status_dim},
                      rank_by="requests")


def _old_rank_leave_type_by_days(rows, leave_type_dim: DimensionSpec) -> list[dict]:
    buckets = bucket_rows(rows, leave_type_dim.key_of, leave_type_dim.empty_label)
    items = [{"key": k, "label": b["label"],
              "value": sum(r.days for r in b["rows"] if r.kind == "line" and r.status == LR_APPROVED)}
             for k, b in buckets.items()]
    items = sorted((i for i in items if i["value"]), key=lambda x: x["value"], reverse=True)
    return items[:BREAKDOWN_LIMIT]


def _old_build_summary(db, user, prof, period, group_by, company_id=None) -> dict:
    from app.modules.company.model import Company
    from app.modules.department.model import Department
    from app.modules.employee.model import Employee
    from app.modules.leave.catalog_model import LeaveType

    type_name = {t.id: t.name for t in db.query(LeaveType.id, LeaveType.name).all()}
    emp_name = ({e.id: e.full_name for e in db.query(Employee.id, Employee.full_name).all()}
               if group_by == "employee" else {})
    company_name = ({c.id: c.name for c in db.query(Company.id, Company.name).all()}
                    if group_by == "company" else {})
    department_name = ({d.id: d.name for d in db.query(Department.id, Department.name).all()}
                       if group_by == "department" else {})
    spec = _old_build_spec(company_name, department_name)

    captured: list[_OldLeaveRow] = []

    def fetch(d_from, d_to):
        rows = _old_fetch_rows(db, user, prof, d_from, d_to, type_name, emp_name, company_id)
        if d_from == period.date_from:
            captured[:] = rows
        return rows

    data = build_report(fetch, spec, period, group_by=group_by)
    if "leave_type" in (data.get("breakdowns") or {}):
        data["breakdowns"]["leave_type"] = _old_rank_leave_type_by_days(captured, spec.dimensions["leave_type"])
    data["notes"] = [
        "Đơn khai nhiều loại nghỉ góp mặt ở MỌI nhóm loại nghỉ có dòng tương ứng (Ngày nghỉ đã "
        "duyệt/đang chờ theo từng loại), nhưng chỉ tính 1 đơn cho Số đơn/Số người nghỉ/Tỷ lệ từ "
        "chối-trả về/Thời gian duyệt TB — nhóm theo loại CHÍNH của đơn (dòng chiếm nhiều ngày nhất).",
        "Đơn vắt qua kỳ tính theo NGÀY BẮT ĐẦU; phòng ban/công ty lấy theo lúc LẬP đơn.",
    ]
    return data


# ═══════════════════════════════ FIXTURE GIÀU ═══════════════════════════════

def _leave_type(db, code, name):
    from app.modules.leave.catalog_model import LeaveType
    lt = LeaveType(code=code, name=name)
    db.add(lt)
    db.flush()
    return lt


def _emp(db, code, full_name, company_id, department_id):
    from app.modules.employee.model import Employee
    e = Employee(code=code, full_name=full_name, company_id=company_id, department_id=department_id)
    db.add(e)
    db.flush()
    return e


def _req(db, code, *, company_id, department_id, employee_id, status, leave_type_id,
         from_date, to_date=None, lines=None, submitted_at=None, decided_at=None):
    req = LeaveRequest(code=code, company_id=company_id, department_id=department_id,
                       employee_id=employee_id, created_by=employee_id or 1,
                       leave_type_id=leave_type_id, from_date=from_date, to_date=to_date or from_date,
                       status=status, is_deleted=False, submitted_at=submitted_at, decided_at=decided_at)
    db.add(req)
    db.flush()
    for lt_id, days in (lines or [(leave_type_id, 1.0)]):
        db.add(LeaveRequestLine(request_id=req.id, leave_type_id=lt_id, days=days))
    db.flush()
    return req


@pytest.fixture
def rich(db, world):
    """Thế giới GIÀU — xem docstring đầu tệp. Trả namespace đủ để test tra cứu nếu cần."""
    world.grant("a1", "leave_request", scope="all", actions=("read",))
    a1 = world.actor("a1")

    lt_pn = _leave_type(db, "RICH-PN", "Phép năm")
    lt_om = _leave_type(db, "RICH-OM", "Ốm")
    #  Loại CHỈ-PHỤ — không bao giờ là loại CHÍNH của bất kỳ đơn nào (canh breakdown xếp theo
    #  ngày, không theo rank_by mặc định).
    lt_kl = _leave_type(db, "RICH-KL", "Không lương")

    co_a, co_b = world.co["A"], world.co["B"]
    d_akt, d_amua = world.dept["A.kt"], world.dept["A.mua"]
    d_bkt, d_bhc = world.dept["B.kt"], world.dept["B.hc"]

    e1 = _emp(db, "RICH-E1", "NV Rich 1", co_a, d_akt)
    e2 = _emp(db, "RICH-E2", "NV Rich 2", co_a, d_amua)
    e3 = _emp(db, "RICH-E3", "NV Rich 3", co_b, d_bkt)
    e4 = _emp(db, "RICH-E4", "NV Rich 4", co_b, d_bhc)
    e5 = _emp(db, "RICH-E5", "NV Rich 5", co_a, d_akt)
    e6 = _emp(db, "RICH-E6", "NV Rich 6", co_b, d_bkt)

    sub = datetime(2026, 1, 3, 8, 0, 0)

    #  ── Dữ liệu 2026 (kỳ HIỆN TẠI của cả B1 lẫn B2) ──────────────────────────
    #  e1 nghỉ 2 LẦN KHÁC NGÀY CÙNG THÁNG 01/2026 — ca hiểm `people_on_leave` ở độ hạt tháng.
    _req(db, "R-E1-A", company_id=co_a, department_id=d_akt, employee_id=e1.id, status=LR_APPROVED,
        leave_type_id=lt_pn.id, from_date=date(2026, 1, 5),
        submitted_at=sub, decided_at=datetime(2026, 1, 3, 10, 30, 0))
    _req(db, "R-E1-B", company_id=co_a, department_id=d_akt, employee_id=e1.id, status=LR_APPROVED,
        leave_type_id=lt_pn.id, from_date=date(2026, 1, 20),
        submitted_at=sub, decided_at=datetime(2026, 1, 5, 8, 0, 0))

    #  Đơn khai NHIỀU loại — PN là CHÍNH (3 ngày), KL là PHỤ (2 ngày): KL không bao giờ là
    #  loại chính của đơn nào trong cả bộ fixture.
    _req(db, "R-E2-MULTI", company_id=co_a, department_id=d_amua, employee_id=e2.id,
        status=LR_APPROVED, leave_type_id=lt_pn.id, from_date=date(2026, 1, 10),
        to_date=date(2026, 1, 14), lines=[(lt_pn.id, 3.0), (lt_kl.id, 2.0)],
        submitted_at=sub, decided_at=datetime(2026, 1, 3, 20, 0, 0))
    _req(db, "R-E3-MULTI", company_id=co_b, department_id=d_bkt, employee_id=e3.id,
        status=LR_APPROVED, leave_type_id=lt_om.id, from_date=date(2026, 2, 2),
        to_date=date(2026, 2, 5), lines=[(lt_om.id, 2.5), (lt_kl.id, 1.5)],
        submitted_at=datetime(2026, 2, 1, 8, 0, 0), decided_at=datetime(2026, 2, 1, 12, 0, 0))

    #  Đủ 5 trạng thái không-nháp, rải nhiều công ty/phòng/loại.
    _req(db, "R-E4-PENDING", company_id=co_b, department_id=d_bhc, employee_id=e4.id,
        status=LR_PENDING, leave_type_id=lt_om.id, from_date=date(2026, 2, 10),
        submitted_at=datetime(2026, 2, 10, 8, 0, 0))   # chưa có decided_at
    _req(db, "R-E5-REJECTED", company_id=co_a, department_id=d_akt, employee_id=e5.id,
        status=LR_REJECTED, leave_type_id=lt_pn.id, from_date=date(2026, 2, 12),
        submitted_at=datetime(2026, 2, 11, 8, 0, 0), decided_at=datetime(2026, 2, 12, 8, 0, 0))
    _req(db, "R-E6-RETURNED", company_id=co_b, department_id=d_bkt, employee_id=e6.id,
        status=LR_RETURNED, leave_type_id=lt_om.id, from_date=date(2026, 2, 15),
        submitted_at=datetime(2026, 2, 14, 8, 0, 0), decided_at=datetime(2026, 2, 15, 9, 0, 0))
    _req(db, "R-E2-CANCELLED", company_id=co_a, department_id=d_amua, employee_id=e2.id,
        status=LR_CANCELLED, leave_type_id=lt_pn.id, from_date=date(2026, 2, 20),
        submitted_at=datetime(2026, 2, 19, 8, 0, 0), decided_at=datetime(2026, 2, 20, 8, 0, 0))

    #  Thêm vài đơn APPROVED rải tháng 3-4/2026 để trục tháng (B1) có ≥ 4 mốc khác 0.
    _req(db, "R-E3-MAR", company_id=co_b, department_id=d_bkt, employee_id=e3.id,
        status=LR_APPROVED, leave_type_id=lt_pn.id, from_date=date(2026, 3, 8),
        submitted_at=datetime(2026, 3, 7, 8, 0, 0), decided_at=datetime(2026, 3, 8, 8, 0, 0))
    _req(db, "R-E6-APR", company_id=co_b, department_id=d_bhc, employee_id=e4.id,
        status=LR_APPROVED, leave_type_id=lt_om.id, from_date=date(2026, 4, 2),
        submitted_at=datetime(2026, 4, 1, 8, 0, 0), decided_at=datetime(2026, 4, 2, 8, 0, 0))

    #  ── Dữ liệu 2025 (kỳ SO SÁNH `year` của B1) ──────────────────────────────
    _req(db, "R-E1-2025", company_id=co_a, department_id=d_akt, employee_id=e1.id,
        status=LR_APPROVED, leave_type_id=lt_pn.id, from_date=date(2025, 1, 8),
        submitted_at=datetime(2025, 1, 7, 8, 0, 0), decided_at=datetime(2025, 1, 8, 8, 0, 0))
    _req(db, "R-E3-2025", company_id=co_b, department_id=d_bkt, employee_id=e3.id,
        status=LR_REJECTED, leave_type_id=lt_om.id, from_date=date(2025, 3, 15),
        submitted_at=datetime(2025, 3, 14, 8, 0, 0), decided_at=datetime(2025, 3, 15, 8, 0, 0))

    #  ── Dữ liệu tháng 01/2026 (kỳ SO SÁNH `previous` của B2 = tháng 01) ──────
    _req(db, "R-E4-JAN", company_id=co_b, department_id=d_bhc, employee_id=e4.id,
        status=LR_APPROVED, leave_type_id=lt_om.id, from_date=date(2026, 1, 25),
        submitted_at=datetime(2026, 1, 24, 8, 0, 0), decided_at=datetime(2026, 1, 25, 8, 0, 0))

    db.commit()
    return {"a1": a1, "lt": {"pn": lt_pn.id, "om": lt_om.id, "kl": lt_kl.id}}


# ═══════════════════════════════ SO KHỚP ═══════════════════════════════

PERIOD_B1 = {"preset": "custom", "date_from": "2026-01-01", "date_to": "2026-04-10", "compare": "year"}
PERIOD_B2 = {"preset": "custom", "date_from": "2026-02-01", "date_to": "2026-02-28", "compare": "previous"}

GROUP_BYS = [None, "company", "department", "employee", "status", "leave_type"]


@pytest.mark.parametrize("period_params", [PERIOD_B1, PERIOD_B2], ids=["B1_nam_thang", "B2_thang_truoc_ngay"])
@pytest.mark.parametrize("group_by", GROUP_BYS, ids=lambda g: g or "none")
def test_moi_khop_cu_tren_fixture_giau(db, world, rich, period_params, group_by):
    a1 = rich["a1"]
    prof = a1.profile()
    period = parse_period(period_params)

    expected = _old_build_summary(db, a1.user, prof, period, group_by)
    actual = report_service.build_summary(db, a1.user, prof, period, group_by)

    assert actual == expected


def test_moi_khop_cu_loc_cong_ty(db, world, rich):
    """`company_id` lọc SAU `apply_scope` (H1) — vẫn phải khớp khi dùng cùng lúc với `group_by`."""
    a1 = rich["a1"]
    prof = a1.profile()
    period = parse_period(PERIOD_B1)
    for cid in (world.co["A"], world.co["B"]):
        expected = _old_build_summary(db, a1.user, prof, period, "employee", company_id=cid)
        actual = report_service.build_summary(db, a1.user, prof, period, "employee", company_id=cid)
        assert actual == expected


def test_moi_khop_cu_vuot_tran_group_limit(db, world):
    """Gói A3 (01/10/2026) thêm `report_aggregate.GROUP_LIMIT=300` cho `aggregate()`. Đường SQL
    này KHÔNG đi qua `aggregate()` nên `report_sql_groups.cap_groups` phải tự cắt lại — ca
    `group_by=employee` > 300 nhân sự CHÍNH LÀ ca GROUP_LIMIT sinh ra để chặn, dựng > 300 nhân
    sự để chắc chắn chạm trần (khác mọi test khác trong tệp này, cố tình < 300 nhóm)."""
    world.grant("a1", "leave_request", scope="all", actions=("read",))
    cap = world.actor("a1")
    lt = _leave_type(db, "CAP-PN", "Phép năm")
    for i in range(310):
        emp = _emp(db, f"CAP-E{i}", f"NV Cap {i}", world.co["A"], world.dept["A.kt"])
        _req(db, f"R-CAP-{i}", company_id=world.co["A"], department_id=world.dept["A.kt"],
            employee_id=emp.id, status=LR_APPROVED, leave_type_id=lt.id,
            from_date=date(2026, 1, 1) + timedelta(days=i % 90),
            submitted_at=datetime(2026, 1, 1, 8, 0, 0), decided_at=datetime(2026, 1, 1, 10, 0, 0))
    db.commit()

    prof = cap.profile()
    period = parse_period({"preset": "custom", "date_from": "2026-01-01", "date_to": "2026-12-31",
                           "compare": "none"})
    expected = _old_build_summary(db, cap.user, prof, period, "employee")
    actual = report_service.build_summary(db, cap.user, prof, period, "employee")

    assert len(expected["groups"]) == 300   # 299 nhóm thật + 1 hàng "(Các nhóm khác)"
    assert actual == expected


def test_moi_khop_cu_khong_co_du_lieu_trong_ky(db, world, rich):
    """Kỳ KHÔNG có đơn nào khớp — nhánh rỗng (COUNT/SUM trên tập rỗng) phải khớp bản cũ."""
    a1 = rich["a1"]
    prof = a1.profile()
    period = parse_period({"preset": "custom", "date_from": "2099-01-01", "date_to": "2099-01-31",
                           "compare": "none"})
    for group_by in GROUP_BYS:
        expected = _old_build_summary(db, a1.user, prof, period, group_by)
        actual = report_service.build_summary(db, a1.user, prof, period, group_by)
        assert actual == expected
