"""Router hai danh mục nền của phân hệ Văn thư.

Dùng `make_crud_router` như các danh mục khác (kho, ĐVT, phân loại) — cả hai chỉ
cần list/get/create/update/delete + audit, không có nghiệp vụ riêng.

`van-thu` D07 cấm đổi `code` của loại văn bản sau khi đã cấp số — cài bằng
`before_update` bên dưới, không phải bằng việc khóa ô nhập trên giao diện.
"""
from app.core.crud import make_crud_router

from .issue_code_guard import ensure_doc_type_code_free
from .model import DocType, ExternalParty
from .schema import (DocTypeCreate, DocTypeOut, DocTypeUpdate,
                     ExternalPartyCreate, ExternalPartyOut, ExternalPartyUpdate)
from .security_level_guard import before_create as _sl_before_create
from .security_level_guard import before_delete as _sl_before_delete
from .security_level_model import SecurityLevel
from .security_level_schema import (SecurityLevelCreate, SecurityLevelOut,
                                    SecurityLevelUpdate)


def _guard_doc_type(db, obj, values: dict):
    """Đổi mã sau khi đã cấp số là hỏng số hiệu đã ban hành; đổi kiểu định danh
    khi đã có văn bản thuộc loại thì hai nhóm văn bản cùng loại mang hai kiểu số
    khác nhau, không xếp chung sổ được."""
    if "code" in values:
        ensure_doc_type_code_free(db, obj.code, values["code"])
    if "id_scheme" in values and values["id_scheme"] != obj.id_scheme:
        from fastapi import HTTPException

        from app.modules.document.model import Document
        if db.query(Document.id).filter(Document.doc_type_id == obj.id).first():
            raise HTTPException(400, "Loại đã có văn bản, không đổi được kiểu định danh")


doc_type_router = make_crud_router(
    "/api/doc-types", "doc_type", DocType,
    DocTypeCreate, DocTypeUpdate, DocTypeOut,
    ["code", "name", "group_code", "is_active", "id_scheme", "default_secrecy",
     "is_confidential_type", "needs_approval", "needs_signature", "needs_decision"],
    before_update=_guard_doc_type,
    csv_headers={"id": "ID", "code": "Mã loại", "name": "Tên loại văn bản",
                 "group_code": "Nhóm", "description": "Mô tả"})

#  Mức mật / độ khẩn. Không khai `code_prefix`: mã ở đây là chữ có nghĩa
#  (CONGKHAI, TUYETMAT) chứ không phải số chạy — nó xuất hiện trong tài liệu vận
#  hành và trong mã nguồn cũ, tự sinh ra `MML001` là mất luôn manh mối.
security_level_router = make_crud_router(
    "/api/security-levels", "security_level", SecurityLevel,
    SecurityLevelCreate, SecurityLevelUpdate, SecurityLevelOut,
    ["code", "name", "kind", "value", "is_active"],
    before_create=_sl_before_create,
    before_delete=_sl_before_delete,
    csv_headers={"id": "ID", "code": "Mã", "name": "Tên mức", "kind": "Thang",
                 "value": "Bậc", "description": "Mô tả"})

external_party_router = make_crud_router(
    "/api/external-parties", "external_party", ExternalParty,
    ExternalPartyCreate, ExternalPartyUpdate, ExternalPartyOut,
    ["code", "name", "kind", "is_active"],
    code_prefix="DVN",
    csv_headers={"id": "ID", "code": "Mã", "name": "Tên đơn vị",
                 "contact_person": "Người liên hệ", "phone": "Điện thoại",
                 "email": "Email", "address": "Địa chỉ"})
