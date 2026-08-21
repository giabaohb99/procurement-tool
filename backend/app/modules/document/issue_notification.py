"""Thông báo cho thành viên khi một phiên bản văn bản được ban hành.

Danh sách người nhận KHÔNG được tự suy lại ở đây. Nó dùng thẳng
``scope_service.applies_to`` để bốn luật bao gồm/loại trừ/cho phép lại chạy
giống hệt màn «Văn bản áp dụng cho tôi».
"""
import html
import logging
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.doc_catalog.model import DocType
from app.modules.employee.model import Employee
from app.modules.notification.email_templates import DOCUMENT_ISSUED_TEMPLATE
from app.modules.notification.model import EmailLog, Notification
from app.modules.notification.service import _abs_link, render_template
from app.modules.user.model import User

from . import scope_service
from .model import Document
from .version_model import DocumentVersion

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class IssueRecipient:
    user: User
    employee: Employee
    email: str


def _email_of(user: User, employee: Employee) -> str:
    """Ưu tiên email hồ sơ nhân sự; tài khoản dạng mã NV không phải địa chỉ mail."""
    for value in (employee.email, user.email):
        address = (value or "").strip()
        if "@" in address and not address.startswith("@") and not address.endswith("@"):
            return address
    return ""


def recipients_for_issue(db: Session, document_id: int) -> list[IssueRecipient]:
    """Mọi tài khoản đang hoạt động có nhân sự thuộc phạm vi văn bản."""
    rows = (
        db.query(User, Employee)
        .join(Employee, Employee.id == User.employee_id)
        .filter(User.is_active.is_(True), Employee.is_active.is_(True))
        .order_by(User.id.asc())
        .all()
    )
    return [
        IssueRecipient(user=user, employee=employee, email=_email_of(user, employee))
        for user, employee in rows
        if scope_service.applies_to(db, document_id, employee)
    ]


def _text(value) -> str:
    return html.escape(str(value or "").strip())


def notify_document_issued(
    db: Session,
    doc: Document,
    version: DocumentVersion,
    actor: int,
) -> int:
    """Tạo chuông + email nền cho đúng tập người nhận sau khi ban hành.

    Email không hợp lệ chỉ bị bỏ qua ở kênh mail; người đó vẫn nhận chuông.
    Trả số người nhận thông báo để tiện kiểm thử và quan sát.
    """
    recipients = recipients_for_issue(db, doc.id)
    if not recipients:
        return 0

    company = db.get(Company, doc.company_id) if doc.company_id else None
    department = db.get(Department, doc.department_id) if doc.department_id else None
    doc_type = db.get(DocType, doc.doc_type_id) if doc.doc_type_id else None
    display_code = doc.doc_code or doc.issue_number or "Chưa cấp số"
    relative_link = f"/document/documents/{doc.id}?readonly=1"
    absolute_link = _abs_link(relative_link)
    effective = version.effective_from or doc.effective_date
    effective_text = effective.strftime("%d/%m/%Y") if effective else "Từ ngày ban hành"
    raw_subject = f"[Văn bản mới] {display_code} — {doc.title}"
    # Notification.title và EmailLog.subject đều VARCHAR(255). Trích yếu cho
    # phép 500 ký tự, nên phải rút gọn trước khi ghi thay vì để MySQL làm hỏng
    # toàn bộ kênh thông báo ở đúng những văn bản tên dài.
    subject = raw_subject if len(raw_subject) <= 255 else f"{raw_subject[:252]}..."
    body = (
        f"{doc.title} · Số hiệu {display_code} · "
        f"Pháp nhân ban hành: {company.name if company else '—'} · "
        f"Hiệu lực từ {effective_text}."
    )

    jobs: list[tuple[int, str, str]] = []
    for recipient in recipients:
        db.add(Notification(
            user_id=recipient.user.id,
            title=subject,
            body=body,
            link=relative_link,
            created_by=actor,
        ))
        if not recipient.email:
            continue

        email_log = EmailLog(
            event="document_issued",
            to_email=recipient.email,
            subject=subject,
            status="pending",
            created_by=actor,
        )
        db.add(email_log)
        db.flush()
        email_html = render_template(DOCUMENT_ISSUED_TEMPLATE, {
            "subject": _text(subject),
            "recipient_name": _text(recipient.employee.full_name),
            "doc_code": _text(display_code),
            "document_title": _text(doc.title),
            "doc_type": _text(doc_type.name if doc_type else "Văn bản"),
            "company": _text(company.name if company else "—"),
            "department": _text(department.name if department else "—"),
            "version_no": _text(version.version_no),
            "effective_date": _text(effective_text),
            "summary": _text(doc.summary),
            "link": _text(absolute_link),
        })
        jobs.append((email_log.id, recipient.email, email_html))

    # Task nền dùng session khác nên EmailLog và thông báo phải tồn tại trước.
    db.commit()

    from app.modules.notification.tasks import send_email_task

    for log_id, to_email, email_html in jobs:
        try:
            # Không ``force``: công tắc EMAIL_ENABLED / EMAIL_HARD_OFF vẫn là
            # hàng rào vận hành. Override email test vẫn được áp dụng ở dev/UAT.
            send_email_task.delay(log_id, to_email, subject, email_html, False, True)
        except Exception as exc:  # noqa: BLE001 — phát hành không được đổ vì broker/mail
            LOGGER.exception("Không xếp được email ban hành văn bản #%s", doc.id)
            log = db.get(EmailLog, log_id)
            if log:
                log.status = "failed"
                log.error = f"Không đưa được email vào hàng đợi: {exc}"
                db.commit()

    return len(recipients)
