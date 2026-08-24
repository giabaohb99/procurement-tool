"""THƯ BÁO BÃI BỎ cho pháp nhân con đang giữ bản riêng.

Bản gốc bị bãi bỏ là tin nặng nhất trong cả vòng đời văn bản: pháp nhân con đang
áp dụng một bản riêng **căn cứ theo** một văn bản vừa chết. Trước ngày
24/08/2026, `service.revoke` chỉ lặng lẽ bật cờ «cần rà lại» lên văn bản con qua
`parent_change_service.apply_obsolete` và **không báo cho ai một tiếng nào** —
người phụ trách bản riêng chỉ biết khi nào tình cờ mở văn bản đó ra.

Gửi **hai đường**, cùng lý lẽ với `clone_notification.py`: chuông luôn ghi được
và nằm trong cùng transaction; thư điện tử phụ thuộc SMTP nên có hỏng cũng không
được kéo đổ việc bãi bỏ.

Người nhận lấy đúng bộ chọn của thư clone (`_users_of_company`): có người phụ
trách bản riêng thì gửi đúng người, không thì gửi mọi tài khoản đang hoạt động
của pháp nhân đó — thà nhiều người nhận còn hơn không ai biết văn bản mình đang
theo đã bị bãi bỏ.
"""
import logging

from sqlalchemy.orm import Session

from app.modules.employee.model import Employee
from app.modules.notification.email_templates import DOCUMENT_REVOKED_TEMPLATE
from app.modules.notification.model import EmailLog, Notification
from app.modules.notification.service import _abs_link, render_template

from .clone_notification import _users_of_company
from .issue_notification import _email_of, _text
from .model import Document

LOGGER = logging.getLogger(__name__)


def notify_clones_revoked(db: Session, source: Document, reason: str, actor: int) -> int:
    """Báo cho mọi pháp nhân con có bản riêng. Trả về số người đã báo.

    ⚠️ Gọi **sau** khi việc bãi bỏ đã commit và bọc trong `try/except` ở chỗ gọi:
    văn bản đã bãi bỏ rồi, không được để một cái thư kéo đổ nó.
    """
    from .clone_service import clones_of

    clones = clones_of(db, source.id)
    if not clones:
        return 0

    goc = source.doc_code or source.issue_number or source.title
    subject = f"Văn bản gốc đã bãi bỏ: {goc}"
    jobs: list[tuple[int, str, str]] = []
    da_bao: set[int] = set()

    for clone in clones:
        for user in _users_of_company(db, clone.company_id, clone.clone_assignee_employee_id):
            #  Một người phụ trách nhiều pháp nhân thì chỉ nhận MỘT thư: cùng
            #  một tin, gửi ba lần là người ta bắt đầu bỏ qua cả ba.
            if user.id in da_bao:
                continue
            da_bao.add(user.id)

            db.add(Notification(
                user_id=user.id,
                title=subject,
                body=(
                    f"Văn bản gốc «{goc}» đã bị bãi bỏ. "
                    f"Bản riêng «{clone.title}» của pháp nhân bạn đang căn cứ theo văn bản này "
                    f"— mở ra rà lại xem còn dùng được không."
                ),
                #  Trỏ vào BẢN RIÊNG chứ không vào bản gốc: người nhận thường
                #  không còn quyền xem bản gốc sau khi nó bị bãi bỏ (xem
                #  `revoke_access.py`), bấm vào chỉ nhận 404.
                link=f"/document/documents/{clone.id}",
                created_by=actor,
            ))

            #  Địa chỉ thư ưu tiên hồ sơ NHÂN SỰ — tài khoản đăng nhập ở đây
            #  thường là mã nhân viên chứ không phải một địa chỉ thật.
            employee = db.get(Employee, user.employee_id) if user.employee_id else None
            email = _email_of(user, employee) if employee else ""
            if not email:
                continue

            email_log = EmailLog(
                event="document_revoked",
                to_email=email,
                subject=subject,
                status="pending",
                created_by=actor,
            )
            db.add(email_log)
            db.flush()
            jobs.append((email_log.id, email, render_template(DOCUMENT_REVOKED_TEMPLATE, {
                "subject": _text(subject),
                "doc_code": _text(goc),
                "document_title": _text(source.title),
                "clone_title": _text(clone.title),
                "reason": _text(reason),
                "link": _text(_abs_link(f"/document/documents/{clone.id}")),
            })))

    # Task nền dùng session khác nên EmailLog phải tồn tại trước khi xếp hàng.
    db.commit()

    from app.modules.notification.tasks import send_email_task

    for log_id, to_email, email_html in jobs:
        try:
            send_email_task.delay(log_id, to_email, subject, email_html, False, True)
        except Exception as exc:  # noqa: BLE001 — bãi bỏ không được đổ vì broker/mail
            LOGGER.exception("Không xếp được email bãi bỏ văn bản #%s", source.id)
            log = db.get(EmailLog, log_id)
            if log:
                log.status = "failed"
                log.error = f"Không đưa được email vào hàng đợi: {exc}"
                db.commit()

    return len(da_bao)
