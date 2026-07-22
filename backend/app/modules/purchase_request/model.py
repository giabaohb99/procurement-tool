from sqlalchemy import BigInteger, Boolean, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, AuditMixin


class PurchaseRequest(Base, AuditMixin):
    """Yêu cầu mua (PYC) — header."""

    __tablename__ = "tab_purchase_request"
    # created_by nằm ở AuditMixin — index qua __table_args__ (apply_scope lọc theo cột này ở MỌI list)
    __table_args__ = (Index("ix_pr_created_by", "created_by"),)

    code: Mapped[str] = mapped_column(String(50), unique=True, default="")
    company_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)  # pháp nhân nhận hóa đơn — apply_scope lọc theo cột này
    requester: Mapped[str] = mapped_column(String(255), default="")        # người yêu cầu
    requester_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)   # id nhân sự người yêu cầu (để so scope)
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

    # Soft delete
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)


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
    price: Mapped[float] = mapped_column(Numeric(18, 2), default=0)        # giá đề xuất (chưa VAT)
    vat_pct: Mapped[float] = mapped_column(Numeric(5, 2), default=0)       # % VAT theo dòng (Task 4)
    amount: Mapped[float] = mapped_column(Numeric(18, 2), default=0)       # thành tiền = qty*price*(1+vat_pct%)
    warehouse: Mapped[str] = mapped_column(String(100), default="")        # kho nhận
    required_date: Mapped[str] = mapped_column(String(10), default="")     # ngày cần hàng (theo dòng)
    expected_date: Mapped[str] = mapped_column(String(10), default="")     # thời gian dự kiến có hàng (NSTM cập nhật; đổi giá trị đã có phải kèm lý do)
    assignee: Mapped[str] = mapped_column(String(100), default="", index=True)  # NSTM phụ trách (mã NV) — scope "được giao" lọc theo cột này
    line_status: Mapped[str] = mapped_column(String(30), default="Chưa đặt hàng")  # trạng thái xử lý dòng
    qty_ordered: Mapped[float] = mapped_column(Numeric(18, 3), default=0)   # tổng SL đã đặt (đồng bộ từ ĐMH liên kết)
    qty_received: Mapped[float] = mapped_column(Numeric(18, 3), default=0)  # tổng SL đã nhận (đồng bộ từ ĐMH liên kết)
    progress_note: Mapped[str] = mapped_column(Text, default="")           # chi tiết tiến độ
    note: Mapped[str] = mapped_column(String(255), default="")
