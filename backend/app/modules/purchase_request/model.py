from sqlalchemy import BigInteger, Boolean, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, AuditMixin


class PurchaseRequest(Base, AuditMixin):
    """Yêu cầu mua (PYC) — header."""

    __tablename__ = "tab_purchase_request"

    code: Mapped[str] = mapped_column(String(50), unique=True, default="")
    company_id: Mapped[int] = mapped_column(BigInteger, default=0)        # pháp nhân nhận hóa đơn
    requester: Mapped[str] = mapped_column(String(255), default="")        # người yêu cầu
    requester_position: Mapped[str] = mapped_column(String(100), default="")  # chức vụ
    department: Mapped[str] = mapped_column(String(255), default="")       # phòng ban/thương hiệu
    head_of_dept: Mapped[str] = mapped_column(String(255), default="")     # trưởng bộ phận
    purpose: Mapped[str] = mapped_column(String(255), default="")          # mục đích mua hàng
    request_date: Mapped[str] = mapped_column(String(10), default="")      # ngày tạo (YYYY-MM-DD)
    need_date: Mapped[str] = mapped_column(String(10), default="")         # ngày cần hàng
    status: Mapped[str] = mapped_column(String(30), default="draft")       # draft|submitted|approved|rejected
    is_urgent: Mapped[bool] = mapped_column(Boolean, default=False)
    vat_rate: Mapped[float] = mapped_column(Numeric(5, 4), default=0.08)
    assignee_id: Mapped[int] = mapped_column(BigInteger, default=0)
    note: Mapped[str] = mapped_column(Text, default="")

    # New columns for suggested supplier and print options
    show_code_on_print: Mapped[bool] = mapped_column(Boolean, default=True)
    suggested_supplier: Mapped[str] = mapped_column(String(255), default="")
    suggested_supplier_tax_code: Mapped[str] = mapped_column(String(50), default="")
    suggested_supplier_contact: Mapped[str] = mapped_column(String(255), default="")
    quote_filename: Mapped[str] = mapped_column(String(255), default="")
    quote_file_url: Mapped[str] = mapped_column(String(1000), default="")


class PurchaseRequestItem(Base, AuditMixin):
    """Dòng hàng của yêu cầu mua (theo Sheet: giá đề xuất, kho, NSPT, trạng thái...)."""

    __tablename__ = "tab_purchase_request_item"

    pr_id: Mapped[int] = mapped_column(BigInteger, index=True)
    product_code: Mapped[str] = mapped_column(String(50), default="")
    product_name: Mapped[str] = mapped_column(String(255))
    item_group: Mapped[str] = mapped_column(String(100), default="")       # phân loại
    group_desc: Mapped[str] = mapped_column(String(255), default="")       # mô tả phân loại (vd thời gian SX)
    qty: Mapped[float] = mapped_column(Numeric(18, 3), default=0)
    unit: Mapped[str] = mapped_column(String(25), default="")
    price: Mapped[float] = mapped_column(Numeric(18, 2), default=0)        # giá đề xuất
    amount: Mapped[float] = mapped_column(Numeric(18, 2), default=0)       # thành tiền = qty*price
    warehouse: Mapped[str] = mapped_column(String(100), default="")        # kho nhận
    assignee: Mapped[str] = mapped_column(String(100), default="")         # NSPT
    line_status: Mapped[str] = mapped_column(String(30), default="")       # trạng thái xử lý dòng
    progress_note: Mapped[str] = mapped_column(Text, default="")           # chi tiết tiến độ
    note: Mapped[str] = mapped_column(String(255), default="")
