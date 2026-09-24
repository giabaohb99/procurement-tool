"""Đọc/ghi HÀNG LOẠT trên bảng nối `tab_document_folder_link` — tách khỏi
`folder_link_service.py` để giữ cả hai tệp dưới 200 dòng.

Hai nhóm:
  * `folders_for_documents`/`primary_folder_path_for_documents` — nạp cho
    `document/serializer.py`, MỘT truy vấn cho cả trang danh sách văn bản.
  * `move_documents`/`bulk_unlink` — gắn/gỡ nhiều văn bản vào một thư mục cùng
    lúc, dùng ở `POST /api/doc-folders/documents/link|unlink` (màn Quản lý cây
    thư mục, phase 05). Mỗi văn bản kiểm quyền SỬA riêng
    (`document/access_service.can`), lỗi một dòng không chặn cả lô — trả về
    `{moved, denied:[{id, reason}]}` để giao diện báo đúng phần thất bại.

    ⚠️ Phase 04 (duoc-CR-475) thêm MỘT cửa nữa TRƯỚC vòng lặp: mức ĐÓNG GÓP
    trên chính THƯ MỤC ĐÍCH (`folder_id`) — quyền sửa văn bản không tự động
    mở quyền "đặt văn bản vào thư mục này", hai thứ tách bạch theo đúng luật
    "quyền thư mục KHÔNG mở quyền văn bản, và ngược lại" của `plan.md`.

    ⚠️ Vá 23/09/2026: `primary_folder_path_for_documents` nay BẮT BUỘC `user`
    để lọc — trước đó gọi `breadcrumb_map` trần, lộ tên/đường dẫn của thư mục
    CHÍNH dù người xem không thấy (lỗ để lại từ phase 04, khác lỗ đã vá ở
    `folders_for_documents` cùng đợt trước).
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record

from . import folder_access_service, folder_link_service
from .folder_constants import LINK_MODE_REPLACE, FolderAccessLevel
from .folder_link_model import DocumentFolderLink
from .folder_model import DocFolder


# ── Đọc hàng loạt cho serializer ──────────────────────────────────────────
def folders_for_documents(db: Session, document_ids: list[int], user=None) -> dict[int, list[dict]]:
    """`{document_id: [{id, name, is_primary}, ...]}` — MỘT truy vấn cho cả trang.

    `user` TÙY CHỌN (phase 04, duoc-CR-475): truyền vào thì lọc bớt thư mục
    người XEM không thấy — "Tên thư mục riêng tư không rò qua breadcrumb của
    văn bản" (`plan.md` §"Bảo mật"). Bỏ trống → giữ hành vi phase 03 (trả hết,
    dành cho những nơi gọi CHƯA có `user` trong tay — xem ghi chú ở
    `document/serializer.py`)."""
    if not document_ids:
        return {}
    from app.modules.company.model import Company

    rows = (
        db.query(DocumentFolderLink.document_id, DocFolder.id, DocFolder.name,
                Company.name, DocumentFolderLink.is_primary)
        .join(DocFolder, DocFolder.id == DocumentFolderLink.folder_id)
        .outerjoin(Company, Company.id == DocFolder.company_id)
        .filter(DocumentFolderLink.document_id.in_(document_ids))
        .all()
    )

    visible_ids = None
    if user is not None:
        visible_ids = set(folder_access_service.effective_levels(db, user).keys())

    result: dict[int, list[dict]] = {}
    for document_id, folder_id, name, company_name, is_primary in rows:
        if visible_ids is not None and folder_id not in visible_ids:
            continue
        result.setdefault(document_id, []).append({
            "id": folder_id, "name": name or company_name or "", "is_primary": bool(is_primary),
        })
    return result


def primary_folder_path_for_documents(db: Session, document_ids: list[int],
                                      user=None) -> dict[int, str]:
    """`{document_id: "Cty A / Hợp đồng / 2026"}` — đường dẫn thư mục CHÍNH,
    tính THEO NGƯỜI XEM (vá 23/09/2026 — cùng gốc với `folders_for_documents`,
    trước đó hàm này KHÔNG lọc gì cả, lộ tên/đường dẫn thư mục riêng tư dù
    trường `folders[]` đã lọc đúng).

    ⚠️ `user=None` → ĐÓNG (rỗng) — KHÁC `folders_for_documents` (hàm đó vẫn giữ
    `user=None` = "trả hết" cho những nơi gọi cũ). Hàm này viết lại từ đầu nên
    không mang theo nợ đó: không có người xem thì không có gì để tính "thấy
    được cái nào", thà rỗng còn hơn lộ.

    Thư mục CHÍNH không thấy được (mất Xem / bị khóa riêng tư) → KHÔNG hiện
    đường dẫn của nó. Rơi về thư mục ĐẦU TIÊN còn thấy được trong số các thư
    mục KHÁC của văn bản (ưu tiên thư mục chính nếu thấy; hết cả thì rỗng —
    không có thư mục nào thấy được thì không có gì để hiện).

    ⚠️ Ancestor bên trong breadcrumb của một thư mục ĐÃ CHỌN (vì thấy được) vẫn
    hiện đủ tên — rule 5 phase 04 ("thấy F thì thấy tên tổ tiên của F", để cây
    không gãy): không lọc lại từng mắt xích của MỘT thư mục đã qua cửa thấy
    được, chỉ chặn ở bước CHỌN thư mục nào để dựng breadcrumb.
    """
    if not document_ids or user is None:
        return {}
    from app.modules.doc_catalog import folder_access_service

    visible_ids = set(folder_access_service.effective_levels(db, user).keys())
    if not visible_ids:
        return {}

    #  MỌI liên kết (không chỉ CHÍNH) — cần để rơi về thư mục phụ còn thấy
    #  được. Sắp CHÍNH lên trước, trong mỗi văn bản theo `id` tăng dần (thư mục
    #  gắn SỚM nhất coi là "đầu tiên") — vẫn MỘT truy vấn cho cả trang.
    rows = (
        db.query(DocumentFolderLink.document_id, DocumentFolderLink.folder_id)
        .filter(DocumentFolderLink.document_id.in_(document_ids))
        .order_by(DocumentFolderLink.document_id,
                  DocumentFolderLink.is_primary.desc(), DocumentFolderLink.id.asc())
        .all()
    )
    if not rows:
        return {}

    chosen: dict[int, int] = {}
    for document_id, folder_id in rows:
        if document_id in chosen or folder_id not in visible_ids:
            continue
        chosen[document_id] = folder_id
    if not chosen:
        return {}

    from .folder_tree_service import breadcrumb_map

    crumbs = breadcrumb_map(db, set(chosen.values()))
    return {
        document_id: " / ".join(c["name"] for c in crumbs.get(folder_id, []))
        for document_id, folder_id in chosen.items()
    }


# ── Gắn / gỡ hàng loạt ─────────────────────────────────────────────────────
def move_documents(db: Session, doc_ids: list[int], folder_id: int, mode: str, user,
                   profile: dict, actor: int) -> dict:
    """Gắn hàng loạt văn bản vào MỘT thư mục. `mode`: `add` (cộng thêm) hoặc
    `replace` (thay hẳn danh sách thư mục hiện có bằng đúng thư mục này)."""
    from app.modules.document import access_service
    from app.modules.document.model import Document

    folder = db.get(DocFolder, folder_id)
    if not folder:
        raise HTTPException(404, "Không tìm thấy thư mục")
    folder_access_service.ensure_level(db, user, folder, int(FolderAccessLevel.CONTRIBUTE), profile)

    #  Nạp văn bản MỘT LƯỢT bằng `IN` (M5, rà soát 23/09/2026) — trước đó
    #  `db.get` từng dòng trong vòng lặp là một query riêng cho mỗi id; `mode`
    #  bị chặn ≤ `MAX_BULK_IDS` (schema) nên đây là MỘT truy vấn có trần.
    ids = list(dict.fromkeys(doc_ids or []))
    docs_by_id = {d.id: d for d in db.query(Document).filter(Document.id.in_(ids)).all()} if ids else {}

    moved: list[int] = []
    denied: list[dict] = []
    for doc_id in ids:
        doc = docs_by_id.get(doc_id)
        if not doc or not access_service.can(db, doc, user, profile, "write"):
            denied.append({"id": doc_id, "reason": "Không tìm thấy hoặc không có quyền"})
            continue
        try:
            if mode == LINK_MODE_REPLACE:
                folder_link_service.set_folders(db, doc, [folder_id], folder_id, actor, user=user)
            else:
                folder_link_service.add(db, doc, folder_id, actor)
            moved.append(doc_id)
        except HTTPException as exc:
            denied.append({"id": doc_id, "reason": exc.detail})

    for doc_id in moved:
        record(db, actor, "document", doc_id, "update", f"Gắn vào thư mục {folder.name}")
    return {"moved": moved, "denied": denied}


def bulk_unlink(db: Session, doc_ids: list[int], folder_id: int, user, profile: dict,
                actor: int) -> dict:
    from app.modules.document import access_service
    from app.modules.document.model import Document

    folder = db.get(DocFolder, folder_id)
    if not folder:
        raise HTTPException(404, "Không tìm thấy thư mục")
    folder_access_service.ensure_level(db, user, folder, int(FolderAccessLevel.CONTRIBUTE), profile)

    #  Nạp văn bản MỘT LƯỢT bằng `IN` — cùng lý do với `move_documents` (M5).
    ids = list(dict.fromkeys(doc_ids or []))
    docs_by_id = {d.id: d for d in db.query(Document).filter(Document.id.in_(ids)).all()} if ids else {}

    moved: list[int] = []
    denied: list[dict] = []
    for doc_id in ids:
        doc = docs_by_id.get(doc_id)
        if not doc or not access_service.can(db, doc, user, profile, "write"):
            denied.append({"id": doc_id, "reason": "Không tìm thấy hoặc không có quyền"})
            continue
        folder_link_service.remove(db, doc, folder_id, actor)
        moved.append(doc_id)

    for doc_id in moved:
        record(db, actor, "document", doc_id, "update", f"Gỡ khỏi thư mục {folder.name}")
    return {"moved": moved, "denied": denied}
