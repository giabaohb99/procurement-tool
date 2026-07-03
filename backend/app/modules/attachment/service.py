from sqlalchemy.orm import Session

from app.core.storage import delete_key

from .model import Attachment


def delete_attachments_for(db: Session, pairs: list[tuple[str, int]]) -> int:
    """Xóa mọi file (DB + R2) của các cặp (entity, entity_id). Dùng khi xóa phiếu cha."""
    n = 0
    for entity, entity_id in pairs:
        rows = db.query(Attachment).filter(
            Attachment.entity == entity, Attachment.entity_id == entity_id).all()
        for a in rows:
            try:
                delete_key(a.file_key)
            except Exception:
                pass
            db.delete(a)
            n += 1
    if n:
        db.commit()
    return n
