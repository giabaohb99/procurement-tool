"""Luật nghiệp vụ kế hoạch nhân sự: pháp nhân / phòng phải có thật, bộ ba (năm, pháp nhân, phòng) duy nhất,
và CHẶN ghi số lương khi người ghi không đọc được HĐLĐ của pháp nhân đó (`labor_contract.read` trong phạm vi)."""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.company.model import Company
from app.modules.department.model import Department

from .model import HeadcountPlan
from .serializer import can_see_payroll

PAYROLL_DENIED = "Cần quyền xem hợp đồng lao động để khai quỹ lương kế hoạch"


def check_refs(db: Session, company_id: int, department_id: int) -> None:
    """Pháp nhân phải có; phòng (khác 0) phải có thật. Sai → 422.

    KHÔNG bắt phòng «thuộc» pháp nhân: phòng ban ở DEGO dùng chung cho mọi pháp nhân —
    `Department.company_id` để 0 và bảng ánh xạ `tab_department_company` còn rỗng (dev + local,
    kiểm 28/10/2026), nên bắt buộc như bản đầu là từ chối MỌI kế hoạch theo phòng. Cặp
    (pháp nhân × phòng) có nghĩa qua hồ sơ nhân sự: số thực tế đếm người có đúng cặp đó."""
    if db.query(Company.id).filter(Company.id == company_id).first() is None:
        raise HTTPException(422, "Pháp nhân không tồn tại")
    if department_id and db.query(Department.id).filter(Department.id == department_id).first() is None:
        raise HTTPException(422, "Phòng ban không tồn tại")


def ensure_unique(db: Session, year: int, company_id: int, department_id: int, exclude_id: int = 0) -> None:
    q = db.query(HeadcountPlan.id).filter(HeadcountPlan.year == year, HeadcountPlan.company_id == company_id,
                                          HeadcountPlan.department_id == department_id)
    if exclude_id:
        q = q.filter(HeadcountPlan.id != exclude_id)
    if q.first() is not None:
        raise HTTPException(400, "Đã có kế hoạch cho năm, pháp nhân và phòng này")


def guard_payroll_write(profile: dict, payroll, company_id: int) -> None:
    """Khai số lương KHÁC 0 cho pháp nhân mà người ghi không đọc được HĐLĐ của nó → 403.

    0 / None không bị chặn: biểu mẫu luôn gửi ô số (trống = 0), nên chặn 0 là người chỉ sửa định biên không lưu nổi.
    Ở đường SỬA, bên gọi phải bỏ số 0 đó đi (`drop_blind_payroll`) — không thì đè mất quỹ lương thật đang bị che."""
    if payroll and not can_see_payroll(profile, company_id):
        raise HTTPException(403, PAYROLL_DENIED)


def drop_blind_payroll(profile: dict, values: dict, company_id: int) -> None:
    """Người không xem được lương của pháp nhân gửi 0 / None → coi như KHÔNG đổi ô lương (giữ số thật bị che)."""
    if "planned_payroll_monthly" in values and not values["planned_payroll_monthly"] \
            and not can_see_payroll(profile, company_id):
        values.pop("planned_payroll_monthly")
