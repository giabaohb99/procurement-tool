"""Danh sách chọn cho ô «Trưởng phòng phê duyệt» của YCMH · YCBG · ĐMH — bao-CR-499.

Đại ca chốt 26/09/2026 (hướng 1): ô chỉ liệt kê những người DUYỆT ĐƯỢC đúng chứng từ đó, do
backend tính, KHÔNG phụ thuộc quyền xem danh mục nhân sự của người lập (người lập phạm vi
«của tôi» vẫn thấy đủ trưởng phòng để chọn).

Luật: tài khoản đang hoạt động, có gắn nhân sự, giữ một vai trò có quyền Duyệt trên entity; rồi
hỏi ĐÚNG `apply_scope(..., action="approve")` xem phạm vi duyệt của người đó có phủ chứng từ này
không — không chép lại luật phạm vi, nếu không danh sách và nút Duyệt sẽ lệch nhau (chọn được một
người không bấm duyệt nổi). Vai trò quản trị hệ thống (`admin`) không tính là «trưởng phòng» nên
không đưa vào danh sách; quyền duyệt của họ không đổi.

Chứng từ CHƯA lưu (màn tạo mới): dựng một bản ghi TẠM trong SAVEPOINT, flush để có id, hỏi
`apply_scope` y như trên rồi rollback — cùng một luật cho tạo mới và sửa.
"""
import uuid

from sqlalchemy.orm import Session

EXCLUDED_ROLE_CODES = frozenset({"admin"})


def _approver_users(db: Session, entity: str):
    from app.modules.role.model import Permission, Role
    from app.modules.user.model import User, UserRole
    role_ids = [rid for (rid,) in db.query(Permission.role_id).join(Role, Role.id == Permission.role_id)
                .filter(Permission.entity == entity, Permission.can_approve == True,    # noqa: E712
                        Role.code.notin_(EXCLUDED_ROLE_CODES)).all()]
    if not role_ids:
        return []
    uids = {uid for (uid,) in db.query(UserRole.user_id).filter(UserRole.role_id.in_(role_ids)).all()}
    if not uids:
        return []
    return db.query(User).filter(User.id.in_(uids), User.is_active == True,           # noqa: E712
                                 User.employee_id > 0).all()


def candidates_for_row(db: Session, model, entity: str, row_id: int) -> list[dict]:
    """Người duyệt được chứng từ `row_id` → [{employee_id, code, name, position}], xếp theo tên."""
    from app.core.auth import get_perm_profile
    from app.core.scoping import apply_scope
    from app.modules.employee.model import Employee
    emp_ids = set()
    for u in _approver_users(db, entity):
        q = db.query(model.id).filter(model.id == row_id)
        if apply_scope(q, model, entity, u, get_perm_profile(db, u), action="approve").first() is not None:
            emp_ids.add(int(u.employee_id))
    if not emp_ids:
        return []
    emps = db.query(Employee).filter(Employee.id.in_(emp_ids), Employee.status != "resigned").all()
    out = [{"employee_id": e.id, "code": e.code or "", "name": e.full_name or "",
            "position": e.position or ""} for e in emps]
    out.sort(key=lambda r: (r["name"], r["employee_id"]))
    return out


def candidates_for_draft(db: Session, model, entity: str, fields: dict) -> list[dict]:
    """Như trên cho chứng từ CHƯA lưu: bản ghi tạm trong savepoint, xong rollback, không để lại gì."""
    sp = db.begin_nested()
    try:
        tmp = model(**{k: v for k, v in fields.items() if hasattr(model, k)})
        if hasattr(model, "code"):
            tmp.code = f"TMP{uuid.uuid4().hex[:12]}"
        if hasattr(model, "status") and not getattr(tmp, "status", None):
            tmp.status = "draft"
        db.add(tmp)
        db.flush()
        return candidates_for_row(db, model, entity, tmp.id)
    finally:
        sp.rollback()


def department_managers(db: Session) -> list[dict]:
    """Trưởng phòng (Department.manager_id) của mọi phòng đang hoạt động — đúng bộ ô «Trưởng bộ
    phận» của YCBG (v2 dựng cùng danh sách ở `survey-request-info-card.tsx`)."""
    from app.modules.department.model import Department
    from app.modules.employee.model import Employee
    ids = {int(m) for (m,) in db.query(Department.manager_id).filter(Department.is_active == True,   # noqa: E712
                                                                      Department.manager_id > 0).all()}
    if not ids:
        return []
    emps = db.query(Employee).filter(Employee.id.in_(ids), Employee.status != "resigned").all()
    out = [{"employee_id": e.id, "code": e.code or "", "name": e.full_name or "", "position": e.position or ""}
           for e in emps]
    out.sort(key=lambda r: (r["name"], r["employee_id"]))
    return out


def draft_fields(db: Session, user, department: str = "", department_id: int = 0, company_id: int = 0,
                 handler_dept_id: int = 0) -> dict:
    """Bộ cột phạm vi của chứng từ đang lập — phòng ban neo bằng id, tên chỉ là đường lùi."""
    from app.modules.purchase_request.service import _find_dept
    dep = _find_dept(db, department, department_id)
    return {"department_id": int(dep.id) if dep else 0, "department": dep.name if dep else (department or ""),
            "company_id": int(company_id or (getattr(dep, "company_id", 0) if dep else 0) or 0),
            "handler_dept_id": int(handler_dept_id or 0),
            "created_by": user.id, "updated_by": user.id}
