from sqlalchemy import BigInteger, Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, AuditMixin


class Company(Base, AuditMixin):
    """Pháp nhân nhận hóa đơn (có phân cấp qua `parent`)."""

    __tablename__ = "tab_company"

    code: Mapped[str] = mapped_column(String(25), unique=True)
    name: Mapped[str] = mapped_column(String(255))
    tax_code: Mapped[str] = mapped_column(String(25), default="")
    address: Mapped[str] = mapped_column(Text, default="")
    invoice_email: Mapped[str] = mapped_column(String(255), default="")
    parent: Mapped[int] = mapped_column(BigInteger, default=0)  # 0 = gốc
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
