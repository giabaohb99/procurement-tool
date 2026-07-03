from sqlalchemy import BigInteger, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import Base, AuditMixin


class Department(Base, AuditMixin):
    """Phòng ban (thuộc công ty, có phân cấp qua `parent`)."""

    __tablename__ = "tab_department"

    code: Mapped[str] = mapped_column(String(25), unique=True)
    name: Mapped[str] = mapped_column(String(255))
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
