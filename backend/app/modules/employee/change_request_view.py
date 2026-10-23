"""Dựng ChangeRequestOut — che nhóm nhạy cảm theo NGƯỜI XEM và tính cờ `can_decide` (duoc-CR-676)."""
from sqlalchemy.orm import Session

from app.core.hr_change_request_codes import EmployeeChangeRequestStatus as Status
from app.core.privilege_escalation import is_system_admin
from app.core.scoping import get_scoped

from . import sensitive
from .change_request_model import EmployeeChangeRequest
from .change_request_service import _norm, current_families, to_json
from .model import Employee

_SENSITIVE_GROUPS = frozenset({"bank", "documents"})


class Viewer:
    """Người đang xem/duyệt: tài khoản + hồ sơ quyền; vai trò admin tra LƯỜI, một lần."""

    def __init__(self, db: Session, user, profile: dict):
        self.db, self.user, self.profile = db, user, profile
        self._admin: bool | None = None

    @property
    def is_admin(self) -> bool:
        if self._admin is None:
            self._admin = is_system_admin(self.db, self.user.id)
        return self._admin

    def is_own(self, employee_id: int) -> bool:
        mine = int(getattr(self.user, "employee_id", 0) or 0)
        return bool(mine) and mine == int(employee_id)


def needs_sensitive(req: EmployeeChangeRequest) -> bool:
    """Yêu cầu có đụng nhóm nhạy cảm không → người duyệt phải có `employee_sensitive.read`."""
    if req.families:
        return True
    return any(i["group"] in _SENSITIVE_GROUPS or i["field"] in sensitive.SENSITIVE_FIELDS
               for i in req.changes or [])


def approve_block_reason(v: Viewer, req: EmployeeChangeRequest) -> str:
    """Lý do KHÔNG được duyệt/từ chối (đã giả định hồ sơ nằm trong phạm vi ghi). Rỗng = được."""
    if v.is_own(req.employee_id) and not v.is_admin:
        return "Không tự duyệt yêu cầu sửa hồ sơ của chính mình — nhờ một người khác trong phòng Nhân sự."
    #  Cố ý đòi `employee_sensitive.read` (không phải `.write`): vai trò mẫu `hr_profile` chỉ có `read`, và
    #  PATCH hồ sơ trực tiếp cũng không đòi quyền nhạy cảm nào — duyệt chỉ cần ĐỌC được thứ mình duyệt.
    if needs_sensitive(req) and not sensitive.can_read_sensitive(v.profile, req.employee_id):
        return "Yêu cầu có thông tin nhạy cảm — cần quyền xem nhạy cảm (employee_sensitive.read) để duyệt."
    return ""


def can_decide(v: Viewer, req: EmployeeChangeRequest, in_scope: bool | None = None) -> bool:
    if req.status != int(Status.PENDING):
        return False
    if in_scope is None:
        in_scope = get_scoped(v.db, Employee, "employee", req.employee_id, v.user, v.profile, "write") is not None
    return in_scope and not approve_block_reason(v, req)


def serialize(req: EmployeeChangeRequest, emp: Employee | None, v: Viewer, names: dict[int, str],
              in_scope: bool | None = None) -> dict:
    allowed = sensitive.can_read_sensitive(v.profile, req.employee_id)
    items = []
    for i in req.changes or []:
        hide = i["field"] in sensitive.SENSITIVE_FIELDS and not allowed
        current = to_json(_norm(i["field"], getattr(emp, i["field"], None))) if emp else None
        items.append({"group": i["group"], "field": i["field"],
                      "before": None if hide else i["before"], "after": None if hide else i["after"],
                      "current": None if hide else current, "masked": hide})
    families = None
    if req.families:
        #  `current` = danh sách hiện hành (để người duyệt thấy hồ sơ đã đổi sau lúc gửi).
        families = {"before": req.families["before"] if allowed else None,
                    "after": req.families["after"] if allowed else None,
                    "current": current_families(v.db, req.employee_id) if allowed and emp else None,
                    "masked": not allowed}
    return {
        "id": req.id, "employee_id": req.employee_id,
        "employee_code": emp.code if emp else "", "employee_name": emp.full_name if emp else "",
        "status": req.status, "items": items, "families": families,
        "note": req.note or "", "reject_reason": req.reject_reason or "",
        "created_at": req.created_at, "created_by_name": names.get(req.created_by, ""),
        "decided_at": req.decided_at, "decided_by_name": names.get(req.decided_by, ""),
        "can_decide": can_decide(v, req, in_scope), "has_sensitive": needs_sensitive(req),
    }


def user_names(db: Session, reqs: list[EmployeeChangeRequest]) -> dict[int, str]:
    """id tài khoản → họ tên nhân sự (hoặc email), gom MỘT truy vấn cho cả trang."""
    from app.modules.user.model import User

    ids = {x for r in reqs for x in (r.created_by, r.decided_by) if x}
    if not ids:
        return {}
    rows = (db.query(User.id, User.email, Employee.full_name)
            .outerjoin(Employee, Employee.id == User.employee_id).filter(User.id.in_(ids)).all())
    return {uid: (name or email or f"Tài khoản #{uid}") for uid, email, name in rows}
