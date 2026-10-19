"""Router hai danh mục nền của phân hệ Văn thư.

Dùng `make_crud_router` như các danh mục khác (kho, ĐVT, phân loại) — cả hai chỉ
cần list/get/create/update/delete + audit, không có nghiệp vụ riêng.

`van-thu` D07 cấm đổi `code` của loại văn bản sau khi đã cấp số — cài bằng
`before_update` bên dưới, không phải bằng việc khóa ô nhập trên giao diện.
"""
from app.core.crud import make_crud_router

from . import references  # noqa: F401  — ai-CR-191: đăng ký chỗ tham chiếu (loại văn bản / đối tác ngoài / thư mục / sổ / quy tắc)
from .issue_code_guard import ensure_doc_type_code_free
from .model import DocType, ExternalParty
from .schema import (DocTypeCreate, DocTypeOut, DocTypeUpdate,
                     ExternalPartyCreate, ExternalPartyOut, ExternalPartyUpdate)
from .security_level_guard import before_create as _sl_before_create
from .security_level_guard import before_delete as _sl_before_delete
from .security_level_model import SecurityLevel
from .security_level_schema import (SecurityLevelCreate, SecurityLevelOut,
                                    SecurityLevelUpdate)


#  duoc-CR-629 (review N2): loại HDLD là loại HỆ THỐNG (bản lưu trữ hợp đồng lao động). KHÓA mọi cờ — mở
#  `is_personal`/duyệt/cấp số… hoặc tắt/đổi mã là mở đường rò hoặc làm cầu đồng bộ chết im lặng.
_HDLD_LOCKED_FIELDS = ("code", "is_active", "is_personal", "needs_approval", "needs_signature",
                       "needs_decision", "needs_request", "id_scheme", "number_when",
                       "is_confidential_type", "default_secrecy", "default_flow_id")


def _is_hdld_code(code) -> bool:
    from app.modules.document.type_metadata import LABOR_CONTRACT_DOC_TYPE
    return str(code or "").strip().upper() == LABOR_CONTRACT_DOC_TYPE


def _guard_doc_type_create(db, data):
    if _is_hdld_code(getattr(data, "code", "")):
        from fastapi import HTTPException
        raise HTTPException(400, "Mã HDLD dành riêng cho bản lưu trữ hợp đồng lao động do hệ thống tạo")


def _guard_doc_type_delete(db, obj):
    if _is_hdld_code(obj.code):
        from fastapi import HTTPException
        raise HTTPException(400, "Loại Hợp đồng lao động là loại hệ thống, không xóa được")


def _guard_doc_type(db, obj, values: dict):
    """Đổi mã sau khi đã cấp số là hỏng số hiệu đã ban hành; đổi kiểu định danh
    khi đã có văn bản thuộc loại thì hai nhóm văn bản cùng loại mang hai kiểu số
    khác nhau, không xếp chung sổ được."""
    if _is_hdld_code(obj.code) or _is_hdld_code(values.get("code")):
        from fastapi import HTTPException
        if _is_hdld_code(obj.code):
            changed = [f for f in _HDLD_LOCKED_FIELDS if f in values and values[f] != getattr(obj, f, None)]
            if changed:
                raise HTTPException(400, "Loại Hợp đồng lao động là loại hệ thống, không sửa được: " + ", ".join(changed))
        elif _is_hdld_code(values.get("code")):
            raise HTTPException(400, "Mã HDLD dành riêng cho bản lưu trữ hợp đồng lao động do hệ thống tạo")
    if "code" in values:
        ensure_doc_type_code_free(db, obj.code, values["code"])
    if "id_scheme" in values and values["id_scheme"] != obj.id_scheme:
        from fastapi import HTTPException

        from app.modules.document.model import Document
        #  ai-CR-177: bản nháp đã xóa mềm không tính là «loại đã có văn bản».
        if db.query(Document.id).filter(Document.doc_type_id == obj.id,
                                        Document.is_deleted == False).first():  # noqa: E712
            raise HTTPException(400, "Loại đã có văn bản, không đổi được kiểu định danh")


doc_type_router = make_crud_router(
    "/api/doc-types", "doc_type", DocType,
    DocTypeCreate, DocTypeUpdate, DocTypeOut,
    ["code", "name", "group_code", "is_active", "id_scheme", "default_secrecy",
     "is_confidential_type", "is_personal", "needs_approval", "needs_signature",
     "needs_decision"],
    before_create=_guard_doc_type_create,
    before_update=_guard_doc_type,
    before_delete=_guard_doc_type_delete,
    #  Nhập CSV đi vòng mọi chốt `before_*` (đặt `is_active`, tạo mã tùy ý) ⇒ không để mở với loại hệ thống HDLD.
    #  Giao diện v2 không dùng đường này.
    csv_import=False,
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
