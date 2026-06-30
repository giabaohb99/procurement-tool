from pydantic import BaseModel


class DeliveryIn(BaseModel):
    id: int | None = None
    delivery_no: int = 1
    warehouse_code: str = ""
    carrier_code: str = ""
    carrier_name: str = ""
    ship_qty: float = 0
    ship_unit: str = ""
    received_qty: float = 0
    promised_date: str = ""
    expected_date: str = ""
    received_date: str = ""
    invoice_no: str = ""
    shipping_unit_price: float = 0
    shipping_amount: float = 0
    qc_result: str = ""
    progress_note: str = ""


class POItemIn(BaseModel):
    id: int | None = None
    product_code: str = ""
    product_name: str = ""
    item_group: str = ""
    spec: str = ""
    unit: str = ""
    qty_request: float = 0
    qty_order: float = 0
    price: float = 0
    vat: float = 0
    warehouse_code: str = ""
    note: str = ""
    deliveries: list[DeliveryIn] = []


class POCreate(BaseModel):
    code: str | None = None
    misa_code: str = ""
    pr_code: str = ""
    survey_code: str = ""
    company_id: int = 0
    supplier_code: str = ""
    supplier_name: str = ""
    department: str = ""
    nspt: str = ""
    order_date: str = ""
    vat_rate: float = 0.08
    is_urgent: bool = False
    note: str = ""
    items: list[POItemIn] = []


class POUpdate(BaseModel):
    misa_code: str | None = None
    pr_code: str | None = None
    survey_code: str | None = None
    company_id: int | None = None
    supplier_code: str | None = None
    supplier_name: str | None = None
    department: str | None = None
    nspt: str | None = None
    order_date: str | None = None
    vat_rate: float | None = None
    is_urgent: bool | None = None
    note: str | None = None
    items: list[POItemIn] | None = None


class RejectIn(BaseModel):
    reason: str = ""
