from sqlalchemy import (BigInteger, Boolean, ForeignKey, SmallInteger, String,
                        UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import Base, AuditMixin


class Department(Base, AuditMixin):
    """Phòng ban (thuộc công ty, có phân cấp qua `parent`)."""

    __tablename__ = "tab_department"

    code: Mapped[str] = mapped_column(String(25), unique=True)
    name: Mapped[str] = mapped_column(String(255))
    #  Mã đi vào số hiệu văn bản (`NS` trong `08/2026/TB-NS-DEGO`) — chỉ chữ và
    #  số, khác `code`. Xem giải thích ở `Company.issue_code`.
    issue_code: Mapped[str] = mapped_column(String(20), default="")
    #  1 phòng chức năng · 2 đơn vị kinh doanh · 3 ban dự án.
    kind: Mapped[int] = mapped_column(SmallInteger, default=1)
    company_id: Mapped[int] = mapped_column(BigInteger, default=0)
    parent: Mapped[int] = mapped_column(BigInteger, default=0)  # 0 = gốc
    manager_id: Mapped[int] = mapped_column(BigInteger, default=0)  # Trưởng bộ phận (nhân sự) — chọn cứng
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    manager = relationship(
        "Employee",
        primaryjoin="foreign(Department.manager_id) == Employee.id",
        uselist=False,
        viewonly=True,
    )

    @property
    def manager_name(self) -> str | None:
        return self.manager.full_name if self.manager else None


class DepartmentCompany(Base, AuditMixin):
    """Một phòng ban hiện diện tại một pháp nhân (A06).

    `Department.company_id` / `manager_id` vẫn là pháp nhân gốc và trưởng phòng
    tại pháp nhân gốc để mã Thu mua cũ tiếp tục chạy. Bảng này là nguồn dữ liệu
    đầy đủ cho trường hợp một phòng dùng chung ở nhiều pháp nhân.
    """

    __tablename__ = "tab_department_company"
    __table_args__ = (
        UniqueConstraint("department_id", "company_id", name="uq_department_company"),
    )

    department_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tab_department.id", ondelete="CASCADE"), index=True
    )
    company_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tab_company.id", ondelete="CASCADE"), index=True
    )
    manager_employee_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("tab_employee.id", ondelete="SET NULL"), nullable=True
    )
    # Một phòng có thể dùng mã riêng tại một pháp nhân; rỗng thì lấy
    # Department.issue_code.
    issue_code_override: Mapped[str] = mapped_column(String(20), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    company = relationship(
        "Company",
        primaryjoin="foreign(DepartmentCompany.company_id) == Company.id",
        uselist=False,
        viewonly=True,
    )
    manager = relationship(
        "Employee",
        primaryjoin="foreign(DepartmentCompany.manager_employee_id) == Employee.id",
        uselist=False,
        viewonly=True,
    )

    @property
    def company_name(self) -> str:
        return self.company.name if self.company else ""

    @property
    def manager_name(self) -> str:
        return self.manager.full_name if self.manager else ""
