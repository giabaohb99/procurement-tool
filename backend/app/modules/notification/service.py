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


def _abs_link(link: str) -> str:
    """Chuyển link tương đối (vd '/purchase-requests/83') thành URL tuyệt đối theo FRONTEND_URL
    để nút trong email bấm được. Link đã là http(s) thì giữ nguyên (vd link reset mật khẩu)."""
    link = (link or "").strip()
    base = (getattr(settings, "FRONTEND_URL", "") or "").rstrip("/")
    if not link:
        return base
    if link.startswith("http://") or link.startswith("https://"):
        return link
    return f"{base}/{link.lstrip('/')}"


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


def send_smtp_email(db_session_factory, log_id: int, to_email: str, subject: str, html_body: str, force: bool = False, apply_override: bool = True):
    """
    Sends SMTP email and updates the EmailLog status.
    Uses a new session to run safely in background tasks.
    force=True: gửi bất kể công tắc email_enabled (dùng cho email thiết yếu như reset mật khẩu).
    apply_override=False: KHÔNG áp email_test_override (dùng cho email workflow đã tự định tuyến
      sẵn về hộp thư test theo vai trò — tránh bị gộp hết về 1 địa chỉ override).
    """
    db = db_session_factory()
    try:
        log = db.query(EmailLog).filter(EmailLog.id == log_id).first()
        if not log:
            return

        # Chặn CỨNG theo môi trường (.env EMAIL_HARD_OFF) — vượt cả force. Dùng cho dev/UAT
        # để không bao giờ gửi mail thật kể cả reset mật khẩu / cấp tài khoản.
        from app.core.config import settings as _cfg
        if getattr(_cfg, "EMAIL_HARD_OFF", False):
            log.status = "disabled"
            log.error = "Email bị chặn cứng ở môi trường này (EMAIL_HARD_OFF=true)"
            db.commit()
            return

        # Tắt gửi email (cấu hình ở trang Cấu hình hệ thống / .env EMAIL_ENABLED).
        # force=True bỏ qua công tắc này (email thiết yếu, người dùng chủ động yêu cầu).
        from app.core import app_settings
        if not force and not app_settings.get("email_enabled"):
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

        # Nếu đặt EMAIL_TEST_OVERRIDE → chuyển hướng mọi email ra địa chỉ test (an toàn khi test).
        # apply_override=False: email workflow đã tự định tuyến theo vai trò → giữ nguyên địa chỉ.
        target = (app_settings.get("email_test_override") if apply_override else "") or to_email

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
    """Gets all active users who have approval permission for the given entity,
    EXCLUDING system admin roles (admin, ADMINISTRATOR)."""
    # 1. Lấy role_ids có quyền approve
    role_ids = [p.role_id for p in db.query(Permission).filter(Permission.entity == entity, Permission.can_approve == True).all()]
    
    # 2. Loại trừ các vai trò Quản trị viên hệ thống (admin / ADMINISTRATOR)
    admin_roles = db.query(Role).filter(Role.code.in_(["admin", "ADMINISTRATOR", "admin_system"])).all()
    admin_role_ids = {r.id for r in admin_roles}
    role_ids = [rid for rid in role_ids if rid not in admin_role_ids]

    if not role_ids:
        qltm_role = db.query(Role).filter(Role.code == "pur_manager").first()
        if qltm_role:
            role_ids = [qltm_role.id]
            
    if not role_ids:
        return []
        
    user_ids = [ur.user_id for ur in db.query(UserRole).filter(UserRole.role_id.in_(role_ids)).all()]
    if not user_ids:
        return []

    users = db.query(User).filter(User.id.in_(user_ids), User.is_active == True).all()
    if admin_role_ids:
        admin_uids = {ur.user_id for ur in db.query(UserRole).filter(UserRole.role_id.in_(admin_role_ids)).all()}
        users = [u for u in users if u.id not in admin_uids]
    return users


def _resolve_dept(db: Session, department_id: int = 0, department_name: str = ""):
    """Phòng ban của phiếu — CR-086: ưu tiên ID; phiếu cũ chưa có id mới dò theo TÊN.

    Dò theo tên là chỗ hỏng âm thầm cũ: đổi tên phòng một cái là thông báo "cần duyệt" gửi
    cho KHÔNG AI mà không có lỗi nào. Giờ vẫn trả None được, nhưng có ghi log để còn lần ra.
    """
    import logging

    from app.modules.department.model import Department
    if department_id:
        dep = db.get(Department, department_id)
        if dep:
            return dep
    name = (department_name or "").strip()
    if not name:
        return None
    dep = db.query(Department).filter(Department.name == name).first()
    if not dep:
        logging.getLogger(__name__).warning(
            "Khong tim ra phong ban de gui thong bao duyet: id=%s ten=%r", department_id, name)
    return dep


def get_department_head_users(db: Session, department_name: str = "", department_id: int = 0) -> list[User]:
    """Tài khoản của Trưởng bộ phận phòng ban (theo Department.manager_id chọn cứng). [] nếu chưa gán."""
    dep = _resolve_dept(db, department_id, department_name)
    if not dep or not dep.manager_id:
        return []
    # manager_id = employee id → tìm tài khoản user gắn nhân sự đó
    return db.query(User).filter(User.employee_id == dep.manager_id, User.is_active == True).all()


def get_dept_approver_recipients(db: Session, department_name: str = "", department_id: int = 0) -> list[User]:
    """Người nhận thông báo "cần duyệt" của 1 phòng ban — GỘP 2 nguồn:
      (1) Trưởng bộ phận đặt cứng ở ô Department.manager_id (1 người);
      (2) MỌI tài khoản có vai trò dept_head thuộc chính phòng đó (theo Employee.department_id).
    Union + khử trùng lặp. Dùng cho pr_submitted/sr_submitted để cả trưởng phòng chính lẫn
    người được tạm quyền trưởng phòng (gán vai trò dept_head + cùng phòng) đều nhận báo."""
    from app.modules.employee.model import Employee

    dep = _resolve_dept(db, department_id, department_name)
    if not dep:
        return []

    out: dict[int, User] = {}
    # (1) Trưởng bộ phận chỉ định (manager_id)
    for u in get_department_head_users(db, department_id=dep.id):
        out[u.id] = u

    # (2) Tài khoản có vai trò dept_head và nhân sự thuộc phòng này
    dh_role_ids = [r.id for r in db.query(Role).filter(Role.code == "dept_head").all()]
    if dh_role_ids:
        uids = [ur.user_id for ur in db.query(UserRole).filter(UserRole.role_id.in_(dh_role_ids)).all()]
        emp_ids = [e.id for e in db.query(Employee).filter(Employee.department_id == dep.id).all()]
        if uids and emp_ids:
            for u in (db.query(User)
                      .filter(User.id.in_(uids), User.employee_id.in_(emp_ids), User.is_active == True)
                      .all()):
                out[u.id] = u
    return list(out.values())


def get_users_by_role_codes(db: Session, codes: list[str]) -> list[User]:
    """Tài khoản thuộc các vai trò theo mã (vd Quản lý TM / Admin TM)."""
    role_ids = [r.id for r in db.query(Role).filter(Role.code.in_(codes)).all()]
    if not role_ids:
        return []
    user_ids = [ur.user_id for ur in db.query(UserRole).filter(UserRole.role_id.in_(role_ids)).all()]
    if not user_ids:
        return []
    return db.query(User).filter(User.id.in_(user_ids), User.is_active == True).all()


# Nhóm vai trò "quản lý/duyệt" — dùng để định tuyến email test về hộp thư quản lý.
# Ngoài danh sách này (vd nhân viên yêu cầu, nhân viên thu mua) coi là nhóm "nhân viên".
_MANAGER_ROLE_CODES = {
    "admin", "ADMINISTRATOR", "pur_manager", "pur_admin",
    "dept_head", "manager", "MANAGER", "manager_purchase", "company_head",
}


def _role_codes_of(db: Session, user_id: int) -> set[str]:
    """Tập mã vai trò của 1 user (rỗng nếu chưa gán)."""
    role_ids = [ur.role_id for ur in db.query(UserRole).filter(UserRole.user_id == user_id).all()]
    if not role_ids:
        return set()
    return {r.code for r in db.query(Role).filter(Role.id.in_(role_ids)).all()}


def _test_route_email(db: Session, user: User) -> str:
    """Địa chỉ hộp thư test theo NHÓM VAI TRÒ của người nhận (khi EMAIL_TEST_MANAGER/STAFF được đặt).
    Có vai trò quản lý / Trưởng bộ phận → hộp quản lý; ngược lại → hộp nhân viên. Trống cấu hình → email thật của user."""
    mgr = (settings.EMAIL_TEST_MANAGER or "").strip()
    stf = (settings.EMAIL_TEST_STAFF or "").strip()
    if not mgr and not stf:
        return user.email or ""
    codes = _role_codes_of(db, user.id)
    is_manager = bool(codes & _MANAGER_ROLE_CODES)
    if not is_manager and getattr(user, "employee_id", 0):
        try:
            from app.modules.department.model import Department
            is_manager = db.query(Department).filter(Department.manager_id == user.employee_id).first() is not None
        except Exception:
            pass
    return (mgr if is_manager else stf) or user.email or ""


def get_user_display_name(db: Session, user: User | None) -> str:
    """Trả về Họ tên nhân sự của User (nếu có); fallback về email hoặc mã tài khoản."""
    if not user:
        return ""
    if getattr(user, "employee_id", 0):
        try:
            from app.modules.employee.model import Employee
            emp = db.get(Employee, user.employee_id)
            if emp and emp.full_name:
                return emp.full_name
        except Exception:
            pass
    return user.email or f"Tài khoản #{user.id}"


def _send_workflow_emails(db: Session, background_tasks, recipients: list, subject: str, body: str,
                          doc_type: str, doc_code: str, creator_name: str,
                          reason: str, approve_note: str, is_urgent: bool, link: str):
    """Gửi EMAIL cho từng người nhận của luồng duyệt — CHỈ khi EMAIL_WORKFLOW_ENABLED (dev/UAT).
    Định tuyến về hộp thư test theo vai trò; dùng template HTML_LAYOUT. Gửi nền, không chặn luồng."""
    if not getattr(settings, "EMAIL_WORKFLOW_ENABLED", False):
        return
    from app.core.database import SessionLocal
    import re
    # Tự động trích xuất mã chứng từ nếu doc_code bị rỗng
    if not doc_code:
        m = re.search(r'([A-Z]{2,6}\d+)', subject + " " + body)
        if m:
            doc_code = m.group(1)

    label = {"purchase_request": "Yêu cầu mua hàng", "survey_request": "Yêu cầu báo giá",
             "survey": "Phiếu khảo sát", "purchase_order": "Đơn mua hàng",
             "payment_request": "Đề nghị thanh toán",
             "ticket": "Phiếu hỗ trợ"}.get(doc_type, "Chứng từ")
    jobs = []
    for r in recipients:
        if not r:
            continue
        target = _test_route_email(db, r)
        if not target:
            continue
        recipient_name = get_user_display_name(db, r)
        html = render_template(HTML_LAYOUT, {
            "subject": subject, "intro_message": body, "doc_type": label, "doc_code": doc_code,
            "creator": creator_name, "recipient_name": recipient_name, "reason": reason,
            "approve_note": approve_note, "is_urgent": is_urgent, "link": _abs_link(link),
        })
        log = EmailLog(event=f"workflow_{doc_type}", to_email=target, subject=subject,
                       status="pending", created_by=r.id)
        db.add(log); db.flush()
        jobs.append((log.id, target, html))
    db.commit()  # bảo đảm EmailLog tồn tại trước khi task nền (session mới) đọc
    # force=True: bỏ qua công tắc email_enabled; apply_override=False: giữ địa chỉ đã định tuyến.
    for log_id, target, html in jobs:
        if background_tasks is not None:
            background_tasks.add_task(send_smtp_email, SessionLocal, log_id, target, subject, html, True, False)
        else:
            send_smtp_email(SessionLocal, log_id, target, subject, html, force=True, apply_override=False)


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
    department_id: int = 0,              # CR-086: phòng ban của phiếu, neo bằng id
    recipient_ids: list | None = None,   # chỉ định thẳng người nhận (vd phân bổ NSTM)
):
    """
    Creates an in-app notification and sends an email notification asynchronously.
    """
    creator = db.query(User).filter(User.id == creator_id).first()
    creator_name = get_user_display_name(db, creator) if creator else "Hệ thống"
    
    # Generate labels and messages based on event
    doc_type_label = "Yêu cầu mua hàng" if doc_type == "purchase_request" else "Phiếu khảo sát"

    # Nhãn loại chứng từ + động từ theo hành động (dùng cho fallback rõ nghĩa, vd Đơn mua hàng)
    DOC_LABEL = {"purchase_request": "Yêu cầu mua hàng", "survey_request": "Yêu cầu báo giá",
                 "survey": "Phiếu khảo sát",
                 "purchase_order": "Đơn mua hàng", "payment_request": "Đề nghị thanh toán"}
    STATUS_VERB = {"submitted": "đã được gửi duyệt", "approved": "đã được duyệt",
                   "rejected": "đã bị từ chối", "cancelled": "đã bị hủy", "returned": "đã bị trả lại (cần sửa & gửi lại)",
                   "completed": "đã hoàn thành", "paid": "đã ghi nhận thanh toán"}

    if event == "pr_assigned":
        subject = f"{doc_code} — Phân công phụ trách PYC"
        body = f"Bạn được phân công phụ trách yêu cầu mua hàng {doc_code}."
    elif event == "pr_expected_date_changed":
        # NSTM vừa đổi "thời gian dự kiến có hàng" trên YCMH -> báo cho NGƯỜI YÊU CẦU biết
        # hàng của họ đổi ngày. `reason` mang chi tiết từng dòng (cũ → mới · lý do).
        subject = f"{doc_code} — Điều chỉnh ngày dự kiến có hàng"
        body = (f"Nhân sự thu mua vừa điều chỉnh thời gian dự kiến có hàng trên yêu cầu mua hàng {doc_code}:\n"
                f"{reason}\n"
                f"Mở phiếu để xem chi tiết.")
    elif event == "pr_submitted":
        subject = f"{doc_code} — Yêu cầu phê duyệt PYC"
        body = f"Có một yêu cầu mua hàng mới (Mã số: {doc_code}) cần bạn phê duyệt."
    elif event == "pr_approved":
        subject = f"{doc_code} — Đã duyệt PYC"
        body = f"Yêu cầu mua hàng {doc_code} của bạn đã được phê duyệt."
    elif event == "pr_rejected":
        subject = f"{doc_code} — Từ chối PYC"
        body = f"Yêu cầu mua hàng {doc_code} của bạn đã bị từ chối phê duyệt."
    elif event == "pr_returned":
        subject = f"{doc_code} — Bị trả lại PYC"
        body = f"Yêu cầu mua hàng {doc_code} của bạn bị trả lại — hãy chỉnh sửa và gửi duyệt lại."
    elif event == "pr_cancelled":
        subject = f"{doc_code} — Đã hủy PYC"
        body = f"Yêu cầu mua hàng {doc_code} của bạn đã bị hủy."
    elif event == "pr_items_received":
        subject = f"{doc_code} — Đã nhận hàng"
        body = f"Yêu cầu mua hàng {doc_code} của bạn đã được cập nhật tiến độ giao nhận hàng."
    elif event == "pr_completed":
        subject = f"{doc_code} — Hoàn thành YCMH"
        body = f"Yêu cầu mua hàng {doc_code} của bạn đã hoàn thành (tất cả hàng hóa đã được giao nhận đủ)."
    elif event == "sr_submitted":
        subject = f"{doc_code} — Yêu cầu phê duyệt YCBG"
        body = f"Có một yêu cầu báo giá mới (Mã số: {doc_code}) cần bạn phê duyệt."
    elif event == "sr_approved":
        subject = f"{doc_code} — Đã duyệt YCBG"
        body = f"Yêu cầu báo giá {doc_code} đã được duyệt, chuyển sang xử lý khảo sát."
    elif event == "sr_rejected":
        subject = f"{doc_code} — Từ chối YCBG"
        body = f"Yêu cầu báo giá {doc_code} của bạn đã bị từ chối phê duyệt."
    elif event == "sr_returned":
        subject = f"{doc_code} — Bị trả lại YCBG"
        body = f"Yêu cầu báo giá {doc_code} của bạn bị trả lại — hãy chỉnh sửa và gửi duyệt lại."
    elif event == "pay_submitted":
        subject = f"{doc_code} — Yêu cầu phê duyệt YCTT"
        body = f"Có một yêu cầu thanh toán mới ({doc_code}) cần bạn phê duyệt."
    elif event == "pay_approved":
        subject = f"{doc_code} — Đã duyệt YCTT"
        body = f"Yêu cầu thanh toán {doc_code} của bạn đã được phê duyệt."
    elif event == "pay_rejected":
        subject = f"{doc_code} — Từ chối YCTT"
        body = f"Yêu cầu thanh toán {doc_code} của bạn đã bị từ chối."
    elif event == "pay_paid":
        subject = f"{doc_code} — Đã chi YCTT"
        body = f"Yêu cầu thanh toán {doc_code} đã được ghi nhận đã chi."
    elif event == "survey_submitted":
        subject = f"{doc_code} — Yêu cầu phê duyệt khảo sát"
        body = f"Có một phiếu khảo sát mới (Mã số: {doc_code}) cần bạn phê duyệt."
    elif event == "survey_approved":
        subject = f"{doc_code} — Đã duyệt khảo sát"
        body = f"Phiếu khảo sát {doc_code} của bạn đã được phê duyệt."
    elif event == "survey_rejected":
        subject = f"{doc_code} — Từ chối khảo sát"
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
    if recipient_ids:
        recipients = db.query(User).filter(User.id.in_(recipient_ids), User.is_active == True).all()
    elif event in ("pr_submitted", "sr_submitted"):
        # Trưởng bộ phận của phòng YC + mọi tk có vai trò dept_head thuộc phòng đó
        # (để người tạm quyền trưởng phòng cũng nhận báo duyệt)
        recipients = get_dept_approver_recipients(db, department, department_id)
    elif event == "pay_submitted":
        # Yêu cầu thanh toán do người có quyền duyệt payment_request duyệt (QL/Admin TM)
        recipients = get_approvers_for_entity(db, "payment_request")
    elif event == "po_submitted":
        # Đơn mua hàng (ĐMH) gửi duyệt → báo người có quyền duyệt PO (QL/Admin TM)
        recipients = get_approvers_for_entity(db, "purchase_order")
    elif event == "pr_approved":
        # DUYỆT XONG PYC → báo người YC + Admin TM (theo yêu cầu: người tạo + Admin TM)
        recipients = ([creator] if creator else []) + get_users_by_role_codes(db, ["pur_admin"])
    else:
        recipients = [creator] if creator else []

    # Khử trùng lặp người nhận
    seen_ids = set()
    recipients = [r for r in recipients if r and not (r.id in seen_ids or seen_ids.add(r.id))]

    # CHỈ tạo thông báo trong app (chuông) — KHÔNG gửi email cho workflow.
    # MỖI SỰ KIỆN = 1 THÔNG BÁO RIÊNG (không gộp) — theo yêu cầu.
    for recipient in recipients:
        if not recipient:
            continue
        db.add(Notification(
            user_id=recipient.id,
            title=subject,
            body=body,
            link=link,
            created_by=creator_id,
        ))

    db.commit()

    # Web Push (best-effort, chạy nền) — đẩy thông báo tới thiết bị đã bật của người nhận
    try:
        from app.modules.push import service as push_service
        from app.core.database import SessionLocal
        uids = [r.id for r in recipients if r]
        if uids:
            if background_tasks is not None:
                background_tasks.add_task(push_service.send_to_users, SessionLocal, uids, subject, body, link)
            else:
                push_service.send_to_users(SessionLocal, uids, subject, body, link)
    except Exception:
        pass

    # EMAIL workflow (chỉ dev/UAT khi EMAIL_WORKFLOW_ENABLED) — best-effort, không chặn luồng.
    try:
        _send_workflow_emails(db, background_tasks, recipients, subject, body,
                              doc_type, doc_code, creator_name, reason, approve_note, is_urgent, link)
    except Exception:
        pass


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
        "link": _abs_link(link)
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
        "link": _abs_link(link)
    })

    from app.core.database import SessionLocal
    background_tasks.add_task(
        send_smtp_email,
        SessionLocal,
        email_log.id,
        email,
        subject,
        html_content,
        True,   # force=True: reset mật khẩu vẫn gửi dù email_enabled=false
    )
    db.commit()
