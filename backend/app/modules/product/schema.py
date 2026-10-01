from datetime import datetime

from pydantic import BaseModel
from app.modules.employee.field_limits import Str25, Str50, Str255


class ProductBase(BaseModel):
    code: Str50
    name: Str255
    invoice_name: Str255 = ""
    legal_name: Str255 = ""
    item_group: Str50 = ""
    unit: Str25 = ""
    hh_code: Str50 = ""
    hh_name: Str255 = ""
    specs: Str255 = ""
    is_active: bool = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Str255 | None = None
    invoice_name: Str255 | None = None
    legal_name: Str255 | None = None
    item_group: Str50 | None = None
    unit: Str25 | None = None
    hh_code: Str50 | None = None
    hh_name: Str255 | None = None
    specs: Str255 | None = None
    is_active: bool | None = None


class ProductOut(ProductBase):
    id: int
    updated_at: datetime | None = None   # bao-CR-294 — cột "Ngày cập nhật" ở màn danh sách
    model_config = {"from_attributes": True}
