import hashlib

from sqlalchemy.orm import Session

from app.core.file_registry import direct_policy, ext_of
from app.core.images import THUMBABLE_EXTS, make_thumb
from app.core.storage import dated_key, delete_key, upload_fileobj
from app.core.upload_guard import guard_upload

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


def create_stored_file(db: Session, *, fileobj, filename: str, kind: str,
                       category: str, actor_id: int,
                       thumb_max_edge: int = 1280) -> StoredFile:
    """Tải 1 tệp lên storage + tạo dòng tab_file ĐỘC LẬP (không FileLink).
    Dùng cho ảnh đại diện: 1 file = 1 người, quản lý/xóa trực tiếp qua avatar_file_id.

    `kind` là khóa trong `DIRECT_FILE_POLICY`. Trước bao-CR-408 hàm này **không kiểm
    một thứ gì**: không đuôi, không dung lượng, không nội dung — đó mới là lỗ thật của
    BM-026, chứ không phải mấy controller gọi nó. Nay mọi luật đi qua `guard_upload`,
    và `content_type` do NỘI DUNG quyết định chứ không còn nhận từ bên gọi (BM-028).
    """
    exts, max_mb = direct_policy(kind)
    content_type, size = guard_upload(filename=filename, fileobj=fileobj,
                                      exts=exts, max_mb=max_mb)
    digest = _sha256_of(fileobj)
    sf = StoredFile(filename=filename, file_key="", url="", content_type=content_type,
                    size=size, sha256=digest, created_by=actor_id, updated_by=actor_id)
    db.add(sf); db.flush()  # lấy id để đặt key có cấu trúc {env}/{category}/{năm}/{tháng}/{id}-tên
    key = dated_key(category, filename, sf.id)
    thumb = make_thumb_for(filename, fileobj, max_edge=thumb_max_edge)
    url = upload_fileobj(fileobj, key, content_type)
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


#  ---- CHỦ SỞ HỮU tệp khi gắn dây (bao-CR-408 — BM-025) -------------------------
#
#  `POST /api/attachments/register` nhận `file_ids` rồi tạo `FileLink` mà **không hỏi
#  tệp của ai**: chỉ cần `db.get(StoredFile, fid)` ra một dòng là gắn. Nghĩa là một tài
#  khoản thường đoán id tệp của người khác, gắn vào một phiếu của chính mình, rồi mở
#  phiếu đó ra đọc — đọc được mọi tệp trong hệ thống. `ticket/service._register_files`
#  chép nguyên lỗi đó.
#
#  Luật đúng đã có sẵn trong mã từ lâu ở `comment/service.attach_files` và
#  `forum/service.attach_files`: tệp phải do CHÍNH người đang thao tác tải lên, và
#  chưa có dây nào. Hai hàm dưới đây là luật ấy tách ra để cả bốn cửa gọi chung.
def own_file_ids(db: Session, file_ids, user_id: int) -> set[int]:
    """Trong `file_ids`, những id là tệp DO CHÍNH `user_id` tải lên (id lạ rơi ra)."""
    ids = [int(i) for i in dict.fromkeys(file_ids or [])]
    if not ids:
        return set()
    return {fid for (fid,) in db.query(StoredFile.id)
            .filter(StoredFile.id.in_(ids), StoredFile.created_by == user_id).all()}


def linked_file_ids(db: Session, file_ids) -> set[int]:
    """Trong `file_ids`, những id ĐÃ có ít nhất một dây (đã gắn vào đâu đó rồi)."""
    ids = [int(i) for i in dict.fromkeys(file_ids or [])]
    if not ids:
        return set()
    return {fid for (fid,) in db.query(FileLink.file_id)
            .filter(FileLink.file_id.in_(ids)).all()}


def select_attachable_ids(db: Session, file_ids, user_id: int) -> list[int]:
    """Id gắn được: của chính mình VÀ chưa có dây. Giữ nguyên thứ tự người gửi.

    Dùng cho những cửa gắn tệp ÂM THẦM bỏ qua id hỏng (bình luận, diễn đàn, phiếu hỗ
    trợ) — ở đó tệp đi kèm lúc tạo bản ghi, ném lỗi giữa chừng là hỏng cả bản ghi.
    """
    owned = own_file_ids(db, file_ids, user_id)
    linked = linked_file_ids(db, file_ids)
    return [int(i) for i in dict.fromkeys(file_ids or []) if int(i) in owned and int(i) not in linked]


#  ---- Tệp MỒ CÔI của cửa tải lên trần (bao-CR-408 — BM-031) --------------------
#
#  `POST /api/attachments/upload-file` tạo `tab_file` TRƯỚC khi bản ghi cha có id;
#  `/register` gắn dây sau. Người dùng bỏ dở form giữa chừng thì tệp nằm lại **vĩnh
#  viễn**: `_delete_file_if_orphan` chỉ chạy khi có ai XÓA MỘT DÂY, mà tệp chưa từng
#  có dây thì không có nhịp nào chạm tới nó.
#
#  Hai chốt, một cho hiện tại một cho quá khứ:
#   - `ensure_orphan_quota` — chặn ngay tại cửa, một tài khoản không thể bơm vô hạn;
#   - `purge_orphan_files` — việc định kỳ dọn tệp mồ côi quá hạn (xem `tasks.py`).
ORPHAN_KEEP_DAYS = 7
MAX_PENDING_ORPHANS = 50

#  Chỉ đụng tệp của khâu ĐÍNH KÈM. `dated_key` sinh `{env}/attachment/{năm}/{tháng}/...`
#  nên dấu này tách chúng khỏi ảnh đại diện, tệp trợ lý, gói xuất báo cáo — mấy loại
#  đó không có `FileLink` theo thiết kế, dọn theo là xóa nhầm.
_ATTACHMENT_KEY_MARK = "/attachment/"


def _orphan_query(db: Session):
    """Các `tab_file` của khâu đính kèm mà KHÔNG có dây nào trỏ tới."""
    linked = db.query(FileLink.file_id).filter(FileLink.file_id == StoredFile.id)
    return (db.query(StoredFile)
            .filter(StoredFile.file_key.like(f"%{_ATTACHMENT_KEY_MARK}%"))
            .filter(~linked.exists()))


def count_pending_orphans(db: Session, user_id: int) -> int:
    """Số tệp người này đã tải lên mà chưa gắn vào bản ghi nào."""
    return _orphan_query(db).filter(StoredFile.created_by == user_id).count()


def ensure_orphan_quota(db: Session, user_id: int) -> None:
    """Chặn cửa tải lên trần khi người dùng còn quá nhiều tệp chưa gắn (BM-031).

    Ném `HTTPException` 429 — đây là trần nhịp độ, không phải lỗi dữ liệu. Người dùng
    bình thường không bao giờ chạm tới: 50 tệp treo cùng lúc nghĩa là bỏ dở vài chục
    cái form liên tiếp mà chưa lần nào lưu.
    """
    from fastapi import HTTPException
    if count_pending_orphans(db, user_id) >= MAX_PENDING_ORPHANS:
        raise HTTPException(
            429, f"Bạn đang có quá {MAX_PENDING_ORPHANS} tệp đã tải lên nhưng chưa gắn vào phiếu nào. "
                 "Hãy lưu hoặc hủy bớt phiếu đang soạn dở rồi thử lại.")


def purge_orphan_files(db: Session, keep_days: int = ORPHAN_KEEP_DAYS) -> int:
    """Xóa hẳn tệp đính kèm mồ côi cũ hơn `keep_days` ngày. Trả số tệp đã xóa."""
    from datetime import datetime, timedelta
    cutoff = datetime.now() - timedelta(days=keep_days)
    rows = _orphan_query(db).filter(StoredFile.created_at < cutoff).all()
    for f in rows:
        _delete_storage_of(f)
        db.delete(f)
    if rows:
        db.commit()
    return len(rows)


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
