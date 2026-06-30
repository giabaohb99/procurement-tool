from pydantic import BaseModel


# ---- Warehouse ----
class WarehouseCreate(BaseModel):
    code: str = ""
    name: str
    address: str = ""
    is_active: bool = True


class WarehouseUpdate(BaseModel):
    name: str | None = None
    address: str | None = None
    is_active: bool | None = None


class WarehouseOut(WarehouseCreate):
    id: int
    model_config = {"from_attributes": True}


# ---- Unit ----
class UnitCreate(BaseModel):
    code: str = ""
    name: str
    is_active: bool = True


class UnitUpdate(BaseModel):
    name: str | None = None
    is_active: bool | None = None


class UnitOut(UnitCreate):
    id: int
    model_config = {"from_attributes": True}


# ---- ItemGroup ----
class ItemGroupCreate(BaseModel):
    code: str = ""
    name: str
    std_days: str = ""
    note: str = ""
    apply_date: str = ""
    is_active: bool = True


class ItemGroupUpdate(BaseModel):
    std_days: str | None = None
    note: str | None = None
    apply_date: str | None = None
    is_active: bool | None = None


class ItemGroupOut(ItemGroupCreate):
    id: int
    model_config = {"from_attributes": True}


# ---- Brand ----
class BrandCreate(BaseModel):
    code: str = ""
    department: str = ""
    is_active: bool = True


class BrandUpdate(BaseModel):
    department: str | None = None
    is_active: bool | None = None


class BrandOut(BrandCreate):
    id: int
    model_config = {"from_attributes": True}
