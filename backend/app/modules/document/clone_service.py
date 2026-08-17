"""CLONE XUỐNG PHÁP NHÂN CON (F06–F11).

Quyết định cũ (04/08/2026) từng cấm hẳn: *"Tuyệt đối không nhân bản văn bản mẹ
thành 12 bản y hệt cho 12 công ty con. Sau 6 tháng sẽ có 12 bản khác nhau và
không ai biết bản nào đúng."* Yêu cầu mới mở lại, nhưng kèm **bốn điều kiện bắt
buộc** — thiếu bất kỳ điều nào thì đúng như cảnh báo cũ, sau hai năm sẽ có 12
bản lệch nhau:

  1. bản clone LUÔN giữ liên kết ngược về bản gốc (quan hệ *căn cứ theo*), và
     không có nút nào xóa được liên kết đó;
  2. bản clone mang **số hiệu của pháp nhân con**, không dùng lại số Tập đoàn;
  3. bản gốc lên phiên bản mới → mọi bản clone tự động *cần rà lại*, người phụ
     trách nhận thông báo, trạng thái hiện ngay trên danh sách;
  4. có một màn hình trả lời được *"12 công ty con đang ở phiên bản nào"*.

Điều 1 và 2 nằm ở `create_clones()`; điều 3 ở `mark_clones_for_review()`; điều 4
ở `tracking()`.
"""
from datetime import date, datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.attachment.model import FileLink
from app.modules.company.model import Company
from app.modules.doc_catalog.link_rule_model import RELATION_BASED_ON
from app.modules.employee.model import Employee

from .link_model import DocumentLink
from .model import (ALIVE_STATUSES, APPLY_MODE_CLONE, STATUS_DRAFT,
                    STATUS_LABELS, Document)
from .service import ATTACH_ENTITY
from .version_model import VERSION_DRAFT, DocumentVersion

# Vòng đời của một bản clone (`04` mục 5.2).
CLONE_SENT = 1       # đã gửi, pháp nhân con chưa đụng tới
CLONE_DRAFTING = 2   # đang soạn
CLONE_SUBMITTED = 3  # đang duyệt
CLONE_ISSUED = 4     # đã ban hành
CLONE_REJECTED = 5   # từ chối áp dụng
CLONE_STALE = 6      # cần rà lại vì bản gốc đã lên phiên bản mới

CLONE_STATUS_LABELS = {
    0: "Chưa đụng tới",
    CLONE_SENT: "Đã gửi",
    CLONE_DRAFTING: "Đang soạn",
    CLONE_SUBMITTED: "Đang duyệt",
    CLONE_ISSUED: "Đã ban hành",
    CLONE_REJECTED: "Từ chối áp dụng",
    CLONE_STALE: "Cần rà lại",
}


def create_clones(db: Session, source: Document, company_ids: list[int],
                  due_date: date | None, note: str, actor: int) -> list[Document]:
    """F06 — sinh bản nháp riêng cho từng pháp nhân con, chép nội dung và tệp."""
    if source.status not in ALIVE_STATUSES:
        raise HTTPException(400, "Chỉ clone được văn bản đã ban hành")

    goc_version = (
        db.get(DocumentVersion, source.current_version_id)
        if source.current_version_id else None
    )
    if goc_version is None:
        raise HTTPException(400, "Bản gốc chưa có phiên bản nào đang dùng")
    if not company_ids:
        raise HTTPException(400, "Chưa chọn pháp nhân nào để clone")

    ket_qua: list[Document] = []
    for company_id in dict.fromkeys(company_ids):
        if company_id == source.company_id:
            raise HTTPException(400, "Không clone văn bản về chính pháp nhân đã ban hành nó")
        company = db.get(Company, company_id)
        if company is None:
            raise HTTPException(400, f"Pháp nhân {company_id} không tồn tại")

        #  UNIQUE(source_document_id, company_id) ở tầng dữ liệu cũng chặn, nhưng
        #  báo trước thì người dùng biết là clone cũ vẫn còn chứ không phải lỗi.
        da_co = (
            db.query(Document.id)
            .filter(Document.source_document_id == source.id,
                    Document.company_id == company_id)
            .first()
        )
        if da_co:
            raise HTTPException(
                400, f"Pháp nhân «{company.name}» đã có bản clone của văn bản này rồi"
            )

        clone = Document(
            origin=source.origin,
            doc_type_id=source.doc_type_id,
            #  Pháp nhân CON — đây là điều kiện 2: số hiệu sẽ cấp theo mã pháp
            #  nhân này lúc bản clone được ban hành, không dùng lại số Tập đoàn.
            company_id=company_id,
            #  Chép người chịu trách nhiệm từ bản gốc. Văn bản nội bộ BẮT BUỘC
            #  có `owner_employee_id` (CHECK ở tầng dữ liệu) — để trống là bản
            #  clone không ai chịu trách nhiệm nội dung. Pháp nhân con đổi lại
            #  người của mình khi soạn.
            department_id=source.department_id,
            owner_employee_id=source.owner_employee_id,
            drafter_employee_id=source.drafter_employee_id,
            title=source.title,
            summary=source.summary,
            keywords=source.keywords,
            secrecy_level=source.secrecy_level,
            urgency=source.urgency,
            status=STATUS_DRAFT,
            apply_mode=APPLY_MODE_CLONE,
            source_document_id=source.id,
            #  Bám theo PHIÊN BẢN nào của gốc — cột làm nên toàn bộ giá trị của
            #  việc theo dõi clone: so với `current_version_id` của gốc là biết
            #  bản clone đã lạc hậu chưa.
            clone_source_version_id=goc_version.id,
            clone_status=CLONE_SENT,
            clone_due_date=due_date,
            clone_note=note,
            cloned_at=date.today(),
            cloned_by=actor,
            created_by=actor, updated_by=actor,
        )
        db.add(clone)
        db.flush()

        version = DocumentVersion(
            document_id=clone.id, major=1, minor=0, status=VERSION_DRAFT,
            content_html=goc_version.content_html,
            created_by=actor, updated_by=actor,
        )
        db.add(version)
        db.flush()
        clone.current_version_id = version.id

        _copy_attachments(db, goc_version.id, version.id, actor)

        #  Điều kiện 1 — liên kết ngược, `is_system` nên không màn hình nào,
        #  không hàm nào xóa được. Xóa được thì vài tháng sau có bản clone mồ
        #  côi, không truy về gốc.
        db.add(DocumentLink(
            source_document_id=clone.id,
            target_document_id=source.id,
            relation=RELATION_BASED_ON,
            is_system=True,
            note="Bản clone của pháp nhân con",
            created_by=actor, updated_by=actor,
        ))
        ket_qua.append(clone)

    db.commit()
    for clone in ket_qua:
        db.refresh(clone)
    return ket_qua


def _copy_attachments(db: Session, from_version_id: int, to_version_id: int, actor: int):
    """Chép LIÊN KẾT tệp, không chép tệp — một tệp gắn được vào nhiều bản ghi."""
    links = (
        db.query(FileLink)
        .filter(FileLink.entity == ATTACH_ENTITY, FileLink.entity_id == from_version_id)
        .all()
    )
    for link in links:
        db.add(FileLink(file_id=link.file_id, entity=ATTACH_ENTITY,
                        entity_id=to_version_id, doc_type=link.doc_type,
                        sort_order=link.sort_order, created_by=actor, updated_by=actor))


def clones_of(db: Session, source_document_id: int) -> list[Document]:
    return (
        db.query(Document)
        .filter(Document.source_document_id == source_document_id)
        .order_by(Document.company_id.asc())
        .all()
    )


def mark_clones_for_review(db: Session, source: Document) -> int:
    """Điều kiện 3 — bản gốc lên phiên bản mới thì mọi bản clone *cần rà lại*."""
    dem = 0
    for clone in clones_of(db, source.id):
        if clone.clone_source_version_id == source.current_version_id:
            continue
        clone.needs_review = True
        clone.needs_review_note = (
            f"Bản gốc đã lên phiên bản mới ngày {date.today():%d/%m/%Y}. "
            "Rà lại xem bản của pháp nhân mình còn đúng không."
        )
        clone.clone_status = CLONE_STALE
        dem += 1
    return dem


def tracking(db: Session, source: Document) -> list[dict]:
    """F10 — *"12 công ty con đang ở phiên bản nào của quy chế này"*.

    Trả lời đủ bốn câu tài liệu đòi: ai đã ban hành, ai còn nháp, ai chưa đụng
    tới, ai đang lệch bản.
    """
    goc_version_id = source.current_version_id

    ket_qua: list[dict] = []
    for clone in clones_of(db, source.id):
        company = db.get(Company, clone.company_id)
        assignee = (
            db.get(Employee, clone.clone_assignee_employee_id)
            if clone.clone_assignee_employee_id else None
        )
        version = (
            db.get(DocumentVersion, clone.current_version_id)
            if clone.current_version_id else None
        )
        #  "Lệch bản" = bản clone đang bám phiên bản CŨ của gốc. Đây là câu hỏi
        #  khó trả lời nhất trong bốn câu, và là lý do cột
        #  `clone_source_version_id` tồn tại.
        lech_ban = bool(goc_version_id and clone.clone_source_version_id != goc_version_id)

        ket_qua.append({
            "document_id": clone.id,
            "company_id": clone.company_id,
            "company_name": company.name if company else "",
            "title": clone.title,
            "display_code": clone.doc_code or clone.issue_number or "",
            "status": clone.status,
            "status_label": STATUS_LABELS.get(clone.status, ""),
            "clone_status": clone.clone_status,
            "clone_status_label": CLONE_STATUS_LABELS.get(clone.clone_status, ""),
            "version_no": version.version_no if version else "",
            "is_outdated": lech_ban,
            "assignee_name": assignee.full_name if assignee else "",
            "due_date": clone.clone_due_date,
            "handled_at": clone.clone_handled_at.isoformat() if clone.clone_handled_at else "",
        })
    return ket_qua


def pending_companies(db: Session, source: Document) -> list[dict]:
    """Pháp nhân CHƯA nhận bản clone nào — phần "ai chưa đụng tới" của F10."""
    da_clone = {clone.company_id for clone in clones_of(db, source.id)}
    da_clone.add(source.company_id)

    rows = (
        db.query(Company)
        .filter(Company.is_active.is_(True), Company.id.notin_(da_clone or {0}))
        .order_by(Company.name.asc())
        .all()
    )
    return [{"company_id": row.id, "company_name": row.name} for row in rows]


def mark_handled(db: Session, clone: Document, clone_status: int, actor: int) -> Document:
    """Pháp nhân con cập nhật tình trạng xử lý bản clone của mình."""
    if clone_status not in CLONE_STATUS_LABELS:
        raise HTTPException(400, "Tình trạng bản clone không hợp lệ")
    if not clone.source_document_id:
        raise HTTPException(400, "Văn bản này không phải bản clone")

    clone.clone_status = clone_status
    if clone_status in (CLONE_ISSUED, CLONE_REJECTED):
        clone.clone_handled_at = datetime.now()
    clone.updated_by = actor
    db.commit()
    db.refresh(clone)
    return clone
