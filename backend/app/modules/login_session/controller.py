"""Màn PHIÊN ĐĂNG NHẬP cho quản trị + Nhân sự (bao-CR-395 / CR-312 P3b).

Một bảng, một API — ba màn đọc cùng nó, khác nhau ở khóa quyền và phạm vi
(`doc/tai-lieu-ky-thuat/nhat-ky-va-phien-dang-nhap.md` §8.5):

* `/system/sessions` — admin: `login_session` scope `all` + `delete` để đá.
* Tab «Tài khoản & thiết bị» trong hồ sơ nhân sự — HR: `login_session.read`
  scope `all`, KHÔNG `delete`; nút khóa tài khoản đi qua `user.write` và hook
  `user/service.set_active` tự thu hồi phiên.
* Tab «Thiết bị của tôi» ở `/me` — KHÔNG ở đây. Nó nằm ở `/api/auth/sessions`
  (`modules/auth/controller.py`) và chỉ đòi đăng nhập: hệ đang chạy thì vai
  trò cũ không tự có khóa mới (D-018), mà ai cũng phải đá được thiết bị lạ
  của chính mình. ⚠️ Đây là chỗ LỆCH với bản thiết kế («`login_session` own
  mặc định cho mọi vai trò») — cố ý, ghi ở §8.5.

Hai đường cắt phiên KHÁC NHAU về hiệu lực, đừng gộp:

* **Đá MỘT thiết bị** (`revoke`) đi qua `revoked_at` → hiệu lực tối đa 60 giây
  (đệm tra phiên ở từng tiến trình uvicorn).
* **Bắt đăng nhập lại** (`logout-all`) đi qua `token_version` → tức thì, vì
  `get_current_user` đọc `tab_user` ở mọi lượt gọi.
"""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.auth import get_perm_profile, require
from app.core.base_controller import pagination
from app.core.database import get_db
from app.core.request_context import get_context
from app.core.response import success
from app.core.scoping import apply_scope, get_scoped, scope_condition
from app.modules.audit.model import AuditLog
from app.modules.employee.model import Employee
from app.modules.login_session.constants import RevokeReason
from app.modules.login_session.model import LoginSession
from app.modules.login_session.schema import (serialize_history_failed,
                                              serialize_history_login, serialize_session)
from app.modules.login_session.service import force_relogin, revoke_session
from app.modules.user.model import User

router = APIRouter(prefix="/api/login-sessions", tags=["login-session"])

ENTITY = "login_session"
#  Lịch sử đăng nhập mặc định 90 ngày (§8.5), trần 365 để câu hỏi «cả năm» vẫn
#  trả lời được mà không ai kéo nổi toàn bảng.
HISTORY_DAYS_DEFAULT = 90
HISTORY_DAYS_MAX = 365
HISTORY_ROWS_MAX = 1000


def _current_session_id() -> int:
    ctx = get_context()
    return int(ctx.session_id or 0) if ctx else 0


def resolve_user_names(db: Session, user_ids: set[int]) -> dict[int, str]:
    """Tên hiển thị của nhiều tài khoản trong HAI truy vấn — cùng luật ưu tiên với
    `core/audit.resolve_actor` (họ tên nhân sự › email › `User #id`), nhưng gom một
    lượt thay vì gọi hàm đó trong vòng lặp (N+1 trên màn 200 dòng)."""
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


def _assert_user_in_scope(db: Session, user, profile: dict, target_user_id: int,
                          action: str) -> None:
    """Người gọi có với tới TÀI KHOẢN này không — dùng cho hai endpoint nhận
    `user_id` thay vì id phiên (`logout-all`, `history`).

    `scope_condition` sinh điều kiện trên DÒNG PHIÊN, mà tài khoản chưa có phiên
    nào thì không có dòng để soi. Nên: phạm vi `all` (điều kiện `None`) qua luôn;
    chính mình qua luôn; còn lại phải có ít nhất một dòng phiên của người đó
    lọt điều kiện. Ngoài phạm vi trả 404 như mọi `get_scoped` khác.
    """
    cond = scope_condition(LoginSession, ENTITY, user, profile, action)
    if cond is None or target_user_id == user.id:
        return
    hit = (db.query(LoginSession.id)
           .filter(LoginSession.user_id == target_user_id, cond).first())
    if not hit:
        raise HTTPException(404, "Không tìm thấy tài khoản")


@router.get("")
def list_sessions(
    user_id: int = Query(0, ge=0),
    active_only: bool = Query(True),
    user=Depends(require(ENTITY, "read")),
    db: Session = Depends(get_db),
    pg: dict = Depends(pagination),
):
    """Danh sách phiên, mới nhất trước. `active_only` = chưa thu hồi (mặc định);
    tắt để xem cả phiên đã kết thúc của một người (tab hồ sơ)."""
    profile = get_perm_profile(db, user)
    query = db.query(LoginSession)
    if user_id:
        query = query.filter(LoginSession.user_id == user_id)
    if active_only:
        query = query.filter(LoginSession.revoked_at.is_(None))
    query = apply_scope(query, LoginSession, ENTITY, user, profile)
    total = query.count()
    rows = (query.order_by(LoginSession.created_at.desc(), LoginSession.id.desc())
            .offset(pg["offset"]).limit(pg["limit"]).all())
    names = resolve_user_names(db, {r.user_id for r in rows} | {r.revoked_by for r in rows})
    current_id = _current_session_id()
    now = datetime.now()
    items = [serialize_session(r, current_session_id=current_id,
                               user_name=names.get(r.user_id, ""),
                               revoked_by_name=names.get(r.revoked_by, "") if r.revoked_at else "",
                               now=now)
             for r in rows]
    return success({"items": items, "total": total,
                    "page": pg["page"], "page_size": pg["page_size"]})


@router.post("/{session_id}/revoke")
def revoke_one(session_id: int, user=Depends(require(ENTITY, "delete")),
               db: Session = Depends(get_db)):
    """Đá MỘT thiết bị. Hiệu lực tối đa 60 giây (đệm tra phiên)."""
    profile = get_perm_profile(db, user)
    row = get_scoped(db, LoginSession, ENTITY, session_id, user, profile, "delete")
    if not row:
        raise HTTPException(404, "Không tìm thấy phiên")
    if row.revoked_at is not None:
        raise HTTPException(400, "Phiên này đã kết thúc rồi")
    revoke_session(db, row, RevokeReason.ADMIN_KICK, user.id)
    names = resolve_user_names(db, {row.user_id})
    record(db, user.id, "auth", row.user_id, "session_revoked",
           f"Đá phiên #{row.id} của {names.get(row.user_id, '')} khỏi thiết bị "
           f"{row.device_label or 'không rõ'} (IP {row.ip or '?'})")
    return success(None, "Đã đá phiên khỏi thiết bị. Có hiệu lực trong vòng 1 phút.")


@router.post("/users/{user_id}/logout-all")
def logout_all(user_id: int, user=Depends(require(ENTITY, "delete")),
               db: Session = Depends(get_db)):
    """Bắt đăng nhập lại: cắt MỌI thiết bị của một người, hiệu lực tức thì.

    ⚠️ Đường dẫn lệch bản thiết kế (`POST /api/users/{id}/logout-all`): để dưới
    `/api/login-sessions` cho cùng khóa quyền với hai endpoint kia, khỏi phải
    cắm `login_session.delete` vào router `user`.
    """
    profile = get_perm_profile(db, user)
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(404, "Không tìm thấy tài khoản")
    _assert_user_in_scope(db, user, profile, user_id, "delete")
    count = force_relogin(db, target, RevokeReason.FORCE_RELOGIN, user.id)
    names = resolve_user_names(db, {user_id})
    record(db, user.id, "auth", user_id, "logout_all",
           f"Bắt {names.get(user_id, '')} đăng nhập lại — cắt {count} phiên đang mở")
    return success({"revoked": count}, f"Đã đăng xuất {count} thiết bị. Có hiệu lực ngay.")


@router.get("/history")
def login_history(
    user_id: int = Query(..., ge=1),
    days: int = Query(HISTORY_DAYS_DEFAULT, ge=1, le=HISTORY_DAYS_MAX),
    user=Depends(require(ENTITY, "read")),
    db: Session = Depends(get_db),
):
    """Lịch sử đăng nhập của MỘT người trong N ngày: mọi dòng phiên (kể cả đã thu
    hồi) HỢP với các dòng `login_failed` của `tab_audit_log`.

    ⚠️ Dòng thất bại ghi `entity_id = 0` (chưa xác định được ai) — nối về người
    này bằng chuỗi `tài khoản '<email | mã NV>'` trong câu thông báo, vì đó là
    thứ duy nhất dòng đó biết. Đổi câu ở `auth/controller.login` là mất khớp.
    """
    profile = get_perm_profile(db, user)
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(404, "Không tìm thấy tài khoản")
    _assert_user_in_scope(db, user, profile, user_id, "read")

    since = datetime.now() - timedelta(days=days)
    sessions = (db.query(LoginSession)
                .filter(LoginSession.user_id == user_id, LoginSession.created_at >= since)
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
    return success({"items": items[:HISTORY_ROWS_MAX], "days": days,
                    "login_count": len(sessions), "failed_count": len(failed)})
