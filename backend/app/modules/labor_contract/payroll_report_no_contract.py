"""Đếm người ĐANG LÀM mà CHƯA có hợp đồng lao động hiệu lực (báo cáo A5, duoc-CR-692).

Quỹ lương chỉ tính từ lương trên HĐLĐ, nên người chưa có HĐ hiệu lực không có mặt trong số tiền; báo cáo nêu số này
riêng để người xem biết quỹ lương chưa phủ hết ai. Chỉ là số ĐẾM (không lộ lương). Một truy vấn đếm duy nhất.

«Có HĐ hiệu lực» xét trên MỌI HĐ của người (không qua phạm vi HĐLĐ): người xem có thể không được xem HĐ của một pháp nhân,
nhưng người đó vẫn có HĐ nên không được tính là «chưa có HĐ».
"""
from __future__ import annotations

from datetime import date

from sqlalchemy import and_, exists, or_
from sqlalchemy.orm import Session

from app.core.labor_contract_codes import LaborContractStatus as S
from app.modules.employee.model import Employee
from app.modules.employee.service import STATUS_RESIGNED

from .model import LaborContract


def count_without_contract(db: Session, employees_q, as_of: date, company_id: int | None = None,
                           department_id: int | None = None) -> int:
    """`employees_q` PHẢI đã qua `apply_scope(Employee, "employee", ...)`. Đếm người còn làm (đang hoạt động, chưa
    nghỉ việc) tại hồ sơ hiện tại mà không có HĐ ký còn hiệu lực ở `as_of` (HĐ đã chấm dứt SAU `as_of` vẫn tính là có)."""
    in_force = exists().where(and_(
        LaborContract.employee_id == Employee.id,
        LaborContract.is_deleted.is_(False),      # đọc thẳng nên tự lọc HĐ đã xóa mềm
        LaborContract.start_date <= as_of,
        or_(LaborContract.end_date.is_(None), LaborContract.end_date >= as_of),
        or_(LaborContract.status == int(S.SIGNED),
            and_(LaborContract.status == int(S.TERMINATED), LaborContract.terminated_date > as_of))))
    q = employees_q.filter(Employee.is_active.is_(True), Employee.status != STATUS_RESIGNED, ~in_force)
    if company_id is not None:
        q = q.filter(Employee.company_id == company_id)
    if department_id is not None:
        q = q.filter(Employee.department_id == department_id)
    return q.count()
