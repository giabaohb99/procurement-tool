from sqlalchemy import BigInteger, Boolean, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, AuditMixin


class Survey(Base, AuditMixin):
    """Phiếu khảo sát (header) — dùng chung NCC & SP (survey_type)."""
    __tablename__ = "tab_survey"

    code: Mapped[str] = mapped_column(String(50), unique=True, default="")
    survey_type: Mapped[str] = mapped_column(String(10))           # supplier | product
    pr_code: Mapped[str] = mapped_column(String(50), default="")    # mã PYC liên kết (cũ, giữ tương thích)
    survey_request_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)  # YCKS liên kết
    sr_code: Mapped[str] = mapped_column(String(50), default="")    # mã YCKS liên kết
    received_date: Mapped[str] = mapped_column(String(10), default="")
    result_due_date: Mapped[str] = mapped_column(String(10), default="")
    item_group: Mapped[str] = mapped_column(String(100), default="")       # Phân loại (item_class)
    main_content: Mapped[str] = mapped_column(String(500), default="")     # Nội dung chính (clone từ Mục đích của YCKS)
    requirement_detail: Mapped[str] = mapped_column(Text, default="")      # Yêu cầu kỹ thuật & chất lượng
    request_qty: Mapped[float] = mapped_column(Numeric(18, 3), default=0)   # SL dự kiến mua
    market_price: Mapped[float] = mapped_column(Numeric(18, 2), default=0)  # (deprecated — không dùng nữa)
    nspt: Mapped[str] = mapped_column(String(100), default="")             # NSPT phụ trách = người tạo
    # Thông tin sản phẩm (khi đã có mã trong hệ thống)
    has_product_code: Mapped[bool] = mapped_column(Boolean, default=False)
    item_code: Mapped[str] = mapped_column(String(50), default="")          # Mã VTBB/VL nội bộ
    item_name: Mapped[str] = mapped_column(String(255), default="")         # Tên VTBB (tự điền theo mã)
    uom: Mapped[str] = mapped_column(String(25), default="")               # ĐVT
    proposed_rate: Mapped[float] = mapped_column(Numeric(18, 4), default=0)  # Giá đề xuất — đơn giá giữ 4 số lẻ
    approve_status: Mapped[str] = mapped_column(String(20), default="")   # Duyệt|Không duyệt
    approve_note: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(30), default="draft")
    import_key: Mapped[str] = mapped_column(String(160), default="", index=True)  # khoá idempotent khi import (phân loại::NCC)


class SurveySupplierLine(Base, AuditMixin):
    """Dòng NCC (Sheet 3)."""
    __tablename__ = "tab_survey_supplier_line"

    survey_id: Mapped[int] = mapped_column(BigInteger, index=True)
    contact_date: Mapped[str] = mapped_column(String(10), default="")
    reply_date: Mapped[str] = mapped_column(String(10), default="")
    result_date: Mapped[str] = mapped_column(String(10), default="")
    supplier_code: Mapped[str] = mapped_column(String(50), default="")
    supplier_name: Mapped[str] = mapped_column(String(255), default="")
    tax_code: Mapped[str] = mapped_column(String(25), default="")
    reg_address: Mapped[str] = mapped_column(Text, default="")
    warehouse_address: Mapped[str] = mapped_column(Text, default="")
    google_maps: Mapped[str] = mapped_column(String(500), default="")
    contact_person: Mapped[str] = mapped_column(String(100), default="")
    contact_phone: Mapped[str] = mapped_column(String(30), default="")
    supply_group: Mapped[str] = mapped_column(String(255), default="")
    quote_folder: Mapped[str] = mapped_column(String(500), default="")
    source_of_information: Mapped[str] = mapped_column(String(255), default="")  # Nguồn thông tin đầu vào
    production_tech: Mapped[str] = mapped_column(String(255), default="")
    production_time: Mapped[str] = mapped_column(String(100), default="")
    nvkd_eval: Mapped[str] = mapped_column(String(100), default="")
    invoice_policy: Mapped[str] = mapped_column(String(255), default="")
    reliability: Mapped[str] = mapped_column(String(255), default="")
    delivery_policy: Mapped[str] = mapped_column(String(255), default="")
    debt_policy: Mapped[str] = mapped_column(String(50), default="")
    defect_return: Mapped[str] = mapped_column(String(255), default="")
    nspt_note: Mapped[str] = mapped_column(String(255), default="")
    nspt_reason: Mapped[str] = mapped_column(Text, default="")
    line_approve: Mapped[str] = mapped_column(String(255), default="")
    line_approve_note: Mapped[str] = mapped_column(Text, default="")
    note: Mapped[str] = mapped_column(Text, default="")                     # Ghi chú nội bộ (KHÔNG show ra Yêu cầu khảo sát)
    import_line_key: Mapped[str] = mapped_column(String(200), default="", index=True)  # khoá idempotent khi import (Mã yêu cầu + MST)


class SurveyProductLine(Base, AuditMixin):
    """Dòng SP (Sheet 4)."""
    __tablename__ = "tab_survey_product_line"

    survey_id: Mapped[int] = mapped_column(BigInteger, index=True)
    contact_date: Mapped[str] = mapped_column(String(10), default="")       # Ngày liên hệ
    reply_date: Mapped[str] = mapped_column(String(10), default="")         # Ngày dự kiến phản hồi
    result_date: Mapped[str] = mapped_column(String(10), default="")        # Ngày dự kiến trả KQ
    supplier_code: Mapped[str] = mapped_column(String(50), default="")
    internal_code: Mapped[str] = mapped_column(String(50), default="")      # Mã SP theo NCC (nhập tay khi khảo sát)
    product_name: Mapped[str] = mapped_column(String(255), default="")
    spec: Mapped[str] = mapped_column(Text, default="")
    origin: Mapped[str] = mapped_column(String(100), default="")
    quote_unit: Mapped[str] = mapped_column(String(25), default="")
    moq: Mapped[float] = mapped_column(Numeric(18, 3), default=0)
    price_by_volume: Mapped[float] = mapped_column(Numeric(18, 4), default=0)   # đơn giá theo sản lượng — 4 số lẻ
    volume_range: Mapped[str] = mapped_column(String(100), default="")
    vat: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    request_qty: Mapped[float] = mapped_column(Numeric(18, 3), default=0)
    amount: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    internal_unit: Mapped[str] = mapped_column(String(25), default="")
    amount_converted: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    shipping_cost: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    delivery_time: Mapped[str] = mapped_column(String(100), default="")
    delivery_place: Mapped[str] = mapped_column(String(255), default="")
    quote_file: Mapped[str] = mapped_column(String(500), default="")
    sample_ready: Mapped[bool] = mapped_column(Boolean, default=False)
    sample_date: Mapped[str] = mapped_column(String(10), default="")
    sample_qty: Mapped[float] = mapped_column(Numeric(18, 3), default=0)
    lab_result: Mapped[str] = mapped_column(String(255), default="")
    lab_note: Mapped[str] = mapped_column(Text, default="")
    nspt_note: Mapped[str] = mapped_column(String(255), default="")
    nspt_reason: Mapped[str] = mapped_column(Text, default="")
    line_approve: Mapped[str] = mapped_column(String(255), default="")
    line_approve_note: Mapped[str] = mapped_column(Text, default="")
    note: Mapped[str] = mapped_column(Text, default="")                     # Ghi chú nội bộ (KHÔNG show ra Yêu cầu khảo sát)
    import_line_key: Mapped[str] = mapped_column(String(200), default="", index=True)  # khoá idempotent khi import (Mã yêu cầu + MST)
