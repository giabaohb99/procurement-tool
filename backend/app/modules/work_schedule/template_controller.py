"""API MẪU LỊCH TUẦN — `/api/work-schedules` + thẻ lịch hiệu lực ở hồ sơ nhân sự.

Khóa quyền `work_schedule` (PUBLIC ở `SCOPE_FIELDS`: danh mục cấu hình, ai đọc được
thì thấy hết). Riêng `/tools/effective` gác theo `employee.read` + `get_scoped` — thẻ
trên hồ sơ không được lộ lịch của người ngoài phạm vi, và cũng không đòi thêm khóa
mới cho vai trò cũ.
"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.auth import require
from app.core.base_controller import apply_filters, apply_sort, pagination
from app.core.database import get_db
from app.core.response import success
from app.core.vn_time import vn_today
from app.core.scoping import apply_scope, get_perm_profile, get_scoped
from app.modules.employee.model import Employee

from . import resolver, roster_service, template_service
from .assignment_schema import YEAR_MAX, YEAR_MIN
from .model import WorkSchedule
from .template_schema import ScheduleCreate, ScheduleUpdate

ENTITY = "work_schedule"
router = APIRouter(prefix="/api/work-schedules", tags=["work_schedule"])


def _get_or_404(db: Session, user, oid: int, action: str = "read") -> WorkSchedule:
    obj = get_scoped(db, WorkSchedule, ENTITY, oid, user, get_perm_profile(db, user), action)
    if obj is None:
        raise HTTPException(404, "Không tìm thấy")
    return obj


@router.get("")
def list_schedules(request: Request, pg: dict = Depends(pagination),
                   sort_by: str | None = None, sort_dir: str = "asc",
                   db: Session = Depends(get_db), user=Depends(require(ENTITY, "read"))):
    q = apply_filters(db.query(WorkSchedule), WorkSchedule, request, ["name", "is_active"])
    q = apply_scope(q, WorkSchedule, ENTITY, user, get_perm_profile(db, user))
    total = q.count()
    q = apply_sort(q, WorkSchedule, sort_by, sort_dir)
    items = q.offset(pg["offset"]).limit(pg["limit"]).all()
    return success({"total": total, "items": template_service.serialize_many(db, items)})


#  Đặt TRƯỚC `/{oid}` cho dễ đọc (hai đoạn nên không đụng nhau).
@router.get("/tools/effective")
def effective_schedule(employee_id: int, on_date: date | None = None,
                       db: Session = Depends(get_db), user=Depends(require("employee", "read"))):
    """Lịch làm việc hiệu lực của một nhân sự vào `on_date` (mặc định hôm nay)."""
    emp = get_scoped(db, Employee, "employee", employee_id, user, get_perm_profile(db, user))
    if emp is None:
        raise HTTPException(404, "Không tìm thấy")
    #  Giờ VN, không `date.today()`: container chạy UTC, 00:00–06:59 sáng VN sẽ lệch một ngày.
    day = on_date or vn_today()
    if not (YEAR_MIN <= day.year <= YEAR_MAX):
        raise HTTPException(422, f"Ngày phải nằm trong năm {YEAR_MIN}–{YEAR_MAX}")
    return success(resolver.effective_for_employee(db, emp, day))


@router.get("/tools/roster")
def work_roster(from_date: date, to_date: date, company_id: int = Query(0, ge=0),
                department_id: int = Query(0, ge=0), q: str = Query("", max_length=100),
                page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=100),
                db: Session = Depends(get_db), user=Depends(require("employee", "read"))):
    """«Ai làm / ai nghỉ» từng ngày — lưới nhân sự × ngày (tối đa 42 ngày, phân trang theo người).

    Hàng theo phạm vi `employee.read`; lớp nghỉ phép theo phạm vi `leave_request.read` (xem
    `roster_service`). Số truy vấn cố định."""
    if not (YEAR_MIN <= from_date.year <= YEAR_MAX and YEAR_MIN <= to_date.year <= YEAR_MAX):
        raise HTTPException(422, f"Ngày phải nằm trong năm {YEAR_MIN}–{YEAR_MAX}")
    if to_date < from_date:
        raise HTTPException(422, "Đến ngày phải sau hoặc bằng Từ ngày")
    if (to_date - from_date).days + 1 > roster_service.MAX_ROSTER_DAYS:
        raise HTTPException(422, f"Chỉ xem tối đa {roster_service.MAX_ROSTER_DAYS} ngày một lần")
    params = {"from_date": from_date, "to_date": to_date, "company_id": company_id,
              "department_id": department_id, "q": q.strip(), "page": page, "page_size": page_size}
    return success(roster_service.build_roster(db, user, get_perm_profile(db, user), params))


@router.get("/{oid}")
def get_schedule(oid: int, db: Session = Depends(get_db), user=Depends(require(ENTITY, "read"))):
    return success(template_service.serialize_one(db, _get_or_404(db, user, oid)))


@router.post("")
def create_schedule(data: ScheduleCreate, db: Session = Depends(get_db),
                    user=Depends(require(ENTITY, "create"))):
    obj = template_service.create_schedule(db, data, user)
    return success(template_service.serialize_one(db, obj), "Đã tạo", 201)


@router.patch("/{oid}")
def update_schedule(oid: int, data: ScheduleUpdate, db: Session = Depends(get_db),
                    user=Depends(require(ENTITY, "write"))):
    obj = template_service.update_schedule(db, _get_or_404(db, user, oid, "write"), data, user)
    return success(template_service.serialize_one(db, obj), "Đã cập nhật")


@router.delete("/{oid}")
def delete_schedule(oid: int, db: Session = Depends(get_db),
                    user=Depends(require(ENTITY, "delete"))):
    template_service.delete_schedule(db, _get_or_404(db, user, oid, "delete"), user)
    return success(None, "Đã xóa")
