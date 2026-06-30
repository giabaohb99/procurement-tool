from pydantic import BaseModel


class ProductBase(BaseModel):
    code: str
    name: str
    invoice_name: str = ""
    item_group: str = ""
    unit: str = ""
    is_active: bool = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: str | None = None
    invoice_name: str | None = None
    item_group: str | None = None
    unit: str | None = None
    is_active: bool | None = None


class ProductOut(ProductBase):
    id: int
    model_config = {"from_attributes": True}
