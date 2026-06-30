from sqlalchemy import Boolean, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, AuditMixin


class Supplier(Base, AuditMixin):
    """Nhà cung cấp. supplier_type: goods = NCC bán hàng, transport = đơn vị vận chuyển."""

    __tablename__ = "tab_supplier"

    code: Mapped[str] = mapped_column(String(50), unique=True)        # tên viết tắt
    name: Mapped[str] = mapped_column(String(255))                   # tên pháp lý
    tax_code: Mapped[str] = mapped_column(String(25), default="")
    address: Mapped[str] = mapped_column(Text, default="")
    supplier_type: Mapped[str] = mapped_column(String(20), default="goods")
    payment_terms: Mapped[str] = mapped_column(String(255), default="")  # hình thức thanh toán
    vat: Mapped[float] = mapped_column(Float, default=0.08)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
