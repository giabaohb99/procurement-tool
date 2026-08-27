"""BẢN XEM TRƯỚC LÚC BAN HÀNH (J04).

Ban hành là thao tác **không lùi được**: số hiệu cấp ra là cấp vĩnh viễn, phiên
bản khóa lại là khóa một chiều, và văn bản cũ bị thay thế thì đổi trạng thái
ngay. Trước khi bấm, người ban hành phải nhìn thấy đủ bốn thứ sắp xảy ra:

  1. số hiệu nào sẽ được cấp;
  2. phiên bản nào bị khóa và áp dụng từ ngày nào;
  3. văn bản nào bị thay thế / bãi bỏ theo;
  4. văn bản này sẽ tới ai (phạm vi áp dụng).

Tách **chặn** ra khỏi **cảnh báo**: chặn là thứ backend sẽ từ chối, cảnh báo là
thứ vẫn ban hành được nhưng gần như chắc chắn là người dùng quên.
"""
from datetime import date

from sqlalchemy.orm import Session

from app.modules.doc_catalog.link_rule_model import (RELATION_ATTACHED,
                                                     RELATION_LABELS)

from . import numbering
from .link_model import DocumentLink
from .link_service import missing_required
from .model import STATUS_LABELS, Document
from .scope_service import scopes_of
from .service import NUMBER_ON_APPROVE, doc_type_or_400, issue_year, open_version
from .supersede_service import SUPERSEDE_EFFECT


def has_decision(db: Session, doc: Document) -> bool:
    """J11 — văn bản có kèm một Quyết định ban hành không.

    Quan hệ «kèm theo» của chính văn bản này trỏ ra ngoài; loại đích do bảng quy
    tắc quyết định (thường là Quyết định).
    """
    return (
        db.query(DocumentLink.id)
        .filter(DocumentLink.source_document_id == doc.id,
                DocumentLink.relation == RELATION_ATTACHED)
        .first()
        is not None
    )


def will_supersede(db: Session, doc: Document) -> list[dict]:
    """Văn bản nào sẽ đổi trạng thái khi văn bản này được ban hành (J10)."""
    links = (
        db.query(DocumentLink)
        .filter(DocumentLink.source_document_id == doc.id,
                DocumentLink.relation.in_(tuple(SUPERSEDE_EFFECT)))
        .all()
    )

    result = []
    for link in links:
        old = db.get(Document, link.target_document_id)
        if old is None:
            continue
        new = SUPERSEDE_EFFECT[link.relation]
        result.append({
            "document_id": old.id,
            "title": old.title,
            "display_code": old.doc_code or old.issue_number or "",
            "relation_label": RELATION_LABELS.get(link.relation, ""),
            "current_status_label": STATUS_LABELS.get(old.status, ""),
            "next_status_label": STATUS_LABELS.get(new, ""),
        })
    return result


def preview(db: Session, doc: Document) -> dict:
    """Mọi thứ sắp xảy ra khi bấm Ban hành. **Chỉ đọc, không đụng gì.**"""
    version = open_version(db, doc)
    doc_type = doc_type_or_400(db, doc.doc_type_id)

    #  Số hiệu: chỉ XEM TRƯỚC, tuyệt đối không chiếm số. Con số này lệch được
    #  nếu có người cấp số xen vào giữa — chấp nhận được với một dòng xem trước.
    issue_number = doc.doc_code or doc.issue_number or ""
    if not issue_number and doc_type.number_when == NUMBER_ON_APPROVE:
        issue_number = numbering.peek(
            db, doc_type, doc.company_id, doc.department_id,
            doc.effective_date or date.today(), doc.book_id,
        )

    effective_date = (version.effective_from if version else None) or doc.effective_date or date.today()
    missing_relations = missing_required(db, doc)
    needs_decision = bool(doc_type.needs_decision)
    decision_exists = has_decision(db, doc)
    scope_row_count = len(scopes_of(db, doc.id))

    #  CHẶN — backend sẽ từ chối, nói trước để khỏi bấm rồi mới biết.
    blockers: list[str] = []
    if version is None:
        blockers.append("Không có phiên bản nào đang chờ duyệt.")
    if missing_relations:
        blockers.append("Chưa khai đủ quan hệ bắt buộc: " + "; ".join(missing_relations))
    if needs_decision and not decision_exists:
        blockers.append(
            f"Loại «{doc_type.name}» phải ban hành kèm một Quyết định. "
            "Khai quan hệ «Kèm theo» tới Quyết định ban hành ở tab Quan hệ."
        )

    #  CẢNH BÁO — vẫn ban hành được, nhưng gần như chắc chắn là quên.
    warning: list[str] = []
    #  Không khai phạm vi KHÔNG còn là thiếu sót: văn bản mặc định áp trong đúng
    #  pháp nhân ban hành (quy tắc 3, xem `scope_service`). Màn xem trước nói ra
    #  chuyện đó ở dòng "Phạm vi áp dụng" chứ không dọa nữa.
    if not doc.signer_employee_id:
        warning.append("Chưa chọn người ký ban hành.")

    return {
        "version_id": version.id if version else None,
        "version_no": version.version_no if version else "",
        #  Ngày hiệu lực quyết định luôn việc văn bản cũ có bị thay thế NGAY hay
        #  không — nên nó phải hiện, không được để người dùng đoán.
        "effective_date": effective_date,
        "effective_now": effective_date <= date.today(),
        "issue_number_preview": issue_number,
        "number_on_approve": doc_type.number_when == NUMBER_ON_APPROVE,
        "needs_decision": needs_decision,
        "has_decision": decision_exists,
        "scope_count": scope_row_count,
        "will_supersede": will_supersede(db, doc),
        "blockers": blockers,
        "warnings": warning,
    }


def ensure_can_issue(db: Session, doc: Document):
    """J11 — loại khai "ban hành phải kèm Quyết định" thì thiếu là không cho ban hành.

    Kiểm ở tầng dịch vụ chứ không chỉ trên màn xem trước: màn đó là tiện ích,
    còn đây là chốt chặn.
    """
    from fastapi import HTTPException

    doc_type = doc_type_or_400(db, doc.doc_type_id)
    if doc_type.needs_decision and not has_decision(db, doc):
        raise HTTPException(
            400,
            f"Loại «{doc_type.name}» phải ban hành kèm một Quyết định. Khai quan hệ "
            "«Kèm theo» tới Quyết định ban hành rồi ban hành lại.",
        )
