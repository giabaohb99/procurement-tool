"""Nghiệp vụ QUAN HỆ CHA–CON giữa các văn bản (E03–E06, E11).

Bốn chốt chặn, **tất cả ở tầng dịch vụ** chứ không phải ẩn ô trên giao diện —
bài kiểm gọi thẳng API để canh việc đó:

1. **Quan hệ phải khớp quy tắc** — loại đích không nằm trong quy tắc thì từ chối.
2. **Cấm vòng lặp** (E05) — kiểm CẢ CHUỖI, không chỉ hai bước.
3. **Đủ quan hệ bắt buộc mới cho gửi duyệt** (E04).
4. **Ba ràng buộc của "trích từ"** (E11) — xem `excerpt_service.py`.
"""
from collections import deque

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.doc_catalog.link_rule_model import (RELATION_EXCERPT,
                                                     RELATION_LABELS,
                                                     RELATION_REFERENCE,
                                                     DocTypeLinkRule)
from app.modules.doc_catalog.model import DocType

from .link_model import DocumentLink
from .model import ALIVE_STATUSES, Document


def rules_for_type(db: Session, source_type_id: int | None) -> list[DocTypeLinkRule]:
    """Các ô quan hệ mà form phải tự hiện khi chọn loại này (E03)."""
    if not source_type_id:
        return []
    return (
        db.query(DocTypeLinkRule)
        .filter(DocTypeLinkRule.source_type_id == source_type_id,
                DocTypeLinkRule.is_active.is_(True))
        .order_by(DocTypeLinkRule.is_required.desc(), DocTypeLinkRule.relation.asc())
        .all()
    )


def allowed_targets(db: Session, rule: DocTypeLinkRule, exclude_document_id: int = 0):
    """Danh sách văn bản chọn được cho một ô quan hệ.

    Lọc đúng loại đích cho phép và **chỉ văn bản đang còn hiệu lực** — người soạn
    không phải nhớ quy tắc, và không lỡ tay trỏ vào một văn bản đã bãi bỏ.
    """
    query = db.query(Document).filter(
        Document.origin == 1,
        Document.status.in_(ALIVE_STATUSES),
        Document.id != exclude_document_id,
    )
    #  `target_type_id` rỗng nghĩa là loại nào cũng được (dòng "bất kỳ tham chiếu bất kỳ").
    if rule.target_type_id:
        query = query.filter(Document.doc_type_id == rule.target_type_id)
    return query.order_by(Document.title.asc()).all()


def links_of(db: Session, document_id: int) -> list[DocumentLink]:
    """Quan hệ mà văn bản này là NGUỒN — "tôi hướng dẫn cho ai"."""
    return (
        db.query(DocumentLink)
        .filter(DocumentLink.source_document_id == document_id)
        .order_by(DocumentLink.relation.asc(), DocumentLink.id.asc())
        .all()
    )


def links_to(db: Session, document_id: int) -> list[DocumentLink]:
    """Quan hệ mà văn bản này là ĐÍCH — "ai hướng dẫn cho tôi"."""
    return (
        db.query(DocumentLink)
        .filter(DocumentLink.target_document_id == document_id)
        .order_by(DocumentLink.relation.asc(), DocumentLink.id.asc())
        .all()
    )


def _rule_for(db: Session, source: Document, relation: int,
              target: Document) -> DocTypeLinkRule | None:
    """Quy tắc khớp nhất: khai đích tường minh thắng dòng "loại nào cũng được"."""
    rules = (
        db.query(DocTypeLinkRule)
        .filter(DocTypeLinkRule.source_type_id == source.doc_type_id,
                DocTypeLinkRule.relation == relation,
                DocTypeLinkRule.is_active.is_(True))
        .all()
    )
    exact = [r for r in rules if r.target_type_id == target.doc_type_id]
    if exact:
        return exact[0]
    wildcard = [r for r in rules if r.target_type_id is None]
    return wildcard[0] if wildcard else None


def would_cycle(db: Session, source_id: int, target_id: int, relation: int) -> bool:
    """Nối `source → target` có tạo vòng lặp không (E05).

    Đi NGƯỢC từ `target` theo cùng loại quan hệ: nếu lần theo các cạnh đã có mà
    quay về được `source` thì thêm cạnh mới sẽ khép vòng.

    Phải duyệt cả chuỗi chứ không chỉ hai bước: A hướng dẫn B, B hướng dẫn C,
    C hướng dẫn A là vòng lặp dài ba cạnh — kiểm hai bước cho lọt hết.
    """
    if source_id == target_id:
        return True

    seen = {target_id}
    queue = deque([target_id])
    while queue:
        current = queue.popleft()
        rows = (
            db.query(DocumentLink.target_document_id)
            .filter(DocumentLink.source_document_id == current,
                    DocumentLink.relation == relation)
            .all()
        )
        for (next_id,) in rows:
            if next_id == source_id:
                return True
            if next_id not in seen:
                seen.add(next_id)
                queue.append(next_id)
    return False


def add_link(db: Session, source: Document, relation: int, target_document_id: int,
             note: str, actor: int) -> DocumentLink:
    """Khai một quan hệ. Bốn phép kiểm, hỏng phép nào cũng từ chối ghi."""
    if relation not in RELATION_LABELS:
        raise HTTPException(400, "Loại quan hệ không hợp lệ")
    #  Trích từ do `excerpt_service` sinh ra kèm `source_version_id`; khai tay
    #  thì thiếu cột đó, mà thiếu là mất luôn khả năng biết bản trích lạc hậu chưa.
    if relation == RELATION_EXCERPT:
        raise HTTPException(
            400, "Quan hệ trích từ chỉ sinh ra khi tạo bản trích, không khai tay được"
        )

    target = db.get(Document, target_document_id)
    if not target or target.origin != 1:
        raise HTTPException(404, "Không tìm thấy văn bản đích")
    if target.id == source.id:
        raise HTTPException(400, "Văn bản không thể có quan hệ với chính nó")

    rule = _rule_for(db, source, relation, target)
    #  «Tham chiếu» là LIÊN KẾT MỀM — tài liệu khai nó là "bất kỳ tham chiếu bất
    #  kỳ", tức không ràng buộc loại nào. Bảng quy tắc lại bắt buộc có
    #  `source_type_id`, nên khai cho đủ 33 loại thì bảng 15–25 dòng phình lên
    #  gấp đôi mà không thêm nghĩa gì. Cho qua thẳng, `rule_id` để rỗng.
    if rule is None and relation != RELATION_REFERENCE:
        raise HTTPException(
            400,
            f"Loại «{_type_name(db, source.doc_type_id)}» không được khai quan hệ "
            f"«{RELATION_LABELS[relation]}» tới loại «{_type_name(db, target.doc_type_id)}». "
            "Muốn cho phép thì thêm dòng ở Quy tắc quan hệ.",
        )

    existing = (
        db.query(DocumentLink)
        .filter(DocumentLink.source_document_id == source.id,
                DocumentLink.target_document_id == target.id,
                DocumentLink.relation == relation)
        .first()
    )
    if existing:
        raise HTTPException(400, "Quan hệ này đã khai rồi")

    if rule and rule.max_count and _count_relation(db, source.id, relation) >= rule.max_count:
        raise HTTPException(
            400,
            f"Quan hệ «{RELATION_LABELS[relation]}» chỉ được khai tối đa "
            f"{rule.max_count} văn bản.",
        )

    if would_cycle(db, source.id, target.id, relation):
        raise HTTPException(
            400,
            f"Nối quan hệ này tạo thành vòng lặp: lần theo «{RELATION_LABELS[relation]}» "
            "từ văn bản đích sẽ quay về chính văn bản đang khai.",
        )

    link = DocumentLink(
        source_document_id=source.id, target_document_id=target.id,
        relation=relation, rule_id=rule.id if rule else None, note=note,
        created_by=actor, updated_by=actor,
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return link


def delete_link(db: Session, source: Document, link_id: int):
    link = db.get(DocumentLink, link_id)
    if not link or link.source_document_id != source.id:
        raise HTTPException(404, "Không tìm thấy quan hệ")
    if link.is_system:
        raise HTTPException(
            400,
            "Quan hệ này do hệ thống tạo, không xóa được. Xóa được thì bản trích "
            "hoặc bản clone thành mồ côi, không truy về gốc được nữa.",
        )
    db.delete(link)
    db.commit()


def missing_required(db: Session, doc: Document) -> list[str]:
    """Các quan hệ bắt buộc còn thiếu (E04). Rỗng nghĩa là đủ điều kiện gửi duyệt."""
    thieu: list[str] = []
    for rule in rules_for_type(db, doc.doc_type_id):
        if not rule.is_required:
            continue
        can = max(rule.min_count, 1)
        dang_co = _count_relation(db, doc.id, rule.relation)
        if dang_co < can:
            ten_dich = _type_name(db, rule.target_type_id) if rule.target_type_id else "văn bản"
            thieu.append(
                f"«{RELATION_LABELS[rule.relation]}» tới {ten_dich} "
                f"(cần {can}, đang có {dang_co})"
            )
    return thieu


def ensure_required_links(db: Session, doc: Document):
    """Chặn gửi duyệt khi thiếu quan hệ bắt buộc, kèm câu báo rõ thiếu gì."""
    thieu = missing_required(db, doc)
    if thieu:
        raise HTTPException(
            400, "Chưa khai đủ quan hệ bắt buộc: " + "; ".join(thieu)
        )


def _count_relation(db: Session, source_id: int, relation: int) -> int:
    return (
        db.query(DocumentLink.id)
        .filter(DocumentLink.source_document_id == source_id,
                DocumentLink.relation == relation)
        .count()
    )


def _type_name(db: Session, doc_type_id: int | None) -> str:
    doc_type = db.get(DocType, doc_type_id) if doc_type_id else None
    return doc_type.name if doc_type else "không rõ"
