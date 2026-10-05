"""API GÁN LỊCH — `/api/work-schedule-assignments` (khóa `work_schedule`, PUBLIC)."""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.auth import require
from app.core.base_controller import apply_filters, apply_sort, pagination
from app.core.database import get_db
from app.core.response import success
from app.core.scoping import apply_scope, get_perm_profile, get_scoped
from app.core.work_schedule_codes import WorkScheduleLevel
from app.modules.employee.model import Employee

from . import assignment_scope as scope
from . import assignment_service as svc
from .assignment_schema import AssignmentCreate, AssignmentUpdate
from .model import WorkScheduleAssignment as Assignment

ENTITY = "work_schedule"
router = APIRouter(prefix="/api/work-schedule-assignments", tags=["work_schedule"])


def _get_or_404(db: Session, user, oid: int, action: str = "read") -> Assignment:
    obj = get_scoped(db, Assignment, ENTITY, oid, user, get_perm_profile(db, user), action)
    #  Dòng cấp Nhân sự của người ngoài phạm vi `employee` -> 404 như id không tồn tại (bug M3).
    if obj is None or not scope.employee_row_visible(db, user, get_perm_profile(db, user), obj):
        raise HTTPException(404, "Không tìm thấy")
    return obj


def _ensure_employee_in_scope(db: Session, user, level: int | None, target_id: int | None) -> None:
    """Gán lịch cho NHÂN SỰ ngoài phạm vi `employee` -> 400 như id không tồn tại (bug M3):
    cùng thông điệp với service nên không lộ nhân sự đó có thật hay không."""
    if level != int(WorkScheduleLevel.EMPLOYEE) or not target_id:
        return
    if get_scoped(db, Employee, "employee", target_id, user, get_perm_profile(db, user)) is None:
        raise HTTPException(400, "Đối tượng được gán lịch không tồn tại")


@router.get("")
def list_assignments(request: Request, pg: dict = Depends(pagination),
                     sort_by: str | None = None, sort_dir: str = "asc",
                     db: Session = Depends(get_db), user=Depends(require(ENTITY, "read"))):
    q = apply_filters(db.query(Assignment), Assignment, request,
                      ["target_level", "target_id", "schedule_id"])
    profile = get_perm_profile(db, user)
    q = apply_scope(q, Assignment, ENTITY, user, profile)
    emp_cond = scope.employee_scope_condition(db, user, profile)
    if emp_cond is not None:
        q = q.filter(emp_cond)
    total = q.count()
    q = apply_sort(q, Assignment, sort_by, sort_dir,
                   default=(Assignment.effective_from.desc(), Assignment.id.desc()))
    items = q.offset(pg["offset"]).limit(pg["limit"]).all()
    return success({"total": total, "items": svc.serialize_many(db, items)})


@router.get("/{oid}")
def get_assignment(oid: int, db: Session = Depends(get_db), user=Depends(require(ENTITY, "read"))):
    return success(svc.serialize_many(db, [_get_or_404(db, user, oid)])[0])


@router.post("")
def create_assignment(data: AssignmentCreate, db: Session = Depends(get_db),
                      user=Depends(require(ENTITY, "create"))):
    _ensure_employee_in_scope(db, user, data.target_level, data.target_id)
    obj = svc.create_assignment(db, data, user)
    return success(svc.serialize_many(db, [obj])[0], "Đã tạo", 201)


@router.patch("/{oid}")
def update_assignment(oid: int, data: AssignmentUpdate, db: Session = Depends(get_db),
                      user=Depends(require(ENTITY, "write"))):
    obj = _get_or_404(db, user, oid, "write")
    _ensure_employee_in_scope(db, user, data.target_level or obj.target_level,
                              data.target_id if data.target_id is not None else obj.target_id)
    obj = svc.update_assignment(db, obj, data, user)
    return success(svc.serialize_many(db, [obj])[0], "Đã cập nhật")


@router.delete("/{oid}")
def delete_assignment(oid: int, db: Session = Depends(get_db),
                      user=Depends(require(ENTITY, "delete"))):
    svc.delete_assignment(db, _get_or_404(db, user, oid, "delete"), user)
    return success(None, "Đã xóa")
