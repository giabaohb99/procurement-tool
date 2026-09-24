"""Cửa HẸP `PUT /api/documents/{id}/folders` — đặt lại TOÀN BỘ thư mục của
MỘT văn bản (dùng ở màn tạo/sửa văn bản). Tách khỏi `folder_controller.py` để
giữ cả hai tệp dưới 200 dòng (phase 03 đặt route này ở `folder_controller.py`;
phase 04 dời sang đây khi thêm cửa kiểm quyền ĐÓNG GÓP).

Quyền: `require("document", "write")` (vai trò) + `access_service.ensure_can`
(quyền SỬA đúng văn bản đó) — như phase 03; phase 04 (duoc-CR-475) thêm MỘT
cửa nữa: mỗi thư mục NGƯỜI DÙNG CHỌN cần ít nhất mức ĐÓNG GÓP, vì quyền sửa
văn bản không tự mở quyền "đặt văn bản vào thư mục này".
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.auth import get_perm_profile, require
from app.core.database import get_db
from app.core.response import success

from . import folder_access_service, folder_link_bulk_service, folder_link_service, folder_service
from .folder_constants import FolderAccessLevel
from .folder_schema import DocumentFolderSetIn

document_folder_router = APIRouter(prefix="/api/documents", tags=["doc_folder"])


def _load_document_for_write(db: Session, document_id: int, user):
    from app.modules.document import access_service, service as document_service

    doc = document_service.get_or_404(db, document_id)
    access_service.ensure_can(db, doc, user, get_perm_profile(db, user), "write")
    return doc


@document_folder_router.put("/{document_id}/folders")
def set_document_folders(
    document_id: int,
    data: DocumentFolderSetIn,
    db: Session = Depends(get_db),
    user=Depends(require("document", "write")),
):
    profile = get_perm_profile(db, user)
    doc = _load_document_for_write(db, document_id, user)
    #  Mỗi thư mục NGƯỜI DÙNG CHỌN cần ít nhất ĐÓNG GÓP — bỏ trống thì
    #  `set_folders` tự rơi về thư mục mặc định, không phải lựa chọn của người
    #  dùng nên không cần kiểm ở đây.
    #  `levels` tính MỘT LẦN cho cả danh sách (M1, rà soát 23/09/2026) — không
    #  để `ensure_level` tự tính lại TOÀN BỘ (2 truy vấn) ở MỖI thư mục.
    levels = folder_access_service.effective_levels(db, user, profile)
    for folder_id in dict.fromkeys(data.folder_ids or []):
        folder = folder_service.get_folder_or_404(db, folder_id)
        folder_access_service.ensure_level(
            db, user, folder, int(FolderAccessLevel.CONTRIBUTE), profile, levels=levels)
    folder_link_service.set_folders(db, doc, data.folder_ids, data.primary_id, user.id, user=user)
    record(db, user.id, "document", doc.id, "update", "Cập nhật thư mục lưu văn bản")
    return success(
        folder_link_bulk_service.folders_for_documents(db, [doc.id]).get(doc.id, []),
        "Đã cập nhật thư mục")
