from pydantic import BaseModel


class SupplierBase(BaseModel):
    code: str
    name: str
    tax_code: str = ""
    address: str = ""
    supplier_type: str = "goods"  # goods | transport
    payment_terms: str = ""
    vat: float = 0.08
    is_active: bool = True


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(BaseModel):
    name: str | None = None
    tax_code: str | None = None
    address: str | None = None
    supplier_type: str | None = None
    payment_terms: str | None = None
    vat: float | None = None
    is_active: bool | None = None


class SupplierOut(SupplierBase):
    id: int
    model_config = {"from_attributes": True}
