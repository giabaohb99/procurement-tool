from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, AuditMixin


class Product(Base, AuditMixin):
    """Hàng hóa / Nguyên liệu / VTBB."""

    __tablename__ = "tab_product"

    code: Mapped[str] = mapped_column(String(50), unique=True)        # Mã VTBB/NL
    name: Mapped[str] = mapped_column(String(255))                   # Tên VTBB/NL
    invoice_name: Mapped[str] = mapped_column(String(255), default="")  # tên trên hóa đơn
    item_group: Mapped[str] = mapped_column(String(50), default="")     # Phân loại (Thùng, Nhãn...)
    unit: Mapped[str] = mapped_column(String(25), default="")           # ĐVT
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
