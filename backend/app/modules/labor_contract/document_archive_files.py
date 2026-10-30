"""Gương TỆP của HĐLĐ sang bản lưu trữ ở phân hệ Văn bản (duoc-CR-629).

Phiên bản hiện hành của văn bản lưu trữ luôn giữ đúng {bản sao tệp .docx đã sinh, bản sao bản ký}
của HĐ — nhiều hơn / ít hơn thì chỉnh lại. So bằng `sha256` nên chạy lại bao nhiêu lần cũng không
sinh bản trùng.

duoc-CR-640: văn bản lưu trữ SỬA ĐƯỢC (kể cả tải thêm "file mềm"), nên đồng bộ chỉ quản lý các bản sao do
CHÍNH NÓ tạo — đánh dấu bằng `FileLink.doc_type = SYNC_MARK` (bản sao tạo trước CR-640 chưa có dấu thì nhận ra
qua thư mục lưu `labor-contract-archive`). Tệp người dùng tải lên KHÔNG bao giờ bị đụng. Người dùng tạo phiên
bản mới ⇒ phiên bản mới chép liên kết (dùng chung tệp), bản cũ giữ nguyên bộ tệp; đồng bộ chỉ chỉnh phiên bản hiện
hành và dùng lại bản sao có sẵn ở phiên bản khác khi cần. Người dùng xóa một bản sao ở Văn bản ⇒
lần đồng bộ kế tiếp có thể thêm lại (chủ ý: văn bản luôn phản ánh tệp hiện có của HĐ).

CHÉP byte sang `tab_file` MỚI (không dùng chung `file_id`): `delete_stored_file` không soi
`FileLink`, nên dùng chung thì lần sinh lại / thay bản ký ở Nhân sự sẽ xóa luôn tệp bên Văn bản.
Byte của bản sao cũ chỉ xóa SAU khi commit.
"""
import hashlib
import logging

from sqlalchemy.orm import Session

from app.modules.attachment.model import FileLink, StoredFile
from app.modules.document.model import Document
from app.modules.document.service import ATTACH_ENTITY
from app.modules.document.version_model import DocumentVersion

from .file_response import delete_files_after_commit, discard_new_file, load_bytes, store_bytes
from .model import LaborContract

log = logging.getLogger("app.labor_contract")

ARCHIVE_CATEGORY = "labor-contract-archive"
#  Dấu "bản sao do đồng bộ tạo" trên `tab_file_link.doc_type` (cột chữ 50 ký tự, văn bản không dùng cho việc khác).
SYNC_MARK = "hdld_sync"
#  (cột file_id của HĐ, sort_order hiển thị): tệp sinh trước, bản ký sau.
_SOURCES = (("generated_file_id", 0), ("signed_file_id", 1))


def _sha_of(db: Session, sf: StoredFile) -> str:
    """sha256 đã lưu ở `tab_file`; tệp cũ chưa có thì băm từ byte."""
    if sf.sha256:
        return sf.sha256
    _, data = load_bytes(db, sf.id)
    return hashlib.sha256(data).hexdigest()


def is_sync_copy(link: FileLink, stored: StoredFile) -> bool:
    """Liên kết tệp này là bản sao do đồng bộ tạo (có dấu, hoặc bản cũ tạo trước CR-640 nằm ở thư mục lưu riêng)."""
    if link.doc_type == SYNC_MARK:
        return True
    return not link.doc_type and f"/{ARCHIVE_CATEGORY}/" in (stored.file_key or "")


def mirror(db: Session, contract: LaborContract, doc: Document, actor_id: int) -> None:
    """Đưa phiên bản hiện hành của `doc` về đúng bộ tệp của `contract`. Commit bên trong."""
    version_id = doc.current_version_id
    if not version_id:
        return

    wanted: dict[str, tuple[StoredFile, int]] = {}   # sha256 -> (tệp gốc, sort_order)
    for column, sort_order in _SOURCES:
        fid = getattr(contract, column) or 0
        sf = db.get(StoredFile, fid) if fid else None
        if sf is not None and sf.file_key:
            wanted.setdefault(_sha_of(db, sf), (sf, sort_order))

    #  Chỉ bản sao do đồng bộ tạo. Tạo phiên bản mới CHÉP LIÊN KẾT (dùng chung file_id) sang bản mới, bản cũ giữ
    #  nguyên bộ tệp lúc duyệt ⇒ chỉ chỉnh các liên kết ở phiên bản HIỆN HÀNH; phiên bản khác chỉ là nguồn để dùng lại.
    rows = [(link, stored) for link, stored in
            db.query(FileLink, StoredFile)
            .join(StoredFile, StoredFile.id == FileLink.file_id)
            .join(DocumentVersion, DocumentVersion.id == FileLink.entity_id)
            .filter(FileLink.entity == ATTACH_ENTITY, DocumentVersion.document_id == doc.id).all()
            if is_sync_copy(link, stored)]
    have: dict[str, list[tuple[FileLink, StoredFile]]] = {}
    elsewhere: dict[str, StoredFile] = {}          # sha -> bản sao đã có ở phiên bản khác
    for link, stored in rows:
        sha = _sha_of(db, stored)
        if link.entity_id == version_id:
            have.setdefault(sha, []).append((link, stored))
        else:
            elsewhere.setdefault(sha, stored)

    removed_file_ids: list[int] = []
    for sha, pairs in have.items():
        #  Không còn mong muốn → gỡ hết; còn mong muốn mà trùng → giữ đúng 1 cái.
        keep = 1 if sha in wanted else 0
        for link, stored in pairs[keep:]:
            removed_file_ids.append(stored.id)
            db.delete(link)
    db.flush()
    #  Chỉ xóa tệp khi KHÔNG còn liên kết nào (phiên bản cũ có thể còn dùng chung).
    #  Đọc KHÓA (FOR UPDATE) để hai lượt đồng bộ song song không cùng thấy "hết liên kết" rồi cùng xóa tệp.
    stale_file_ids = [fid for fid in dict.fromkeys(removed_file_ids)
                      if db.query(FileLink.id).filter(FileLink.file_id == fid).with_for_update().first() is None]

    created: list[StoredFile] = []
    try:
        for sha, (source, sort_order) in wanted.items():
            if sha in have:
                continue
            if sha in elsewhere:      # bản sao đã có ở phiên bản khác: gắn thêm liên kết, không chép lại byte
                file_id = elsewhere[sha].id
            else:
                _, data = load_bytes(db, source.id)
                copy = store_bytes(db, data, source.filename, _kind_of(contract, source), ARCHIVE_CATEGORY,
                                   actor_id)
                created.append(copy)
                file_id = copy.id
            db.add(FileLink(file_id=file_id, entity=ATTACH_ENTITY, entity_id=version_id, doc_type=SYNC_MARK,
                            sort_order=sort_order, created_by=actor_id, updated_by=actor_id))
        db.commit()
    except Exception:
        db.rollback()
        for copy in created:
            discard_new_file(copy)
        raise
    if stale_file_ids:
        _drop_copies(db, stale_file_ids)


def _kind_of(contract: LaborContract, source: StoredFile) -> str:
    """`kind` của chính chính sách tải lên mà tệp gốc đã qua (docx sinh / bản ký scan)."""
    from .generate_service import DOCX_KIND, SIGNED_KIND
    return DOCX_KIND if source.id == contract.generated_file_id else SIGNED_KIND


def _drop_copies(db: Session, file_ids: list[int]) -> None:
    """Xóa dòng `tab_file` + byte của bản sao cũ — SAU commit, lỗi chỉ để lại tệp mồ côi."""
    delete_files_after_commit(db, *file_ids)


def drop_all(db: Session, doc: Document) -> None:
    """Gỡ các bản sao do đồng bộ tạo (không đụng tệp người dùng tải lên)."""
    if not doc.current_version_id:
        return
    rows = [(link, stored) for link, stored in
            db.query(FileLink, StoredFile).join(StoredFile, StoredFile.id == FileLink.file_id)
            .join(DocumentVersion, DocumentVersion.id == FileLink.entity_id)
            .filter(FileLink.entity == ATTACH_ENTITY, DocumentVersion.document_id == doc.id).all()
            if is_sync_copy(link, stored)]
    ids = list(dict.fromkeys(stored.id for _, stored in rows))
    for link, _ in rows:
        db.delete(link)
    db.commit()
    if ids:
        _drop_copies(db, ids)
