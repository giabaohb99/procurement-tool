"""API PHÂN BỔ CHÍNH SÁCH NGHỈ PHÉP (duoc-CR-717).

Gác bằng `leave_balance` (D4): `read` xem, `write` tạo / sửa / xóa — phân bổ là cho thêm / bớt ngày phép nên cùng mức
nguy hiểm với "Điều chỉnh" quỹ. Nhân sự được phân bổ phải nằm trong phạm vi `employee` của người bấm VÀ phạm vi ghi
`leave_balance` (ngoài phạm vi → 404 / `skipped`, xem `policy_assignment_scope`); không tự phân bổ / sửa / xóa phân bổ
của chính mình trừ admin (D5).

⚠️ `/preview` và `/bulk` khai TRƯỚC `/{aid}` (cùng tệp) để đường tĩnh không bị `/{aid}` nuốt.
"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.auth import get_perm_profile, require
from app.core.base_controller import apply_filters, pagination
from app.core.database import get_db
from app.core.privilege_escalation import is_system_admin
from app.core.response import success
from app.core.scoping import apply_scope, get_scoped
from app.core.vn_time import vn_today
from app.modules.department.model import Department
from app.modules.employee.model import Employee

from . import policy_assignment_service as service
from .policy_assignment_plan import SELF_MESSAGE, plan_change
from .policy_assignment_view import dump_assignment, lookup_names, search_condition
from .policy_balance_links import quotas_for_assignments
from .policy_assignment_scope import is_own_employee, writable_employee_query
from .policy_model import LeavePolicy, LeavePolicyAssignment
from .policy_schema import (AssignmentBulk, AssignmentCreate, AssignmentPreview, AssignmentUpdate,
                            MAX_BULK)

router = APIRouter(prefix="/api/leave-policy-assignments", tags=["leave"])

ENTITY = "leave_balance"
FILTERABLE = ["employee_id", "policy_id", "company_id"]
CONFLICT_DUP = "Nhân sự đã có phân bổ bắt đầu đúng ngày này."
NOT_FOUND_EMPLOYEE = "Không tìm thấy nhân sự (đã nghỉ việc, hoặc ngoài phạm vi của bạn)."
MAX_SEARCH = 100


def _policy_or_404(db: Session, policy_id: int) -> LeavePolicy:
    obj = db.query(LeavePolicy).filter(LeavePolicy.id == policy_id).first()
    if obj is None:
        raise HTTPException(404, "Không tìm thấy chính sách nghỉ phép")
    return obj


def _commit(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, CONFLICT_DUP)
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(500, f"Lỗi cơ sở dữ liệu khi lưu phân bổ ({type(exc).__name__}).")


@router.get("")
def list_assignments(request: Request, pg: dict = Depends(pagination),
                     search: str | None = Query(None, max_length=MAX_SEARCH),
                     active_on: date | None = None, db: Session = Depends(get_db),
                     user=Depends(require(ENTITY, "read"))):
    """Phân bổ trong phạm vi người xem. Lọc: `employee_id`, `policy_id`, `company_id`, `active_on` (ngày), `search` (tên / mã).

    Mỗi dòng kèm `current_year_quotas` (duoc-CR-745): hạn mức năm nay theo loại nghỉ của gói + `balance_id` dòng quỹ
    (0 = chưa cấp); rỗng khi phân bổ không chạm năm nay. Dòng quỹ lọc theo phạm vi `leave_balance` của người xem.
    """
    query = apply_filters(db.query(LeavePolicyAssignment), LeavePolicyAssignment, request, FILTERABLE)
    if search and search.strip():
        query = query.filter(search_condition(search))
    if active_on:
        query = query.filter(LeavePolicyAssignment.effective_from <= active_on,
                             (LeavePolicyAssignment.effective_to.is_(None))
                             | (LeavePolicyAssignment.effective_to >= active_on))
    prof = get_perm_profile(db, user)
    query = apply_scope(query, LeavePolicyAssignment, ENTITY, user, prof)
    total = query.count()
    rows = (query.order_by(LeavePolicyAssignment.effective_from.desc(), LeavePolicyAssignment.id.desc())
            .offset(pg["offset"]).limit(pg["limit"]).all())
    emps, policies = lookup_names(db, rows)
    today = vn_today()
    #  duoc-CR-745: hạn mức năm nay của các loại trong gói, kèm id dòng quỹ để bấm sang Quỹ phép năm.
    quotas = quotas_for_assignments(db, rows, user, prof, today.year)
    items = [{**dump_assignment(r, emps, policies, today), "current_year_quotas": quotas.get(r.id, [])} for r in rows]
    return success({"total": total, "items": items})


@router.post("/preview")
def preview_assignment(data: AssignmentPreview, db: Session = Depends(get_db),
                       user=Depends(require(ENTITY, "write"))):
    """XEM TRƯỚC — dùng chung `plan_change` với đường ghi, KHÔNG ghi gì. Trần 500 người (`truncated`)."""
    policy = _policy_or_404(db, data.policy_id)
    today = vn_today()
    query = writable_employee_query(db, user).filter(Employee.is_active.is_(True))
    if data.employee_ids:
        query = query.filter(Employee.id.in_(set(data.employee_ids)))
    else:
        for column, value in ((Employee.company_id, data.company_id), (Employee.department_id, data.department_id),
                              (Employee.employment_type, data.employment_type), (Employee.job_level, data.job_level)):
            if value:
                query = query.filter(column == value)
        if data.only_without_active:
            active = db.query(LeavePolicyAssignment.employee_id).filter(
                LeavePolicyAssignment.effective_from <= today,
                (LeavePolicyAssignment.effective_to.is_(None)) | (LeavePolicyAssignment.effective_to >= today))
            query = query.filter(Employee.id.notin_(active))
    total = query.count()
    employees = query.order_by(Employee.code).limit(MAX_BULK).all()
    #  Id khai thẳng mà không nằm trong phạm vi / đã nghỉ việc → vẫn hiện một dòng nêu lý do (cùng chữ với `skipped`
    #  của /bulk), để màn xem trước không hứa điều đường ghi sẽ chặn.
    found_ids = {e.id for e in employees}
    outside = [{
        "employee_id": i, "code": "", "name": "", "department_name": "", "hire_date": None, "current": None,
        "conflict": "scope", "conflict_message": NOT_FOUND_EMPLOYEE, "changes": [],
    } for i in dict.fromkeys(data.employee_ids or []) if i not in found_ids]
    items, ctx = plan_change(db, employees, policy, data.effective_from, data.effective_to, data.close_previous,
                             today.year, today, actor_employee_id=getattr(user, "employee_id", 0) or 0,
                             actor_is_admin=is_system_admin(db, user.id))
    depts = {i: n for i, n in db.query(Department.id, Department.name).filter(
        Department.id.in_({e.department_id for e in employees if e.department_id} or {0})).all()}
    return success({"items": [{
        "employee_id": it.employee.id, "code": it.employee.code, "name": it.employee.full_name,
        "department_name": depts.get(it.employee.department_id, ""), "hire_date": it.employee.hire_date,
        "current": ({"policy_name": ctx.policy_names.get(it.current.policy_id, ""),
                     "from": it.current.effective_from, "to": it.current.effective_to} if it.current else None),
        "conflict": it.conflict, "conflict_message": it.message, "changes": it.changes,
    } for it in items] + outside, "total": total, "truncated": total > MAX_BULK})


@router.post("/bulk")
def bulk_assign(data: AssignmentBulk, db: Session = Depends(get_db), user=Depends(require(ENTITY, "write"))):
    """Phân bổ HÀNG LOẠT (≤500). Người vướng chốt (chồng ngày / tự phân bổ / ngoài phạm vi) vào `skipped`, không hỏng cả lô."""
    policy = _policy_or_404(db, data.policy_id)
    wanted = list(dict.fromkeys(data.employee_ids))
    found = {e.id: e for e in writable_employee_query(db, user).filter(
        Employee.id.in_(wanted), Employee.is_active.is_(True)).all()}
    outside = [{"employee_id": i, "name": "", "reason": NOT_FOUND_EMPLOYEE} for i in wanted if i not in found]
    try:
        result = service.create_bulk(
            db, user, [found[i] for i in wanted if i in found], policy, data.effective_from, data.effective_to,
            data.recalc_current_year, data.close_previous, vn_today().year, vn_today(),
            actor_employee_id=getattr(user, "employee_id", 0) or 0, actor_is_admin=is_system_admin(db, user.id))
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, CONFLICT_DUP + " Không lưu gì — thử lại.")
    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(500, f"Lỗi cơ sở dữ liệu khi phân bổ hàng loạt ({type(exc).__name__}) — chưa lưu gì.")
    _commit(db)
    result["skipped"] = outside + result["skipped"]
    return success(result, f"Đã phân bổ {result['created']} nhân sự, bỏ qua {len(result['skipped'])}")


@router.post("")
def create_assignment(data: AssignmentCreate, db: Session = Depends(get_db),
                      user=Depends(require(ENTITY, "write"))):
    """Phân bổ cho MỘT nhân sự → `{assignment, balances:{created, recalculated[], kept, negative_after[]}}`."""
    employee = writable_employee_query(db, user).filter(
        Employee.id == data.employee_id, Employee.is_active.is_(True)).first()
    if employee is None:
        raise HTTPException(404, "Không tìm thấy nhân sự")
    policy = _policy_or_404(db, data.policy_id)
    today = vn_today()
    try:
        assignment, balances = service.create_one(
            db, user, employee, policy, data.effective_from, data.effective_to, data.note,
            data.recalc_current_year, data.close_previous, today.year, today,
            actor_employee_id=getattr(user, "employee_id", 0) or 0, actor_is_admin=is_system_admin(db, user.id))
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, CONFLICT_DUP)
    except Exception:
        db.rollback()
        raise
    _commit(db)
    emps, policies = lookup_names(db, [assignment])
    return success({"assignment": dump_assignment(assignment, emps, policies, today), "balances": balances},
                   "Đã phân bổ chính sách")


@router.get("/{aid}")
def get_assignment(aid: int, db: Session = Depends(get_db), user=Depends(require(ENTITY, "read"))):
    obj = get_scoped(db, LeavePolicyAssignment, ENTITY, aid, user, get_perm_profile(db, user))
    if obj is None:
        raise HTTPException(404, "Không tìm thấy phân bổ")
    emps, policies = lookup_names(db, [obj])
    return success(dump_assignment(obj, emps, policies, vn_today()))


def _writable(db: Session, user, aid: int) -> LeavePolicyAssignment:
    obj = get_scoped(db, LeavePolicyAssignment, ENTITY, aid, user, get_perm_profile(db, user), "write")
    if obj is None:
        raise HTTPException(404, "Không tìm thấy phân bổ")
    #  D5 áp cả sửa / xóa: không tự nới / thu ngày phép của chính mình qua đường vòng (review M1).
    if is_own_employee(user, obj.employee_id) and not is_system_admin(db, user.id):
        raise HTTPException(403, SELF_MESSAGE)
    return obj


@router.patch("/{aid}")
def update_assignment(aid: int, data: AssignmentUpdate, db: Session = Depends(get_db),
                      user=Depends(require(ENTITY, "write"))):
    """Chỉ sửa `effective_to` (null = không thời hạn) và `note`; đổi gói / ngày bắt đầu = xóa rồi tạo lại."""
    obj = _writable(db, user, aid)
    try:
        balances = service.update_one(db, user, obj, data.model_dump(exclude_unset=True),
                                      data.recalc_current_year, vn_today().year)
    except Exception:
        db.rollback()
        raise
    _commit(db)
    emps, policies = lookup_names(db, [obj])
    return success({"assignment": dump_assignment(obj, emps, policies, vn_today()), "balances": balances}, "Đã cập nhật")


@router.delete("/{aid}")
def delete_assignment(aid: int, recalc_current_year: bool = Query(False), db: Session = Depends(get_db),
                      user=Depends(require(ENTITY, "write"))):
    """Xóa phân bổ; `?recalc_current_year=true` thì tính lại các loại của gói về luật của loại."""
    obj = _writable(db, user, aid)
    try:
        balances = service.delete_one(db, user, obj, recalc_current_year, vn_today().year)
    except Exception:
        db.rollback()
        raise
    _commit(db)
    return success({"balances": balances}, "Đã xóa phân bổ")
