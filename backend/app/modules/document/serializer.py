"""Dựng bản ghi VĂN BẢN trả về cho màn hình.

Tách khỏi `service.py` vì đây thuần là việc ghép tên và đếm — không có quyết
định nghiệp vụ nào.

Nguyên tắc: **dựng cả danh sách một lượt**, không để từng dòng tự đi tra tên.
Danh sách văn bản là màn mở nhiều nhất của phân hệ; tra lẻ thì 50 dòng thành hơn
250 lượt gọi cơ sở dữ liệu.
"""
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.modules.attachment.model import FileLink
from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.doc_catalog.book_model import DocumentBook
from app.modules.doc_catalog.model import DocType
from app.modules.doc_catalog.numbering_rule_model import DocumentNumberingRule
from app.modules.employee.model import Employee

from .model import STATUS_LABELS, Document
from .version_model import VERSION_STATUS_LABELS, DocumentVersion

ATTACH_ENTITY = "document_version"


def _lookup(db: Session, model, ids, *fields) -> dict[int, tuple]:
    ids = {i for i in ids if i}
    if not ids:
        return {}
    cols = [getattr(model, f) for f in fields]
    rows = db.query(model.id, *cols).filter(model.id.in_(ids)).all()
    return {row[0]: tuple(row[1:]) for row in rows}


def serialize_many(db: Session, docs: list[Document]) -> list[dict]:
    if not docs:
        return []

    types = _lookup(db, DocType, {d.doc_type_id for d in docs}, "name", "code")
    books = _lookup(db, DocumentBook, {d.book_id for d in docs}, "name", "number_prefix")
    companies = _lookup(db, Company, {d.company_id for d in docs}, "name")
    departments = _lookup(db, Department, {d.department_id for d in docs}, "name")
    employees = _lookup(db, Employee, {
        *(d.owner_employee_id for d in docs),
        *(d.drafter_employee_id for d in docs),
        *(d.signer_employee_id for d in docs),
    }, "full_name")
    numbering_rules = _lookup(
        db,
        DocumentNumberingRule,
        {d.numbering_rule_id for d in docs},
        "allow_manual",
    )

    version_ids = [d.current_version_id for d in docs if d.current_version_id]
    versions = {
        v.id: v for v in
        db.query(DocumentVersion).filter(DocumentVersion.id.in_(version_ids)).all()
    } if version_ids else {}

    version_counts = dict(
        db.query(DocumentVersion.document_id, func.count(DocumentVersion.id))
        .filter(DocumentVersion.document_id.in_([d.id for d in docs]))
        .group_by(DocumentVersion.document_id).all()
    )
    attach_counts = dict(
        db.query(FileLink.entity_id, func.count(FileLink.id))
        .filter(FileLink.entity == ATTACH_ENTITY, FileLink.entity_id.in_(version_ids))
        .group_by(FileLink.entity_id).all()
    ) if version_ids else {}

    def name(table: dict, key, index: int = 0) -> str:
        row = table.get(key)
        return row[index] if row else ""

    out = []
    for doc in docs:
        version = versions.get(doc.current_version_id)
        out.append({
            **base_fields(doc),
            "doc_type_name": name(types, doc.doc_type_id),
            "doc_type_code": name(types, doc.doc_type_id, 1),
            "company_name": name(companies, doc.company_id),
            "department_name": name(departments, doc.department_id),
            "owner_name": name(employees, doc.owner_employee_id),
            "drafter_name": name(employees, doc.drafter_employee_id),
            "signer_name": name(employees, doc.signer_employee_id),
            "book_name": name(books, doc.book_id),
            "book_number_display": _book_number(
                name(books, doc.book_id, 1), doc.book_seq_no, doc.book_year),
            "version_no": version.version_no if version else "",
            "version_count": version_counts.get(doc.id, 0),
            "attachment_count": attach_counts.get(doc.current_version_id, 0),
            "allow_manual_number": bool(
                numbering_rules.get(doc.numbering_rule_id, (False,))[0]
                and doc.issue_number
            ),
        })
    return out


def serialize(db: Session, doc: Document) -> dict:
    return serialize_many(db, [doc])[0]


def base_fields(doc: Document) -> dict:
    return {
        "id": doc.id,
        "origin": doc.origin,
        "doc_code": doc.doc_code,
        "issue_number": doc.issue_number,
        #  Số hiện trên bảng: mã bất biến nếu có, không thì số theo sổ.
        "display_code": doc.doc_code or doc.issue_number or "",
        "seq_no": doc.seq_no,
        "issue_year": doc.issue_year,
        "legacy_code": doc.legacy_code,
        "doc_type_id": doc.doc_type_id,
        "company_id": doc.company_id,
        "department_id": doc.department_id,
        "owner_employee_id": doc.owner_employee_id,
        "drafter_employee_id": doc.drafter_employee_id,
        "signer_employee_id": doc.signer_employee_id,
        "title": doc.title,
        "summary": doc.summary,
        "keywords": doc.keywords,
        "secrecy_level": doc.secrecy_level,
        "urgency": doc.urgency,
        "status": doc.status,
        "status_label": STATUS_LABELS.get(doc.status, str(doc.status)),
        "effective_date": doc.effective_date,
        "expire_date": doc.expire_date,
        "current_version_id": doc.current_version_id,
        #  Bản gốc của BẢN RIÊNG. Danh sách dựa vào cột này để thụt lề dòng con
        #  và để biết dòng nào là bản riêng của dòng nào.
        "source_document_id": doc.source_document_id,
        #  F13 — cơ chế áp dụng, hộp thoại ban hành chọn sẵn theo giá trị này.
        "apply_mode": doc.apply_mode,
        #  Băng "cần rà lại" trên trang chi tiết đọc thẳng hai cột này (E11 a/b).
        "needs_review": doc.needs_review,
        "needs_review_note": doc.needs_review_note,
        #  Số VÀO SỔ — khác `issue_number` (số đi ra ngoài). Xem
        #  `service.assign_book_number`.
        "book_id": doc.book_id,
        "book_seq_no": doc.book_seq_no,
        "book_year": doc.book_year,
        "created_at": doc.created_at.isoformat() if doc.created_at else "",
    }


def _book_number(prefix: str, seq: int | None, year: int | None) -> str:
    """`CVĐ 08/2026` — chuỗi số vào sổ để hiển thị. Chưa vào sổ thì rỗng."""
    if not seq:
        return ""
    body = f"{seq:02d}/{year}" if year else f"{seq:02d}"
    return f"{prefix} {body}".strip()


def serialize_version(db: Session, version: DocumentVersion, doc: Document,
                      with_content: bool = False) -> dict:
    approvers = _lookup(db, Employee, {version.approved_by}, "full_name")
    data = {
        "id": version.id,
        "document_id": version.document_id,
        "version_no": version.version_no,
        "major": version.major,
        "minor": version.minor,
        "status": version.status,
        "status_label": VERSION_STATUS_LABELS.get(version.status, str(version.status)),
        "is_locked": version.is_locked,
        "change_kind": version.change_kind,
        "change_summary": version.change_summary,
        "change_reason": version.change_reason,
        "requires_reconfirm": version.requires_reconfirm,
        "effective_from": version.effective_from,
        "content_sha256": version.content_sha256,
        "prev_version_id": version.prev_version_id,
        "approved_at": version.approved_at.isoformat() if version.approved_at else "",
        "approved_by_name": approvers.get(version.approved_by, ("",))[0],
        "created_by_name": holder_name(db, version.created_by),
        "created_at": version.created_at.isoformat() if version.created_at else "",
        #  Bản đang được văn bản dùng — băng cảnh báo "đã bị thay thế" dựa vào đây.
        "is_current": doc.current_version_id == version.id,
    }
    if with_content:
        data["content_html"] = version.content_html or ""
    return data


def serialize_access(db: Session, rows: list) -> list[dict]:
    """Bảng chia sẻ của một văn bản, đã ghép TÊN của đối tượng.

    Tên tra một lượt theo từng loại đối tượng — bảng này thường 3–10 dòng, nhưng
    để mỗi dòng tự tra thì vẫn là 10 lượt gọi cho một cái bảng con.
    """
    from app.modules.company.model import Company
    from app.modules.department.model import Department
    from app.modules.role.model import Role

    from .access_model import (EFFECT_LABELS, SUBJECT_COMPANY, SUBJECT_DEPARTMENT,
                               SUBJECT_EMPLOYEE, SUBJECT_LABELS, SUBJECT_ROLE)

    if not rows:
        return []

    by_kind = {
        SUBJECT_EMPLOYEE: (Employee, "full_name"),
        SUBJECT_DEPARTMENT: (Department, "name"),
        SUBJECT_COMPANY: (Company, "name"),
        SUBJECT_ROLE: (Role, "name"),
    }
    names: dict[int, dict[int, str]] = {}
    for kind, (model, field) in by_kind.items():
        ids = {r.subject_id for r in rows if r.subject_kind == kind}
        names[kind] = {k: v[0] for k, v in _lookup(db, model, ids, field).items()}

    return [{
        "id": row.id,
        "document_id": row.document_id,
        "subject_kind": row.subject_kind,
        "subject_kind_label": SUBJECT_LABELS.get(row.subject_kind, ""),
        "subject_id": row.subject_id,
        "subject_name": names.get(row.subject_kind, {}).get(row.subject_id, ""),
        "effect": row.effect,
        "effect_label": EFFECT_LABELS.get(row.effect, ""),
        "can_read": row.can_read,
        "can_write": row.can_write,
        "can_delete": row.can_delete,
        "valid_from": row.valid_from,
        "valid_to": row.valid_to,
        "reason": row.reason,
        #  Thu hồi rồi thì dòng vẫn ở lại bảng, chỉ tắt cờ này (G19, G20).
        "is_active": row.revoked_at is None,
        "revoked_at": row.revoked_at.isoformat() if row.revoked_at else "",
        "revoked_by_name": holder_name(db, row.revoked_by),
        "revoke_reason": row.revoke_reason,
        "granted_by_name": holder_name(db, row.created_by),
        "created_at": row.created_at.isoformat() if row.created_at else "",
    } for row in rows]


def holder_name(db: Session, user_id: int) -> str:
    """Tên người giữ bản nháp. `created_by` là id TÀI KHOẢN, không phải nhân sự.

    Dùng trong câu báo lỗi "bản nháp 2.0 đang do ông X giữ" — không có tên thì
    người thứ hai chỉ thấy "không mở được" mà không biết hỏi ai.
    """
    if not user_id:
        return ""
    from app.modules.user.model import User
    user = db.get(User, user_id)
    if not user:
        return ""
    employee = db.get(Employee, user.employee_id) if user.employee_id else None
    return employee.full_name if employee else (user.email or "")
