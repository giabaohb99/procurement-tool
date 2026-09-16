"""Chốt chung cho MỌI cửa nhận tệp từ người dùng (bao-CR-408 — BM-027/028/030).

Trước CR này mỗi cửa tự chép một bộ luật khác nhau: `attachment/_store_one` kiểm đuôi
và dung lượng; `attachment/create_stored_file` (ảnh đại diện, chữ ký) KHÔNG kiểm gì
cả; Trung tâm HDSD tự khai một danh sách trắng **có cả `svg`**; hai cửa chữ ký chỉ hỏi
`content_type.startswith("image/")` — tức là tin **lời khai của máy khách**. Gom về một
hàm để khi cửa thứ năm mọc ra thì có sẵn chỗ mà gọi, thay vì lại quên đúng những thứ
bốn cửa kia đã quên.

Ba thứ hàm này làm mà trước đây không cửa nào làm:

- **Đọc byte đầu.** Đuôi khai là ảnh thì nội dung phải đúng là ảnh (BM-027). Đổi tên
  `payload.svg` thành `payload.png` không còn lọt, và `svg` cũng không còn nằm trong
  bất kỳ danh sách trắng nào.
- **Suy `content_type` từ đuôi tệp, không lấy lời khai** (BM-028). Chuỗi đó về sau
  thành `media_type` của hồi đáp `/view` và `ContentType` của đối tượng trên R2 —
  không được để người gửi tự đặt.
- **Chặn tên tệp quá dài ngay tại chốt, trả 422** (BM-030). `tab_file.filename` là
  `String(255)`; trước đây một cái tên 304 ký tự đi thẳng xuống DB rồi vỡ thành 500.

⚠️ Bài kiểm cho luật độ dài **không được** viết bằng cách ghi xuống DB: `test/backend`
chạy SQLite trong RAM, mà SQLite KHÔNG ép `VARCHAR(n)` — bài kiểm sẽ xanh giả (đúng
cái bẫy của `duoc-CR-316`). Kiểm thẳng ở tầng chốt này.
"""
from fastapi import HTTPException

from app.core.file_registry import ext_of

# `tab_file.filename` là String(255) — chặn ở đây thì được 422 có thông điệp,
# để lọt xuống DB thì được 500 không ai đọc nổi.
MAX_FILENAME_LEN = 255

# Trần số tệp mỗi lượt. `files: list[UploadFile]` trước đây nhận bao nhiêu cũng được.
# 20 là rộng rãi so với mọi màn đang chạy (nhiều nhất là ảnh sản phẩm, chục tấm).
MAX_FILES_PER_REQUEST = 20

# Số byte đầu cần đọc để nhận diện. Dài nhất là WebP (`RIFF` + `WEBP` ở byte 8-12)
# và MP4 (`ftyp` ở byte 4-8); 32 byte là dư.
_HEAD_BYTES = 32

#  Bảng MIME theo ĐUÔI TỆP. Đây là nguồn sự thật cho `content_type`, thay cho chuỗi
#  máy khách gửi lên. Đuôi lạ (không có trong bảng) → `application/octet-stream`:
#  trình duyệt tải về chứ không mở, đó là hành vi an toàn muốn có.
_MIME_BY_EXT: dict[str, str] = {
    "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
    "gif": "image/gif", "webp": "image/webp", "bmp": "image/bmp",
    "pdf": "application/pdf",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "xls": "application/vnd.ms-excel",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "doc": "application/msword",
    "txt": "text/plain", "csv": "text/csv", "xml": "application/xml",
    "msg": "application/vnd.ms-outlook", "eml": "message/rfc822",
    "cdr": "application/x-coreldraw",
    "mp4": "video/mp4", "webm": "video/webm",
}

#  Đuôi nào BẮT BUỘC nội dung phải khớp. Cố ý CHỈ gồm ảnh, PDF và video — đúng những
#  loại mà trình duyệt tự mở, tức là những loại đẻ ra XSS/lừa đảo nếu nội dung nói dối.
#  Không xét .doc/.xls/.docx/.xlsx: ngoài đời đầy tệp `.doc` thật ra là RTF hoặc HTML
#  do Word đời cũ xuất ra, siết vào là chặn nhầm người dùng thật mà chẳng được gì —
#  mấy loại đó không bao giờ được hiển thị nội tuyến (xem `INLINE_VIEW_TYPES`).
_EXPECTED_FAMILY: dict[str, str] = {
    "jpg": "jpeg", "jpeg": "jpeg", "png": "png", "gif": "gif",
    "webp": "webp", "bmp": "bmp", "pdf": "pdf", "mp4": "mp4", "webm": "webm",
}

_FAMILY_LABEL: dict[str, str] = {
    "jpeg": "JPG", "png": "PNG", "gif": "GIF", "webp": "WebP", "bmp": "BMP",
    "pdf": "PDF", "mp4": "MP4", "webm": "WebM",
}


def sniff_family(head: bytes) -> str | None:
    """Họ định dạng đọc được từ mấy byte đầu; không nhận ra thì None.

    Cùng cách `assistant/attachments.detect_type` đã làm đúng từ CR-204, mở rộng
    thêm GIF/BMP/MP4/WebM cho đủ tập đuôi của `FILE_POLICY`.
    """
    if head.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if head.startswith(b"GIF87a") or head.startswith(b"GIF89a"):
        return "gif"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "webp"
    if head.startswith(b"BM"):
        return "bmp"
    if head.startswith(b"%PDF"):
        return "pdf"
    if head[4:8] == b"ftyp":
        return "mp4"
    if head.startswith(b"\x1a\x45\xdf\xa3"):
        return "webm"
    return None


def content_type_of(filename: str) -> str:
    """MIME suy từ ĐUÔI TỆP (BM-028) — không bao giờ lấy chuỗi máy khách gửi lên."""
    return _MIME_BY_EXT.get(ext_of(filename or ""), "application/octet-stream")


def ensure_filename_ok(filename: str) -> str:
    """Tên tệp phải có và không vượt 255 ký tự. Sai khuôn đầu vào → 422, không phải 400."""
    name = (filename or "").strip()
    if not name:
        raise HTTPException(422, "Tệp thiếu tên")
    if len(name) > MAX_FILENAME_LEN:
        raise HTTPException(422, f"Tên tệp quá dài ({len(name)} ký tự, tối đa {MAX_FILENAME_LEN})")
    return name


def ensure_batch_ok(files: list) -> list:
    """Trần số tệp mỗi lượt tải lên (BM-030)."""
    if not files:
        raise HTTPException(422, "Chưa chọn tệp nào")
    if len(files) > MAX_FILES_PER_REQUEST:
        raise HTTPException(422, f"Tối đa {MAX_FILES_PER_REQUEST} tệp mỗi lượt tải lên")
    return files


def guard_upload(*, filename: str, fileobj, exts: set[str], max_mb: int) -> tuple[str, int]:
    """Kiểm MỘT tệp trước khi lưu. Trả `(content_type suy từ đuôi, size)`.

    Ném 422 khi tên tệp sai khuôn, 400 khi đuôi / dung lượng / nội dung không được
    phép. Con trỏ `fileobj` luôn được trả về đầu để bên gọi băm và đẩy lên storage.
    """
    name = ensure_filename_ok(filename)

    ext = ext_of(name)
    if ext not in exts:
        raise HTTPException(
            400, f"Định dạng .{ext or '?'} không được phép (cho phép: {', '.join(sorted(exts))})")

    fileobj.seek(0, 2)
    size = fileobj.tell()
    fileobj.seek(0)
    if size <= 0:
        raise HTTPException(400, f"Tệp '{name}' rỗng")
    if size > max_mb * 1024 * 1024:
        raise HTTPException(400, f"File '{name}' vượt {max_mb}MB")

    expected = _EXPECTED_FAMILY.get(ext)
    if expected:
        head = fileobj.read(_HEAD_BYTES)
        fileobj.seek(0)
        if sniff_family(head) != expected:
            label = _FAMILY_LABEL.get(expected, expected.upper())
            raise HTTPException(
                400, f"Nội dung tệp '{name}' không phải {label} thật (đuôi .{ext} nhưng byte đầu khác)")

    return content_type_of(name), size
