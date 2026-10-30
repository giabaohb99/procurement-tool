"""Dữ liệu hàng cho báo cáo B4 "Đối tượng cần chú ý theo luật" (khóa 29, duoc-CR-689).

Mỗi (nhân sự, loại) là MỘT hàng — một người có thể vừa sắp nghỉ hưu vừa đang nuôi con nhỏ. Tình trạng tại
mốc `as_of` (= min(cuối kỳ, hôm nay)), không có trục thời gian. Chỉ nhân sự ĐANG LÀM, trong phạm vi.

Bốn loại (`KINDS`):
  - `retire_12m`: thời điểm nghỉ hưu (CUỐI THÁNG đủ tuổi, `legal_watch_retirement`) rơi vào `[as_of, as_of + 12 tháng]`.
    Cần ngày sinh + giới tính (nam / nữ); thiếu một trong hai thì không tính.
  - `past_retirement`: thời điểm nghỉ hưu đã QUA (< `as_of`) mà người đó vẫn đang làm (hàng nhân sự chỉ gồm người đang làm).
  - `maternity_now`: TÍNH CẢ HAI (một người đếm 1 lần) — (a) có đơn nghỉ ĐÃ DUYỆT loại thai sản phủ `as_of`, hoặc
    (b) hồ sơ nhân sự đang ở trạng thái "Nghỉ thai sản" (`STATUS_MATERNITY`). Trạng thái hồ sơ là trạng thái
    HIỆN TẠI nên nhánh (b) chỉ áp khi `as_of` là hôm nay (kỳ chưa kết thúc); kỳ quá khứ chỉ theo đơn. Người
    không có đơn thì mốc = None. Nhánh (b) không cần quyền nghỉ phép, nhánh (a) vẫn theo phạm vi đơn nghỉ. NHẬN LOẠI THAI SẢN bằng mã loại nghỉ
    `maternity` (`tab_leave_type.code`, seed `seed_nghi_phep.py`, `core/leave_codes.py`) — loại nào mang mã
    đó, ở đầu đơn HOẶC ở một dòng loại nghỉ của đơn nhiều loại. Mốc = ngày đi làm lại (ngày sau khoảng cuối).
  - `child_under_12m`: lao động nữ (giới tính nữ) có con (quan hệ con trai / con gái trong `tab_employee_family`)
    sinh trong 12 tháng gần nhất. Mốc = ngày con đủ 12 tháng. Mỗi người một hàng (con nhỏ nhất).

Số truy vấn CỐ ĐỊNH: nhân sự · [loại nghỉ · đơn · khoảng ngày — khi có `leave_q`] · hộ gia đình.
Không nạp / không trả ngày sinh ra ngoài: hàng chỉ mang MỐC đã tính.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import exists, or_
from sqlalchemy.orm import Session

from app.core.scoping import not_deleted_cond
from app.core.vn_time import vn_today
from app.modules.leave.constants import LR_APPROVED
from app.modules.leave.catalog_model import LeaveType
from app.modules.leave.period_spans import periods_by_request
from app.modules.leave.request_model import LeaveRequest, LeaveRequestLine

from .constants import RELATION_DAUGHTER, RELATION_SON
from .contact_model import EmployeeFamily
from .legal_watch_retirement import GENDER_FEMALE, add_months, retirement_date
from .model import Employee
from .service import STATUS_RESIGNED

KINDS = ("retire_12m", "past_retirement", "maternity_now", "child_under_12m")
MATERNITY_CODE = "maternity"
STATUS_MATERNITY = "maternity_leave"      # mã `Employee.status` "Nghỉ thai sản" (core/status_codes.EMPLOYEE_STATUS)


@dataclass(frozen=True)
class WatchRow:
    employee_id: int
    employee_code: str
    employee_name: str
    company_id: int
    department_id: int
    kind: str
    milestone: date | None      # None: nghỉ thai sản theo hồ sơ nhưng không có đơn → chưa biết ngày đi làm lại


def _maternity_return_dates(db: Session, leave_q, emp_ids: set[int], as_of: date) -> dict[int, date]:
    """`{employee_id: ngày đi làm lại}` của người có đơn thai sản đã duyệt phủ `as_of`.
    `leave_q` PHẢI đã qua `apply_scope(LeaveRequest, 'leave_request')` (đã loại đơn xóa mềm) — người xem chỉ
    thấy thai sản trong phạm vi đơn nghỉ phép của mình."""
    type_ids = [i for (i,) in db.query(LeaveType.id).filter(LeaveType.code == MATERNITY_CODE).all()]
    if not type_ids or not emp_ids:
        return {}
    on_line = exists().where(LeaveRequestLine.request_id == LeaveRequest.id,
                             LeaveRequestLine.leave_type_id.in_(type_ids))
    q = leave_q.with_entities(LeaveRequest.id, LeaveRequest.employee_id).filter(
        LeaveRequest.status == LR_APPROVED, LeaveRequest.from_date <= as_of, LeaveRequest.to_date >= as_of,
        LeaveRequest.employee_id.in_(emp_ids), or_(LeaveRequest.leave_type_id.in_(type_ids), on_line))
    reqs = q.all()
    spans = periods_by_request(db, [r.id for r in reqs])
    out: dict[int, date] = {}
    for r in reqs:
        ps = spans.get(r.id, [])
        if any(p.from_date <= as_of <= p.to_date for p in ps):      # khe giữa các khoảng không tính là đang nghỉ
            back = max(p.to_date for p in ps) + timedelta(days=1)
            out[r.employee_id] = max(back, out.get(r.employee_id, back))
    return out


def load_rows(db: Session, employees_q, as_of: date, *, leave_q=None,
              company_id: int | None = None, department_id: int | None = None) -> list[WatchRow]:
    """`employees_q` PHẢI đã qua `apply_scope(Employee, 'employee')`; `leave_q` (đã qua `apply_scope` đơn nghỉ phép,
    `None` = người xem không được xem đơn nghỉ → không có loại thai sản); hai bộ lọc chỉ thu hẹp thêm."""
    q = employees_q.filter(Employee.status != STATUS_RESIGNED, Employee.is_active == True)  # noqa: E712
    if company_id is not None:
        q = q.filter(Employee.company_id == company_id)
    if department_id is not None:
        q = q.filter(Employee.department_id == department_id)
    emps = q.with_entities(Employee.id, Employee.code, Employee.full_name, Employee.company_id,
                           Employee.department_id, Employee.gender, Employee.date_of_birth, Employee.status).all()
    by_id = {e.id: e for e in emps}
    out: list[WatchRow] = []

    def add(e, kind: str, milestone: date | None) -> None:
        out.append(WatchRow(e.id, e.code or "", e.full_name or "", e.company_id or 0, e.department_id or 0,
                            kind, milestone))

    horizon = add_months(as_of, 12)
    for e in emps:
        if e.date_of_birth:
            ret = retirement_date(e.date_of_birth, int(e.gender or 0))
            if ret and as_of <= ret <= horizon:
                add(e, "retire_12m", ret)
            elif ret and ret < as_of:
                add(e, "past_retirement", ret)
    #  Thai sản: đơn đã duyệt (theo phạm vi đơn nghỉ) HỢP trạng thái hồ sơ (chỉ khi mốc là hôm nay); đếm 1 lần/người.
    back_by_emp = _maternity_return_dates(db, leave_q, set(by_id), as_of) if leave_q is not None else {}
    if as_of >= vn_today():
        for e in emps:
            if (e.status or "") == STATUS_MATERNITY:
                back_by_emp.setdefault(e.id, None)
    for eid, back in back_by_emp.items():
        add(by_id[eid], "maternity_now", back)
    women = {i for i, e in by_id.items() if int(e.gender or 0) == GENDER_FEMALE}
    if women:
        oldest = add_months(as_of, -12)
        youngest: dict[int, date] = {}
        fam = db.query(EmployeeFamily.employee_id, EmployeeFamily.date_of_birth).filter(
            EmployeeFamily.employee_id.in_(women), EmployeeFamily.relation.in_((RELATION_SON, RELATION_DAUGHTER)),
            EmployeeFamily.date_of_birth > oldest, EmployeeFamily.date_of_birth <= as_of)
        gone = not_deleted_cond(EmployeeFamily)        # None nếu bảng không xóa mềm
        if gone is not None:
            fam = fam.filter(gone)
        for eid, dob in fam.all():
            youngest[eid] = max(dob, youngest.get(eid, dob))
        for eid, dob in youngest.items():
            add(by_id[eid], "child_under_12m", add_months(dob, 12))
    return out
