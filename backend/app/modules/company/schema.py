from pydantic import BaseModel


class CompanyBase(BaseModel):
    code: str = ""
    name: str
    tax_code: str = ""
    address: str = ""
    invoice_email: str = ""
    parent: int = 0
    is_active: bool = True


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: str | None = None
    tax_code: str | None = None
    address: str | None = None
    invoice_email: str | None = None
    parent: int | None = None
    is_active: bool | None = None


class CompanyOut(CompanyBase):
    id: int
    model_config = {"from_attributes": True}
