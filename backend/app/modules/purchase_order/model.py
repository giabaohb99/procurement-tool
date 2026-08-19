from sqlalchemy import BigInteger, Boolean, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, AuditMixin


class PurchaseOrder(Base, AuditMixin):
    """Đơn mua hàng (PO) — header. Là module trung tâm của vòng đời mua hàng."""

    __tablename__ = "tab_purchase_order"
    # created_by nằm ở AuditMixin — index qua __table_args__ (apply_scope lọc theo cột này ở MỌI list)
    __table_args__ = (Index("ix_po_created_by", "created_by"),)

    code: Mapped[str] = mapped_column(String(50), unique=True, default="")     # PO00045
    misa_code: Mapped[str] = mapped_column(String(50), default="")
    pr_code: Mapped[str] = mapped_column(String(50), default="", index=True)   # nguồn PYC — cross-ref nóng (sync/tiến độ/list theo PYC)
    survey_code: Mapped[str] = mapped_column(String(50), default="")
    company_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True) # pháp nhân nhận HĐ — apply_scope lọc theo cột này
    supplier_code: Mapped[str] = mapped_column(String(50), default="")         # NCC bán hàng
    supplier_name: Mapped[str] = mapped_column(String(255), default="")
    # CR-086: phòng ban neo bằng ID (xem PurchaseRequest.department_id). Cột `department` bên dưới
    # hạ xuống làm BẢN CHỤP TÊN — chỉ để in/đối chiếu, không khớp nghiệp vụ bằng nó nữa.
    department_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    department: Mapped[str] = mapped_column(String(255), default="", index=True)  # BẢN CHỤP tên (sẽ xóa — N-008)
    # CR-087: NSPT phụ trách neo bằng ID nhân sự. `full_name` KHÔNG duy nhất — khớp bằng tên
    # là cho người trùng tên thấy đơn của nhau (prod đang có 1 cặp). Cột `nspt` hạ xuống làm
    # BẢN CHỤP TÊN để in/xuất Excel (sẽ xóa — N-008).
    nspt_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    nspt: Mapped[str] = mapped_column(String(100), default="")
    order_date: Mapped[str] = mapped_column(String(10), default="", index=True)
    vat_rate: Mapped[float] = mapped_column(Numeric(5, 4), default=0.08)
    payment_terms: Mapped[str] = mapped_column(String(255), default="")    # hình thức TT cho NCC (col46)
    is_urgent: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(30), default="draft")
    # draft | submitted | approved | partial | received | cancelled
    # Trạng thái hồ sơ chứng từ — người dùng cập nhật TAY (Task 10b):
    #   "chưa có chứng từ" · "đã có thông tin chứng từ" · "đã đủ chứng từ"
    document_status: Mapped[str] = mapped_column(String(30), default="chưa có chứng từ", index=True)
    note: Mapped[str] = mapped_column(Text, default="")
    approve_note: Mapped[str] = mapped_column(Text, default="")


class POItem(Base, AuditMixin):
    """Dòng hàng của PO."""

    __tablename__ = "tab_po_item"

    po_id: Mapped[int] = mapped_column(BigInteger, index=True)
    product_code: Mapped[str] = mapped_column(String(50), default="")
    product_name: Mapped[str] = mapped_column(String(255), default="")
    invoice_name: Mapped[str] = mapped_column(String(255), default="")      # tên trên hóa đơn (col15/43)
    item_group: Mapped[str] = mapped_column(String(100), default="")
    spec: Mapped[str] = mapped_column(String(255), default="")              # xuất xứ/TSKT/chất liệu
    fg_code: Mapped[str] = mapped_column(String(50), default="")           # Mã HH / thành phẩm (col42)
    fg_name: Mapped[str] = mapped_column(String(255), default="")          # Tên HH / thành phẩm (theo master SP)
    invoice_no: Mapped[str] = mapped_column(String(50), default="")        # Số hóa đơn (theo sản phẩm, col31)
    invoice_date: Mapped[str] = mapped_column(String(10), default="")       # Ngày hóa đơn — tự set = hôm nay khi nhập số hóa đơn, sửa tay được
    document_delivery_date: Mapped[str] = mapped_column(String(10), default="")  # Ngày giao chứng từ cho KT (Task 8)
    supplier_ready: Mapped[bool] = mapped_column(Boolean, default=False)    # NCC có sẵn hàng (col17)
    required_date: Mapped[str] = mapped_column(String(10), default="")      # ngày yêu cầu có hàng (col3)
    expected_date: Mapped[str] = mapped_column(String(10), default="")      # dự kiến có hàng — copy xuống từ dòng YCMH, sửa tay được
    unit: Mapped[str] = mapped_column(String(25), default="")
    qty_request: Mapped[float] = mapped_column(Numeric(18, 3), default=0)
    qty_order: Mapped[float] = mapped_column(Numeric(18, 3), default=0)
    price: Mapped[float] = mapped_column(Numeric(18, 4), default=0)        # ĐƠN GIÁ giữ 4 số lẻ (giá quy đổi hay lẻ tới phần nghìn đồng)
    vat: Mapped[float] = mapped_column(Numeric(5, 2), default=0)            # % VAT của dòng
    amount: Mapped[float] = mapped_column(Numeric(18, 2), default=0)        # qty_order*price*(1+vat%)
    qty_received: Mapped[float] = mapped_column(Numeric(18, 3), default=0)  # auto = Σ giao đã nhận
    qty_remaining: Mapped[float] = mapped_column(Numeric(18, 3), default=0)
    line_status: Mapped[str] = mapped_column(String(30), default="")        # Chưa giao/Đang giao/Đủ
    warehouse_code: Mapped[str] = mapped_column(String(50), default="")     # kho mặc định cho dòng
    note: Mapped[str] = mapped_column(String(255), default="")
    progress_status: Mapped[str] = mapped_column(String(40), default="Chưa đặt hàng", index=True)  # cột P — máy trạng thái tiến độ (lọc ở màn Tiến độ mua hàng)
    pay_confirm_date: Mapped[str] = mapped_column(String(10), default="")   # AU — Ngày KT xác nhận thanh toán
    pause_reason: Mapped[str] = mapped_column(String(500), default="")      # AV — Lý do hủy/tạm ngưng
    status_before_pause: Mapped[str] = mapped_column(String(40), default="")  # AW — trạng thái trước khi tạm ngưng


class PODelivery(Base, AuditMixin):
    """Một lần giao của 1 dòng hàng (1 sản phẩm có thể giao nhiều lần)."""

    __tablename__ = "tab_po_delivery"

    po_id: Mapped[int] = mapped_column(BigInteger, index=True)
    po_item_id: Mapped[int] = mapped_column(BigInteger, index=True)
    delivery_no: Mapped[int] = mapped_column(BigInteger, default=1)
    warehouse_code: Mapped[str] = mapped_column(String(50), default="")
    carrier_code: Mapped[str] = mapped_column(String(50), default="")       # đơn vị vận chuyển
    carrier_name: Mapped[str] = mapped_column(String(255), default="")
    ship_qty: Mapped[float] = mapped_column(Numeric(18, 3), default=0)
    ship_unit: Mapped[str] = mapped_column(String(25), default="")
    received_qty: Mapped[float] = mapped_column(Numeric(18, 3), default=0)
    promised_date: Mapped[str] = mapped_column(String(10), default="")      # NCC cam kết giao
    expected_date: Mapped[str] = mapped_column(String(10), default="")      # BỎ DÙNG — không nơi nào ghi; "dự kiến có hàng" nay ở POItem.expected_date. Giữ cột theo luật "CSDL cũ: chỉ thêm, không sửa"
    received_date: Mapped[str] = mapped_column(String(10), default="", index=True)  # ngày nhận thực tế
    std_days: Mapped[int] = mapped_column(BigInteger, default=0)            # số ngày quy định (AH)
    regulated_date: Mapped[str] = mapped_column(String(10), default="")     # ngày quy định (AI)
    diff_promise: Mapped[int] = mapped_column(BigInteger, default=0)        # CL cam kết−nhận (AL) <0=trễ
    diff_regulated: Mapped[int] = mapped_column(BigInteger, default=0)      # CL quy định−nhận (AM)
    diff_required: Mapped[int] = mapped_column(BigInteger, default=0)       # CL quy định−KD yêu cầu (AN)
    invoice_no: Mapped[str] = mapped_column(String(50), default="")
    invoice_date: Mapped[str] = mapped_column(String(10), default="")
    shipping_unit_price: Mapped[float] = mapped_column(Numeric(18, 4), default=0)   # đơn giá vận chuyển — cũng cho 4 số lẻ
    shipping_amount: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    qc_result: Mapped[str] = mapped_column(String(20), default="")          # Đạt | Thiếu | Lỗi
    status: Mapped[str] = mapped_column(String(30), default="")            # trạng thái giao (P)
    extra_request: Mapped[str] = mapped_column(Text, default="")           # yêu cầu khác (AC)
    progress_note: Mapped[str] = mapped_column(Text, default="")           # chi tiết tiến độ (AG)
