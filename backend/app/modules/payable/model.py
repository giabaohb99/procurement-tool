from sqlalchemy import BigInteger, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, AuditMixin


class Payable(Base, AuditMixin):
    """Khoản công nợ phải trả — SINH NGẦM khi nhận hàng. 1 dòng = 1 lần giao × 1 luồng.

    source_type: goods = nợ NCC bán hàng ; shipping = nợ đơn vị vận chuyển.
    """

    __tablename__ = "tab_payable"

    company_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    supplier_code: Mapped[str] = mapped_column(String(50), default="", index=True)
    supplier_name: Mapped[str] = mapped_column(String(255), default="")
    source_type: Mapped[str] = mapped_column(String(20), default="goods", index=True)
    ref_type: Mapped[str] = mapped_column(String(20), default="delivery")
    ref_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    po_id: Mapped[int] = mapped_column(BigInteger, default=0)
    po_code: Mapped[str] = mapped_column(String(50), default="", index=True)
    invoice_no: Mapped[str] = mapped_column(String(50), default="")
    incur_date: Mapped[str] = mapped_column(String(10), default="")    # ngày phát sinh (= ngày nhận)
    due_date: Mapped[str] = mapped_column(String(10), default="")      # hạn trả
    amount: Mapped[float] = mapped_column(Numeric(18, 2), default=0)   # trước VAT
    vat: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    total: Mapped[float] = mapped_column(Numeric(18, 2), default=0)    # phải trả = amount + vat
    paid_amount: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    status: Mapped[str] = mapped_column(String(20), default="Chờ TT")  # Chờ TT | Trả một phần | Đã TT
