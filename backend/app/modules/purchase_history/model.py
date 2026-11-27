from sqlalchemy import BigInteger, Index, Numeric, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, AuditMixin


class PurchaseHistory(Base, AuditMixin):
    """Lịch sử mua hàng — mỗi dòng hàng của ĐMH một bản ghi, có từ lúc HÀNG VỀ KHO (bao-CR-790).

    1 record = 1 dòng hàng (line item). ĐMH có 2 dòng → 2 record.
    Phục vụ 2 màn: chi tiết Sản phẩm (lọc `product_code`) và chi tiết NCC (lọc `supplier_code`).

    HAI GIAI ĐOẠN (`line_stage`, cùng bộ mã `LedgerLineStage` của sổ giá):
    - ĐANG MỞ (1): dòng ĐMH đã nhận hàng (SL nhận > 0) nhưng chưa hoàn thành. Còn đồng bộ theo ĐMH — đổi giá / SL / VAT / NCC
      thì cập nhật đúng bản ghi; dòng hủy, SL nhận về 0, ĐMH bị hủy / bỏ duyệt / xóa thì bản ghi bị xóa
      (`purchase_history.service.sync_po_history`).
    - ĐÃ CHỐT (2): dòng vào `completed` (`snapshot_line`) hoặc dữ liệu cũ. BẤT BIẾN: không sửa / xóa nữa. An toàn vì dòng
      `completed` là điểm cuối và bị khóa sửa — `auto_advance_line` bỏ qua dòng đã ở điểm cuối. `po_item_id` unique là lớp
      bảo hiểm: một dòng ĐMH chỉ có MỘT bản ghi suốt đời (id giữ nguyên khi chuyển từ đang mở sang đã chốt).

    Ngoài ra bảng còn chứa DỮ LIỆU CŨ (`source='legacy'`) nhập từ file Excel lịch sử mua hàng
    của giai đoạn trước khi có hệ thống: không có ĐMH nên `po_item_id`/`po_code` rỗng.

    Cột PHẲNG = thứ được lọc/sắp xếp/hiển thị trên bảng. Phần "thông tin chung" còn lại chỉ để
    tham khảo → gói vào `extra` (chuỗi JSON, theo quy ước repo: import_tool/report dùng Text).
    """

    __tablename__ = "tab_purchase_history"
    __table_args__ = (
        Index("ix_ph_product_date", "product_code", "order_date"),
        Index("ix_ph_supplier_date", "supplier_code", "order_date"),
    )

    # ── Khóa & truy vấn ────────────────────────────────────────────────
    # NULL cho dòng DỮ LIỆU CŨ (nhập từ file Excel, không có ĐMH trong hệ thống).
    # MySQL cho phép nhiều NULL trong unique index nên vẫn giữ được lớp chống ghi trùng
    # cho dòng sinh từ luồng chạy thật.
    po_item_id: Mapped[int | None] = mapped_column(BigInteger, unique=True, nullable=True)
    # bao-CR-790: giai đoạn của bản ghi (bộ mã `LedgerLineStage`): 1 = đang mở (đã nhận hàng, còn đồng bộ theo ĐMH),
    # 2 = đã chốt (dòng hoàn thành hoặc dữ liệu cũ, bất biến). Dòng có từ trước migration `phstage790` đều là 2.
    line_stage: Mapped[int] = mapped_column(SmallInteger, default=2, server_default="2")
    # system = sinh từ dòng ĐMH của hệ thống (từ lúc nhận hàng) | legacy = nhập từ file lịch sử cũ
    source: Mapped[str] = mapped_column(String(10), default="system", index=True)
    # Khóa nguồn của dòng dữ liệu cũ (file + sheet + số dòng) — để truy ngược và chống nhập trùng.
    # NULL với dòng sinh từ hệ thống.
    legacy_key: Mapped[str | None] = mapped_column(String(190), unique=True, nullable=True)
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
    # ĐƠN GIÁ 4 số lẻ (migration c1f7b9d34e02) — khớp `tab_po_item.price`, nếu để 2 số lẻ
    # thì MySQL làm tròn ngay lúc chụp snapshot và mất số lẻ vĩnh viễn.
    price: Mapped[float] = mapped_column(Numeric(18, 4), default=0)
    vat: Mapped[float] = mapped_column(Numeric(5, 2), default=0)              # % VAT của dòng
    amount: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    completed_at: Mapped[str] = mapped_column(String(10), default="")         # ngày dòng vào `completed`; rỗng khi còn đang mở

    # ── Phần còn lại của "Thông tin chung" + dòng hàng (JSON, không lọc/sort) ──
    # {pr_code, misa_code, nspt, payment_terms, is_urgent, po_note, department,
    #  item_group, spec, invoice_name, fg_code, fg_name, qty_received,
    #  required_date, invoice_no, invoice_date, warehouse_code, item_note}
    extra: Mapped[str] = mapped_column(Text, default="")
