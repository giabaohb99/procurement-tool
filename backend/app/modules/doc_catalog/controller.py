"""Router hai danh mục nền của phân hệ Văn thư.

Dùng `make_crud_router` như các danh mục khác (kho, ĐVT, phân loại) — cả hai chỉ
cần list/get/create/update/delete + audit, không có nghiệp vụ riêng.

⚠️ Một ràng buộc CHƯA cài được ở đây: `van-thu` D07 cấm đổi `code` của loại văn
bản sau khi đã cấp số. Bộ cấp số (`tab_number_sequence`) thuộc bước 3a của plan,
chưa có bảng nên chưa kiểm được. Khi làm bước đó phải thêm chốt chặn vào đây —
đổi mã sau khi đã có văn bản mang số cũ là hỏng số hiệu đã ban hành.
"""
from app.core.crud import make_crud_router

from .model import DocType, ExternalParty
from .schema import (DocTypeCreate, DocTypeOut, DocTypeUpdate,
                     ExternalPartyCreate, ExternalPartyOut, ExternalPartyUpdate)

doc_type_router = make_crud_router(
    "/api/doc-types", "doc_type", DocType,
    DocTypeCreate, DocTypeUpdate, DocTypeOut,
    ["code", "name", "group_code", "is_active", "id_scheme", "default_secrecy",
     "is_confidential_type", "needs_approval", "needs_signature", "needs_decision"],
    csv_headers={"id": "ID", "code": "Mã loại", "name": "Tên loại văn bản",
                 "group_code": "Nhóm", "description": "Mô tả"})

external_party_router = make_crud_router(
    "/api/external-parties", "external_party", ExternalParty,
    ExternalPartyCreate, ExternalPartyUpdate, ExternalPartyOut,
    ["code", "name", "kind", "is_active"],
    code_prefix="DVN",
    csv_headers={"id": "ID", "code": "Mã", "name": "Tên đơn vị",
                 "contact_person": "Người liên hệ", "phone": "Điện thoại",
                 "email": "Email", "address": "Địa chỉ"})
