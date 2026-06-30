from sqlalchemy import Boolean, String, Text, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import Base, AuditMixin


class Warehouse(Base, AuditMixin):
    __tablename__ = "tab_warehouse"
    code: Mapped[str] = mapped_column(String(25), unique=True)
    name: Mapped[str] = mapped_column(String(255))
    address: Mapped[str] = mapped_column(Text, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Unit(Base, AuditMixin):
    __tablename__ = "tab_unit"
    code: Mapped[str] = mapped_column(String(25), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class ItemGroup(Base, AuditMixin):
    """Phân loại VTBB/NL + thời gian quy định (Sheet phân loại)."""
    __tablename__ = "tab_item_group"
    code: Mapped[str] = mapped_column(String(25), unique=True, default="")
    name: Mapped[str] = mapped_column(String(100), unique=True)
    std_days: Mapped[str] = mapped_column(String(20), default="")          # số ngày QĐ khi NCC CÓ sẵn hàng
    std_days_unavail: Mapped[str] = mapped_column(String(20), default="")  # số ngày QĐ khi KHÔNG sẵn hàng
    note: Mapped[str] = mapped_column(Text, default="")
    apply_date: Mapped[str] = mapped_column(String(20), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Brand(Base, AuditMixin):
    """Thương hiệu / bộ phận đặt hàng."""
    __tablename__ = "tab_brand"
    code: Mapped[str] = mapped_column(String(25), unique=True)
    department: Mapped[str] = mapped_column(String(255), default="")
    manager_id: Mapped[int] = mapped_column(BigInteger, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    manager = relationship(
        "Employee",
        primaryjoin="foreign(Brand.manager_id) == Employee.id",
        uselist=False,
        viewonly=True
    )

    @property
    def manager_name(self) -> str | None:
        return self.manager.full_name if self.manager else None
