"""Báo cáo Quỹ phép năm (phase 04, `GET /api/leave-balances/summary`).

Kỳ ở đây là NĂM, không phải khoảng ngày — `fetch(d_from, d_to)` của khung bỏ
qua `d_from`. Quỹ phép không có cột ngày bên trong một năm nên KHÔNG có trục
thời gian — `trend` luôn bị ghi đè thành rỗng sau khi gọi `build_report`; FE
ẩn hẳn biểu đồ xu hướng theo cấu hình riêng của trang (`periodMode: 'year'`).

⚠️ H2 (review 01/10/2026): năm so sánh LUÔN là `period.date_to.year - 1` khi
`compare != none`, KHÔNG suy từ `period.compare_to` — `compare=previous` của
`parse_period` lùi theo ĐƠN VỊ LỊCH của preset (`this_month` lùi 1 THÁNG,
`this_quarter` lùi 1 QUÝ...), nên `compare_to.year` chỉ tình cờ trùng năm
trước khi preset là `this_year`/`last_year`. Báo cáo này LUÔN là năm-so-năm
bất kể preset đang chọn, nên `fetch` so sánh trực tiếp `d_to == period.date_to`
(gọi lần 1, kỳ NÀY) để chọn năm hiện tại hay năm trước, bỏ qua giá trị thật
của `compare_to`.

Phòng ban của quỹ phép không có cột riêng (`SCOPE_FIELDS["leave_balance"]`
không khai `dept_id`) — chiều "Phòng ban" join `Employee.department_id` HIỆN
TẠI của người giữ quỹ (không có lịch sử điều chuyển, xem `notes`).

Hiệu năng: `LeaveBalance.year == <năm>` lọc NGAY TRONG SQL (có index
`ix_leave_balance_emp_year`); `company_id` (H1) lọc SAU `apply_scope`, chỉ
thu hẹp. `with_entities` chỉ nạp 11 cột thô rồi tính `granted`/`remaining`
bằng công thức giống HỆT `LeaveBalance.total_days`/`remaining_days` (xem
`balance_model.py`) — tránh nạp cả đối tượng ORM. Số truy vấn CỐ ĐỊNH: 1 câu
quỹ phép + 1 câu loại nghỉ (luôn cần, breakdown) mỗi lần `fetch`, cộng
Employee/Company/Department CHỈ KHI `group_by` cần tới.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from app.core.report_aggregate import DerivedSpec, DimensionSpec, MetricSpec, ReportSpec, build_report
from app.core.report_period import Period
from app.core.scoping import apply_scope
from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.leave.balance_model import LeaveBalance
from app.modules.leave.catalog_model import LeaveType

_BAL_COLS = (LeaveBalance.company_id, LeaveBalance.leave_type_id, LeaveBalance.employee_id,
            LeaveBalance.allocated_days, LeaveBalance.seniority_days, LeaveBalance.carried_days,
            LeaveBalance.adjusted_days, LeaveBalance.used_days, LeaveBalance.pending_days,
            LeaveBalance.carried_out_days)


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


def _rows_of(db: Session, user, prof: dict, year: int, type_name: dict, emp_dept: dict,
            emp_name: dict, company_id: int | None = None) -> list[BalanceRow]:
    q = apply_scope(db.query(LeaveBalance), LeaveBalance, "leave_balance", user, prof)
    if company_id is not None:
        q = q.filter(LeaveBalance.company_id == company_id)  # H1: chỉ THU HẸP, sau apply_scope
    rows = q.filter(LeaveBalance.year == year).with_entities(*_BAL_COLS).all()
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
            remaining=remaining))
    return out


def _build_spec(company_name: dict, department_name: dict) -> ReportSpec:
    metrics = [
        MetricSpec("granted", "Được cấp", kind="days", value_of=lambda r: r.granted),
        MetricSpec("used", "Đã dùng", kind="days", value_of=lambda r: r.used),
        MetricSpec("pending", "Đang giữ chỗ", kind="days", value_of=lambda r: r.pending),
        MetricSpec("remaining", "Còn lại", kind="days", value_of=lambda r: r.remaining),
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


def build_summary(db: Session, user, prof: dict, period: Period, group_by: str | None,
                  company_id: int | None = None) -> dict:
    """Hợp đồng chuẩn `build_report` cho `/api/leave-balances/summary` (+ `/export`)."""
    type_name = {t.id: t.name for t in db.query(LeaveType.id, LeaveType.name).all()}
    #  Phòng ban HIỆN TẠI đi qua Employee — chỉ tra khi "Xem theo" thật sự cần (phòng ban HOẶC
    #  nhân sự); công ty có sẵn cột trên quỹ phép nên không cần Employee cho chiều đó.
    emp_dept, emp_name = {}, {}
    if group_by in ("department", "employee"):
        for e in db.query(Employee.id, Employee.department_id, Employee.full_name).all():
            emp_dept[e.id] = e.department_id or 0
            emp_name[e.id] = e.full_name
    company_name = ({c.id: c.name for c in db.query(Company.id, Company.name).all()}
                    if group_by == "company" else {})
    department_name = ({d.id: d.name for d in db.query(Department.id, Department.name).all()}
                       if group_by == "department" else {})
    spec = _build_spec(company_name, department_name)

    def fetch(_d_from: date, d_to: date):
        #  H2: NĂM so sánh LUÔN = năm hiện tại - 1, không suy từ `d_to` của lần gọi so sánh
        #  (xem docstring đầu tệp) — chỉ lần gọi KỲ NÀY (d_to == period.date_to) dùng năm thật.
        year = period.date_to.year if d_to == period.date_to else period.date_to.year - 1
        return _rows_of(db, user, prof, year, type_name, emp_dept, emp_name, company_id)

    data = build_report(fetch, spec, period, group_by=group_by)
    data["trend"] = []  # Quỹ phép không có trục ngày trong một năm, xem docstring đầu tệp
    data["notes"] = [
        "Kỳ của báo cáo này là NĂM (lấy năm của ngày kết thúc kỳ đang xem) — không có biểu đồ "
        "xu hướng theo ngày/tuần/tháng.",
        "Phòng ban lấy theo hồ sơ HIỆN TẠI của nhân sự (hệ thống chưa lưu lịch sử điều chuyển).",
    ]
    return data
