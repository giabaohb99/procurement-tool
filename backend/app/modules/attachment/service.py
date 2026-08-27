import hashlib

from sqlalchemy.orm import Session

from app.core.file_registry import ext_of
from app.core.images import THUMBABLE_EXTS, make_thumb
from app.core.storage import dated_key, delete_key, upload_fileobj

from .model import FileLink, StoredFile


def make_thumb_for(filename: str, fileobj, *, max_edge: int = 1280):
    """Sinh bản thumbnail trong RAM. PHẢI gọi TRƯỚC khi upload bản gốc:
    boto3 `upload_fileobj` ĐÓNG fileobj khi đẩy xong, gọi sau là chỉ còn
    luồng chết và make_thumb lặng lẽ trả None (không thumb nào được sinh)."""
    if ext_of(filename or "") not in THUMBABLE_EXTS:
        return None
    return make_thumb(fileobj, max_edge=max_edge)


def attach_thumb(sf: StoredFile, thumb):
    """Tải bản thumbnail đã sinh sẵn lên storage, cạnh bản gốc (chưa commit).
    Mọi lỗi nuốt trong im lặng — thiếu thumb thì bên đọc fallback về `url`,
    không được vì thumb mà hỏng cú upload."""
    if not thumb:
        return
    key = f"{sf.file_key}.thumb.jpg"
    try:
        sf.thumb_url = upload_fileobj(thumb, key, "image/jpeg")
        sf.thumb_key = key
    except Exception:
        pass


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
                       category: str, actor_id: int,
                       thumb_max_edge: int = 1280) -> StoredFile:
    """Tải 1 tệp lên storage + tạo dòng tab_file ĐỘC LẬP (không FileLink).
    Dùng cho ảnh đại diện: 1 file = 1 người, quản lý/xóa trực tiếp qua avatar_file_id."""
    fileobj.seek(0, 2); size = fileobj.tell(); fileobj.seek(0)
    digest = _sha256_of(fileobj)
    sf = StoredFile(filename=filename, file_key="", url="", content_type=content_type or "",
                    size=size, sha256=digest, created_by=actor_id, updated_by=actor_id)
    db.add(sf); db.flush()  # lấy id để đặt key có cấu trúc {env}/{category}/{năm}/{tháng}/{id}-tên
    key = dated_key(category, filename, sf.id)
    thumb = make_thumb_for(filename, fileobj, max_edge=thumb_max_edge)
    url = upload_fileobj(fileobj, key, content_type or "")
    sf.file_key = key; sf.url = url
    attach_thumb(sf, thumb)
    db.flush()
    return sf


def delete_stored_file(db: Session, file_id: int):
    """Xóa hẳn 1 tab_file + file trên storage. Dùng cho ảnh đại diện cũ (không đi qua
    FileLink nên không cần kiểm mồ côi như đính kèm phiếu)."""
    if not file_id:
        return
    f = db.get(StoredFile, file_id)
    if f:
        _delete_storage_of(f)
        db.delete(f)


def _delete_storage_of(f: StoredFile):
    """Xóa tệp gốc + bản thumbnail (nếu có) trên storage."""
    for key in (f.file_key, f.thumb_key):
        if not key:
            continue
        try:
            delete_key(key)
        except Exception:
            pass


def _delete_file_if_orphan(db: Session, file_id: int):
    """Xóa StoredFile + file trên storage nếu không còn link nào dùng."""
    if db.query(FileLink).filter(FileLink.file_id == file_id).first():
        return
    f = db.get(StoredFile, file_id)
    if f:
        _delete_storage_of(f)
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
