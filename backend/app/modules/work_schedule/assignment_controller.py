"""API GÁN LỊCH — `/api/work-schedule-assignments` (khóa `work_schedule`, PUBLIC).

Đọc (list / get) chỉ cần `work_schedule.read` — vai trò nào cũng có, nên Trưởng phòng thấy dòng lịch riêng của người
phòng mình (qua phạm vi `employee.read`). Ghi (POST / PATCH / DELETE) có HAI đường: khóa Nhân sự `work_schedule.*` (mọi
cấp, luật cũ) và khóa Trưởng phòng `work_schedule_personal.*` (chỉ lịch riêng cấp Nhân sự của người trong phạm vi, không
cho chính mình) — xem `assignment_access`. Đường Trưởng phòng dùng chung `assignment_service`, nên chồng ngày, tự đóng /
mở lại dòng cũ (`assignment_heal`) vẫn chạy và chỉ chạm các dòng của CÙNG nhân sự đó.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, require
from app.core.base_controller import apply_filters, apply_sort, pagination
from app.core.database import get_db
from app.core.response import success
from app.core.scoping import apply_scope, get_perm_profile, get_scoped
from app.core.work_schedule_codes import WorkScheduleLevel
from app.modules.employee.model import Employee

from . import assignment_access as access
from . import assignment_picker as picker
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


@router.get("/tools/assignable-employees")
def assignable_employees(q: str | None = None, pg: dict = Depends(pagination), db: Session = Depends(get_db),
                         user=Depends(get_current_user)):
    """Danh sách nhân sự ĐANG LÀM mà người gọi gán được lịch riêng cho — nguồn của ô chọn đối tượng ở màn gán lịch.

    Quyền: `work_schedule.create` (mọi nhân sự trong phạm vi `employee.read`) hoặc `work_schedule_personal.create` (nhân
    sự trong phạm vi khóa đó, kể cả ô "Phòng ban được xem", trừ chính mình); thiếu cả hai → 403. `q` tìm theo mã / họ tên
    không dấu. Sắp theo họ tên; số truy vấn cố định.
    """
    total, items = picker.list_assignable(db, user, q, pg["offset"], pg["limit"])
    return success({"total": total, "items": items})


@router.get("/{oid}")
def get_assignment(oid: int, db: Session = Depends(get_db), user=Depends(require(ENTITY, "read"))):
    return success(svc.serialize_many(db, [_get_or_404(db, user, oid)])[0])


@router.post("")
def create_assignment(data: AssignmentCreate, db: Session = Depends(get_db),
                      user=Depends(access.require_assignment_action("create"))):
    """Gán một mẫu lịch cho hệ thống / pháp nhân / phòng ban / nhân sự.

    Quyền: `work_schedule.create` (mọi cấp), hoặc `work_schedule_personal.create` (chỉ cấp Nhân sự, nhân sự trong phạm vi,
    không phải chính mình, mẫu lịch phải đang dùng, ngày hiệu lực từ hôm nay trở đi). Lỗi riêng: 400 đích không tồn tại /
    chồng ngày, 403 vượt giới hạn, 422 ngày hiệu lực trong quá khứ.
    """
    if access.holds_hr_key(db, user, "create"):
        _ensure_employee_in_scope(db, user, data.target_level, data.target_id)
    else:
        access.check_personal_target(db, user, get_perm_profile(db, user), "create",
                                     data.target_level, data.target_id)
        access.check_personal_start_date(data.effective_from)
    obj = svc.create_assignment(db, data, user)
    return success(svc.serialize_many(db, [obj])[0], "Đã tạo", 201)


@router.patch("/{oid}")
def update_assignment(oid: int, data: AssignmentUpdate, db: Session = Depends(get_db),
                      user=Depends(access.require_assignment_action("write"))):
    """Sửa một dòng gán lịch (mẫu lịch, khoảng ngày, ghi chú, đích).

    Quyền: `work_schedule.write`, hoặc `work_schedule_personal.write` — khi đó cả dòng đang có lẫn giá trị mới đều phải là
    lịch riêng cấp Nhân sự của người trong phạm vi, không phải của chính người sửa; dòng phải do chính người sửa gán
    (`created_by`, nếu không 403); ngày hiệu lực mới (khi đổi) phải từ hôm nay trở đi (422). Dòng đã bắt đầu chỉ đổi được
    ngày kết thúc (từ hôm qua trở đi) và ghi chú (403 nếu đổi gì khác); dòng đã thay lịch trước đó không đổi được đích /
    ngày (400, xóa rồi tạo lại).
    """
    hr_path = access.holds_hr_key(db, user, "write")
    #  Đường Trưởng phòng đọc dòng bằng quyền `read` (khóa `work_schedule` là PUBLIC, mọi vai trò có `read`): quyền ghi
    #  của họ nằm ở khóa riêng, không có dòng `write` của `work_schedule` để `get_scoped` khớp.
    obj = _get_or_404(db, user, oid, "write" if hr_path else "read")
    new_level = data.target_level or obj.target_level
    new_target = data.target_id if data.target_id is not None else obj.target_id
    if hr_path:
        _ensure_employee_in_scope(db, user, new_level, new_target)
    else:
        profile = get_perm_profile(db, user)
        access.check_personal_existing_row(db, user, profile, "write", obj)
        access.check_personal_target(db, user, profile, "write", new_level, new_target)
        access.check_personal_update(db, obj, data)
        if data.effective_from is not None and data.effective_from != obj.effective_from:
            access.check_personal_start_date(data.effective_from)
    obj = svc.update_assignment(db, obj, data, user)
    return success(svc.serialize_many(db, [obj])[0], "Đã cập nhật")


@router.delete("/{oid}")
def delete_assignment(oid: int, db: Session = Depends(get_db),
                      user=Depends(access.require_assignment_action("delete"))):
    """Xóa một dòng gán lịch (và tự mở lại lịch cũ nếu dòng này từng đóng nó).

    Quyền: `work_schedule.delete`, hoặc `work_schedule_personal.delete` — chỉ xóa được dòng lịch riêng cấp Nhân sự của
    người trong phạm vi, không phải của chính mình, do chính mình gán và CHƯA bắt đầu (dòng ngoài phạm vi → 404, dòng người
    khác gán hoặc đã bắt đầu → 403).
    """
    hr_path = access.holds_hr_key(db, user, "delete")
    obj = _get_or_404(db, user, oid, "delete" if hr_path else "read")
    if not hr_path:
        access.check_personal_existing_row(db, user, get_perm_profile(db, user), "delete", obj)
        access.check_personal_delete(obj)
    svc.delete_assignment(db, obj, user)
    return success(None, "Đã xóa")
