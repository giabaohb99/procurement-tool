"""CRUD + di chuyển thư mục THƯỜNG — `tab_doc_folder`.

Mẫu cây tham khảo: `help_center/service.py` (`get_tree`, `next_sort_order`,
`_validate_new_parent`, xóa nhánh, gập dấu). Khác ở một điểm cốt lõi: cây thư
mục văn bản dùng ĐƯỜNG DẪN VẬT HÓA (`path`/`depth`) thay vì đệ quy theo
`parent_id`, vì `folder_tree_service` cần lọc CẢ NHÁNH bằng một chỉ mục
(`path LIKE 'prefix%'`) — cây văn bản có thể sâu tới 6 cấp × hàng trăm thư mục,
đệ quy Python từng cấp một là N+1 truy vấn.

Thư mục PHÁP NHÂN (gốc, tự sinh) ở `folder_root_service.py`; hàm gập dấu + kiểm
tên trùng anh em ở `folder_naming.py`.

⚠️ `path`/`depth` CHỈ được ghi ở đây (luật phải giữ, `plan.md`). Nơi khác cần
lọc cả nhánh thì đọc `path`, không tự tính lại.
"""
from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.audit import record

from .folder_constants import MAX_DEPTH, FOLDER_ACCESS_LEVEL_LABELS, FolderKind, FolderStatus
from .folder_model import DocFolder
from .folder_naming import ensure_name_unique_among_siblings
from .folder_schema import FolderCreate, FolderUpdate

AUDIT_ENTITY = "doc_folder"


# ── Đọc / kiểm ────────────────────────────────────────────────────────────
def get_folder_or_404(db: Session, folder_id: int) -> DocFolder:
    folder = db.get(DocFolder, folder_id)
    if not folder:
        raise HTTPException(404, "Không tìm thấy thư mục")
    return folder


def next_sort_order(db: Session, parent_id: int) -> int:
    value = db.query(func.max(DocFolder.sort_order)).filter(DocFolder.parent_id == parent_id).scalar()
    return int((value or 0) + 1)


def _get_active_parent_or_400(db: Session, parent_id: int) -> DocFolder:
    if not parent_id:
        raise HTTPException(400, "Thiếu thư mục cha — thư mục thường không tạo ngang hàng gốc")
    parent = db.get(DocFolder, parent_id)
    if not parent:
        raise HTTPException(404, "Không tìm thấy thư mục cha")
    if parent.status != int(FolderStatus.ACTIVE):
        raise HTTPException(400, "Thư mục cha đang ngừng dùng, không tạo thư mục con được")
    return parent


def create_folder(db: Session, data: FolderCreate, actor: int) -> DocFolder:
    parent = _get_active_parent_or_400(db, data.parent_id)
    if parent.depth + 1 > MAX_DEPTH:
        raise HTTPException(400, f"Cây thư mục sâu tối đa {MAX_DEPTH} cấp (tính cả gốc)")

    name = data.name.strip()
    if not name:
        raise HTTPException(400, "Tên thư mục không được để trống")
    ensure_name_unique_among_siblings(db, parent.id, name)

    folder = DocFolder(
        company_id=parent.company_id, parent_id=parent.id, kind=int(FolderKind.NORMAL),
        name=name, code=(data.code or "").strip(), description=data.description or "",
        path="", depth=parent.depth + 1,
        sort_order=data.sort_order if data.sort_order is not None else next_sort_order(db, parent.id),
        status=int(FolderStatus.ACTIVE), default_access=None,
        created_by=actor, updated_by=actor,
    )
    db.add(folder)
    db.flush()
    folder.path = f"{parent.path}{folder.id}/"
    db.commit()
    db.refresh(folder)
    record(db, actor, AUDIT_ENTITY, folder.id, "create", f"Tạo thư mục {folder.name}")
    return folder


def _apply_status_change(db: Session, folder: DocFolder, new_status: int) -> str:
    """Đổi tình trạng. Ngừng dùng thì kéo CẢ NHÁNH; khôi phục chỉ đúng thư mục
    này (không tự bật lại con — người dùng khôi phục từng cấp cần thì bấm tiếp).

    Trả về hậu tố để ghép vào câu nhật ký (vd " (cùng 3 thư mục con)")."""
    if new_status not in (int(FolderStatus.ACTIVE), int(FolderStatus.ARCHIVED)):
        raise HTTPException(400, "Tình trạng thư mục không hợp lệ")

    if new_status == int(FolderStatus.ARCHIVED):
        #  Khóa CẢ NHÁNH trước khi đổi tình trạng (M7, rà soát 23/09/2026,
        #  cùng lý do với `folder_move_service.move_folder`) — một lệnh DỜI
        #  đang chạy song song có thể đang đổi `path` của chính nhánh này giữa
        #  lúc đọc và lúc ghi. `with_for_update()` là khóa thật trên MySQL
        #  (prod), SQLite (bài kiểm) tự bỏ qua vô hại.
        ids = (
            [r[0] for r in db.query(DocFolder.id)
                          .filter(DocFolder.path.like(f"{folder.path}%"))
                          .with_for_update().all()]
            if folder.path else [folder.id]
        )
        db.query(DocFolder).filter(DocFolder.id.in_(ids)).update(
            {DocFolder.status: int(FolderStatus.ARCHIVED)}, synchronize_session=False)
        db.flush()
        db.refresh(folder)
        extra = len(ids) - 1
        return f" (cùng {extra} thư mục con)" if extra else ""

    folder.status = int(FolderStatus.ACTIVE)
    return ""


def update_folder(db: Session, folder: DocFolder, data: FolderUpdate, actor: int) -> DocFolder:
    values = data.model_dump(exclude_unset=True)
    #  Thư mục pháp nhân sửa được Y HỆT thư mục thường (đại ca chốt 24/09/2026:
    #  tên công ty chỉ là tên thư mục — nơi lưu trữ + phân quyền, không có gì
    #  đặc biệt). Đổi tên thì `folder.name` thắng tên công ty khi hiển thị
    #  (`folder_tree_service._display_label_of`).

    changes: list[str] = []

    if "name" in values and values["name"] is not None:
        name = values["name"].strip()
        if not name:
            raise HTTPException(400, "Tên thư mục không được để trống")
        if name != folder.name:
            ensure_name_unique_among_siblings(db, folder.parent_id, name, exclude_id=folder.id)
            folder.name = name
            changes.append("đổi tên")
    if "code" in values:
        folder.code = (values["code"] or "").strip()
    if "description" in values:
        folder.description = values["description"] or ""
        changes.append("sửa mô tả")
    if "sort_order" in values and values["sort_order"] is not None:
        folder.sort_order = values["sort_order"]
    #  Mức nền (phase 04, duoc-CR-475) — route đã gác `ensure_level(..., MANAGE)`,
    #  ở đây chỉ còn kiểm DẢI GIÁ TRỊ hợp lệ.
    if "default_access" in values and values["default_access"] is not None:
        level = values["default_access"]
        if level not in FOLDER_ACCESS_LEVEL_LABELS:
            raise HTTPException(400, f"Mức quyền nền không hợp lệ: {level}")
        folder.default_access = level
        changes.append(f"đặt mức nền {FOLDER_ACCESS_LEVEL_LABELS.get(level, '')}")

    branch_note = ""
    if "status" in values and values["status"] is not None and values["status"] != folder.status:
        branch_note = _apply_status_change(db, folder, values["status"])
        changes.append("ngừng dùng" if values["status"] == int(FolderStatus.ARCHIVED) else "khôi phục")

    folder.updated_by = actor
    db.commit()
    db.refresh(folder)
    if changes:
        record(db, actor, AUDIT_ENTITY, folder.id, "update",
              f"Cập nhật thư mục {folder.name}: {', '.join(changes)}{branch_note}")
    return folder


def reorder_siblings(db: Session, items: list[dict], actor: int) -> int:
    """`items = [{"id", "sort_order"}, ...]` — phải CÙNG một thư mục cha."""
    ids = [it["id"] for it in items]
    rows = {f.id: f for f in db.query(DocFolder).filter(DocFolder.id.in_(ids)).all()}
    missing = [i for i in ids if i not in rows]
    if missing:
        raise HTTPException(404, f"Không tìm thấy thư mục {missing}")
    parent_ids = {rows[i].parent_id for i in ids}
    if len(parent_ids) > 1:
        raise HTTPException(400, "Chỉ sắp thứ tự được các thư mục cùng một cấp cha")

    changed = 0
    for it in items:
        folder = rows[it["id"]]
        if folder.sort_order != it["sort_order"]:
            folder.sort_order = it["sort_order"]
            folder.updated_by = actor
            changed += 1
    if changed:
        db.commit()
    return changed


def _guard_deletable(db: Session, folder: DocFolder) -> None:
    #  Thư mục pháp nhân + thư mục nhóm «Công ty» KHÔNG xóa được (đại ca chốt
    #  24/09/2026 — đảo lại quyết định cho xóa gốc pháp nhân trước đó).
    if folder.kind in (int(FolderKind.COMPANY), int(FolderKind.COMPANY_GROUP)):
        raise HTTPException(400, "Thư mục công ty do hệ thống quản lý, không xóa được")
    if db.query(DocFolder.id).filter(DocFolder.parent_id == folder.id).first():
        raise HTTPException(400, "Thư mục còn thư mục con, không xóa được")


def _split_documents(db: Session, folder_id: int) -> tuple[list, list[int]]:
    """Dòng nối của thư mục + id văn bản sẽ MỒ CÔI (không còn thư mục nào khác)
    nếu xóa nó. Đếm TOÀN HỆ, không lọc theo quyền người xóa — văn bản người đó
    không thấy vẫn là văn bản thật cần chỗ ở."""
    from .folder_link_model import DocumentFolderLink

    links = db.query(DocumentFolderLink).filter(DocumentFolderLink.folder_id == folder_id).all()
    doc_ids = [row.document_id for row in links]
    if not doc_ids:
        return links, []
    elsewhere = {doc_id for (doc_id,) in db.query(DocumentFolderLink.document_id).filter(
        DocumentFolderLink.document_id.in_(doc_ids),
        DocumentFolderLink.folder_id != folder_id).distinct()}
    return links, [doc_id for doc_id in doc_ids if doc_id not in elsewhere]


def delete_preview(db: Session, folder: DocFolder) -> dict:
    """Hộp xác nhận xóa cần biết trước: có xóa được không, bao nhiêu văn bản
    đang nằm trong đó, bao nhiêu văn bản sẽ mồ côi (phải chọn nơi lưu mới)."""
    blocked = ""
    try:
        _guard_deletable(db, folder)
    except HTTPException as exc:
        blocked = str(exc.detail)
    links, orphans = _split_documents(db, folder.id)
    return {"blocked_reason": blocked, "document_count": len(links),
            "orphan_count": len(orphans), "parent_id": folder.parent_id}


def delete_folder(db: Session, folder: DocFolder, actor: int,
                  move_to: DocFolder | None = None) -> None:
    """Xóa thư mục, KỂ CẢ khi còn văn bản (đại ca chốt 25/09/2026 — trước đó
    chặn cứng "còn văn bản không xóa được"). Văn bản thì KHÔNG bị xóa theo:

    - văn bản còn nằm ở thư mục KHÁC → chỉ gỡ khỏi thư mục này; nếu đây là
      thư mục chính của nó thì thư mục cũ nhất còn lại lên làm chính;
    - văn bản chỉ nằm ở ĐÂY (sẽ mồ côi) → chuyển sang `move_to` (người xóa
      chọn ở hộp xác nhận). Không truyền `move_to` (xóa hàng loạt) thì rơi về
      thư mục pháp nhân qua `ensure_not_orphan` — luật «không mồ côi» có sẵn.

    Vẫn chặn thư mục còn thư mục con: xóa nguyên nhánh là việc khác, không làm
    lén trong một lần bấm."""
    from app.modules.document.model import Document

    from . import folder_link_service
    from .folder_link_model import DocumentFolderLink

    _guard_deletable(db, folder)
    if move_to is not None and move_to.id == folder.id:
        raise HTTPException(400, "Chọn một thư mục KHÁC để chuyển văn bản sang")
    if move_to is not None and move_to.status != int(FolderStatus.ACTIVE):
        raise HTTPException(400, "Thư mục nhận văn bản đang ngừng dùng")

    links, orphans = _split_documents(db, folder.id)
    orphan_set = set(orphans)
    for row in links:
        if row.document_id in orphan_set:
            if move_to is not None:
                db.add(DocumentFolderLink(document_id=row.document_id, folder_id=move_to.id,
                                          is_primary=True, created_by=actor))
        elif row.is_primary:
            nxt = (db.query(DocumentFolderLink)
                   .filter(DocumentFolderLink.document_id == row.document_id,
                           DocumentFolderLink.folder_id != folder.id)
                   .order_by(DocumentFolderLink.id.asc()).first())
            if nxt:
                nxt.is_primary = True
        db.delete(row)

    name = folder.name
    folder_id = folder.id
    db.delete(folder)
    db.commit()

    if move_to is None:
        for doc in db.query(Document).filter(Document.id.in_(orphans)).all() if orphans else []:
            folder_link_service.ensure_not_orphan(db, doc, actor)

    moved = f", chuyển {len(orphans)} văn bản sang «{move_to.name}»" if move_to and orphans else ""
    record(db, actor, AUDIT_ENTITY, folder_id, "delete",
           f"Xóa thư mục {name} ({len(links)} văn bản){moved}")
