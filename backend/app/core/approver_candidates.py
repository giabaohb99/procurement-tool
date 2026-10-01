"""Danh sách chọn cho ô «Trưởng phòng phê duyệt» của YCMH · YCBG · ĐMH — bao-CR-499, sửa ở bao-CR-552.

Đại ca chốt 01/10/2026 (bao-CR-552): ô liệt kê MỌI người duyệt được đúng chứng từ đó — không chỉ
trưởng phòng theo phòng như bản 26/09 — NHƯNG bỏ hẳn tài khoản giữ vai trò Quản trị hệ thống
(«lòi ra tài khoản admin, hoặc tài khoản của anh thì không hay»), và LUÔN có Trưởng bộ phận của
phiếu («phòng IT không có người duyệt nhưng lại ra anh Giang thì ô phê duyệt cũng phải có»).

Luật: tài khoản đang hoạt động, có gắn nhân sự, giữ một vai trò có quyền Duyệt trên entity, KHÔNG
giữ vai trò `admin`; rồi hỏi ĐÚNG `apply_scope(..., action="approve")` xem phạm vi duyệt của người
đó có phủ chứng từ này không — không chép lại luật phạm vi, nếu không danh sách và nút Duyệt lệch
nhau (chọn được một người không bấm duyệt nổi). Cộng thêm Trưởng bộ phận (ô TBP của phiếu, trống
thì trưởng phòng của phòng lập) — người này là mặc định của ô, có duyệt được hay không.

Chứng từ CHƯA lưu (màn tạo mới): dựng một bản ghi TẠM trong SAVEPOINT, flush để có id, hỏi
`apply_scope` y như trên rồi rollback — cùng một luật cho tạo mới và sửa.
"""
import uuid

from sqlalchemy.orm import Session

#  Vai trò Quản trị hệ thống: người giữ nó KHÔNG lên danh sách (bao-CR-552), quyền duyệt không đổi.
EXCLUDED_ROLE_CODES = frozenset({"admin"})


def _get_excluded_user_ids(db: Session) -> set[int]:
    from app.modules.role.model import Role
    from app.modules.user.model import UserRole
    return {uid for (uid,) in db.query(UserRole.user_id).join(Role, Role.id == UserRole.role_id)
            .filter(Role.code.in_(EXCLUDED_ROLE_CODES)).all()}


def _approver_users(db: Session, entity: str):
    from app.modules.role.model import Permission, Role
    from app.modules.user.model import User, UserRole
    role_ids = [rid for (rid,) in db.query(Permission.role_id).join(Role, Role.id == Permission.role_id)
                .filter(Permission.entity == entity, Permission.can_approve == True,    # noqa: E712
                        Role.code.notin_(EXCLUDED_ROLE_CODES)).all()]
    if not role_ids:
        return []
    uids = {uid for (uid,) in db.query(UserRole.user_id).filter(UserRole.role_id.in_(role_ids)).all()}
    uids -= _get_excluded_user_ids(db)
    if not uids:
        return []
    return db.query(User).filter(User.id.in_(uids), User.is_active == True,           # noqa: E712
                                 User.employee_id > 0).all()


def _build_employee_rows(db: Session, emp_ids: set[int]) -> list[dict]:
    from app.modules.employee.model import Employee
    if not emp_ids:
        return []
    emps = db.query(Employee).filter(Employee.id.in_(emp_ids), Employee.status != "resigned").all()
    out = [{"employee_id": e.id, "code": e.code or "", "name": e.full_name or "",
            "position": e.position or ""} for e in emps]
    out.sort(key=lambda r: (r["name"], r["employee_id"]))
    return out


def get_department_head_id(db: Session, department_id: int) -> int:
    """Trưởng phòng (Department.manager_id) của một phòng; 0 nếu chưa gán."""
    from app.modules.department.model import Department
    if not department_id:
        return 0
    dep = db.get(Department, int(department_id))
    return int(getattr(dep, "manager_id", 0) or 0) if dep else 0


def get_head_of_dept_id(db: Session, row) -> int:
    """Trưởng bộ phận của phiếu: ô TBP đã chọn, trống thì trưởng phòng của phòng lập."""
    head = int(getattr(row, "head_of_dept_id", 0) or 0)
    return head or get_department_head_id(db, int(getattr(row, "department_id", 0) or 0))


def candidates_for_row(db: Session, model, entity: str, row_id: int,
                       extra_employee_ids: tuple[int, ...] = ()) -> list[dict]:
    """Người duyệt được chứng từ `row_id` (+ `extra_employee_ids`) → [{employee_id, code, name,
    position}], xếp theo tên."""
    from app.core.auth import get_perm_profile
    from app.core.scoping import apply_scope
    emp_ids = {int(e) for e in extra_employee_ids if e}
    for u in _approver_users(db, entity):
        q = db.query(model.id).filter(model.id == row_id)
        if apply_scope(q, model, entity, u, get_perm_profile(db, u), action="approve").first() is not None:
            emp_ids.add(int(u.employee_id))
    return _build_employee_rows(db, emp_ids)


def candidates_for_draft(db: Session, model, entity: str, fields: dict,
                         extra_employee_ids: tuple[int, ...] = ()) -> list[dict]:
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
        return candidates_for_row(db, model, entity, tmp.id, extra_employee_ids)
    finally:
        sp.rollback()


def list_candidates_for_row(db: Session, model, entity: str, row) -> list[dict]:
    """Ô «Trưởng phòng phê duyệt» của một phiếu ĐÃ lưu: người duyệt được + Trưởng bộ phận."""
    return candidates_for_row(db, model, entity, row.id, (get_head_of_dept_id(db, row),))


def list_candidates_for_draft(db: Session, model, entity: str, fields: dict,
                              head_of_dept_id: int = 0) -> list[dict]:
    """Ô «Trưởng phòng phê duyệt» của màn TẠO MỚI: người duyệt được + Trưởng bộ phận (ô TBP đang
    chọn, trống thì trưởng phòng của phòng lập)."""
    head = int(head_of_dept_id or 0) or get_department_head_id(db, int(fields.get("department_id") or 0))
    return candidates_for_draft(db, model, entity, fields, (head,))


def department_managers(db: Session) -> list[dict]:
    """Trưởng phòng (Department.manager_id) của mọi phòng đang hoạt động — đúng bộ ô «Trưởng bộ
    phận» của YCBG (v2 dựng cùng danh sách ở `survey-request-info-card.tsx`)."""
    from app.modules.department.model import Department
    ids = {int(m) for (m,) in db.query(Department.manager_id).filter(Department.is_active == True,   # noqa: E712
                                                                      Department.manager_id > 0).all()}
    return _build_employee_rows(db, ids)


def draft_fields(db: Session, user, department: str = "", department_id: int = 0, company_id: int = 0,
                 handler_dept_id: int = 0) -> dict:
    """Bộ cột phạm vi của chứng từ đang lập — phòng ban neo bằng id, tên chỉ là đường lùi."""
    from app.modules.purchase_request.service import _find_dept
    dep = _find_dept(db, department, department_id)
    return {"department_id": int(dep.id) if dep else 0, "department": dep.name if dep else (department or ""),
            "company_id": int(company_id or (getattr(dep, "company_id", 0) if dep else 0) or 0),
            "handler_dept_id": int(handler_dept_id or 0),
            "created_by": user.id, "updated_by": user.id}
