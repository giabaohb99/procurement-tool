"""HỢP ĐỒNG LAO ĐỘNG của nhân sự — `tab_labor_contract`.

KHÔNG lẫn với `modules/contract` (hợp đồng NCC / khách).

⚠️ FK MỀM: `employee_id`, `company_id`, `department_id`, `template_id`, các `*_file_id`
đều KHÔNG khai `ForeignKey` (khuôn `tab_employee_work_history`) — dọn ở tầng service.
`company_id` / `department_id` là SNAPSHOT lúc lập (phục vụ phạm vi dữ liệu).
⚠️ Tiền = đồng NGUYÊN (BigInteger), không lẻ. Lương nằm sau khóa quyền riêng `labor_contract`.
⚠️ Trạng thái EXPIRED không ghi DB — suy ra từ SIGNED + end_date < hôm nay.
"""
from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, Index, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base


class LaborContract(Base, AuditMixin):
    __tablename__ = "tab_labor_contract"
    __table_args__ = (
        Index("ix_labor_contract_emp_start", "employee_id", "start_date"),
        Index("ix_labor_contract_company_status", "company_id", "status"),
    )

    code: Mapped[str] = mapped_column(String(25), unique=True)       # HDLD001...
    contract_no: Mapped[str] = mapped_column(String(50), default="")  # số in trên HĐ; rỗng → dùng code
    employee_id: Mapped[int] = mapped_column(BigInteger)
    company_id: Mapped[int] = mapped_column(BigInteger, default=0)
    department_id: Mapped[int] = mapped_column(BigInteger, default=0)
    template_id: Mapped[int] = mapped_column(BigInteger, default=0)
    #  `LaborContractType` / `LaborContractStatus` (core/labor_contract_codes.py)
    contract_type: Mapped[int] = mapped_column(SmallInteger)
    status: Mapped[int] = mapped_column(SmallInteger, default=1)

    sign_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    job_title: Mapped[str] = mapped_column(String(100), default="")   # khớp Employee.position
    work_location: Mapped[str] = mapped_column(String(255), default="")
    base_salary: Mapped[int] = mapped_column(BigInteger, default=0)
    insurance_salary: Mapped[int] = mapped_column(BigInteger, default=0)
    allowance: Mapped[int] = mapped_column(BigInteger, default=0)      # tổng phụ cấp, một khoản
    allowance_note: Mapped[str] = mapped_column(String(500), default="")
    note: Mapped[str] = mapped_column(String(500), default="")

    generated_file_id: Mapped[int] = mapped_column(BigInteger, default=0)
    generated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    generated_by: Mapped[int] = mapped_column(BigInteger, default=0)
    signed_file_id: Mapped[int] = mapped_column(BigInteger, default=0)

    terminated_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    terminate_reason: Mapped[str] = mapped_column(String(500), default="")
