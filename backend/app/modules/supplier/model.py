from sqlalchemy import Boolean, Float, SmallInteger, String, Text
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
    bank_account_name: Mapped[str] = mapped_column(String(255), default="")  # tên TK thụ hưởng
    vat: Mapped[float] = mapped_column(Float, default=0.08)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    # bao-CR-321 — điều khoản in trên Đơn mua hàng, theo từng NCC. 0 / rỗng = chưa khai,
    # bản in lùi về mặc định (15 ngày · 07 ngày · "Chậm nhất 24h kể từ khi nhận hàng").
    # Chép xuống đơn lúc chọn NCC (như payment_terms), trên đơn sửa lại được cho từng đơn.
    inspection_days: Mapped[int] = mapped_column(SmallInteger, default=0)     # số ngày bên mua kiểm tra hàng
    return_days: Mapped[int] = mapped_column(SmallInteger, default=0)         # số ngày bên bán thu hồi / đổi trả
    invoice_deadline: Mapped[str] = mapped_column(String(255), default="")    # hạn xuất hóa đơn (chữ ngắn)
