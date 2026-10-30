"""Ký HĐLĐ -> tự cập nhật ô lương trên hồ sơ nhân sự (duoc-CR-693).

Hồ sơ nhân sự là NƠI DUY NHẤT báo cáo Quỹ lương đọc số lương (`employee.salary_monthly` / `allowance_monthly`);
hợp đồng đã ký chỉ là một nguồn điền ô đó cho khỏi nhập hai lần.

Điều kiện — chỉ khi HĐ vừa ký là HĐ HIỆU LỰC MỚI NHẤT của người đó:
  - đã bắt đầu (`start_date` <= hôm nay) và chưa hết hạn (`end_date` rỗng hoặc >= hôm nay);
  - không có HĐ Đã ký nào khác (chưa xóa mềm) đã bắt đầu muộn hơn (hòa ngày thì HĐ có id lớn hơn thắng).
Ký một HĐ cũ bổ sung, hay HĐ chưa tới ngày hiệu lực, thì KHÔNG ghi đè lương của HĐ đang chạy.
Nháp là trạng thái duy nhất sửa được lương trên HĐ, nên chỉ cần gọi một lần lúc chuyển DRAFT -> SIGNED.
"""
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.labor_contract_codes import LaborContractStatus as S
from app.core.vn_time import vn_today
from app.modules.employee.model import Employee
from app.modules.employee.service import set_salary

from .model import LaborContract


def is_latest_in_force(db: Session, row: LaborContract, today) -> bool:
    """`row` (đã ký) là HĐ hiệu lực mới nhất của nhân sự tại `today`."""
    if int(row.status) != int(S.SIGNED) or row.start_date > today:
        return False
    if row.end_date is not None and row.end_date < today:
        return False
    newer = db.query(LaborContract.id).filter(
        LaborContract.employee_id == row.employee_id, LaborContract.id != row.id,
        LaborContract.is_deleted.is_(False), LaborContract.status == int(S.SIGNED),
        LaborContract.start_date <= today,
        or_(LaborContract.end_date.is_(None), LaborContract.end_date >= today),
        or_(LaborContract.start_date > row.start_date,
            and_(LaborContract.start_date == row.start_date, LaborContract.id > row.id)))
    return newer.first() is None


def sync_profile_salary(db: Session, row: LaborContract, actor_id: int) -> bool:
    """Chép lương cơ bản / phụ cấp của HĐ sang hồ sơ nếu đủ điều kiện. KHÔNG commit (chung giao dịch với việc ký).
    Trả `True` nếu hồ sơ đổi. Nhật ký chỉ ghi "đã cập nhật lương", không kèm số."""
    if not is_latest_in_force(db, row, vn_today()):
        return False
    emp = db.get(Employee, row.employee_id)
    if emp is None or not set_salary(emp, row.base_salary or 0, row.allowance or 0):
        return False
    emp.updated_by = actor_id
    record(db, actor_id, "employee", emp.id, "update",
           f"Cập nhật lương theo hợp đồng lao động {row.code} (ký hợp đồng)", doc_code=emp.code or "", commit=False)
    return True
