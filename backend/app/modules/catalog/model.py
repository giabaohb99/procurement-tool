from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

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
    std_days: Mapped[str] = mapped_column(String(20), default="")   # thời gian quy định (ngày)
    note: Mapped[str] = mapped_column(Text, default="")
    apply_date: Mapped[str] = mapped_column(String(20), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Brand(Base, AuditMixin):
    """Thương hiệu / bộ phận đặt hàng."""
    __tablename__ = "tab_brand"
    code: Mapped[str] = mapped_column(String(25), unique=True)
    department: Mapped[str] = mapped_column(String(255), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
