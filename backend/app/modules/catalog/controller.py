from app.core.crud import make_crud_router

from .model import Brand, ItemGroup, Unit, Warehouse
from .schema import (BrandCreate, BrandOut, BrandUpdate, ItemGroupCreate,
                     ItemGroupOut, ItemGroupUpdate, UnitCreate, UnitOut,
                     UnitUpdate, WarehouseCreate, WarehouseOut, WarehouseUpdate)

warehouse_router = make_crud_router(
    "/api/warehouses", "warehouse", Warehouse,
    WarehouseCreate, WarehouseUpdate, WarehouseOut, ["code", "name"])

unit_router = make_crud_router(
    "/api/units", "unit", Unit,
    UnitCreate, UnitUpdate, UnitOut, ["code", "name"])

item_group_router = make_crud_router(
    "/api/item-groups", "item_group", ItemGroup,
    ItemGroupCreate, ItemGroupUpdate, ItemGroupOut, ["name"], unique_field="name")

brand_router = make_crud_router(
    "/api/brands", "brand", Brand,
    BrandCreate, BrandUpdate, BrandOut, ["code", "department"])
