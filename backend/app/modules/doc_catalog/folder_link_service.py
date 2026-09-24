"""Gắn/gỡ văn bản vào thư mục — `tab_document_folder_link`.

Ba luật xuyên suốt tệp này (`plan.md` §"Luật phải giữ"):
  * mọi văn bản luôn có ≥ 1 thư mục — `ensure_not_orphan` là lưới đỡ cuối cùng;
  * đúng MỘT thư mục chính (`is_primary`) tại mọi thời điểm;
  * gắn văn bản phải qua **quyền sửa văn bản** (`document/access_service`) —
    quyền ĐÓNG GÓP của thư mục (phase 04) sẽ cộng thêm một cửa nữa, chưa có ở
    phase 03.
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from .folder_constants import FolderKind, FolderStatus
from .folder_link_model import DocumentFolderLink
from .folder_model import DocFolder


# ── Thư mục mặc định ──────────────────────────────────────────────────────
def _company_root_id(db: Session, company_id: int) -> int:
    """LẤY id gốc của công ty, TẠO LAZY nếu chưa có (rà soát 24/09/2026: gốc
    không còn tự sinh ở seed/tạo pháp nhân — chỉ sinh đúng lúc một văn bản cần
    nó, và CHỈ đúng công ty này, không hồi sinh gốc đã xóa của công ty khác)."""
    from .folder_root_service import get_or_create_company_root

    root = get_or_create_company_root(db, company_id)
    if not root:
        raise HTTPException(400, "Pháp nhân của văn bản không tồn tại, không tạo được thư mục lưu")
    return root.id


def resolve_default_for(db: Session, doc_type_id: int | None, company_id: int) -> int | None:
    """Thư mục dùng khi lưu văn bản mà KHÔNG chọn thư mục nào: ưu tiên
    `DocType.default_folder_id` (nếu còn dùng + đúng pháp nhân), sau đó mới
    rơi về thư mục pháp nhân.

    `company_id=0` (chưa gắn pháp nhân — vd đơn nghỉ phép của nhân sự chưa gắn
    công ty, `leave/approval_bridge.py`) → `None`, KHÔNG raise: không có gốc
    pháp nhân nào để rơi về, và văn bản mồ côi kiểu này là CỐ Ý (xem migration
    `e4a1c9d572b6`), không phải lỗi dữ liệu cần chặn (rà soát 23/09/2026, H3).

    Tách khỏi `resolve_default(db, doc)` để gọi được TRƯỚC khi văn bản có `id`
    — validate thư mục trước `db.add(doc)`.
    """
    if not company_id:
        return None
    from app.modules.doc_catalog.model import DocType

    doc_type = db.get(DocType, doc_type_id) if doc_type_id else None
    if doc_type and doc_type.default_folder_id:
        default_folder = db.get(DocFolder, doc_type.default_folder_id)
        if (default_folder and default_folder.status == int(FolderStatus.ACTIVE)
                and default_folder.company_id == company_id):
            return default_folder.id
    return _company_root_id(db, company_id)


def resolve_default(db: Session, doc) -> int | None:
    return resolve_default_for(db, doc.doc_type_id, doc.company_id)


# ── Gắn / gỡ MỘT văn bản ──────────────────────────────────────────────────
def validate_folder_for_company(db: Session, folder_id: int, company_id: int) -> DocFolder:
    """Kiểm một thư mục DÙNG ĐƯỢC cho văn bản của pháp nhân `company_id`
    không: tồn tại · đang ACTIVE. `company_id` giữ trong chữ ký cho nơi gọi cũ. Nhận thẳng `company_id`
    (không phải `doc`) để gọi được TRƯỚC khi văn bản có `id` (H3)."""
    folder = db.get(DocFolder, folder_id)
    if not folder:
        raise HTTPException(400, f"Không tìm thấy thư mục #{folder_id}")
    #  KHÔNG còn buộc cùng pháp nhân (đại ca chốt 24/09/2026: thư mục là chỗ
    #  người dùng tự sắp xếp, chuyển/gắn đâu tùy ý). Gắn vào thư mục không mở
    #  quyền đọc văn bản — `document/access_service` vẫn lọc như cũ.
    if folder.status != int(FolderStatus.ACTIVE):
        raise HTTPException(400, f"Thư mục «{folder.name}» đang ngừng dùng")
    return folder


def _validate_folder_for_doc(db: Session, folder_id: int, doc) -> DocFolder:
    return validate_folder_for_company(db, folder_id, doc.company_id)


def stage_folders(db: Session, doc, folder_ids: list[int] | None, primary_id: int | None,
                  actor: int, *, user=None) -> list[DocumentFolderLink]:
    """Đặt lại thư mục của một văn bản theo ĐÚNG những gì người gọi THẤY —
    CHỈ `flush`, không `commit` (dùng khi việc gắn thư mục phải nằm TRONG cùng
    transaction với thao tác khác, vd tạo văn bản: H3, rà soát 23/09/2026, lỗi
    ở bước nào cũng rollback sạch, không để lại văn bản mồ côi đã cấp số).
    `set_folders` bên dưới gọi hàm này rồi tự `commit` — dùng cho các đường
    gọi ĐỘC LẬP (`PUT /documents/{id}/folders`, gắn hàng loạt, …).

    Rỗng (và không có gì để giữ) → về thư mục mặc định; `company_id=0` mà
    không chọn thư mục nào → không thư mục nào cả (cố ý, xem
    `resolve_default_for`).

    `user` TÙY CHỌN — đường tạo TỰ ĐỘNG (`leave/approval_bridge.py`, …) chỉ có
    `actor: int`, không có người dùng thật để tính quyền, bỏ qua ba bước dưới
    (giữ nguyên hành vi cũ: ghi đè đúng bằng `folder_ids`). Có `user` thì
    (code-reviewer C1):
      1. Liên kết cũ tới thư mục người gọi KHÔNG THẤY (ACL cấm / khác phạm vi)
         → GIỮ NGUYÊN dù không có trong `folder_ids` — form chỉnh sửa chỉ hiện
         những gì người dùng thấy nên "gửi lại đúng danh sách đang thấy" không
         phải là "tôi muốn gỡ phần còn lại" (cùng bài học `pickWritableProfile`,
         CR-315).
      2. GỠ một thư mục người gọi THẤY nhưng CHƯA đạt mức Đóng góp → 403, không
         âm thầm bỏ qua.
      3. Thư mục CHÍNH đang ẩn với người gọi thì GIỮ NGUYÊN làm chính, trừ khi
         người gọi chọn thẳng một thư mục KHÁC (đang thấy) làm chính.
    """
    ids = list(dict.fromkeys(fid for fid in (folder_ids or []) if fid))
    if not ids:
        default_id = resolve_default(db, doc)
        ids = [default_id] if default_id is not None else []
    for fid in ids:
        _validate_folder_for_doc(db, fid, doc)

    existing_rows = db.query(DocumentFolderLink).filter(
        DocumentFolderLink.document_id == doc.id).all()
    existing_ids = {row.folder_id for row in existing_rows}
    existing_primary_id = next((row.folder_id for row in existing_rows if row.is_primary), None)

    hidden_keep_ids: set[int] = set()
    if user is not None and existing_ids:
        from app.core.auth import get_perm_profile

        from . import folder_access_service
        from .folder_constants import FolderAccessLevel

        profile = get_perm_profile(db, user)
        visible = folder_access_service.effective_levels(db, user, profile)
        hidden_keep_ids = existing_ids - set(visible)
        removed_visible_ids = existing_ids - set(ids) - hidden_keep_ids
        for fid in removed_visible_ids:
            if visible.get(fid, 0) < int(FolderAccessLevel.CONTRIBUTE):
                folder = db.get(DocFolder, fid)
                name = folder.name if folder else f"#{fid}"
                raise HTTPException(
                    403,
                    f"Cần quyền Đóng góp trở lên trên thư mục «{name}» mới gỡ được "
                    "văn bản khỏi đó")

    final_ids = list(dict.fromkeys([*ids, *(fid for fid in existing_ids if fid in hidden_keep_ids)]))

    if primary_id is not None and primary_id in ids:
        primary = primary_id
    elif existing_primary_id is not None and existing_primary_id in hidden_keep_ids:
        primary = existing_primary_id
    elif ids:
        primary = ids[0]
    else:
        primary = final_ids[0] if final_ids else None

    db.query(DocumentFolderLink).filter(DocumentFolderLink.document_id == doc.id).delete(
        synchronize_session=False)
    rows = [
        DocumentFolderLink(document_id=doc.id, folder_id=fid, is_primary=(fid == primary),
                           created_by=actor)
        for fid in final_ids
    ]
    db.add_all(rows)
    db.flush()
    return rows


def set_folders(db: Session, doc, folder_ids: list[int] | None, primary_id: int | None,
                actor: int, *, user=None) -> list[DocumentFolderLink]:
    """Như `stage_folders` nhưng `commit` ngay — dùng cho các đường gọi ĐỘC
    LẬP (không nằm giữa một transaction lớn hơn của module gọi)."""
    rows = stage_folders(db, doc, folder_ids, primary_id, actor, user=user)
    db.commit()
    for row in rows:
        db.refresh(row)
    return rows


def add(db: Session, doc, folder_id: int, actor: int) -> DocumentFolderLink:
    folder = _validate_folder_for_doc(db, folder_id, doc)
    existing = db.query(DocumentFolderLink).filter(
        DocumentFolderLink.document_id == doc.id, DocumentFolderLink.folder_id == folder.id).first()
    if existing:
        return existing
    has_primary = db.query(DocumentFolderLink.id).filter(
        DocumentFolderLink.document_id == doc.id, DocumentFolderLink.is_primary.is_(True)).first()
    row = DocumentFolderLink(document_id=doc.id, folder_id=folder.id,
                             is_primary=not bool(has_primary), created_by=actor)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def remove(db: Session, doc, folder_id: int, actor: int) -> None:
    row = db.query(DocumentFolderLink).filter(
        DocumentFolderLink.document_id == doc.id, DocumentFolderLink.folder_id == folder_id).first()
    if not row:
        return
    was_primary = row.is_primary
    db.delete(row)
    db.flush()
    if was_primary:
        #  Còn thư mục khác thì dòng CŨ NHẤT lên làm chính — đơn giản, ổn định,
        #  không bắt người dùng chọn lại ngay lập tức.
        nxt = (db.query(DocumentFolderLink)
               .filter(DocumentFolderLink.document_id == doc.id)
               .order_by(DocumentFolderLink.id.asc()).first())
        if nxt:
            nxt.is_primary = True
    db.commit()
    ensure_not_orphan(db, doc, actor)


def ensure_not_orphan(db: Session, doc, actor: int = 0) -> None:
    """Gỡ thư mục cuối cùng → tự quay về thư mục PHÁP NHÂN (không phải mặc
    định theo loại — luật «không mồ côi» chỉ hứa đúng một chỗ hạ cánh chắc
    chắn luôn tồn tại).

    `company_id=0` → bỏ qua: không có gốc pháp nhân nào để rơi về, và mồ côi
    kiểu này là CỐ Ý (H3, rà soát 23/09/2026 — xem `resolve_default_for`)."""
    has_any = db.query(DocumentFolderLink.id).filter(
        DocumentFolderLink.document_id == doc.id).first()
    if has_any or not doc.company_id:
        return
    root_id = _company_root_id(db, doc.company_id)
    db.add(DocumentFolderLink(document_id=doc.id, folder_id=root_id, is_primary=True,
                              created_by=actor))
    db.commit()


def on_company_change(db: Session, doc, old_company_id: int, actor: int) -> None:
    """Đổi pháp nhân mà văn bản CHỈ đang ở thư mục pháp nhân CŨ → chuyển sang
    thư mục pháp nhân MỚI. Văn bản đã có thư mục thường tự chọn thì GIỮ
    NGUYÊN — không đoán người dùng muốn gì với những thư mục đó."""
    if not old_company_id or old_company_id == doc.company_id or not doc.company_id:
        return
    links = db.query(DocumentFolderLink).filter(DocumentFolderLink.document_id == doc.id).all()
    if len(links) != 1:
        return
    old_root = (
        db.query(DocFolder)
        .filter(DocFolder.company_id == old_company_id, DocFolder.kind == int(FolderKind.COMPANY))
        .first()
    )
    if not old_root or links[0].folder_id != old_root.id:
        return
    links[0].folder_id = _company_root_id(db, doc.company_id)
    links[0].is_primary = True
    db.commit()


#  Đọc HÀNG LOẠT cho serializer (`folders_for_documents`, `primary_folder_path_for_documents`)
#  và gắn/gỡ HÀNG LOẠT (nhiều văn bản × một thư mục) chuyển sang
#  `folder_link_bulk_service.py` — tách khỏi tệp này để giữ dưới 200 dòng.
