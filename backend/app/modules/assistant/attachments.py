"""Tệp đính kèm chat Trợ lý AI (CR-204): nhận ảnh chụp màn hình / PDF để model phân tích.

Khuôn lưu trữ giống `export_tool` (StoredFile + key `assistant-upload/`), nhưng chiều NGƯỢC
lại: người dùng tải LÊN, nội dung được nhét vào lượt gọi model dạng block base64. Quyền là
quyền SỞ HỮU — chỉ chính chủ (created_by) gắn được tệp vào tin của mình; key phải nằm trong
thư mục `assistant-upload/` để id tệp ở nơi khác (đính kèm chứng từ...) không lấy được.

Loại tệp nhận diện theo MAGIC BYTES chứ không tin content-type client gửi — đổi đuôi .exe
thành .png cũng không lọt.
"""
import base64
from io import BytesIO

from sqlalchemy.orm import Session

from app.core.storage import dated_key, download_bytes, safe_name, upload_fileobj
from app.modules.attachment.model import StoredFile

KEY_CATEGORY = "assistant-upload"
# Dấu nhận diện trong file_key khi kiểm quyền (dated_key sinh {env}/{category}/...).
KEY_MARK = "/assistant-upload/"

MB = 1024 * 1024
# Trần dung lượng theo loại: ảnh 5MB, PDF 10MB — file to quá thì TỪ CHỐI nhận
# (thỏa thuận CR-204), không nén/hạ chất lượng hộ.
SIZE_LIMITS: dict[str, int] = {
    "image/jpeg": 5 * MB,
    "image/png": 5 * MB,
    "image/webp": 5 * MB,
    "application/pdf": 10 * MB,
}
MAX_UPLOAD_BYTES = max(SIZE_LIMITS.values())
MAX_FILES_PER_MESSAGE = 3


def detect_type(data: bytes) -> str | None:
    """Loại tệp theo magic bytes. Không thuộc 4 loại cho phép -> None."""
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    if data.startswith(b"%PDF"):
        return "application/pdf"
    return None


def store_upload(db: Session, user, filename: str, data: bytes) -> dict:
    """Kiểm loại + trần dung lượng rồi lưu MỘT tệp; trả metadata cho FE gắn vào tin.

    Ném ValueError với thông điệp tiếng Việt khi từ chối — endpoint đổi thành 400.
    """
    if not data:
        raise ValueError("Tệp rỗng")
    ctype = detect_type(data)
    if ctype is None:
        raise ValueError("Chỉ nhận ảnh JPG/PNG/WebP hoặc PDF")
    limit = SIZE_LIMITS[ctype]
    if len(data) > limit:
        kind = "PDF" if ctype == "application/pdf" else "Ảnh"
        raise ValueError(f"{kind} tối đa {limit // MB}MB — tệp này {len(data) / MB:.1f}MB")

    #  Tạo bản ghi trước (flush lấy id) để đặt key theo cấu trúc chung của storage —
    #  giống hệt export_tool / _store_one của module attachment.
    sf = StoredFile(filename=safe_name(filename), file_key="", url="", content_type=ctype,
                    size=len(data), created_by=user.id, updated_by=user.id)
    db.add(sf)
    db.flush()
    key = dated_key(KEY_CATEGORY, sf.filename, sf.id)
    upload_fileobj(BytesIO(data), key, ctype)
    sf.file_key = key
    db.commit()
    return {"id": sf.id, "filename": sf.filename, "content_type": ctype, "size": sf.size}


def resolve_owned(db: Session, user, ids: list[int]) -> list[StoredFile]:
    """Đổi danh sách id thành StoredFile — CHẶN tệp không phải của mình / không phải
    tệp chat (key ngoài `assistant-upload/`). Sai bất kỳ id nào là chặn cả lượt."""
    if not ids:
        return []
    if len(ids) > MAX_FILES_PER_MESSAGE:
        raise ValueError(f"Tối đa {MAX_FILES_PER_MESSAGE} tệp mỗi tin")
    files: list[StoredFile] = []
    for fid in dict.fromkeys(ids):  # bỏ id trùng, giữ thứ tự
        f = db.get(StoredFile, fid)
        if not f or f.created_by != user.id or KEY_MARK not in (f.file_key or ""):
            raise PermissionError("Không tìm thấy tệp đính kèm")
        files.append(f)
    return files


def build_blocks(files: list[StoredFile]) -> list[dict]:
    """Đọc nội dung từ storage, đóng thành block TRUNG LẬP cho tầng provider.

    Hình dạng block: {type: "file", media_type, data_b64, filename} — Claude đổi thành
    image/document base64, Gemini đổi thành inline_data (xem provider/claude.py, gemini.py).
    """
    return [
        {
            "type": "file",
            "media_type": f.content_type or "application/octet-stream",
            "data_b64": base64.b64encode(download_bytes(f.file_key)).decode("ascii"),
            "filename": f.filename,
        }
        for f in files
    ]


def meta_of(files: list[StoredFile]) -> list[dict]:
    """Metadata gọn để LƯU vào tin nhắn (JSON) + trả cho FE vẽ chip tệp."""
    return [
        {"id": f.id, "filename": f.filename, "content_type": f.content_type, "size": f.size}
        for f in files
    ]


def placeholder_text(meta: list[dict]) -> str:
    """Dòng thế chỗ cho tin CŨ khi nạp lại lịch sử — giữ ngữ cảnh 'từng gửi tệp gì'
    mà không tốn token nạp lại nguyên tệp."""
    names = ", ".join(str(m.get("filename") or "tệp") for m in meta)
    return f"[Đã gửi kèm tệp: {names}]"
