from sqlalchemy import Boolean, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, AuditMixin
from app.core.status_codes import SUPPLIER_LEGAL_TYPE


class Supplier(Base, AuditMixin):
    """Nhà cung cấp. supplier_type: goods = NCC bán hàng, transport = đơn vị vận chuyển."""

    __tablename__ = "tab_supplier"

    code: Mapped[str] = mapped_column(String(50), unique=True)        # tên viết tắt
    name: Mapped[str] = mapped_column(String(255))                   # tên pháp lý
    # B-03: MÃ tiếng Anh, bộ cố định `SUPPLIER_LEGAL_TYPE` ở `app/core/status_codes.py`.
    # Rỗng = chưa chọn (đa số dòng đang rỗng).
    legal_type: Mapped[str] = mapped_column(String(30), default="")
    tax_code: Mapped[str] = mapped_column(String(25), default="")
    address: Mapped[str] = mapped_column(Text, default="")
    supplier_type: Mapped[str] = mapped_column(String(20), default="goods")
    contact_person: Mapped[str] = mapped_column(String(100), default="")
    phone: Mapped[str] = mapped_column(String(30), default="")
    payment_terms: Mapped[str] = mapped_column(String(255), default="")  # hình thức thanh toán
    bank_account: Mapped[str] = mapped_column(String(50), default="")    # số TK
    bank_name: Mapped[str] = mapped_column(String(255), default="")      # ngân hàng
    bank_account_name: Mapped[str] = mapped_column(String(255), default="")  # tên TK thụ hưởng
    vat: Mapped[float] = mapped_column(Float, default=0.08)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    @property
    def legal_type_label(self) -> str:
        """Nhãn tiếng Việt của `legal_type` (B-03). Mã lạ / rỗng -> rỗng."""
        return SUPPLIER_LEGAL_TYPE.label_of(self.legal_type)
