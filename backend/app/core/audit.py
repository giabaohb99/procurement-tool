"""Ghi & đọc nhật ký thao tác (audit log) dùng chung."""
from sqlalchemy.orm import Session

from app.core.action_catalog import group_of_action
from app.core.logging_codes import ACTOR_KIND_SYSTEM
from app.core.request_context import bump_audit_count, get_context


def record(db: Session, user_id: int, entity: str, entity_id: int, action: str, message: str = "",
           doc_code: str = "", parent: tuple[str, int] | None = None, on_behalf_of: int = 0):
    """Ghi một dòng nhật ký thao tác.

    Sáu tham số đầu **giữ nguyên thứ tự và ý nghĩa** của bản cũ — 213 lời gọi
    đang gọi theo vị trí, đụng vào là hỏng hết. Ba tham số cuối là tùy chọn,
    bổ sung dần ở những chỗ có gì để nói thêm (bao-CR-312 P1):

    - `doc_code`: số phiếu tại thời điểm đó, cho phiếu sau này bị xóa;
    - `parent`: `("purchase_order", 129)` khi dấu vết ghi trên DÒNG chứ không
      trên phiếu — dòng đứng một mình thì đọc ra mồ côi;
    - `on_behalf_of`: hành chính bấm hộ ai.

    Phần ngữ cảnh còn lại (`request_id`, `ip`, `session_id`, `actor_kind`) do
    middleware đặt trong `ContextVar`, hàm này tự đọc — cố ý KHÔNG nhận qua
    tham số, nếu không thì mỗi lời gọi lại phải nhớ truyền.

    ⚠️ Vẫn `db.commit()` như bản cũ. Bẫy 1 ở §6 của tài liệu (gom bộ đệm, ghi
    một lần cuối request) là việc của P4 — đổi ở P1 là đổi nhịp commit của 213
    chỗ đang chạy thật mà chưa có gì bù lại.
    """
    from app.modules.audit.model import AuditLog

    ctx = get_context()
    parent_entity, parent_id = (parent or ("", 0))
    db.add(AuditLog(
        entity=entity, entity_id=entity_id, action=action, message=message,
        created_by=user_id, updated_by=user_id,
        actor_kind=ctx.actor_kind if ctx else ACTOR_KIND_SYSTEM,
        session_id=ctx.session_id if ctx else None,
        request_id=ctx.request_id if ctx else None,
        ip=(ctx.ip if ctx else "")[:45],
        on_behalf_of=on_behalf_of,
        doc_code=(doc_code or "")[:50],
        parent_entity=(parent_entity or "")[:50],
        parent_id=int(parent_id or 0),
        action_group=group_of_action(action),
    ))
    db.commit()
    bump_audit_count()


def resolve_actor(db: Session, user_id: int) -> str:
    from app.modules.employee.model import Employee
    from app.modules.user.model import User

    if not user_id:
        return "Hệ thống"
    user = db.get(User, user_id)
    if not user:
        return f"User #{user_id}"
    emp = db.get(Employee, user.employee_id) if user.employee_id else None
    return emp.full_name if emp else (user.email or f"User #{user_id}")


def resolve_signature_by_employee(db: Session, employee_id: int) -> str:
    """URL ảnh chữ ký của một NHÂN SỰ (qua tài khoản đăng nhập gắn với nhân sự đó).
    Trả "" nếu nhân sự chưa có tài khoản hoặc tài khoản chưa tải chữ ký lên.
    Dùng cho phiếu in: chữ ký phải khớp đúng TÊN đang in, nên tra theo nhân sự chứ không theo
    người bấm nút."""
    from app.modules.user.model import User

    if not employee_id:
        return ""
    user = (db.query(User)
            .filter(User.employee_id == employee_id, User.is_active == True)  # noqa: E712
            .order_by(User.id).first())
    return (user.signature or "") if user else ""


def resolve_signature(db: Session, user_id: int) -> str:
    """URL ảnh chữ ký của một TÀI KHOẢN. Trả "" nếu chưa tải chữ ký lên."""
    from app.modules.user.model import User

    user = db.get(User, user_id) if user_id else None
    return (user.signature or "") if user else ""


def resolve_actor_profile(db: Session, user_id: int) -> dict:
    """Thông tin nhân sự của người dùng để in phiếu: họ tên, chức vụ, bộ phận, trưởng BP."""
    from app.modules.department.model import Department
    from app.modules.employee.model import Employee
    from app.modules.user.model import User

    out = {"name": resolve_actor(db, user_id), "position": "", "department": "", "manager": ""}
    user = db.get(User, user_id) if user_id else None
    emp = db.get(Employee, user.employee_id) if (user and user.employee_id) else None
    if not emp:
        return out
    out["position"] = emp.position or ""
    dept = db.get(Department, emp.department_id) if emp.department_id else None
    if dept:
        out["department"] = dept.name or ""
        out["manager"] = dept.manager_name or ""
    return out
