"""SAO CHÉP VĂN BẢN thành một bản ghi nháp độc lập.

Khác hoàn toàn ``clone_service``: clone nghiệp vụ tạo bản riêng cho một pháp
nhân khác và giữ liên kết về bản gốc. Hàm trong tệp này chỉ giúp người dùng tạo
nhanh dữ liệu thử trong CÙNG pháp nhân. Bản sao không thuộc cây clone, không
mang số hiệu/trạng thái duyệt của nguồn và có thể xóa như mọi bản nháp mới.
"""

from sqlalchemy.orm import Session

from app.modules.attachment.model import FileLink

from . import service
from .access_model import DocumentAccess
from .link_model import DocumentLink
from .model import STATUS_DRAFT, Document
from .scope_model import DocumentScope
from .version_model import VERSION_DRAFT, DocumentVersion


def duplicate(db: Session, source: Document, actor: int) -> Document:
    """Tạo một văn bản nháp độc lập, chép dữ liệu đang nhìn thấy ở bản nguồn.

    Những thứ được chép: bộ trường chung, nội dung + thể thức phiên bản đang mở
    (nếu có), tệp đính kèm, phạm vi ban hành, quyền đặc cách đang còn hiệu lực
    và các quan hệ khai tay đi ra từ văn bản.

    Những thứ bắt buộc làm mới: ID, trạng thái, số hiệu/số vào sổ, dấu duyệt,
    quan hệ clone, lịch sử phê duyệt và quan hệ hệ thống. Đây là dữ liệu nhận
    diện/pháp lý của bản cũ, chép nguyên sẽ tạo hai hồ sơ cùng số hoặc làm bản
    thử bị hiểu nhầm là bản clone xuống pháp nhân con.
    """
    doc_type = service.doc_type_or_400(db, source.doc_type_id)
    base = _version_to_copy(db, source)

    copied = Document(
        origin=source.origin,
        doc_type_id=source.doc_type_id,
        company_id=source.company_id,
        department_id=source.department_id,
        owner_employee_id=source.owner_employee_id,
        drafter_employee_id=source.drafter_employee_id,
        signer_employee_id=source.signer_employee_id,
        # Nhìn tên là phân biệt được ngay dữ liệu thử với hồ sơ nguồn. Giữ hậu
        # tố ngắn, quen thuộc để cả bảng danh sách không bị kéo dài quá mức.
        title=f"{source.title} (Copy)",
        summary=source.summary,
        keywords=source.keywords,
        secrecy_level=source.secrecy_level,
        urgency=source.urgency,
        status=STATUS_DRAFT,
        effective_date=source.effective_date,
        expire_date=source.expire_date,
        next_review_date=source.next_review_date,
        legacy_code=source.legacy_code,
        storage_location=source.storage_location,
        apply_mode=source.apply_mode,
        legal_issuer=source.legal_issuer,
        legal_url=source.legal_url,
        recipient_summary=source.recipient_summary,
        copies=source.copies,
        register_note=source.register_note,
        book_id=source.book_id,
        is_active=True,
        # Không chép doc_code/issue_number/seq/book_seq hay bất kỳ cột clone nào.
        created_by=actor,
        updated_by=actor,
    )
    db.add(copied)
    db.flush()

    # Loại cấp số ngay khi tạo nháp vẫn phải chạy đúng quy tắc và lấy số MỚI.
    if doc_type.number_when == service.NUMBER_ON_DRAFT:
        service.numbering.assign(db, copied, doc_type, service.issue_year(copied))

    version = DocumentVersion(
        document_id=copied.id,
        major=1,
        minor=0,
        status=VERSION_DRAFT,
        content_html=base.content_html,
        margin_left_mm=base.margin_left_mm,
        margin_right_mm=base.margin_right_mm,
        auto_heading_number=base.auto_heading_number,
        header_left=base.header_left,
        header_right=base.header_right,
        footer_left=base.footer_left,
        footer_right=base.footer_right,
        effective_from=base.effective_from,
        created_by=actor,
        updated_by=actor,
    )
    db.add(version)
    db.flush()
    copied.current_version_id = version.id

    _copy_attachments(db, base.id, version.id, actor)
    _copy_scopes(db, source.id, copied.id, actor)
    _copy_live_access(db, source.id, copied.id, actor)
    _copy_manual_links(db, source.id, copied.id, actor)

    db.commit()
    db.refresh(copied)
    return copied


def _version_to_copy(db: Session, source: Document) -> DocumentVersion:
    # Trang chi tiết ưu tiên bản đang mở; thao tác sao chép phải lấy cùng phần
    # nội dung người dùng đang nhìn, không âm thầm lùi về bản đã duyệt cũ.
    version = service.open_version(db, source)
    if version is None and source.current_version_id:
        version = db.get(DocumentVersion, source.current_version_id)
    if version is None:
        version = (
            db.query(DocumentVersion)
            .filter(DocumentVersion.document_id == source.id)
            .order_by(DocumentVersion.major.desc(), DocumentVersion.minor.desc())
            .first()
        )
    if version is None:
        from fastapi import HTTPException

        raise HTTPException(400, "Văn bản nguồn chưa có phiên bản để sao chép")
    return version


def _copy_attachments(
    db: Session, source_version_id: int, target_version_id: int, actor: int,
) -> None:
    rows = (
        db.query(FileLink)
        .filter(FileLink.entity == service.ATTACH_ENTITY,
                FileLink.entity_id == source_version_id)
        .all()
    )
    for row in rows:
        db.add(FileLink(
            file_id=row.file_id,
            entity=service.ATTACH_ENTITY,
            entity_id=target_version_id,
            purchase_order_id=row.purchase_order_id,
            doc_type=row.doc_type,
            sort_order=row.sort_order,
            created_by=actor,
            updated_by=actor,
        ))


def _copy_scopes(db: Session, source_id: int, target_id: int, actor: int) -> None:
    for row in db.query(DocumentScope).filter(DocumentScope.document_id == source_id).all():
        db.add(DocumentScope(
            document_id=target_id,
            dim=row.dim,
            company_id=row.company_id,
            department_id=row.department_id,
            employee_id=row.employee_id,
            include_children=row.include_children,
            mode=row.mode,
            created_by=actor,
            updated_by=actor,
        ))


def _copy_live_access(db: Session, source_id: int, target_id: int, actor: int) -> None:
    rows = (
        db.query(DocumentAccess)
        .filter(DocumentAccess.document_id == source_id,
                DocumentAccess.revoked_at.is_(None))
        .all()
    )
    for row in rows:
        db.add(DocumentAccess(
            document_id=target_id,
            subject_kind=row.subject_kind,
            subject_id=row.subject_id,
            effect=row.effect,
            can_read=row.can_read,
            can_write=row.can_write,
            can_delete=row.can_delete,
            valid_from=row.valid_from,
            valid_to=row.valid_to,
            reason=row.reason,
            created_by=actor,
            updated_by=actor,
        ))


def _copy_manual_links(db: Session, source_id: int, target_id: int, actor: int) -> None:
    rows = (
        db.query(DocumentLink)
        .filter(DocumentLink.source_document_id == source_id,
                DocumentLink.is_system.is_(False))
        .all()
    )
    for row in rows:
        db.add(DocumentLink(
            source_document_id=target_id,
            target_document_id=row.target_document_id,
            relation=row.relation,
            rule_id=row.rule_id,
            note=row.note,
            is_system=False,
            created_by=actor,
            updated_by=actor,
        ))
