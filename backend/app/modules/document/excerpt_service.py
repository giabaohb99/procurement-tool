"""BẢN TRÍCH NỘI BỘ (C19) và ba ràng buộc của quan hệ "trích từ" (E11).

**C19 khác C20 — hai việc khác nhau, đừng gộp.** Bản trích nội bộ dùng để chia
một phần nội dung xuống nhà máy / lab / dây chuyền: nó là một văn bản thường,
mang **đúng loại của bản gốc**, KHÔNG có số hiệu riêng (gọi theo số của gốc),
không có người ký. Trích lục chính thức (C20) mới là loại riêng, có số riêng, có
người ký "sao đúng với bản gốc", đi luồng duyệt riêng — chờ chốt câu B12.

**Ba ràng buộc của E11**, khóa cứng ở đây, quy tắc không tắt được:

  (a) gốc lên phiên bản mới → mọi bản trích bị đánh dấu *cần rà lại*;
  (b) gốc bị bãi bỏ → bản trích *hết hiệu lực* theo;
  (c) mức mật bản trích luôn **≤ gốc**.

Vì sao không dùng chung quan hệ "thuộc về": Biểu mẫu thuộc về Quy trình là hai
văn bản KHÁC nội dung, cha đổi thì con chưa chắc sai. Bản trích là CÙNG nội
dung, chỉ ít hơn — cha đổi là con sai theo.
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.doc_catalog.link_rule_model import RELATION_EXCERPT
from app.modules.doc_catalog.security_level_model import KIND_CONFIDENTIAL
from app.modules.doc_catalog.security_level_service import ensure_valid

from .link_model import DocumentLink
from .model import STATUS_DRAFT, STATUS_EXPIRED, Document
from .version_model import VERSION_DRAFT, DocumentVersion


def create_excerpt(db: Session, source: Document, title: str, content_html: str,
                   secrecy_level: int, note: str, actor: int) -> Document:
    """Tách một phần nội dung bản gốc thành văn bản riêng mức mật thấp hơn."""
    version = db.get(DocumentVersion, source.current_version_id) if source.current_version_id else None
    if version is None:
        raise HTTPException(400, "Bản gốc chưa có phiên bản nào đang dùng để trích")
    if not (content_html or "").strip():
        raise HTTPException(400, "Chưa chọn phần nội dung nào để trích")

    #  (c) — chặn ở đây, và chặn lại lần nữa ở `update_document` vì người dùng có
    #  thể nâng mức mật sau khi bản trích đã tạo.
    #  Dải hợp lệ theo DANH MỤC, không phải `le=4` trong schema.
    ensure_valid(db, KIND_CONFIDENTIAL, secrecy_level)
    ensure_secrecy_within_source(secrecy_level, source.secrecy_level)

    excerpt = Document(
        #  Mang ĐÚNG loại của bản gốc — C19 không thêm loại nào vào danh mục.
        origin=source.origin,
        doc_type_id=source.doc_type_id,
        company_id=source.company_id,
        department_id=source.department_id,
        owner_employee_id=source.owner_employee_id,
        drafter_employee_id=source.drafter_employee_id,
        title=title.strip(),
        summary=f"Bản trích nội bộ từ {source.title}",
        secrecy_level=secrecy_level,
        status=STATUS_DRAFT,
        created_by=actor, updated_by=actor,
    )
    db.add(excerpt)
    db.flush()

    excerpt_version = DocumentVersion(
        document_id=excerpt.id, major=1, minor=0, status=VERSION_DRAFT,
        content_html=content_html,
        created_by=actor, updated_by=actor,
    )
    db.add(excerpt_version)
    db.flush()
    excerpt.current_version_id = excerpt_version.id

    #  `is_system` — không màn hình nào, không nút nào xóa được dòng này. Xóa
    #  được thì sáu tháng sau không ai biết bản trích lấy từ đâu, và đó chính là
    #  cách nội dung cũ rò rỉ ra ngoài dưới danh nghĩa văn bản còn hiệu lực.
    db.add(DocumentLink(
        source_document_id=excerpt.id,
        target_document_id=source.id,
        relation=RELATION_EXCERPT,
        #  Bắt buộc có: so với `current_version_id` của gốc để biết bản trích đã
        #  lạc hậu chưa.
        source_version_id=version.id,
        note=note,
        is_system=True,
        created_by=actor, updated_by=actor,
    ))
    db.commit()
    db.refresh(excerpt)
    return excerpt


def ensure_secrecy_within_source(secrecy_level: int, source_secrecy: int):
    if secrecy_level > source_secrecy:
        raise HTTPException(
            400,
            f"Bản trích không được đặt mức mật cao hơn bản gốc (gốc đang ở mức "
            f"{source_secrecy}). Bản trích luôn ≤ gốc.",
        )


def source_link_of(db: Session, document_id: int) -> DocumentLink | None:
    """Dòng "trích từ" của một văn bản. Có nghĩa là văn bản này LÀ một bản trích."""
    return (
        db.query(DocumentLink)
        .filter(DocumentLink.source_document_id == document_id,
                DocumentLink.relation == RELATION_EXCERPT)
        .first()
    )


def is_excerpt(db: Session, document_id: int) -> bool:
    """Bản trích **không cấp số hiệu riêng** — gọi theo số của bản gốc (C19)."""
    return source_link_of(db, document_id) is not None


def excerpts_of(db: Session, source_document_id: int) -> list[DocumentLink]:
    return (
        db.query(DocumentLink)
        .filter(DocumentLink.target_document_id == source_document_id,
                DocumentLink.relation == RELATION_EXCERPT)
        .all()
    )


def mark_excerpts_for_review(db: Session, source: Document, reason: str) -> int:
    """(a) Gốc lên phiên bản mới → mọi bản trích bị đánh dấu *cần rà lại*.

    Chỉ ĐÁNH DẤU. Không tự sửa nội dung, không tự bãi bỏ — người rà quyết định.
    """
    count = 0
    for link in excerpts_of(db, source.id):
        excerpt = db.get(Document, link.source_document_id)
        if excerpt is None or excerpt.status == STATUS_EXPIRED:
            continue
        excerpt.needs_review = True
        excerpt.needs_review_note = reason
        count += 1
    return count


def expire_excerpts(db: Session, source: Document) -> int:
    """(b) Gốc bị bãi bỏ → bản trích hết hiệu lực theo. Không có lựa chọn "không làm gì"."""
    count = 0
    for link in excerpts_of(db, source.id):
        excerpt = db.get(Document, link.source_document_id)
        if excerpt is None or excerpt.status == STATUS_EXPIRED:
            continue
        excerpt.status = STATUS_EXPIRED
        excerpt.needs_review = True
        excerpt.needs_review_note = f"Bản gốc «{source.title}» đã bị bãi bỏ."
        count += 1
    return count
