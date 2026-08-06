from sqlalchemy import BigInteger, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, AuditMixin


class PurchaseHistory(Base, AuditMixin):
    """Lịch sử mua hàng — SNAPSHOT 1 dòng hàng của ĐMH tại thời điểm dòng đó "Hoàn thành".

    1 record = 1 dòng hàng (line item). ĐMH có 2 dòng → 2 record.
    Phục vụ 2 màn: chi tiết Sản phẩm (lọc `product_code`) và chi tiết NCC (lọc `supplier_code`).

    BẤT BIẾN: ghi 1 lần, không sửa/xóa. An toàn vì dòng đã "Hoàn thành" là điểm cuối và bị
    khóa sửa (purchase_order/service.py) — `auto_advance_line` bỏ qua dòng đã ở điểm cuối nên
    hook ghi chỉ chạy đúng 1 lần cho mỗi dòng. `po_item_id` unique là lớp bảo hiểm.

    Cột PHẲNG = thứ được lọc/sắp xếp/hiển thị trên bảng. Phần "thông tin chung" còn lại chỉ để
    tham khảo → gói vào `extra` (chuỗi JSON, theo quy ước repo: import_tool/report dùng Text).
    """

    __tablename__ = "tab_purchase_history"
    __table_args__ = (
        Index("ix_ph_product_date", "product_code", "order_date"),
        Index("ix_ph_supplier_date", "supplier_code", "order_date"),
    )

    # ── Khóa & truy vấn ────────────────────────────────────────────────
    po_item_id: Mapped[int] = mapped_column(BigInteger, unique=True)          # chống ghi trùng
    po_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    po_code: Mapped[str] = mapped_column(String(50), default="")
    # 2 cột dưới KHÔNG cần index đơn — composite ix_ph_*_date đã phủ (leftmost prefix)
    product_code: Mapped[str] = mapped_column(String(50), default="")   # nối màn Sản phẩm
    supplier_code: Mapped[str] = mapped_column(String(50), default="")  # nối màn NCC
    order_date: Mapped[str] = mapped_column(String(10), default="", index=True)     # sort mặc định (desc)
    company_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)

    # ── Hiển thị trên bảng (denormalize theo đúng tinh thần snapshot) ──
    product_name: Mapped[str] = mapped_column(String(255), default="")
    supplier_name: Mapped[str] = mapped_column(String(255), default="")
    company_name: Mapped[str] = mapped_column(String(255), default="")
    unit: Mapped[str] = mapped_column(String(25), default="")
    qty_order: Mapped[float] = mapped_column(Numeric(18, 3), default=0)
    price: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    vat: Mapped[float] = mapped_column(Numeric(5, 2), default=0)              # % VAT của dòng
    amount: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    completed_at: Mapped[str] = mapped_column(String(10), default="")         # ngày dòng vào "Hoàn thành"

    # ── Phần còn lại của "Thông tin chung" + dòng hàng (JSON, không lọc/sort) ──
    # {pr_code, misa_code, nspt, payment_terms, is_urgent, po_note, department,
    #  item_group, spec, invoice_name, fg_code, fg_name, qty_received,
    #  required_date, invoice_no, invoice_date, warehouse_code, item_note}
    extra: Mapped[str] = mapped_column(Text, default="")
