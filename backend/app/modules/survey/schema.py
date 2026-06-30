from pydantic import BaseModel


class SupplierLineIn(BaseModel):
    contact_date: str = ""
    reply_date: str = ""
    result_date: str = ""
    supplier_code: str = ""
    supplier_name: str = ""
    tax_code: str = ""
    reg_address: str = ""
    warehouse_address: str = ""
    google_maps: str = ""
    contact_person: str = ""
    contact_phone: str = ""
    supply_group: str = ""
    quote_folder: str = ""
    production_tech: str = ""
    production_time: str = ""
    nvkd_eval: str = ""
    invoice_policy: str = ""
    reliability: str = ""
    delivery_policy: str = ""
    debt_policy: str = ""
    defect_return: str = ""
    nspt_note: str = ""
    nspt_reason: str = ""
    line_approve: str = ""
    line_approve_note: str = ""


class ProductLineIn(BaseModel):
    supplier_code: str = ""
    internal_code: str = ""
    product_name: str = ""
    spec: str = ""
    origin: str = ""
    quote_unit: str = ""
    moq: float = 0
    price_by_volume: float = 0
    volume_range: str = ""
    vat: float = 0
    request_qty: float = 0
    internal_unit: str = ""
    amount_converted: float = 0
    shipping_cost: float = 0
    delivery_time: str = ""
    delivery_place: str = ""
    quote_file: str = ""
    sample_ready: bool = False
    sample_date: str = ""
    sample_qty: float = 0
    lab_result: str = ""
    lab_note: str = ""
    nspt_note: str = ""
    nspt_reason: str = ""
    line_approve: str = ""
    line_approve_note: str = ""


class _SurveyHeader(BaseModel):
    pr_code: str = ""
    received_date: str = ""
    result_due_date: str = ""
    item_group: str = ""
    requirement_detail: str = ""
    request_qty: float = 0
    market_price: float = 0
    nspt: str = ""


class SupplierSurveyCreate(_SurveyHeader):
    code: str | None = None
    lines: list[SupplierLineIn] = []


class ProductSurveyCreate(_SurveyHeader):
    code: str | None = None
    lines: list[ProductLineIn] = []


class SupplierSurveyUpdate(BaseModel):
    pr_code: str | None = None
    received_date: str | None = None
    result_due_date: str | None = None
    item_group: str | None = None
    requirement_detail: str | None = None
    request_qty: float | None = None
    market_price: float | None = None
    nspt: str | None = None
    lines: list[SupplierLineIn] | None = None


class ProductSurveyUpdate(BaseModel):
    pr_code: str | None = None
    received_date: str | None = None
    result_due_date: str | None = None
    item_group: str | None = None
    requirement_detail: str | None = None
    request_qty: float | None = None
    market_price: float | None = None
    nspt: str | None = None
    lines: list[ProductLineIn] | None = None


class RejectIn(BaseModel):
    reason: str = ""
