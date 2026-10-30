"""Hàng dữ liệu + khai báo chỉ số của báo cáo Quỹ phép năm — tách khỏi
`balance_report_service.py` (giữ < 200 dòng). Xem docstring `balance_report_service.py` cho các
luật H1/H2 (lọc công ty, năm so sánh).

duoc-CR-686: thêm tham số `employee_status` (mặc định chỉ NHÂN SỰ ĐANG LÀM), lọc phòng ban HIỆN TẠI
của người giữ quỹ, 5 chỉ số cấu phần quỹ (cơ bản/thâm niên/chuyển sang/điều chỉnh/chuyển đã hết
hạn) và 2 chỉ số ĐẾM NGƯỜI (vượt quỹ · chưa nghỉ ngày nào).
"""
from __future__ import annotations

from dataclasses import dataclass

from fastapi import HTTPException
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.core.report_aggregate import DerivedSpec, DimensionSpec, MetricSpec, ReportSpec
from app.core.scoping import apply_scope
from app.modules.employee.model import Employee
from app.modules.employee.service import STATUS_RESIGNED
from app.modules.leave.balance_model import LeaveBalance

EMPLOYEE_STATUSES = ("working", "resigned", "all")
#  Chỉ số bấm được ra danh sách (`GET /api/leave-balances/summary/rows`).
DRILLDOWN_METRICS = {"remaining": "Còn lại", "people_over_quota": "Số người vượt quỹ",
                     "people_unused": "Chưa nghỉ ngày nào", "carried_expired": "Phép chuyển đã hết hạn",
                     "people_missing_balance": "Chưa được cấp quỹ"}

BAL_COLS = (LeaveBalance.company_id, LeaveBalance.leave_type_id, LeaveBalance.employee_id,
            LeaveBalance.allocated_days, LeaveBalance.seniority_days, LeaveBalance.carried_days,
            LeaveBalance.adjusted_days, LeaveBalance.used_days, LeaveBalance.pending_days,
            LeaveBalance.carried_out_days, LeaveBalance.carried_expired_days)


@dataclass(frozen=True)
class BalanceRow:
    company_id: int
    department_id: int
    leave_type_id: int
    leave_type_name: str
    employee_id: int
    employee_name: str
    granted: float
    used: float
    pending: float
    remaining: float
    allocated: float = 0.0
    seniority: float = 0.0
    carried: float = 0.0
    adjusted: float = 0.0
    carried_expired: float = 0.0
    #  Cờ THEO NGƯỜI (cộng mọi dòng quỹ của người đó): được cấp > 0 mà đã dùng + giữ chỗ = 0.
    person_unused: bool = False


def valid_employee_status(raw) -> str:
    """`employee_status` từ query string: rỗng → `working`; ngoài ba giá trị → 422."""
    v = (raw or "").strip() or "working"
    if v not in EMPLOYEE_STATUSES:
        raise HTTPException(422, "employee_status phải là working, resigned hoặc all")
    return v


def employee_conds(status: str, department_id: int | None) -> list:
    """Điều kiện trên `Employee`: `working` = chưa nghỉ việc VÀ còn hoạt động; `resigned` = phần bù.
    Phòng ban = phòng HIỆN TẠI của người giữ quỹ (không có lịch sử điều chuyển)."""
    conds = []
    working = and_(Employee.status != STATUS_RESIGNED, Employee.is_active.is_(True))
    if status == "working":
        conds.append(working)
    elif status == "resigned":
        conds.append(or_(Employee.status == STATUS_RESIGNED, Employee.is_active.is_(False)))
    if department_id is not None:
        conds.append(Employee.department_id == department_id)
    return conds


def rows_of(db: Session, user, prof: dict, year: int, type_name: dict, emp_dept: dict,
            emp_name: dict, company_id: int | None = None, status: str = "working",
            department_id: int | None = None) -> list[BalanceRow]:
    q = apply_scope(db.query(LeaveBalance), LeaveBalance, "leave_balance", user, prof)
    if company_id is not None:
        q = q.filter(LeaveBalance.company_id == company_id)  # H1: chỉ THU HẸP, sau apply_scope
    conds = employee_conds(status, department_id)
    if conds:   # lọc NGAY trong SQL bằng truy vấn con — không thêm truy vấn riêng
        q = q.filter(LeaveBalance.employee_id.in_(db.query(Employee.id).filter(*conds)))
    rows = q.filter(LeaveBalance.year == year).with_entities(*BAL_COLS).all()
    #  "Chưa nghỉ ngày nào" xét THEO NGƯỜI: tổng cấp > 0 và tổng (dùng + giữ chỗ) = 0 trên MỌI
    #  dòng quỹ — người đã nghỉ phép năm nhưng còn quỹ ốm chưa đụng thì KHÔNG tính.
    granted_sum, spent_sum = {}, {}
    for r in rows:
        granted_sum[r.employee_id] = granted_sum.get(r.employee_id, 0.0) + (
            (r.allocated_days or 0) + (r.seniority_days or 0) + (r.carried_days or 0)
            + (r.adjusted_days or 0))
        spent_sum[r.employee_id] = spent_sum.get(r.employee_id, 0.0) + (
            (r.used_days or 0) + (r.pending_days or 0))
    out = []
    for r in rows:
        #  CÙNG công thức `LeaveBalance.total_days`/`remaining_days` (balance_model.py) — chép
        #  lại vì `with_entities` không nạp @property, chỉ nạp cột thô. Đổi công thức ở model
        #  thì nhớ sửa luôn ở đây.
        granted = round((r.allocated_days or 0) + (r.seniority_days or 0) + (r.carried_days or 0)
                        + (r.adjusted_days or 0), 2)
        remaining = round(granted - (r.used_days or 0) - (r.pending_days or 0)
                          - (r.carried_out_days or 0), 2)
        out.append(BalanceRow(
            company_id=r.company_id or 0, department_id=emp_dept.get(r.employee_id, 0),
            leave_type_id=r.leave_type_id or 0, leave_type_name=type_name.get(r.leave_type_id, ""),
            employee_id=r.employee_id or 0, employee_name=emp_name.get(r.employee_id, ""),
            granted=granted, used=r.used_days or 0.0, pending=r.pending_days or 0.0,
            remaining=remaining, allocated=r.allocated_days or 0.0,
            seniority=r.seniority_days or 0.0, carried=r.carried_days or 0.0,
            adjusted=r.adjusted_days or 0.0, carried_expired=r.carried_expired_days or 0.0,
            person_unused=(round(granted_sum[r.employee_id], 2) > 0
                           and round(spent_sum[r.employee_id], 2) == 0)))
    return out


def build_spec(company_name: dict, department_name: dict) -> ReportSpec:
    def _days(key, label, field):
        return MetricSpec(key, label, kind="days", value_of=lambda r: getattr(r, field))

    metrics = [
        _days("granted", "Được cấp", "granted"), _days("used", "Đã dùng", "used"),
        _days("pending", "Đang giữ chỗ", "pending"), _days("remaining", "Còn lại", "remaining"),
        _days("allocated", "Phép năm cơ bản", "allocated"),
        _days("seniority", "Phép thâm niên", "seniority"),
        _days("carried", "Chuyển từ năm trước", "carried"), _days("adjusted", "Điều chỉnh", "adjusted"),
        _days("carried_expired", "Phép chuyển đã hết hạn", "carried_expired"),
        MetricSpec("people_over_quota", "Số người vượt quỹ", kind="int", good="down",
                  distinct_of=lambda r: r.employee_id if r.remaining < 0 else None),
        MetricSpec("people_unused", "Chưa nghỉ ngày nào", kind="int", good="down",
                  distinct_of=lambda r: r.employee_id if r.person_unused else None),
        #  Số THỜI ĐIỂM, chỉ có ở Tổng: nhân sự đang làm KHÔNG có dòng quỹ nào (xem
        #  `balance_report_missing`). `value_of` luôn 0 — giá trị thật ghép vào `totals` sau.
        MetricSpec("people_missing_balance", "Chưa được cấp quỹ", kind="int", good="down",
                  snapshot=True, value_of=lambda r: 0),
    ]
    derived = [DerivedSpec("usage_rate", "Tỷ lệ sử dụng", num="used", den="granted")]
    leave_type_dim = DimensionSpec("leave_type", "Loại nghỉ", key_of=lambda r: (
        [(r.leave_type_id, r.leave_type_name)] if r.leave_type_id else []))
    dimensions = {
        "leave_type": leave_type_dim,
        "company": DimensionSpec("company", "Công ty", key_of=lambda r: (
            [(r.company_id, company_name.get(r.company_id, ""))] if r.company_id else [])),
        "department": DimensionSpec("department", "Phòng ban", key_of=lambda r: (
            [(r.department_id, department_name.get(r.department_id, ""))] if r.department_id else [])),
        "employee": DimensionSpec("employee", "Nhân sự", key_of=lambda r: (
            [(r.employee_id, r.employee_name)] if r.employee_id else [])),
    }
    return ReportSpec(date_of=lambda r: None, metrics=metrics, derived=derived,
                      dimensions=dimensions, breakdowns={"leave_type": leave_type_dim},
                      rank_by="granted")
