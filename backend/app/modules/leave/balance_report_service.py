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

duoc-CR-686: `employee_status` (mặc định chỉ người đang làm) + `department_id` lọc qua truy vấn
con trên `Employee` ngay trong câu quỹ phép; `people_missing_balance` (snapshot, chỉ ở Tổng) ở
`balance_report_missing.py`; danh sách người ở `balance_report_drill_rows.py`; dòng dữ liệu +
khai báo chỉ số ở `balance_report_spec.py`.

Hiệu năng: `LeaveBalance.year == <năm>` lọc NGAY TRONG SQL (có index
`ix_leave_balance_emp_year`); `company_id` (H1) lọc SAU `apply_scope`, chỉ
thu hẹp. `with_entities` chỉ nạp 11 cột thô rồi tính `granted`/`remaining`
bằng công thức giống HỆT `LeaveBalance.total_days`/`remaining_days` (xem
`balance_model.py`) — tránh nạp cả đối tượng ORM. Số truy vấn CỐ ĐỊNH: 1 câu
quỹ phép + 1 câu loại nghỉ (luôn cần, breakdown) mỗi lần `fetch`, cộng
Employee/Company/Department CHỈ KHI `group_by` cần tới.
"""
from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.core.report_aggregate import build_report
from app.core.report_period import Period
from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.leave.balance_report_missing import count_missing_balance
from app.modules.leave.balance_report_spec import DRILLDOWN_METRICS, build_spec, rows_of
from app.modules.leave.catalog_model import LeaveType

NOTES = [
    "Kỳ của báo cáo này là NĂM (lấy năm của ngày kết thúc kỳ đang xem) — không có biểu đồ "
    "xu hướng theo ngày/tuần/tháng.",
    "Phòng ban lấy theo hồ sơ HIỆN TẠI của nhân sự (hệ thống chưa lưu lịch sử điều chuyển).",
    "Mặc định chỉ tính nhân sự ĐANG LÀM; đổi 'Trạng thái nhân sự' để xem người đã nghỉ việc hoặc "
    "tất cả. 'Chưa được cấp quỹ' chỉ đếm người đang làm không có dòng quỹ năm nay cho loại nghỉ "
    "nào tính quỹ, chỉ hiện ở Tổng.",
]


def load_lookups(db: Session, group_by: str | None) -> tuple[dict, dict, dict, dict, dict]:
    """(tên loại nghỉ, phòng ban hiện tại, tên nhân sự, tên công ty, tên phòng ban). Phòng ban
    HIỆN TẠI đi qua Employee — chỉ tra khi 'Xem theo' thật sự cần (phòng ban HOẶC nhân sự)."""
    type_name = {t.id: t.name for t in db.query(LeaveType.id, LeaveType.name).all()}
    emp_dept, emp_name = {}, {}
    if group_by in ("department", "employee"):
        for e in db.query(Employee.id, Employee.department_id, Employee.full_name).all():
            emp_dept[e.id] = e.department_id or 0
            emp_name[e.id] = e.full_name
    company_name = ({c.id: c.name for c in db.query(Company.id, Company.name).all()}
                    if group_by == "company" else {})
    department_name = ({d.id: d.name for d in db.query(Department.id, Department.name).all()}
                       if group_by == "department" else {})
    return type_name, emp_dept, emp_name, company_name, department_name


def build_summary(db: Session, user, prof: dict, period: Period, group_by: str | None,
                  company_id: int | None = None, department_id: int | None = None,
                  employee_status: str = "working") -> dict:
    """Hợp đồng chuẩn `build_report` cho `/api/leave-balances/summary` (+ `/export`)."""
    type_name, emp_dept, emp_name, company_name, department_name = load_lookups(db, group_by)
    spec = build_spec(company_name, department_name)

    def year_of(d_to: date) -> int:
        #  H2: NĂM so sánh LUÔN = năm hiện tại - 1, không suy từ `d_to` của lần gọi so sánh
        #  (xem docstring đầu tệp) — chỉ lần gọi KỲ NÀY (d_to == period.date_to) dùng năm thật.
        return period.date_to.year if d_to == period.date_to else period.date_to.year - 1

    def fetch(_d_from: date, d_to: date):
        return rows_of(db, user, prof, year_of(d_to), type_name, emp_dept, emp_name, company_id,
                       employee_status, department_id)

    def snapshot(d_to: date) -> dict:
        return {"people_missing_balance": count_missing_balance(
            db, user, prof, year_of(d_to), employee_status, company_id, department_id)}

    data = build_report(fetch, spec, period, group_by=group_by, snapshot=snapshot)
    data["trend"] = []  # Quỹ phép không có trục ngày trong một năm, xem docstring đầu tệp
    data["meta"]["drilldown_metrics"] = list(DRILLDOWN_METRICS)
    data["notes"] = list(NOTES)
    return data
