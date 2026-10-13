"""ai-CR-191 — sổ tham chiếu của danh mục LOẠI CON DẤU (`seal_type`).

Phiếu duyệt dấu ghi `seal_type_id` (không FK); còn phiếu nào — kể cả đã xóa mềm — thì chỉ ngưng dùng.
`catalog_controller.py` import tệp này; `make_crud_router` tự gọi chốt theo entity.
"""
from app.core.reference_guard import Reference, register

from .model import SealRequest

register("seal_type", "Loại con dấu", [
    Reference(SealRequest, "seal_type_id", "phiếu duyệt dấu"),
])
