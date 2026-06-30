from sqlalchemy import BigInteger, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, AuditMixin


class PaymentRequest(Base, AuditMixin):
    """Phiếu yêu cầu thanh toán — CHỈ 1 NCC/phiếu, gom nhiều khoản nợ (nhiều PO). In được."""

    __tablename__ = "tab_payment_request"

    code: Mapped[str] = mapped_column(String(50), default="")          # YCTT00045
    supplier_code: Mapped[str] = mapped_column(String(50), default="", index=True)
    supplier_name: Mapped[str] = mapped_column(String(255), default="")
    company_id: Mapped[int] = mapped_column(BigInteger, default=0)
    source_type: Mapped[str] = mapped_column(String(20), default="goods")  # goods | shipping
    request_date: Mapped[str] = mapped_column(String(10), default="")
    total: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    note: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="draft")
    # draft | submitted | approved | paid


class PaymentRequestLine(Base, AuditMixin):
    __tablename__ = "tab_payment_request_line"

    request_id: Mapped[int] = mapped_column(BigInteger, index=True)
    payable_id: Mapped[int] = mapped_column(BigInteger, default=0)
    po_code: Mapped[str] = mapped_column(String(50), default="")
    invoice_no: Mapped[str] = mapped_column(String(50), default="")
    amount: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
