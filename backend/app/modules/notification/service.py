import smtplib
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.user.model import User, UserRole
from app.modules.role.model import Role, Permission
from .model import Notification, EmailLog
from .email_templates import HTML_LAYOUT


def render_template(html: str, context: dict) -> str:
    """A self-contained custom template engine replacing Jinja2 with regex matching."""
    # Process {% if cond %} ... {% endif %}
    def replace_if(match):
        cond = match.group(1).strip()
        body = match.group(2)
        val = context.get(cond, False)
        return body if val else ""
        
    html = re.sub(r'\{%\s*if\s+(\w+)\s*%\}(.*?)\{%\s*endif\s*%\}', replace_if, html, flags=re.DOTALL)
    
    # Process {{ var }}
    for k, v in context.items():
        html = html.replace(f"{{{{ {k} }}}}", str(v if v is not None else ""))
        html = html.replace(f"{{{{{k}}}}}", str(v if v is not None else ""))
        
    return html


def send_smtp_email(db_session_factory, log_id: int, to_email: str, subject: str, html_body: str):
    """
    Sends SMTP email and updates the EmailLog status.
    Uses a new session to run safely in background tasks.
    """
    db = db_session_factory()
    try:
        log = db.query(EmailLog).filter(EmailLog.id == log_id).first()
        if not log:
            return
            
        if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            log.status = "failed"
            log.error = "SMTP credentials not configured in settings."
            db.commit()
            return

        msg = MIMEMultipart()
        msg["From"] = settings.SMTP_FROM or settings.SMTP_USER
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(html_body, "html"))

        # Connect and send
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            from email.utils import parseaddr
            _, from_email = parseaddr(msg["From"])
            server.sendmail(from_email or msg["From"], to_email, msg.as_string())

        log.status = "sent"
        log.sent_at = datetime.utcnow()
        db.commit()
    except Exception as ex:
        db.rollback()
        log = db.query(EmailLog).filter(EmailLog.id == log_id).first()
        if log:
            log.status = "failed"
            log.error = str(ex)
            db.commit()
    finally:
        db.close()


def get_approvers_for_entity(db: Session, entity: str) -> list[User]:
    """Gets all active users who have approval permission for the given entity."""
    role_ids = [p.role_id for p in db.query(Permission).filter(Permission.entity == entity, Permission.can_approve == True).all()]
    if not role_ids:
        qltm_role = db.query(Role).filter(Role.code == "qltm").first()
        if qltm_role:
            role_ids = [qltm_role.id]
            
    if not role_ids:
        return []
        
    user_ids = [ur.user_id for ur in db.query(UserRole).filter(UserRole.role_id.in_(role_ids)).all()]
    if not user_ids:
        return []
        
    return db.query(User).filter(User.id.in_(user_ids), User.is_active == True).all()


def trigger_notification(
    db: Session,
    event: str,
    doc_type: str,
    doc_code: str,
    creator_id: int,
    background_tasks,
    reason: str = "",
    approve_note: str = "",
    is_urgent: bool = False,
    link: str = ""
):
    """
    Creates an in-app notification and sends an email notification asynchronously.
    """
    creator = db.query(User).filter(User.id == creator_id).first()
    creator_name = creator.email if creator else "Hệ thống"
    
    # Generate labels and messages based on event
    doc_type_label = "Yêu cầu mua hàng" if doc_type == "purchase_request" else "Phiếu khảo sát"
    
    if event == "pr_submitted":
        subject = f"[Yêu cầu phê duyệt] PYC {doc_code}"
        body = f"Có một yêu cầu mua hàng mới (Mã số: {doc_code}) cần bạn phê duyệt."
    elif event == "pr_approved":
        subject = f"[Đã duyệt] PYC {doc_code}"
        body = f"Yêu cầu mua hàng {doc_code} của bạn đã được phê duyệt."
    elif event == "pr_rejected":
        subject = f"[Từ chối] PYC {doc_code}"
        body = f"Yêu cầu mua hàng {doc_code} của bạn đã bị từ chối phê duyệt."
    elif event == "survey_submitted":
        subject = f"[Yêu cầu phê duyệt] Khảo sát {doc_code}"
        body = f"Có một phiếu khảo sát mới (Mã số: {doc_code}) cần bạn phê duyệt."
    elif event == "survey_approved":
        subject = f"[Đã duyệt] Khảo sát {doc_code}"
        body = f"Phiếu khảo sát {doc_code} của bạn đã được phê duyệt."
    elif event == "survey_rejected":
        subject = f"[Từ chối] Khảo sát {doc_code}"
        body = f"Phiếu khảo sát {doc_code} của bạn đã bị từ chối phê duyệt."
    else:
        subject = f"Thông báo mới: {doc_code}"
        body = f"Chứng từ {doc_code} vừa có thay đổi trạng thái."

    if is_urgent:
        subject = f"[GẤP] {subject}"

    # Determine recipients
    if event in ["pr_submitted", "survey_submitted"]:
        recipients = get_approvers_for_entity(db, doc_type)
    else:
        recipients = [creator] if creator else []

    # Insert Notification and EmailLog for each recipient
    for recipient in recipients:
        if not recipient:
            continue
            
        # 1. In-app notification
        notif = Notification(
            user_id=recipient.id,
            title=subject,
            body=body,
            link=link,
            created_by=creator_id
        )
        db.add(notif)
        
        # 2. Email log & sending
        if recipient.email:
            email_log = EmailLog(
                event=event,
                to_email=recipient.email,
                subject=subject,
                status="pending",
                created_by=creator_id
            )
            db.add(email_log)
            db.flush() # get email_log.id
            
            # Render template
            html_content = render_template(HTML_LAYOUT, {
                "subject": subject,
                "is_urgent": is_urgent,
                "intro_message": body,
                "doc_type": doc_type_label,
                "doc_code": doc_code,
                "creator": creator_name,
                "reason": reason,
                "approve_note": approve_note,
                "link": link
            })
            
            # Enqueue task
            from app.core.database import SessionLocal
            background_tasks.add_task(
                send_smtp_email,
                SessionLocal,
                email_log.id,
                recipient.email,
                subject,
                html_content
            )
            
    db.commit()

def send_account_creation_email(db: Session, user_id: int, background_tasks, full_name: str, email: str, link: str):
    from .email_templates import ACCOUNT_CREATION_TEMPLATE
    
    subject = "Thông Báo Cấp Tài Khoản Hệ Thống Dego ERP"
    login_url = settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else "http://localhost:5173"
    
    email_log = EmailLog(
        event="account_creation",
        to_email=email,
        subject=subject,
        status="pending",
        created_by=user_id
    )
    db.add(email_log)
    db.flush()
    
    html_content = render_template(ACCOUNT_CREATION_TEMPLATE, {
        "full_name": full_name,
        "email": email,
        "login_url": login_url,
        "link": link
    })
    
    from app.core.database import SessionLocal
    background_tasks.add_task(
        send_smtp_email,
        SessionLocal,
        email_log.id,
        email,
        subject,
        html_content
    )
    db.commit()

def send_password_reset_email(db: Session, user_id: int, background_tasks, full_name: str, email: str, link: str):
    from .email_templates import PASSWORD_RESET_TEMPLATE
    
    subject = "Yêu Cầu Thiết Lập Lại Mật Khẩu"
    
    email_log = EmailLog(
        event="password_reset",
        to_email=email,
        subject=subject,
        status="pending",
        created_by=user_id
    )
    db.add(email_log)
    db.flush()
    
    html_content = render_template(PASSWORD_RESET_TEMPLATE, {
        "full_name": full_name,
        "email": email,
        "link": link
    })
    
    from app.core.database import SessionLocal
    background_tasks.add_task(
        send_smtp_email,
        SessionLocal,
        email_log.id,
        email,
        subject,
        html_content
    )
    db.commit()
