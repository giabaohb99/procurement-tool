"""Danh mục Loại con dấu — CRUD đơn giản qua khung chung.

Danh mục nền (entity `seal_type`, khai PUBLIC ở scoping) nên dùng `make_crud_router`:
tự gác `require`, phân trang/sắp xếp/lọc, audit, kèm CSV. Khóa tự nhiên là TÊN (unique).
"""
from app.core.crud import make_crud_router

from .model import SealType
from .schema import SealTypeCreate, SealTypeResponse, SealTypeUpdate

seal_type_router = make_crud_router(
    "/api/seal-types", "seal_type", SealType,
    SealTypeCreate, SealTypeUpdate, SealTypeResponse,
    ["name", "is_active"],
    unique_field="name", code_prefix=None,
    csv_headers={
        "id": "ID", "name": "Tên loại con dấu", "description": "Mô tả", "is_active": "Đang dùng",
    },
)
