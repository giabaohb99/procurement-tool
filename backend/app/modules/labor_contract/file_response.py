"""Tệp của HĐLĐ: lưu / đọc / xóa / trả về cho trình duyệt. Dùng chung cho Mẫu và HĐ.

Tệp nằm ở `tab_file` + cột `*_file_id`, KHÔNG qua `FileLink` ⇒ mọi đường tải phải đi qua endpoint
riêng đã `get_scoped`. Không bao giờ trả `url` / `file_key` của storage ra ngoài.
"""
import logging
import re
from io import BytesIO
from urllib.parse import quote

from fastapi import HTTPException, Response
from sqlalchemy.orm import Session

from app.core.storage import delete_key, download_bytes
from app.modules.attachment.model import StoredFile
from app.modules.attachment.service import create_stored_file, delete_stored_file

log = logging.getLogger("app.labor_contract")

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
_BAD_NAME_CHARS = re.compile(r'[\x00-\x1f\x7f/\\:*?"<>|]+')


def safe_filename(name: str, default: str = "tai-lieu", max_len: int = 150) -> str:
    """Tên tệp an toàn: bỏ ký tự điều khiển / đường dẫn (chặn header injection + path traversal)."""
    cleaned = _BAD_NAME_CHARS.sub("-", name or "").strip(" .-")
    if len(cleaned) > max_len:
        #  Cắt phần tên, GIỮ đuôi tệp (mất đuôi thì guard_upload báo «định dạng .? không được phép» khó hiểu).
        stem, dot, ext = cleaned.rpartition(".")
        ext = ext if dot and 0 < len(ext) <= 10 else ""
        keep = max_len - (len(ext) + 1 if ext else 0)
        cleaned = (stem if ext else cleaned)[:keep].strip(" .-") + (f".{ext}" if ext else "")
    return cleaned or default


def store_bytes(db: Session, data: bytes, filename: str, kind: str, category: str,
                actor_id: int) -> StoredFile:
    """Lưu `data` thành tệp riêng (qua `guard_upload` của `create_stored_file`)."""
    return create_stored_file(db, fileobj=BytesIO(data), filename=safe_filename(filename, "tep"),
                              kind=kind, category=category, actor_id=actor_id)


def discard_new_file(sf: StoredFile | None) -> None:
    """Dọn tệp VỪA đẩy lên storage khi giao dịch DB hỏng (dòng `tab_file` đã rollback theo)."""
    if sf is not None and sf.file_key:
        try:
            delete_key(sf.file_key)
        except Exception:  # why: dọn rác kiểu best-effort, tệp mồ côi vô hại
            log.warning("Không dọn được tệp mồ côi %s", sf.file_key)


def delete_files_after_commit(db: Session, *file_ids: int) -> None:
    """Xóa tệp CŨ — gọi SAU khi commit thành công. Lỗi ở đây chỉ để lại tệp mồ côi, không làm hỏng nghiệp vụ."""
    try:
        for fid in file_ids:
            delete_stored_file(db, fid)
        db.commit()
    except Exception:  # why: dọn rác kiểu best-effort
        db.rollback()
        log.warning("Không xóa được tệp cũ %s", file_ids)


def load_bytes(db: Session, file_id: int) -> tuple[StoredFile, bytes]:
    sf = db.get(StoredFile, file_id) if file_id else None
    if sf is None or not sf.file_key:
        raise HTTPException(404, "Không tìm thấy tệp")
    try:
        return sf, download_bytes(sf.file_key)
    except HTTPException:
        raise
    except Exception:  # why: R2/mạng lỗi → trả 502 rõ ràng thay vì 500 mã sự cố
        log.exception("Đọc tệp %s từ storage lỗi", sf.file_key)
        raise HTTPException(502, "Không đọc được tệp từ kho lưu trữ, thử lại sau")


def download_response(data: bytes, filename: str, media_type: str) -> Response:
    """Phản hồi tải về. Tên tệp luôn qua `safe_filename` + `quote` (RFC 5987)."""
    name = safe_filename(filename)
    return Response(content=data, media_type=media_type,
                    headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(name)}",
                             "Cache-Control": "private, no-store"})
