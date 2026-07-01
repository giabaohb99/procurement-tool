from sqlalchemy import Boolean, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, AuditMixin


class Supplier(Base, AuditMixin):
    """Nhà cung cấp. supplier_type: goods = NCC bán hàng, transport = đơn vị vận chuyển."""

    __tablename__ = "tab_supplier"

    code: Mapped[str] = mapped_column(String(50), unique=True)        # tên viết tắt
    name: Mapped[str] = mapped_column(String(255))                   # tên pháp lý
    legal_type: Mapped[str] = mapped_column(String(30), default="")  # Công ty/Cá nhân/Hợp danh/Hộ kinh doanh
    tax_code: Mapped[str] = mapped_column(String(25), default="")
    address: Mapped[str] = mapped_column(Text, default="")
    supplier_type: Mapped[str] = mapped_column(String(20), default="goods")
    contact_person: Mapped[str] = mapped_column(String(100), default="")
    phone: Mapped[str] = mapped_column(String(30), default="")
    payment_terms: Mapped[str] = mapped_column(String(255), default="")  # hình thức thanh toán
    bank_account: Mapped[str] = mapped_column(String(50), default="")    # số TK
    bank_name: Mapped[str] = mapped_column(String(255), default="")      # ngân hàng
    vat: Mapped[float] = mapped_column(Float, default=0.08)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
