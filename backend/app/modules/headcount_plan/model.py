"""Kế hoạch nhân sự — `tab_headcount_plan` (duoc-CR-689, phase 17).

Một dòng = định biên + quỹ lương kế hoạch của MỘT phòng trong MỘT pháp nhân MỘT năm.
`department_id = 0` là dòng của CẢ pháp nhân (so với tổng pháp nhân ở báo cáo A4, không cộng dồn với
các dòng phòng). FK MỀM (không khai `ForeignKey`), khuôn `tab_labor_contract`; tồn tại của pháp nhân /
phòng kiểm ở `service`. Xóa CỨNG: ràng buộc duy nhất sẽ chặn nhập lại nếu xóa mềm.
⚠️ `planned_payroll_monthly` là số LƯƠNG (đồng NGUYÊN) — chỉ trả cho người có `labor_contract.read`.
"""
from sqlalchemy import BigInteger, Index, Integer, SmallInteger, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base


class HeadcountPlan(Base, AuditMixin):
    __tablename__ = "tab_headcount_plan"
    __table_args__ = (
        UniqueConstraint("year", "company_id", "department_id", name="uq_headcount_plan_scope"),
        Index("ix_headcount_plan_company_year", "company_id", "year"),
    )

    year: Mapped[int] = mapped_column(SmallInteger)
    company_id: Mapped[int] = mapped_column(BigInteger)
    department_id: Mapped[int] = mapped_column(BigInteger, default=0)   # 0 = toàn pháp nhân
    planned_headcount: Mapped[int] = mapped_column(Integer, default=0)
    planned_payroll_monthly: Mapped[int] = mapped_column(BigInteger, default=0)   # VND / tháng
    note: Mapped[str] = mapped_column(String(500), default="")
