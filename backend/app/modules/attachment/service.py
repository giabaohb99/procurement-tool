from sqlalchemy.orm import Session

from app.core.storage import delete_key

from .model import FileLink, StoredFile


def _delete_file_if_orphan(db: Session, file_id: int):
    """Xóa StoredFile + file trên storage nếu không còn link nào dùng."""
    if db.query(FileLink).filter(FileLink.file_id == file_id).first():
        return
    f = db.get(StoredFile, file_id)
    if f:
        try:
            delete_key(f.file_key)
        except Exception:
            pass
        db.delete(f)


def delete_attachments_for(db: Session, pairs: list[tuple[str, int]]) -> int:
    """Xóa liên kết file (và file nếu không còn ai dùng) cho các cặp (entity, entity_id).
    Dùng khi xóa phiếu cha."""
    n = 0
    file_ids: set[int] = set()
    for entity, entity_id in pairs:
        links = db.query(FileLink).filter(
            FileLink.entity == entity, FileLink.entity_id == entity_id).all()
        for lk in links:
            file_ids.add(lk.file_id)
            db.delete(lk)
            n += 1
    db.flush()
    for fid in file_ids:
        _delete_file_if_orphan(db, fid)
    if n or file_ids:
        db.commit()
    return n
