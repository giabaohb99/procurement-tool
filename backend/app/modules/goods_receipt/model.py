from sqlalchemy import BigInteger, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, AuditMixin


class GoodsReceipt(Base, AuditMixin):
    """Phiếu nhập kho — SINH NGẦM khi nhận hàng trên dòng giao của PO (1 phiếu/lần giao)."""

    __tablename__ = "tab_goods_receipt"

    code: Mapped[str] = mapped_column(String(50), default="")
    po_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    po_code: Mapped[str] = mapped_column(String(50), default="")
    delivery_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True, unique=True)
    company_id: Mapped[int] = mapped_column(BigInteger, default=0)
    warehouse_code: Mapped[str] = mapped_column(String(50), default="")
    product_code: Mapped[str] = mapped_column(String(50), default="")
    product_name: Mapped[str] = mapped_column(String(255), default="")
    unit: Mapped[str] = mapped_column(String(25), default="")
    qty_received: Mapped[float] = mapped_column(Numeric(18, 3), default=0)
    received_date: Mapped[str] = mapped_column(String(10), default="")
    qc_result: Mapped[str] = mapped_column(String(20), default="")     # Đạt | Thiếu | Lỗi
    note: Mapped[str] = mapped_column(Text, default="")
