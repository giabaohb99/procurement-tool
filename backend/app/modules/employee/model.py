from sqlalchemy import BigInteger, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import Base, AuditMixin


class Employee(Base, AuditMixin):
    """Nhân viên — thuộc công ty & phòng ban; gắn với tài khoản qua tab_user.employee_id."""

    __tablename__ = "tab_employee"

    code: Mapped[str] = mapped_column(String(25), unique=True)
    full_name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), default="")
    phone: Mapped[str] = mapped_column(String(25), default="")
    company_id: Mapped[int] = mapped_column(BigInteger, default=0)
    department_id: Mapped[int] = mapped_column(BigInteger, default=0)
    position: Mapped[str] = mapped_column(String(100), default="")
    role_name: Mapped[str] = mapped_column(String(100), default="")
    status: Mapped[str] = mapped_column(String(50), default="Chính thức")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    department = relationship(
        "Department",
        primaryjoin="foreign(Employee.department_id) == Department.id",
        uselist=False,
        viewonly=True
    )

    @property
    def department_name(self) -> str | None:
        return self.department.name if self.department else None

    @property
    def manager_name(self) -> str | None:
        return self.department.manager_name if self.department else None
