"""API cấp / thu QUYỀN TRÊN THƯ MỤC — `/api/doc-folders/{folder_id}/access`.

Chỉ mức **Quản lý** gọi được cả ba route — gác bằng `require("doc_folder",
"write")` (vai trò) RỒI `folder_access_service.ensure_level(..., MANAGE)`
(thư mục cụ thể), đúng hai lớp như mọi route ghi khác của phase 04.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import get_perm_profile, require
from app.core.database import get_db
from app.core.response import success

from . import (folder_access_bulk_service, folder_access_grant_service,
              folder_access_view_service, folder_service)
from .folder_access_schema import (FolderAccessBulkGrantIn, FolderAccessGrantIn,
                                   FolderAccessLevelPatchIn, FolderAccessRevokeIn)
from .folder_access_service import ensure_level
from .folder_constants import FolderAccessLevel

router = APIRouter(prefix="/api/doc-folders", tags=["doc_folder_access"])


def _folder_for_manage(db: Session, folder_id: int, user, profile: dict):
    folder = folder_service.get_folder_or_404(db, folder_id)
    ensure_level(db, user, folder, int(FolderAccessLevel.MANAGE), profile)
    return folder


@router.get("/{folder_id}/access")
def list_access(
    folder_id: int,
    db: Session = Depends(get_db),
    user=Depends(require("doc_folder", "write")),
):
    profile = get_perm_profile(db, user)
    folder = _folder_for_manage(db, folder_id, user, profile)
    rows = folder_access_grant_service.list_direct(db, folder.id)
    return success(folder_access_view_service.serialize_rows(db, folder.id, rows))


@router.post("/{folder_id}/access")
def grant_access(
    folder_id: int,
    data: FolderAccessGrantIn,
    db: Session = Depends(get_db),
    user=Depends(require("doc_folder", "write")),
):
    profile = get_perm_profile(db, user)
    folder = _folder_for_manage(db, folder_id, user, profile)
    row = folder_access_grant_service.grant(db, folder, data, user.id)
    return success(
        folder_access_view_service.serialize_rows(db, folder.id, [row])[0],
        "Đã cấp quyền", 201)


@router.post("/{folder_id}/access/bulk")
def grant_access_bulk(
    folder_id: int,
    data: FolderAccessBulkGrantIn,
    db: Session = Depends(get_db),
    user=Depends(require("doc_folder", "write")),
):
    """Hộp «Chia sẻ» kiểu Drive — cấp CÙNG một mức cho CẢ danh sách chủ thể
    trong một lượt (phase 10B, đặc tả §C). `{created, updated, skipped}` —
    không trả danh sách dòng, giao diện tự `invalidateQueries` sau khi thành
    công (đúng lối `useLinkDocumentsToFolder`)."""
    profile = get_perm_profile(db, user)
    folder = _folder_for_manage(db, folder_id, user, profile)
    result = folder_access_bulk_service.grant_bulk(db, folder, data, user.id)
    return success(result, "Đã cấp quyền hàng loạt", 201)


@router.patch("/{folder_id}/access/{access_id}")
def update_access_level(
    folder_id: int,
    access_id: int,
    data: FolderAccessLevelPatchIn,
    db: Session = Depends(get_db),
    user=Depends(require("doc_folder", "write")),
):
    """Đổi MỨC tại chỗ — menu thả xuống trên dòng «Người có quyền» của hộp
    «Chia sẻ», không phải thu hồi rồi cấp lại."""
    profile = get_perm_profile(db, user)
    folder = _folder_for_manage(db, folder_id, user, profile)
    row = folder_access_bulk_service.update_level(db, folder, access_id, data.level, user.id)
    return success(
        folder_access_view_service.serialize_rows(db, folder.id, [row])[0], "Đã đổi mức quyền")


@router.delete("/{folder_id}/access/{access_id}")
def revoke_access(
    folder_id: int,
    access_id: int,
    data: FolderAccessRevokeIn,
    db: Session = Depends(get_db),
    user=Depends(require("doc_folder", "write")),
):
    profile = get_perm_profile(db, user)
    folder = _folder_for_manage(db, folder_id, user, profile)
    row = folder_access_grant_service.revoke(db, folder, access_id, data.reason, user.id)
    return success(
        folder_access_view_service.serialize_rows(db, folder.id, [row])[0], "Đã thu hồi quyền")
