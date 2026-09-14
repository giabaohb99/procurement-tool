"""Dựng LỊCH SỬ ĐĂNG NHẬP của một người — dùng chung cho hai cửa (bao-CR-400).

* Quản trị / Nhân sự: `GET /api/login-sessions/history?user_id=` (khóa `login_session.read`).
* Chính mình: `GET /api/auth/sessions/history` (chỉ đòi đăng nhập, khóa cứng `user.id`).

Tách ra đây để hai cửa không bao giờ lệch nhau về cách nối dòng thất bại: dòng
`login_failed` của `tab_audit_log` ghi `entity_id = 0` (lúc đó chưa biết là ai),
nên nối về người này bằng chuỗi `tài khoản '<email | mã NV>'` trong câu thông báo
— thứ duy nhất dòng đó biết. Đổi câu ở `auth/controller.login` là mất khớp.
"""
from datetime import datetime, timedelta

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.modules.audit.model import AuditLog
from app.modules.employee.model import Employee
from app.modules.login_session.model import LoginSession
from app.modules.login_session.schema import serialize_history_failed, serialize_history_login

#  Lịch sử đăng nhập mặc định 90 ngày (§8.5), trần 365 để câu hỏi «cả năm» vẫn
#  trả lời được mà không ai kéo nổi toàn bảng.
HISTORY_DAYS_DEFAULT = 90
HISTORY_DAYS_MAX = 365
HISTORY_ROWS_MAX = 1000


def resolve_user_names(db: Session, user_ids: set[int]) -> dict[int, str]:
    """Tên hiển thị của nhiều tài khoản trong HAI truy vấn — cùng luật ưu tiên với
    `core/audit.resolve_actor` (họ tên nhân sự › email › `User #id`), nhưng gom một
    lượt thay vì gọi hàm đó trong vòng lặp (N+1 trên màn 200 dòng)."""
    from app.modules.user.model import User

    ids = {int(i) for i in user_ids if i}
    names: dict[int, str] = {0: "Hệ thống"}
    if not ids:
        return names
    users = db.query(User).filter(User.id.in_(ids)).all()
    emp_ids = {u.employee_id for u in users if u.employee_id}
    emp_names = {}
    if emp_ids:
        emp_names = {e.id: e.full_name for e in
                     db.query(Employee).filter(Employee.id.in_(emp_ids)).all()}
    for u in users:
        names[u.id] = emp_names.get(u.employee_id) or u.email or f"User #{u.id}"
    for i in ids - set(names):
        names[i] = f"User #{i}"
    return names


def build_login_history(db: Session, target, days: int) -> dict:
    """Mọi dòng phiên (kể cả đã thu hồi) của `target` trong `days` ngày, HỢP với
    các dòng `login_failed` nối được về người đó; mới nhất trước."""
    since = datetime.now() - timedelta(days=days)
    sessions = (db.query(LoginSession)
                .filter(LoginSession.user_id == target.id, LoginSession.created_at >= since)
                .order_by(LoginSession.created_at.desc())
                .limit(HISTORY_ROWS_MAX).all())

    usernames = [target.email or ""]
    emp = db.get(Employee, target.employee_id) if target.employee_id else None
    if emp and emp.code:
        usernames.append(emp.code)
    patterns = [AuditLog.message.like(f"%tài khoản '{u}'%") for u in usernames if u]
    failed = []
    if patterns:
        failed = (db.query(AuditLog)
                  .filter(AuditLog.entity == "auth", AuditLog.action == "login_failed",
                          AuditLog.created_at >= since, or_(*patterns))
                  .order_by(AuditLog.created_at.desc())
                  .limit(HISTORY_ROWS_MAX).all())

    names = resolve_user_names(db, {s.revoked_by for s in sessions if s.revoked_at})
    now = datetime.now()
    items = [serialize_history_login(s, revoked_by_name=names.get(s.revoked_by, ""), now=now)
             for s in sessions]
    items += [serialize_history_failed(a) for a in failed]
    items.sort(key=lambda it: it["at"] or datetime.min, reverse=True)
    return {"items": items[:HISTORY_ROWS_MAX], "days": days,
            "login_count": len(sessions), "failed_count": len(failed)}


def count_alive_sessions(db: Session, user_id: int) -> int:
    """Số phiên ĐANG CÒN HIỆU LỰC: chưa thu hồi và chưa quá hạn."""
    now = datetime.now()
    return (db.query(LoginSession)
            .filter(LoginSession.user_id == user_id, LoginSession.revoked_at.is_(None),
                    or_(LoginSession.expires_at.is_(None), LoginSession.expires_at > now))
            .count())
