from datetime import datetime
from pydantic import BaseModel
from app.modules.employee.field_limits import Str20, Str25, Str100, Str255


# ---- Warehouse ----
class WarehouseCreate(BaseModel):
    code: Str25 = ""
    name: Str255
    address: str = ""
    is_active: bool = True


class WarehouseUpdate(BaseModel):
    name: Str255 | None = None
    address: str | None = None
    is_active: bool | None = None


class WarehouseOut(WarehouseCreate):
    id: int
    model_config = {"from_attributes": True}


# ---- Unit ----
class UnitCreate(BaseModel):
    code: Str25 = ""
    name: Str100
    is_active: bool = True


class UnitUpdate(BaseModel):
    name: Str100 | None = None
    is_active: bool | None = None


class UnitOut(UnitCreate):
    id: int
    model_config = {"from_attributes": True}


# ---- ItemGroup ----
class ItemGroupCreate(BaseModel):
    code: Str25 = ""
    name: Str100
    std_days: Str20 = ""
    std_days_unavail: Str20 = ""
    note: str = ""
    apply_date: Str20 = ""
    is_active: bool = True


class ItemGroupUpdate(BaseModel):
    std_days: Str20 | None = None
    std_days_unavail: Str20 | None = None
    note: str | None = None
    apply_date: Str20 | None = None
    is_active: bool | None = None


class ItemGroupOut(ItemGroupCreate):
    id: int
    model_config = {"from_attributes": True}


# ---- Brand ----
class BrandCreate(BaseModel):
    code: Str25 = ""
    department: Str255 = ""
    manager_id: int | None = 0
    is_active: bool = True


class BrandUpdate(BaseModel):
    department: Str255 | None = None
    manager_id: int | None = None
    is_active: bool | None = None


class BrandBase(BaseModel):
    department: Str255 | None = ""
    manager_id: int | None = 0
    is_active: bool | None = True


class BrandOut(BrandBase):
    id: int
    code: str
    manager_name: str | None = None
    created_at: datetime | None = None
    model_config = {"from_attributes": True}
