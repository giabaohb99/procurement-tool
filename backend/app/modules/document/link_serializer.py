"""Dựng dữ liệu cho màn QUAN HỆ và CÂY TÀI LIỆU (E06).

Tách khỏi `serializer.py` vì hai thứ khác nhau: bên đó trả một văn bản đầy đủ,
bên này trả **tóm tắt một dòng** — vừa đủ để nhìn ra văn bản là cái gì mà không
kéo theo cả nội dung.
"""
from sqlalchemy.orm import Session

from app.modules.doc_catalog.link_rule_model import (RELATION_EXCERPT,
                                                     RELATION_LABELS,
                                                     RELATION_REVERSE_LABELS)

from .link_model import DocumentLink
from .model import STATUS_LABELS, Document
from .version_model import DocumentVersion

#  Cây sâu quá thì màn hình không đọc được nữa, mà truy vấn thì nở theo cấp.
#  Ba cấp đủ cho Quy chế → Quy trình → Hướng dẫn/Biểu mẫu.
MAX_TREE_DEPTH = 3


def summary_of(db: Session, doc: Document | None) -> dict | None:
    """Tóm tắt một dòng: đủ nhìn ra văn bản gì, đang ở trạng thái nào, bản mấy."""
    if doc is None:
        return None
    version = (
        db.get(DocumentVersion, doc.current_version_id) if doc.current_version_id else None
    )
    return {
        "id": doc.id,
        "title": doc.title,
        "display_code": doc.doc_code or doc.issue_number or "",
        "doc_type_id": doc.doc_type_id,
        "status": doc.status,
        "status_label": STATUS_LABELS.get(doc.status, str(doc.status)),
        "secrecy_level": doc.secrecy_level,
        "version_no": version.version_no if version else "",
        "needs_review": doc.needs_review,
    }


def serialize_link(db: Session, link: DocumentLink, *, viewed_from: int) -> dict:
    """Một dòng quan hệ, ĐỌC THEO PHÍA ĐANG XEM.

    Cùng một dòng dữ liệu đọc ra hai câu khác nhau: mở Hướng dẫn công việc thì
    thấy "hướng dẫn cho Quy trình X", mở Quy trình X thì thấy "được hướng dẫn
    bởi Hướng dẫn công việc". Không đảo câu thì trang văn bản đích đọc ngược
    nghĩa hoàn toàn.
    """
    is_source = link.source_document_id == viewed_from
    other_id = link.target_document_id if is_source else link.source_document_id
    labels = RELATION_LABELS if is_source else RELATION_REVERSE_LABELS

    return {
        "id": link.id,
        "relation": link.relation,
        "relation_label": labels.get(link.relation, str(link.relation)),
        #  `outgoing` = văn bản đang xem là NGUỒN. Chỉ chiều này mới gỡ được quan
        #  hệ — gỡ từ phía đích là sửa dữ liệu của văn bản người khác.
        "direction": "outgoing" if is_source else "incoming",
        "document": summary_of(db, db.get(Document, other_id)),
        "note": link.note,
        "is_system": link.is_system,
        "source_version_id": link.source_version_id,
        "is_outdated": _is_outdated(db, link),
    }


def _is_outdated(db: Session, link: DocumentLink) -> bool:
    """Bản trích có đang bám theo một phiên bản cũ của gốc không.

    Chỉ có nghĩa với quan hệ "trích từ" — các quan hệ khác nối hai văn bản KHÁC
    nội dung nên cha lên bản mới không làm con sai.
    """
    if link.relation != RELATION_EXCERPT or not link.source_version_id:
        return False
    source = db.get(Document, link.target_document_id)
    return bool(source and source.current_version_id != link.source_version_id)


def build_tree(db: Session, root: Document, depth: int = MAX_TREE_DEPTH) -> dict:
    """Cây tài liệu (E06): mở một Quy trình thấy ngay Hướng dẫn và Biểu mẫu của nó.

    Con = văn bản TRỎ VÀO văn bản này. "Biểu mẫu thuộc về Quy trình" ghi Biểu mẫu
    là nguồn, Quy trình là đích — nên đi ngược cạnh mới ra được cây.

    `seen` chặn lặp vô hạn: cấm vòng lặp chỉ ép trong PHẠM VI MỘT loại quan hệ,
    nên A hướng dẫn B mà B thuộc về A vẫn ghi được, và đó là một vòng khi duyệt
    cây không phân biệt loại quan hệ.
    """
    node = summary_of(db, root) or {}
    node["children"] = _children(db, root.id, depth, {root.id})
    return node


def _children(db: Session, document_id: int, depth: int, seen: set[int]) -> list[dict]:
    if depth <= 0:
        return []

    links = (
        db.query(DocumentLink)
        .filter(DocumentLink.target_document_id == document_id)
        .order_by(DocumentLink.relation.asc(), DocumentLink.id.asc())
        .all()
    )

    nodes: list[dict] = []
    for link in links:
        if link.source_document_id in seen:
            continue
        child = db.get(Document, link.source_document_id)
        if child is None:
            continue
        seen.add(child.id)
        node = summary_of(db, child) or {}
        node["relation"] = link.relation
        node["relation_label"] = RELATION_LABELS.get(link.relation, str(link.relation))
        node["is_outdated"] = _is_outdated(db, link)
        node["children"] = _children(db, child.id, depth - 1, seen)
        nodes.append(node)
    return nodes
