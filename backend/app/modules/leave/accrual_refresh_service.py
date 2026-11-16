"""TÍNH LẠI `allocated_days` năm NAY của quỹ phép loại MONTHLY_AFTER (duoc-CR-762) — MỘT hàm dùng chung.

Hạn mức của chế độ này phụ thuộc ngày làm chính thức (`accrual_start_service`), mà ngày đó đổi sau khi quỹ đã cấp:
  · HĐLĐ chuyển sang Đã ký (`labor_contract.service.transition`),
  · hình thức nhân viên đổi từ / sang Thử việc, hoặc ngày vào làm đổi (`employee.service.update_employee_core`),
  · loại nghỉ được đổi sang chế độ này ở form / API (`catalog_controller`) và script chuyển Phép năm
    (`scripts/apply_monthly_after_annual_leave.py`).
Cả bốn gọi `refresh_monthly_after_allocation` — cùng đường cấp quỹ của `ensure_balance`
(`policy_allocation.allocated_days`, đã tính phân bổ chính sách) và cùng hàm ghi / nhật ký của duoc-CR-717
(`policy_assignment_balances.apply_values`). Chỉ cột `allocated_days` của dòng quỹ NĂM NAY (giờ Việt Nam) VÀ CÁC NĂM SAU đã có dòng quỹ bị đụng;
năm đã qua, thâm niên, mang sang, điều chỉnh, nghỉ bù, đã dùng, giữ chỗ, đã thanh toán giữ nguyên.

`previous_starts` (`{employee_id: AccrualStart}` dựng TRƯỚC khi nơi gọi đổi hồ sơ / HĐ) bật chế độ "chỉ làm lại khi mốc
tích đổi thật": người nào mốc không đổi thì quỹ KHÔNG bị đụng (không để một lần sửa hồ sơ lặt vặt kéo theo việc áp lại
hạn mức hiện hành lên quỹ đã cấp từ hạn mức cũ). Không truyền = tính lại hết (script, đổi chế độ loại nghỉ).

Chỉ `flush`, KHÔNG commit — nơi gọi commit cùng giao dịch của mình.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from sqlalchemy.orm import Session

from app.core.vn_time import vn_today
from app.modules.employee.model import Employee

from . import accrual_start_service, policy_allocation
from .balance_model import LeaveBalance
from .catalog_model import LeaveType
from .constants import LeaveAccrualMode
from .policy_assignment_balances import apply_values
from .policy_assignment_service import lock_employees

DEFAULT_LABEL = "Tính lại Phép năm cộng dần sau mỗi tháng làm đủ (duoc-CR-762)"


@dataclass
class RefreshItem:
    """Một dòng quỹ đã xét: `old` / `new` là `allocated_days` trước / sau (bằng nhau = giữ nguyên)."""

    balance: LeaveBalance
    employee: Employee
    leave_type: LeaveType
    old: float
    new: float
    start: accrual_start_service.AccrualStart

    @property
    def changed(self) -> bool:
        return abs(self.old - self.new) > 1e-9


def refresh_monthly_after_allocation(db: Session, employee_ids: Iterable[int] | None = None, *,
                                     leave_type_ids: Iterable[int] | None = None,
                                     previous_starts: dict[int, accrual_start_service.AccrualStart] | None = None,
                                     actor: int = 0, label: str = DEFAULT_LABEL) -> list[RefreshItem]:
    """Tính lại quỹ NĂM NAY VÀ CÁC NĂM SAU của các loại MONTHLY_AFTER cho `employee_ids` (`None` = mọi người có dòng quỹ).

    `leave_type_ids` thu hẹp thêm theo loại (script, đổi chế độ loại nghỉ). `previous_starts` xem docstring đầu tệp.
    Loại chưa có dòng quỹ thì KHÔNG tạo — dòng quỹ sẽ được cấp đúng mốc lúc người đó chạm tới (`ensure_balance`).
    Không có loại MONTHLY_AFTER nào → trả `[]` sau một truy vấn. Thứ tự khóa như đường phân bổ chính sách: hồ sơ (id tăng
    dần) rồi dòng quỹ. Mốc tích nạp gom MỘT lần rồi truyền thẳng xuống `allocated_days` (không truy vấn HĐLĐ từng dòng)."""
    ids = None if employee_ids is None else {int(i) for i in employee_ids}
    if ids is not None and not ids:
        return []
    #  Ghi trước những gì nơi gọi vừa đổi (HĐ vừa Đã ký, hồ sơ vừa sang Thử việc, loại vừa đổi chế độ): các truy vấn dưới
    #  đây đọc từ DB và phiên tắt autoflush — không flush thì tính ra theo trạng thái CŨ (kể cả bước dò loại MONTHLY_AFTER).
    db.flush()
    types = db.query(LeaveType).filter(LeaveType.accrual_mode == int(LeaveAccrualMode.MONTHLY_AFTER))
    if leave_type_ids is not None:
        types = types.filter(LeaveType.id.in_({int(i) for i in leave_type_ids} or {0}))
    types = {t.id: t for t in types.all()}
    if not types:
        return []

    this_year = vn_today().year

    def balance_query():
        query = db.query(LeaveBalance).filter(LeaveBalance.year >= this_year, LeaveBalance.leave_type_id.in_(types))
        return query if ids is None else query.filter(LeaveBalance.employee_id.in_(ids))

    emp_ids = sorted({i for (i,) in balance_query().with_entities(LeaveBalance.employee_id).distinct().all()})
    if not emp_ids:
        return []
    lock_employees(db, emp_ids)
    balances = policy_allocation.with_row_lock(
        db, balance_query().order_by(LeaveBalance.employee_id, LeaveBalance.year, LeaveBalance.leave_type_id),
        exclusive=True).all()
    employees = {e.id: e for e in db.query(Employee).filter(Employee.id.in_(emp_ids)).all()}
    starts = accrual_start_service.official_start_map(db, employees.values())

    items: list[RefreshItem] = []
    seniority_cache: dict = {}
    for balance in balances:
        emp = employees.get(balance.employee_id)
        if emp is None:     # dòng quỹ mồ côi (hồ sơ đã xóa) — không có người để tính
            continue
        before = (previous_starts or {}).get(emp.id)
        if before is not None and before.math_date == starts[emp.id].math_date:
            continue        # mốc tích không đổi → quỹ đã cấp giữ nguyên (không áp lại hạn mức hiện hành)
        leave_type = types[balance.leave_type_id]
        old = float(balance.allocated_days or 0.0)
        new = policy_allocation.allocated_days(db, leave_type, emp, balance.year, lock=True, starts=starts)
        apply_values(db, emp, {leave_type.id: new}, types, {(emp.id, leave_type.id): balance}, balance.year,
                     recalc=True, actor=actor, label=label, create_missing=False,
                     seniority_cache=seniority_cache, starts=starts)
        items.append(RefreshItem(balance, emp, leave_type, old, new, starts[emp.id]))
    db.flush()
    return items
