from app.core.crud import make_crud_router

from .model import Brand, ItemGroup, Unit, Warehouse
from .schema import (BrandCreate, BrandOut, BrandUpdate, ItemGroupCreate,
                     ItemGroupOut, ItemGroupUpdate, UnitCreate, UnitOut,
                     UnitUpdate, WarehouseCreate, WarehouseOut, WarehouseUpdate)

warehouse_router = make_crud_router(
    "/api/warehouses", "warehouse", Warehouse,
    WarehouseCreate, WarehouseUpdate, WarehouseOut, ["code", "name", "is_active"], 
    code_prefix=None, csv_headers={"id": "ID", "code": "Mã", "name": "Tên kho", "address": "Địa chỉ"})

unit_router = make_crud_router(
    "/api/units", "unit", Unit,
    UnitCreate, UnitUpdate, UnitOut, ["code", "name", "is_active"], 
    code_prefix="DVT", csv_headers={"id": "ID", "code": "Mã", "name": "Tên ĐVT"})

item_group_router = make_crud_router(
    "/api/item-groups", "item_group", ItemGroup,
    ItemGroupCreate, ItemGroupUpdate, ItemGroupOut, ["code", "name", "is_active"], 
    unique_field="code", code_prefix="PLO", 
    csv_headers={"id": "ID", "code": "Mã", "name": "Phân loại", "std_days": "Số ngày quy định", "apply_date": "Ngày áp dụng", "note": "Ghi chú"})

brand_router = make_crud_router(
    "/api/brands", "brand", Brand,
    BrandCreate, BrandUpdate, BrandOut, ["code", "department", "is_active"], 
    code_prefix="PBA", csv_headers={"id": "ID", "code": "Mã", "department": "Bộ phận đặt hàng"})
