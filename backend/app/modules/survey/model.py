from sqlalchemy import BigInteger, Boolean, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, AuditMixin


class Survey(Base, AuditMixin):
    """Phiếu khảo sát (header) — dùng chung NCC & SP (survey_type)."""
    __tablename__ = "tab_survey"

    code: Mapped[str] = mapped_column(String(50), unique=True, default="")
    survey_type: Mapped[str] = mapped_column(String(10))           # supplier | product
    pr_code: Mapped[str] = mapped_column(String(50), default="")    # mã PYC liên kết
    received_date: Mapped[str] = mapped_column(String(10), default="")
    result_due_date: Mapped[str] = mapped_column(String(10), default="")
    item_group: Mapped[str] = mapped_column(String(100), default="")
    requirement_detail: Mapped[str] = mapped_column(Text, default="")
    request_qty: Mapped[float] = mapped_column(Numeric(18, 3), default=0)
    market_price: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    nspt: Mapped[str] = mapped_column(String(100), default="")
    approve_status: Mapped[str] = mapped_column(String(20), default="")   # Duyệt|Không duyệt
    approve_note: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(30), default="draft")


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
    production_tech: Mapped[str] = mapped_column(String(255), default="")
    production_time: Mapped[str] = mapped_column(String(100), default="")
    nvkd_eval: Mapped[str] = mapped_column(String(100), default="")
    invoice_policy: Mapped[str] = mapped_column(String(255), default="")
    reliability: Mapped[str] = mapped_column(String(20), default="")
    delivery_policy: Mapped[str] = mapped_column(String(255), default="")
    debt_policy: Mapped[str] = mapped_column(String(50), default="")
    defect_return: Mapped[str] = mapped_column(String(255), default="")
    nspt_note: Mapped[str] = mapped_column(String(20), default="")
    nspt_reason: Mapped[str] = mapped_column(Text, default="")
    line_approve: Mapped[str] = mapped_column(String(20), default="")
    line_approve_note: Mapped[str] = mapped_column(Text, default="")


class SurveyProductLine(Base, AuditMixin):
    """Dòng SP (Sheet 4)."""
    __tablename__ = "tab_survey_product_line"

    survey_id: Mapped[int] = mapped_column(BigInteger, index=True)
    supplier_code: Mapped[str] = mapped_column(String(50), default="")
    internal_code: Mapped[str] = mapped_column(String(50), default="")
    product_name: Mapped[str] = mapped_column(String(255), default="")
    spec: Mapped[str] = mapped_column(Text, default="")
    origin: Mapped[str] = mapped_column(String(100), default="")
    quote_unit: Mapped[str] = mapped_column(String(25), default="")
    moq: Mapped[float] = mapped_column(Numeric(18, 3), default=0)
    price_by_volume: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
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
    lab_result: Mapped[str] = mapped_column(String(20), default="")
    lab_note: Mapped[str] = mapped_column(Text, default="")
    nspt_note: Mapped[str] = mapped_column(String(20), default="")
    nspt_reason: Mapped[str] = mapped_column(Text, default="")
    line_approve: Mapped[str] = mapped_column(String(20), default="")
    line_approve_note: Mapped[str] = mapped_column(Text, default="")
