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

        # Tắt gửi email (cấu hình ở trang Cấu hình hệ thống / .env EMAIL_ENABLED)
        from app.core import app_settings
        if not app_settings.get("email_enabled"):
            log.status = "disabled"
            log.error = "Email đang tắt (EMAIL_ENABLED=false)"
            db.commit()
            return

        smtp_user = app_settings.get("smtp_user")
        smtp_pass = app_settings.get("smtp_password")
        if not smtp_user or not smtp_pass:
            log.status = "failed"
            log.error = "SMTP credentials not configured in settings."
            db.commit()
            return

        # Nếu đặt EMAIL_TEST_OVERRIDE → chuyển hướng mọi email ra địa chỉ test (an toàn khi test)
        target = app_settings.get("email_test_override") or to_email

        msg = MIMEMultipart()
        msg["From"] = app_settings.get("smtp_from") or smtp_user
        msg["To"] = target
        msg["Subject"] = subject
        msg.attach(MIMEText(html_body, "html"))

        # Connect and send
        with smtplib.SMTP(app_settings.get("smtp_host"), int(app_settings.get("smtp_port") or 587)) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            from email.utils import parseaddr
            _, from_email = parseaddr(msg["From"])
            server.sendmail(from_email or msg["From"], target, msg.as_string())

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


def get_department_head_users(db: Session, department_name: str) -> list[User]:
    """Tài khoản của Trưởng bộ phận phòng ban (theo Department.manager_id chọn cứng). [] nếu chưa gán."""
    if not department_name:
        return []
    from app.modules.department.model import Department
    dep = db.query(Department).filter(Department.name == department_name).first()
    if not dep or not dep.manager_id:
        return []
    # manager_id = employee id → tìm tài khoản user gắn nhân sự đó
    return db.query(User).filter(User.employee_id == dep.manager_id, User.is_active == True).all()


def get_users_by_role_codes(db: Session, codes: list[str]) -> list[User]:
    """Tài khoản thuộc các vai trò theo mã (vd Quản lý TM / Admin TM)."""
    role_ids = [r.id for r in db.query(Role).filter(Role.code.in_(codes)).all()]
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
    link: str = "",
    department: str = "",
):
    """
    Creates an in-app notification and sends an email notification asynchronously.
    """
    creator = db.query(User).filter(User.id == creator_id).first()
    creator_name = creator.email if creator else "Hệ thống"
    
    # Generate labels and messages based on event
    doc_type_label = "Yêu cầu mua hàng" if doc_type == "purchase_request" else "Phiếu khảo sát"

    # Nhãn loại chứng từ + động từ theo hành động (dùng cho fallback rõ nghĩa, vd Đơn mua hàng)
    DOC_LABEL = {"purchase_request": "Yêu cầu mua hàng", "survey_request": "Phiếu khảo sát",
                 "purchase_order": "Đơn mua hàng", "payment_request": "Đề nghị thanh toán"}
    STATUS_VERB = {"submitted": "đã được gửi duyệt", "approved": "đã được duyệt",
                   "rejected": "đã bị từ chối", "cancelled": "đã bị hủy", "returned": "đã bị trả lại (cần sửa & gửi lại)",
                   "completed": "đã hoàn thành", "paid": "đã ghi nhận thanh toán"}

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
        # Fallback rõ nghĩa: suy nhãn loại + hành động từ event (vd "po_approved" → Đơn mua hàng … đã được duyệt)
        label = DOC_LABEL.get(doc_type, "Chứng từ")
        verb = STATUS_VERB.get(event.rsplit("_", 1)[-1], "vừa được cập nhật")
        subject = f"{label} {doc_code}"
        body = f"{label} {doc_code} {verb}."

    if is_urgent:
        subject = f"[GẤP] {subject}"

    # Xác định người nhận chuông
    if event == "pr_submitted":
        # CHỈ Trưởng bộ phận của phòng — KHÔNG fallback sang quản lý/admin (tránh spam, ~300 phiếu/ngày).
        # Chưa gán trưởng phòng thì không báo ai; quản lý vẫn thấy phiếu trong danh sách (scope all).
        recipients = get_department_head_users(db, department)
    elif event == "survey_submitted":
        # Khảo sát do Quản lý thu mua / Admin duyệt
        recipients = get_approvers_for_entity(db, doc_type)
    elif event == "pr_approved":
        # DUYỆT XONG → báo người YC + Quản lý TM + Admin TM (để phân bổ nhân sự trên line)
        recipients = ([creator] if creator else []) + get_users_by_role_codes(db, ["pur_manager", "pur_admin"])
    else:
        recipients = [creator] if creator else []

    # Khử trùng lặp người nhận
    seen_ids = set()
    recipients = [r for r in recipients if r and not (r.id in seen_ids or seen_ids.add(r.id))]

    # CHỈ tạo thông báo trong app (chuông) — KHÔNG gửi email cho workflow.
    # Email chỉ dùng cho cấp tài khoản / reset mật khẩu (hàm riêng bên dưới).
    # GỘP SỰ KIỆN: nếu người nhận đã có 1 thông báo CHƯA ĐỌC cùng chứng từ (link) trong
    # COALESCE_MINUTES phút gần đây → cập nhật cái đó thay vì tạo mới (tránh spam vd submit→approve).
    from datetime import datetime, timedelta
    COALESCE_MINUTES = 5
    now = datetime.utcnow()
    cutoff = now - timedelta(minutes=COALESCE_MINUTES)
    for recipient in recipients:
        if not recipient:
            continue
        existing = None
        if link:
            existing = (db.query(Notification)
                        .filter(Notification.user_id == recipient.id,
                                Notification.link == link,
                                Notification.is_read == False,
                                Notification.created_at >= cutoff)
                        .order_by(Notification.id.desc()).first())
        if existing:
            existing.title = subject
            existing.body = body
            existing.created_at = now      # đẩy lên mới nhất, không tăng số chưa đọc
            existing.updated_by = creator_id
        else:
            db.add(Notification(
                user_id=recipient.id,
                title=subject,
                body=body,
                link=link,
                created_by=creator_id,
            ))

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
