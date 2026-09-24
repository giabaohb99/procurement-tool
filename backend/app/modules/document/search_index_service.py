"""Dựng CHỈ MỤC tìm kiếm toàn văn cho MỘT văn bản — dữ liệu dẫn xuất, ghi vào
`tab_document_search` (`search_model.py`).

Gọi SAU KHI đã commit ở mọi đường lưu (`document/service.py`,
`document/version_service.py`, `attachment/controller.py` cho entity
`document_version`) — đọc dữ liệu MỚI NHẤT từ DB, không đọc đối tượng đang dở
transaction. Script chữa cháy/dựng lần đầu: `app/scripts/reindex_documents.py`.
"""
import hashlib
import logging
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.text_fold import fold
from app.modules.attachment.model import FileLink, StoredFile

from . import search_extract
from .model import Document
from .search_model import DocumentSearch
from .service import ATTACH_ENTITY
from .version_model import DocumentVersion

log = logging.getLogger("app.document.search")

#  Trần TỔNG chữ tệp của MỘT văn bản (Rủi ro §, phase 07) — một quy chế kèm 30
#  phụ lục PDF không được phép làm một dòng CSDL nặng vô hạn.
MAX_TOTAL_FILE_TEXT = 1 * 1024 * 1024


def _read_attachment_bytes(f: StoredFile) -> bytes:
    """Tách riêng khỏi `_file_text` để BÀI KIỂM monkeypatch — pytest không
    được gọi mạng thật (R2/kho app cũ) để đọc byte tệp."""
    from app.core.legacy_files import read_file_bytes

    return read_file_bytes(f)


def _meta_text(db: Session, doc: Document) -> str:
    """SỐ/KÝ HIỆU, TRÍCH YẾU, TỪ KHÓA, TÓM TẮT, NGƯỜI KÝ, LOẠI — gộp một
    chuỗi rồi gập dấu một lần."""
    from app.modules.doc_catalog.model import DocType
    from app.modules.employee.model import Employee

    doc_type = db.get(DocType, doc.doc_type_id) if doc.doc_type_id else None
    signer = db.get(Employee, doc.signer_employee_id) if doc.signer_employee_id else None
    parts = [
        doc.title, doc.summary, doc.keywords,
        doc.doc_code or "", doc.issue_number, doc.legacy_code,
        doc_type.name if doc_type else "",
        signer.full_name if signer else "",
    ]
    return fold(" ".join(p for p in parts if p))


def _body_text(db: Session, doc: Document) -> str:
    """Nội dung soạn thảo của phiên bản ĐANG DÙNG (`current_version_id`) —
    chưa có phiên bản nào (văn bản vừa mở nháp rồi bị xóa giữa chừng, hoặc gọi
    lệch nhịp) thì rỗng, không phải lỗi."""
    if not doc.current_version_id:
        return ""
    version = db.get(DocumentVersion, doc.current_version_id)
    if not version:
        return ""
    return fold(search_extract.strip_html(version.content_html))


def _file_rows(db: Session, doc: Document) -> list[tuple[FileLink, StoredFile]]:
    if not doc.current_version_id:
        return []
    return (
        db.query(FileLink, StoredFile)
        .join(StoredFile, StoredFile.id == FileLink.file_id)
        .filter(FileLink.entity == ATTACH_ENTITY, FileLink.entity_id == doc.current_version_id)
        .order_by(FileLink.sort_order.asc(), FileLink.id.asc())
        .all()
    )


def _file_fingerprint(rows: list[tuple[FileLink, StoredFile]]) -> str:
    """Băm DANH TÍNH bộ tệp — id liên kết + id/sha256/dung lượng từng tệp.
    KHÔNG đụng byte tệp (rẻ, chỉ đọc hai bảng CSDL thường) — dùng để biết có
    cần trích lại chữ từ tệp hay không, TRƯỚC KHI mở tệp ra đọc.
    """
    raw = "|".join(f"{link.id}:{f.id}:{f.sha256}:{f.size}" for link, f in rows)
    return hashlib.sha256(raw.encode("utf-8", "ignore")).hexdigest()


def _file_text_from_rows(
    file_rows: list[tuple[FileLink, StoredFile]],
) -> tuple[str, str, list[dict]]:
    """Trả `(file_text gập dấu, file_text_raw bản gốc, file_names)` từ danh
    sách liên kết tệp ĐÃ CÓ SẴN (`_file_rows`) — tách khỏi việc đọc CSDL để gọi
    được từ `reindex()` chỉ khi `_file_fingerprint` báo bộ tệp thật sự đổi.

    Ghép nối tiếp các tệp, phân cách bằng ĐÚNG một ký tự `"\\n"` ở CẢ HAI bản
    (gập + gốc) để offset của bản này dùng thẳng được trên bản kia.
    """
    folded_parts: list[str] = []
    raw_parts: list[str] = []
    file_names: list[dict] = []
    cursor = 0
    total_raw_len = 0

    for link, f in file_rows:
        if total_raw_len >= MAX_TOTAL_FILE_TEXT:
            break
        raw = search_extract.extract_file_text(f.filename, _read_attachment_bytes(f))
        if not raw:
            continue
        folded = fold(raw)
        #  `fold_char` giữ ĐÚNG một ký tự / một ký tự gốc (bắt buộc để offset
        #  không lệch) — trường hợp lạ nào phá vỡ điều đó thì bỏ tệp, không
        #  lưu offset sai (đoạn trích cắt sai chỗ còn tệ hơn thiếu đoạn trích).
        if len(folded) != len(raw):
            log.warning("Gập dấu lệch độ dài cho tệp #%s — bỏ qua tệp này khỏi chỉ mục", f.id)
            continue
        start = cursor
        end = start + len(folded)
        folded_parts.append(folded)
        raw_parts.append(raw)
        file_names.append({"attachment_id": link.id, "name": f.filename,
                           "start": start, "end": end})
        cursor = end + 1  # +1 cho ký tự phân cách nối tệp kế tiếp
        total_raw_len += len(raw)

    return ("\n".join(folded_parts)[:MAX_TOTAL_FILE_TEXT],
            "\n".join(raw_parts)[:MAX_TOTAL_FILE_TEXT],
            file_names)


def _source_hash(doc: Document, meta_text: str, body_text: str, file_text: str) -> str:
    #  Băm trên CHÍNH ba chuỗi đã tính (không băm riêng từng nguồn rồi ghép):
    #  đơn giản, và tự động đúng với BẤT CỨ điều gì làm ba chuỗi đổi — kể cả
    #  khi nguyên nhân không phải một lượt lưu nội dung (vd đổi tên LOẠI văn
    #  bản làm `meta_text` đổi theo dù văn bản không hề được sửa).
    raw = f"{doc.updated_at}|{meta_text}|{body_text}|{file_text}".encode("utf-8", "ignore")
    return hashlib.sha256(raw).hexdigest()


def reindex(db: Session, document_id: int) -> DocumentSearch | None:
    """Dựng lại TOÀN BỘ dòng chỉ mục của một văn bản.

    Văn bản không còn tồn tại (đã xóa) → xóa dòng chỉ mục nếu có, trả `None`.
    Băm nguồn không đổi so với dòng đang có → BỎ QUA, không ghi lại (giữ
    `indexed_at` cũ, đỡ một lượt ghi vô ích).
    """
    doc = db.get(Document, document_id)
    row = db.get(DocumentSearch, document_id)
    if doc is None:
        if row is not None:
            db.delete(row)
            db.commit()
        return None

    meta_text = _meta_text(db, doc)
    body_text = _body_text(db, doc)

    #  Trích chữ từ tệp là việc ĐẮT (mạng + phân tích PDF/docx) — chỉ làm lại
    #  khi BỘ TỆP thật sự đổi, không phải mỗi lần `meta_text`/`body_text` đổi
    #  (tự động lưu chạy theo nhịp gõ thì `body_text` gần như luôn đổi).
    file_rows = _file_rows(db, doc)
    fingerprint = _file_fingerprint(file_rows)
    if row is not None and row.file_fingerprint == fingerprint:
        file_text, file_text_raw, file_names = row.file_text, row.file_text_raw, row.file_names
    else:
        file_text, file_text_raw, file_names = _file_text_from_rows(file_rows)

    source_hash = _source_hash(doc, meta_text, body_text, file_text)
    if row is not None and row.source_hash == source_hash:
        return row

    if row is None:
        row = DocumentSearch(document_id=document_id)
        db.add(row)
    row.meta_text = meta_text
    row.body_text = body_text
    row.file_text = file_text
    row.file_text_raw = file_text_raw
    row.file_names = file_names
    row.file_fingerprint = fingerprint
    row.source_hash = source_hash
    row.indexed_at = datetime.now()
    db.commit()
    db.refresh(row)
    return row


def queue_reindex(db: Session, document_id: int) -> None:
    """Xếp hàng dựng lại chỉ mục — gọi SAU commit ở mọi đường lưu văn bản.

    Ưu tiên Celery (`.delay`, best-effort, không chặn request đang trả lời
    người dùng). Dự phòng ĐỒNG BỘ khi broker không xếp hàng được — Rủi ro của
    phase 07 nói rõ: "chỉ mục cũ khi hook bị bỏ sót", không được để một broker
    tạm sập biến thành một chỉ mục lặng lẽ không bao giờ cập nhật.

    Cờ cấu hình `settings.DOCUMENT_SEARCH_INDEX_SYNC` (mặc định tắt) ép LUÔN
    chạy đồng bộ — bài kiểm (`test/backend`) bật cờ này: tiến trình pytest
    không có celery-worker nào tiêu thụ hàng đợi, mà tác vụ nền lại mở
    `SessionLocal()` RIÊNG (kết nối MySQL thật) nên không bao giờ thấy được DB
    SQLite trong bộ nhớ của bài kiểm — phải chạy ngay trên CHÍNH session `db`
    được truyền vào.

    ⚠️ KHÔNG BAO GIỜ để lỗi ở đây thoát ra ngoài (M11, rà soát 23/09/2026) —
    hàm này LUÔN được gọi SAU khi văn bản/phiên bản/liên kết đã `commit`
    (xem docstring đầu tệp). Đường dự phòng đồng bộ tự trích chữ từ MỌI tệp
    đính kèm ngay trong request (mạng + PDF/docx) — một tệp hỏng đọc byte lỗi
    hay một PDF quái dị đều không được làm response trả về 500 cho một thao
    tác THỰC RA đã thành công; văn bản đã lưu, chỉ mục cũ đi tới lần
    `scripts/reindex_documents.py` kế tiếp là chấp nhận được, mất cả response
    thì không.
    """
    from app.core.config import settings

    try:
        if settings.DOCUMENT_SEARCH_INDEX_SYNC:
            reindex(db, document_id)
            return
        try:
            from .search_tasks import reindex_document_task
            reindex_document_task.delay(document_id)
        except Exception:  # noqa: BLE001 — broker sập không được làm vỡ nghiệp vụ
            log.warning(
                "Xếp hàng dựng chỉ mục tìm kiếm thất bại, chạy đồng bộ thay thế: văn bản #%s",
                document_id, exc_info=True)
            reindex(db, document_id)
    except Exception:  # noqa: BLE001 — xem cảnh báo ở docstring, không lộ ra response
        log.error(
            "Dựng chỉ mục tìm kiếm THẤT BẠI cho văn bản #%s — văn bản đã lưu, chỉ mục sẽ "
            "cũ tới lần `scripts/reindex_documents.py` kế tiếp", document_id, exc_info=True)
