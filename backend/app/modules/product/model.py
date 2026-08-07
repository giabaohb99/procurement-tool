from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, AuditMixin


class Product(Base, AuditMixin):
    """Hàng hóa / Nguyên liệu / VTBB."""

    __tablename__ = "tab_product"

    code: Mapped[str] = mapped_column(String(50), unique=True)        # Mã VTBB/NL
    name: Mapped[str] = mapped_column(String(255))                   # Tên VTBB/NL
    invoice_name: Mapped[str] = mapped_column(String(255), default="")  # tên trên hóa đơn
    legal_name: Mapped[str] = mapped_column(String(255), default="")    # tên pháp lý HH (col45)
    item_group: Mapped[str] = mapped_column(String(50), default="")     # Phân loại (Thùng, Nhãn...)
    unit: Mapped[str] = mapped_column(String(25), default="")           # ĐVT
    hh_code: Mapped[str] = mapped_column(String(50), default="", index=True)  # Mã HH (sản phẩm/hàng hóa) — liên kết
    hh_name: Mapped[str] = mapped_column(String(255), default="")       # Tên Sản phẩm (HH)
    # Thông số kỹ thuật — tự điền vào ô "Xuất xứ / TSKT / chất liệu" của dòng hàng ĐMH khi chọn SP.
    # Giới hạn 255 khớp POItem.spec để không bị cắt cụt khi copy sang đơn.
    specs: Mapped[str] = mapped_column(String(255), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
