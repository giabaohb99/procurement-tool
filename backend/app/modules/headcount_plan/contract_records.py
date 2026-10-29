"""Đường nạp HĐLĐ DUY NHẤT cho phần «thực tế» của kế hoạch nhân sự (duoc-CR-690): chi tiết kế hoạch (`actual_detail`) và
gợi ý theo vị trí (`position_stats`) cùng đi qua đây, giống báo cáo A5 (`apply_scope(labor_contract)` rồi `load_records`).

Lý do gom một chỗ: HĐ chứa lương, nên mọi nơi đọc HĐ phải qua phạm vi dữ liệu của người xem (kể cả «loại trừ phòng ban»,
«chọn công ty») và bỏ HĐ đã xóa mềm — nơi nào tự `db.query(LaborContract)` trần là lộ lương ngoài quyền. «HĐ còn hiệu lực
tại ngày» dùng đúng `payroll_report_data.rows_at` (HĐ đã ký + HĐ chấm dứt SAU ngày đó, mỗi người×pháp nhân một HĐ).
"""
from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.core.scoping import apply_scope, exclude_deleted
from app.modules.labor_contract.model import LaborContract
from app.modules.labor_contract.payroll_report_data import PayRecord, load_records


def scoped_contract_records(db: Session, user, profile: dict, lo: date, hi: date, today: date,
                            company_id: int | None = None, department_id: int | None = None) -> list[PayRecord]:
    """HĐ có thể còn hiệu lực ở một mốc trong [lo, hi], đã qua phạm vi `labor_contract.read` của người xem."""
    q = exclude_deleted(apply_scope(db.query(LaborContract), LaborContract, "labor_contract", user, profile),
                        LaborContract)
    return load_records(db, q, lo, hi, today, company_id, department_id)


def scope_hides_contracts(db: Session, user, profile: dict, company_id: int, department_id: int | None = None) -> bool:
    """Phạm vi `labor_contract` của người xem có bỏ bớt HĐ nào của pháp nhân (× phòng) này không — để «Thực tế» của kế
    hoạch không âm thầm thiếu lương các phòng bị loại trừ mà người xem tưởng là đủ (soát E2E CR-690)."""
    base = exclude_deleted(db.query(LaborContract), LaborContract).filter(LaborContract.company_id == company_id)
    if department_id:
        base = base.filter(LaborContract.department_id == department_id)
    scoped = apply_scope(base, LaborContract, "labor_contract", user, profile)
    return scoped.count() < base.count()
