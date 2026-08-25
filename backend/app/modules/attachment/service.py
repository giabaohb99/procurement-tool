import hashlib

from sqlalchemy.orm import Session

from app.core.storage import dated_key, delete_key, upload_fileobj

from .model import FileLink, StoredFile


def _sha256_of(fileobj) -> str:
    """Băm nội dung theo khối (tệp lớn không nằm hết trong RAM). Trả con trỏ về đầu
    để `upload_fileobj` ngay sau đọc lại đúng luồng — quên seek(0) là đẩy lên tệp rỗng."""
    h = hashlib.sha256()
    fileobj.seek(0)
    while chunk := fileobj.read(1024 * 1024):
        h.update(chunk)
    fileobj.seek(0)
    return h.hexdigest()


def create_stored_file(db: Session, *, fileobj, filename: str, content_type: str,
                       category: str, actor_id: int) -> StoredFile:
    """Tải 1 tệp lên storage + tạo dòng tab_file ĐỘC LẬP (không FileLink).
    Dùng cho ảnh đại diện: 1 file = 1 người, quản lý/xóa trực tiếp qua avatar_file_id."""
    fileobj.seek(0, 2); size = fileobj.tell(); fileobj.seek(0)
    digest = _sha256_of(fileobj)
    sf = StoredFile(filename=filename, file_key="", url="", content_type=content_type or "",
                    size=size, sha256=digest, created_by=actor_id, updated_by=actor_id)
    db.add(sf); db.flush()  # lấy id để đặt key có cấu trúc {env}/{category}/{năm}/{tháng}/{id}-tên
    key = dated_key(category, filename, sf.id)
    url = upload_fileobj(fileobj, key, content_type or "")
    sf.file_key = key; sf.url = url
    db.flush()
    return sf


def delete_stored_file(db: Session, file_id: int):
    """Xóa hẳn 1 tab_file + file trên storage. Dùng cho ảnh đại diện cũ (không đi qua
    FileLink nên không cần kiểm mồ côi như đính kèm phiếu)."""
    if not file_id:
        return
    f = db.get(StoredFile, file_id)
    if f:
        try:
            delete_key(f.file_key)
        except Exception:
            pass
        db.delete(f)


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
