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

    ket_qua = []
    for link in links:
        cu = db.get(Document, link.target_document_id)
        if cu is None:
            continue
        moi = SUPERSEDE_EFFECT[link.relation]
        ket_qua.append({
            "document_id": cu.id,
            "title": cu.title,
            "display_code": cu.doc_code or cu.issue_number or "",
            "relation_label": RELATION_LABELS.get(link.relation, ""),
            "current_status_label": STATUS_LABELS.get(cu.status, ""),
            "next_status_label": STATUS_LABELS.get(moi, ""),
        })
    return ket_qua


def preview(db: Session, doc: Document) -> dict:
    """Mọi thứ sắp xảy ra khi bấm Ban hành. **Chỉ đọc, không đụng gì.**"""
    version = open_version(db, doc)
    doc_type = doc_type_or_400(db, doc.doc_type_id)

    #  Số hiệu: chỉ XEM TRƯỚC, tuyệt đối không chiếm số. Con số này lệch được
    #  nếu có người cấp số xen vào giữa — chấp nhận được với một dòng xem trước.
    so_hieu = doc.doc_code or doc.issue_number or ""
    if not so_hieu and doc_type.number_when == NUMBER_ON_APPROVE:
        so_hieu = numbering.peek(
            db, doc_type, doc.company_id, doc.department_id,
            doc.effective_date or date.today(), doc.book_id,
        )

    hieu_luc = (version.effective_from if version else None) or doc.effective_date or date.today()
    thieu_quan_he = missing_required(db, doc)
    can_quyet_dinh = bool(doc_type.needs_decision)
    co_quyet_dinh = has_decision(db, doc)
    so_dong_pham_vi = len(scopes_of(db, doc.id))

    #  CHẶN — backend sẽ từ chối, nói trước để khỏi bấm rồi mới biết.
    chan: list[str] = []
    if version is None:
        chan.append("Không có phiên bản nào đang chờ duyệt.")
    if thieu_quan_he:
        chan.append("Chưa khai đủ quan hệ bắt buộc: " + "; ".join(thieu_quan_he))
    if can_quyet_dinh and not co_quyet_dinh:
        chan.append(
            f"Loại «{doc_type.name}» phải ban hành kèm một Quyết định. "
            "Khai quan hệ «Kèm theo» tới Quyết định ban hành ở tab Quan hệ."
        )

    #  CẢNH BÁO — vẫn ban hành được, nhưng gần như chắc chắn là quên.
    canh_bao: list[str] = []
    if so_dong_pham_vi == 0:
        canh_bao.append(
            "Chưa khai phạm vi áp dụng — văn bản sẽ không hiện trong mục "
            "«Văn bản áp dụng cho tôi» của bất kỳ ai."
        )
    if not doc.signer_employee_id:
        canh_bao.append("Chưa chọn người ký ban hành.")

    return {
        "version_id": version.id if version else None,
        "version_no": version.version_no if version else "",
        #  Ngày hiệu lực quyết định luôn việc văn bản cũ có bị thay thế NGAY hay
        #  không — nên nó phải hiện, không được để người dùng đoán.
        "effective_date": hieu_luc,
        "effective_now": hieu_luc <= date.today(),
        "issue_number_preview": so_hieu,
        "number_on_approve": doc_type.number_when == NUMBER_ON_APPROVE,
        "needs_decision": can_quyet_dinh,
        "has_decision": co_quyet_dinh,
        "scope_count": so_dong_pham_vi,
        "will_supersede": will_supersede(db, doc),
        "blockers": chan,
        "warnings": canh_bao,
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
