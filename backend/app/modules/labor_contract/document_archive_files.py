"""Gương TỆP của HĐLĐ sang bản lưu trữ ở phân hệ Văn bản (duoc-CR-629).

Phiên bản hiện hành của văn bản lưu trữ luôn giữ đúng {bản sao tệp .docx đã sinh, bản sao bản ký}
của HĐ — nhiều hơn / ít hơn thì chỉnh lại. So bằng `sha256` nên chạy lại bao nhiêu lần cũng không
sinh bản trùng.

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

from .file_response import delete_files_after_commit, discard_new_file, load_bytes, store_bytes
from .model import LaborContract

log = logging.getLogger("app.labor_contract")

ARCHIVE_CATEGORY = "labor-contract-archive"
#  (cột file_id của HĐ, sort_order hiển thị): tệp sinh trước, bản ký sau.
_SOURCES = (("generated_file_id", 0), ("signed_file_id", 1))


def _sha_of(db: Session, sf: StoredFile) -> str:
    """sha256 đã lưu ở `tab_file`; tệp cũ chưa có thì băm từ byte."""
    if sf.sha256:
        return sf.sha256
    _, data = load_bytes(db, sf.id)
    return hashlib.sha256(data).hexdigest()


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

    existing = (db.query(FileLink, StoredFile)
                .join(StoredFile, StoredFile.id == FileLink.file_id)
                .filter(FileLink.entity == ATTACH_ENTITY, FileLink.entity_id == version_id).all())
    have: dict[str, list[tuple[FileLink, StoredFile]]] = {}
    for link, stored in existing:
        have.setdefault(_sha_of(db, stored), []).append((link, stored))

    stale_file_ids: list[int] = []
    for sha, pairs in have.items():
        #  Không còn mong muốn → gỡ hết; còn mong muốn mà trùng → giữ đúng 1 cái.
        keep = 1 if sha in wanted else 0
        for link, stored in pairs[keep:]:
            stale_file_ids.append(stored.id)
            db.delete(link)

    created: list[StoredFile] = []
    try:
        for sha, (source, sort_order) in wanted.items():
            if sha in have:
                continue
            _, data = load_bytes(db, source.id)
            copy = store_bytes(db, data, source.filename, _kind_of(contract, source), ARCHIVE_CATEGORY,
                               actor_id)
            created.append(copy)
            db.add(FileLink(file_id=copy.id, entity=ATTACH_ENTITY, entity_id=version_id,
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
    """Gỡ MỌI liên kết tệp của phiên bản hiện hành (không dùng ngoài script rollback)."""
    if not doc.current_version_id:
        return
    rows = (db.query(FileLink).filter(FileLink.entity == ATTACH_ENTITY,
                                      FileLink.entity_id == doc.current_version_id).all())
    ids = [r.file_id for r in rows]
    for r in rows:
        db.delete(r)
    db.commit()
    if ids:
        _drop_copies(db, ids)
