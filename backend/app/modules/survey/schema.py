from app.modules.employee.field_limits import Str10, Str25, Str30, Str50, Str100, Str255, Str355, Str500, Str600
from pydantic import BaseModel, Field


class SupplierLineIn(BaseModel):
    contact_date: Str10 = ""
    reply_date: Str10 = ""
    result_date: Str10 = ""
    supplier_code: Str50 = ""
    supplier_name: Str255 = ""
    tax_code: Str25 = ""
    reg_address: str = ""
    warehouse_address: str = ""
    google_maps: Str500 = ""
    contact_person: Str100 = ""
    contact_phone: Str30 = ""
    supply_group: Str255 = ""
    quote_folder: Str500 = ""
    source_of_information: Str355 = ""
    production_tech: Str355 = ""
    production_time: Str100 = ""
    nvkd_eval: Str100 = ""
    invoice_policy: Str355 = ""
    reliability: Str355 = ""
    delivery_policy: Str355 = ""
    debt_policy: Str100 = ""
    defect_return: Str355 = ""
    nspt_note: str = Field(default="", max_length=5000)  # bao-CR-537: cột TEXT, chặn 422 thay vì 500
    nspt_reason: str = ""
    line_approve: Str255 = ""
    line_approve_note: str = ""
    note: str = ""


class ProductLineIn(BaseModel):
    contact_date: Str10 = ""
    reply_date: Str10 = ""
    result_date: Str10 = ""
    supplier_code: Str50 = ""
    internal_code: Str50 = ""
    product_name: Str255 = ""
    invoice_name: Str255 = ""          # Tên trên hoá đơn (CR-111)
    spec: str = ""
    active_ingredient: Str355 = ""     # Hàm lượng hoạt chất (CR-111)
    origin: Str100 = ""
    quote_unit: Str25 = ""
    moq: float = 0
    price_by_volume: float = 0
    volume_range: Str100 = ""
    # Hai mốc giá lấy từ Lịch sử mua hàng, FE điền sẵn và cho sửa đè (CR-111).
    last_purchase_price: float = 0
    max_purchase_price: float = 0
    # % VAT theo phương án, nhập tay từ CR-058 → chặn 0 ≤ VAT < 100 (cột DB Numeric(5,2)).
    vat: float = Field(0, ge=0, lt=100)
    request_qty: float = 0
    amount: float = 0
    internal_unit: Str25 = ""
    amount_converted: float = 0
    shipping_cost: float = 0
    extra_shipping_cost: float = 0  # Phí VC phát sinh đến kho yêu cầu (CR-111)
    shipping_policy: Str355 = ""       # Chính sách vận chuyển (CR-111)
    debt_policy: Str100 = ""           # Ngày công nợ (CR-111)
    delivery_time: Str100 = ""
    delivery_place: Str255 = ""
    quote_file: Str500 = ""
    sample_ready: bool = False
    sample_date: Str10 = ""
    sample_qty: float = 0
    lab_result: Str255 = ""
    lab_note: str = ""
    nspt_note: str = Field(default="", max_length=5000)  # bao-CR-537: cột TEXT, chặn 422 thay vì 500
    nspt_reason: str = ""
    line_approve: Str255 = ""
    line_approve_note: str = ""
    note: str = ""


class _SurveyHeader(BaseModel):
    pr_code: Str50 = ""
    survey_request_id: int = 0
    sr_code: Str50 = ""
    received_date: Str10 = ""
    result_due_date: Str10 = ""
    item_group: Str100 = ""
    main_content: Str600 = ""
    requirement_detail: str = ""
    request_qty: float = 0
    market_price: float = 0
    nspt: Str100 = ""
    has_product_code: bool = False
    item_code: Str50 = ""
    item_name: Str255 = ""
    uom: Str25 = ""
    proposed_rate: float = 0


class SupplierSurveyCreate(_SurveyHeader):
    code: Str50 | None = None
    lines: list[SupplierLineIn] = []


class ProductSurveyCreate(_SurveyHeader):
    code: Str50 | None = None
    lines: list[ProductLineIn] = []


class _HeaderUpdate(BaseModel):
    pr_code: Str50 | None = None
    survey_request_id: int | None = None
    sr_code: Str50 | None = None
    received_date: Str10 | None = None
    result_due_date: Str10 | None = None
    item_group: Str100 | None = None
    main_content: Str600 | None = None
    requirement_detail: str | None = None
    request_qty: float | None = None
    market_price: float | None = None
    nspt: Str100 | None = None
    has_product_code: bool | None = None
    item_code: Str50 | None = None
    item_name: Str255 | None = None
    uom: Str25 | None = None
    proposed_rate: float | None = None


class SupplierSurveyUpdate(_HeaderUpdate):
    lines: list[SupplierLineIn] | None = None


class ProductSurveyUpdate(_HeaderUpdate):
    lines: list[ProductLineIn] | None = None


class RejectIn(BaseModel):
    reason: str = ""


class LineApproveItem(BaseModel):
    id: int
    line_approve: Str255 | None = None
    line_approve_note: str | None = None


class LineApproveIn(BaseModel):
    lines: list[LineApproveItem] = []


# ===== Phiếu khảo sát GỘP (1 phiếu = 2 bảng: NCC + SP) =====
class SurveyCreate(_SurveyHeader):
    code: Str50 | None = None
    supplier_lines: list[SupplierLineIn] = []
    product_lines: list[ProductLineIn] = []


class SurveyUpdate(_HeaderUpdate):
    supplier_lines: list[SupplierLineIn] | None = None
    product_lines: list[ProductLineIn] | None = None


class LineApproveCombined(BaseModel):
    supplier_lines: list[LineApproveItem] = []
    product_lines: list[LineApproveItem] = []
