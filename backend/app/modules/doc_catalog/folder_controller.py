"""API CÂY THƯ MỤC VĂN BẢN — `/api/doc-folders` (CRUD + tra cứu + gắn hàng
loạt). Cửa hẹp `PUT /api/documents/{id}/folders` (đặt thư mục của MỘT văn
bản) tách sang `folder_document_link_controller.py` để giữ tệp này < 200 dòng.

Quyền — HAI LỚP, cả hai đều phải qua (phase 04, duoc-CR-475):
  1. `require("doc_folder", ...)` — vai trò có được đụng vào MÀN thư mục không.
  2. `folder_access_service.ensure_level(...)` — MỨC hiệu lực trên ĐÚNG thư mục
     đó (Xem/Đóng góp/Quản lý), tính theo cây + ACL. Không thấy → 404 (không
     phải 403, để không dò được tên thư mục riêng của người khác).

Ngưỡng theo hành động (bảng "Ba mức quyền" của đặc tả phase 04):
  * XEM (VIEW)       — mở `/{id}`.
  * ĐÓNG GÓP         — tạo thư mục con (trên CHA), gắn/gỡ văn bản (trên thư mục
    ĐÍCH, kiểm ở `folder_link_bulk_service.py` vì hai route đó đã có
    `user`/`profile` sẵn), đặt thư mục của một văn bản (`PUT .../folders`).
  * QUẢN LÝ          — đổi tên/mô tả/`default_access`, chuyển (+ĐÓNG GÓP trên
    cha MỚI), sắp thứ tự (trên cha CHUNG), ngừng dùng/khôi phục, xóa.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.auth import get_perm_profile, require
from app.core.database import get_db
from app.core.response import success

from . import (folder_access_service, folder_free_root_service, folder_link_bulk_service, folder_move_service,
              folder_service, folder_tree_service)
from .folder_constants import FolderAccessLevel
from .folder_schema import FolderCreate, FolderLinkIn, FolderMoveIn, FolderReorderIn, FolderUnlinkIn, FolderUpdate

router = APIRouter(prefix="/api/doc-folders", tags=["doc_folder"])

VIEW = int(FolderAccessLevel.VIEW)
CONTRIBUTE = int(FolderAccessLevel.CONTRIBUTE)
MANAGE = int(FolderAccessLevel.MANAGE)


@router.get("/tree")
def get_tree(
    include_archived: bool = Query(False),
    db: Session = Depends(get_db),
    user=Depends(require("doc_folder", "read")),
):
    return success(folder_tree_service.tree(db, user, include_archived=include_archived))


@router.get("/search")
def search_folders(
    q: str = Query(""),
    db: Session = Depends(get_db),
    user=Depends(require("doc_folder", "read")),
):
    return success(folder_tree_service.search_folders(db, user, q))


@router.get("/{folder_id}")
def get_folder(
    folder_id: int,
    db: Session = Depends(get_db),
    user=Depends(require("doc_folder", "read")),
):
    profile = get_perm_profile(db, user)
    folder = folder_service.get_folder_or_404(db, folder_id)
    folder_access_service.ensure_level(db, user, folder, VIEW, profile)
    return success(folder_tree_service.get_detail(db, folder, user))


@router.post("")
def create_folder(
    data: FolderCreate,
    db: Session = Depends(get_db),
    user=Depends(require("doc_folder", "create")),
):
    profile = get_perm_profile(db, user)
    if data.parent_id == 0:
        #  Gốc cây: chỉ cần `doc_folder.create` (đã gác ở `require` trên) —
        #  không có thư mục cha nào để hỏi mức. Người tạo tự nhận Quản lý.
        folder = folder_free_root_service.create_free_root_folder(
            db, data, user.id, int(profile.get("employee_id") or 0))
        return success(folder_tree_service.get_detail(db, folder, user), "Đã tạo thư mục", 201)
    parent = folder_service.get_folder_or_404(db, data.parent_id)
    folder_access_service.ensure_level(db, user, parent, CONTRIBUTE, profile)
    folder = folder_service.create_folder(db, data, user.id)
    return success(folder_tree_service.get_detail(db, folder, user), "Đã tạo thư mục", 201)


@router.patch("/{folder_id}")
def update_folder(
    folder_id: int,
    data: FolderUpdate,
    db: Session = Depends(get_db),
    user=Depends(require("doc_folder", "write")),
):
    profile = get_perm_profile(db, user)
    folder = folder_service.get_folder_or_404(db, folder_id)
    folder_access_service.ensure_level(db, user, folder, MANAGE, profile)
    folder = folder_service.update_folder(db, folder, data, user.id)
    return success(folder_tree_service.get_detail(db, folder, user), "Đã cập nhật thư mục")


@router.post("/{folder_id}/move")
def move_folder(
    folder_id: int,
    data: FolderMoveIn,
    db: Session = Depends(get_db),
    user=Depends(require("doc_folder", "write")),
):
    profile = get_perm_profile(db, user)
    folder = folder_service.get_folder_or_404(db, folder_id)
    folder_access_service.ensure_level(db, user, folder, MANAGE, profile)
    #  Chuyển vào một nhánh phải có ít nhất ĐÓNG GÓP ở CHA MỚI — không thì ai
    #  đó dời được thư mục của mình vào một nhánh họ không có quyền đặt gì vào.
    #  Ra GỐC cây (`0`) thì không có cha nào để hỏi mức — chỉ cần Quản lý trên
    #  chính thư mục đang chuyển (đã gác ở trên).
    if data.new_parent_id:
        new_parent = folder_service.get_folder_or_404(db, data.new_parent_id)
        folder_access_service.ensure_level(db, user, new_parent, CONTRIBUTE, profile)
    folder = folder_move_service.move_folder(
        db, folder, data.new_parent_id, user.id, int(profile.get("employee_id") or 0))
    return success(folder_tree_service.get_detail(db, folder, user), "Đã chuyển thư mục")


def _ensure_reorder_access(db: Session, user, profile: dict, items) -> None:
    """QUẢN LÝ trên CHA CHUNG — sắp lại thứ tự đổi vị trí của mọi anh em cùng
    cha, nên cần quyền trên đúng thư mục cha đó (hoặc trên chính nó, nếu đang
    sắp các thư mục pháp nhân — `parent_id=0`).

    `levels` tính MỘT LẦN cho cả danh sách (M1, rà soát 23/09/2026) — không để
    `ensure_level` tự tính lại TOÀN BỘ (2 truy vấn) ở MỖI thư mục."""
    levels = folder_access_service.effective_levels(db, user, profile)
    for item in items:
        folder = folder_service.get_folder_or_404(db, item.id)
        target = (folder if folder.parent_id == 0
                 else folder_service.get_folder_or_404(db, folder.parent_id))
        folder_access_service.ensure_level(db, user, target, MANAGE, profile, levels=levels)


@router.post("/reorder")
def reorder_folders(
    data: FolderReorderIn,
    db: Session = Depends(get_db),
    user=Depends(require("doc_folder", "write")),
):
    profile = get_perm_profile(db, user)
    _ensure_reorder_access(db, user, profile, data.items)
    changed = folder_service.reorder_siblings(db, [item.model_dump() for item in data.items], user.id)
    return success({"changed": changed}, "Đã sắp lại thứ tự")


@router.get("/{folder_id}/delete-preview")
def delete_folder_preview(
    folder_id: int,
    db: Session = Depends(get_db),
    user=Depends(require("doc_folder", "delete")),
):
    """Số văn bản trong thư mục + số văn bản sẽ mồ côi nếu xóa — cho hộp xác nhận."""
    profile = get_perm_profile(db, user)
    folder = folder_service.get_folder_or_404(db, folder_id)
    folder_access_service.ensure_level(db, user, folder, MANAGE, profile)
    return success(folder_service.delete_preview(db, folder))


@router.delete("/{folder_id}")
def delete_folder(
    folder_id: int,
    move_to: int = Query(0, ge=0, description="Thư mục nhận văn bản sẽ mồ côi; 0 = về thư mục pháp nhân"),
    db: Session = Depends(get_db),
    user=Depends(require("doc_folder", "delete")),
):
    profile = get_perm_profile(db, user)
    folder = folder_service.get_folder_or_404(db, folder_id)
    folder_access_service.ensure_level(db, user, folder, MANAGE, profile)
    target = None
    if move_to:
        target = folder_service.get_folder_or_404(db, move_to)
        #  Chuyển văn bản VÀO đâu thì phải có quyền thêm văn bản ở đó — cùng
        #  mức với gắn văn bản vào thư mục (`/documents/link`).
        folder_access_service.ensure_level(db, user, target, CONTRIBUTE, profile)
    folder_service.delete_folder(db, folder, user.id, target)
    return success(None, "Đã xóa thư mục")


@router.post("/documents/link")
def link_documents(
    data: FolderLinkIn,
    db: Session = Depends(get_db),
    user=Depends(require("document", "write")),
):
    #  Mức ĐÓNG GÓP trên thư mục ĐÍCH kiểm ở `folder_link_bulk_service.move_documents`
    #  — hàm đó đã nhận sẵn `user`/`profile` để kiểm quyền SỬA từng văn bản.
    result = folder_link_bulk_service.move_documents(
        db, data.document_ids, data.folder_id, data.mode, user, get_perm_profile(db, user), user.id)
    return success(result, "Đã gắn văn bản vào thư mục")


@router.post("/documents/unlink")
def unlink_documents(
    data: FolderUnlinkIn,
    db: Session = Depends(get_db),
    user=Depends(require("document", "write")),
):
    result = folder_link_bulk_service.bulk_unlink(
        db, data.document_ids, data.folder_id, user, get_perm_profile(db, user), user.id)
    return success(result, "Đã gỡ văn bản khỏi thư mục")
