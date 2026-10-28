"""CRUD kế hoạch nhân sự `/api/headcount-plans` (duoc-CR-689, entity `headcount_plan`).

Viết tay (không dùng `make_crud_router`): bộ sinh đó nhập CSV theo `code` + cột `is_active`, trong khi bảng
này khóa theo (năm, pháp nhân, phòng) và phải CHE số lương theo quyền `labor_contract.read`.
Mọi đường qua `require` + `apply_scope` / `get_scoped`; xuất dùng phạm vi `export`.
"""
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.auth import require
from app.core.base_controller import pagination
from app.core.crud import commit_or_conflict
from app.core.database import get_db
from app.core.response import success
from app.core.scoping import apply_scope, get_perm_profile, get_scoped

from . import csv_service, service
from .model import HeadcountPlan
from .schema import HeadcountPlanCreate, HeadcountPlanUpdate
from .serializer import serialize_plans

ENTITY = "headcount_plan"
router = APIRouter(prefix="/api/headcount-plans", tags=[ENTITY])


def _filtered(db: Session, user, year, company_id, department_id, action: str = "read"):
    q = db.query(HeadcountPlan)
    for col, val in ((HeadcountPlan.year, year), (HeadcountPlan.company_id, company_id),
                     (HeadcountPlan.department_id, department_id)):
        if val is not None:
            q = q.filter(col == val)
    return apply_scope(q, HeadcountPlan, ENTITY, user, get_perm_profile(db, user), action)


_ORDER = (HeadcountPlan.year.desc(), HeadcountPlan.company_id, HeadcountPlan.department_id)


@router.get("")
def list_plans(year: int | None = None, company_id: int | None = None, department_id: int | None = None,
               pg: dict = Depends(pagination), db: Session = Depends(get_db), user=Depends(require(ENTITY, "read"))):
    q = _filtered(db, user, year, company_id, department_id)
    items = q.order_by(*_ORDER).offset(pg["offset"]).limit(pg["limit"]).all()
    return success({"total": q.count(), "items": serialize_plans(db, items, get_perm_profile(db, user))})


@router.get("/export/csv")
def export_csv(year: int | None = None, company_id: int | None = None, department_id: int | None = None,
               db: Session = Depends(get_db), user=Depends(require(ENTITY, "export"))):
    plans = _filtered(db, user, year, company_id, department_id, "export").order_by(*_ORDER).all()
    body = csv_service.to_csv(csv_service.export_rows(db, plans, get_perm_profile(db, user)))
    return Response(content=body, media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": "attachment; filename=ke-hoach-nhan-su.csv"})


@router.post("/import/csv", dependencies=[Depends(require(ENTITY, "create"))])
def import_csv(file: UploadFile = File(...), db: Session = Depends(get_db), user=Depends(require(ENTITY, "write"))):
    result = csv_service.import_rows(db, file.file.read(csv_service.MAX_BYTES + 1), user, get_perm_profile(db, user))
    record(db, user.id, ENTITY, 0, "import", f"Thêm {result['created']}, cập nhật {result['updated']}")
    return success(result, f"Đã nhập: thêm {result['created']}, cập nhật {result['updated']}")


@router.get("/{oid}")
def get_plan(oid: int, db: Session = Depends(get_db), user=Depends(require(ENTITY, "read"))):
    prof = get_perm_profile(db, user)
    obj = get_scoped(db, HeadcountPlan, ENTITY, oid, user, prof)
    if obj is None:
        raise HTTPException(404, "Không tìm thấy")
    return success(serialize_plans(db, [obj], prof)[0])


@router.post("")
def create_plan(data: HeadcountPlanCreate, db: Session = Depends(get_db), user=Depends(require(ENTITY, "create"))):
    prof = get_perm_profile(db, user)
    service.guard_payroll_write(prof, data.planned_payroll_monthly, data.company_id)
    service.check_refs(db, data.company_id, data.department_id)
    service.ensure_unique(db, data.year, data.company_id, data.department_id)
    obj = HeadcountPlan(**{**data.model_dump(), "planned_payroll_monthly": data.planned_payroll_monthly or 0},
                        created_by=user.id, updated_by=user.id)
    db.add(obj)
    db.flush()
    if get_scoped(db, HeadcountPlan, ENTITY, obj.id, user, prof, "create") is None:   # dòng mới phải nằm trong phạm vi
        db.rollback()
        raise HTTPException(403, "Kế hoạch nằm ngoài phạm vi dữ liệu của bạn")
    commit_or_conflict(db, "Đã có kế hoạch cho năm, pháp nhân và phòng này")
    record(db, user.id, ENTITY, obj.id, "create")
    return success(serialize_plans(db, [obj], prof)[0], "Đã tạo", 201)


@router.patch("/{oid}")
def update_plan(oid: int, data: HeadcountPlanUpdate, db: Session = Depends(get_db),
                user=Depends(require(ENTITY, "write"))):
    prof = get_perm_profile(db, user)
    obj = get_scoped(db, HeadcountPlan, ENTITY, oid, user, prof, "write")
    if obj is None:
        raise HTTPException(404, "Không tìm thấy")
    values = data.model_dump(exclude_unset=True)
    for k in ("year", "company_id", "department_id", "planned_headcount", "note"):
        if k in values and values[k] is None:
            raise HTTPException(422, f"{k} không được để trống")
    service.drop_blind_payroll(prof, values, obj.company_id)
    service.guard_payroll_write(prof, values.get("planned_payroll_monthly"), values.get("company_id", obj.company_id))
    new_company = values.get("company_id", obj.company_id)
    if new_company != obj.company_id and obj.planned_payroll_monthly:
        #  Dời dòng đang có quỹ lương sang pháp nhân khác: phải đọc được lương ở CẢ HAI bên — nếu không, người
        #  không xem được quỹ của A dời sang B (mình xem được) là đọc ra số của A, hoặc gán số của mình cho B.
        service.guard_payroll_write(prof, obj.planned_payroll_monthly, obj.company_id)
        if values.get("planned_payroll_monthly", obj.planned_payroll_monthly):
            service.guard_payroll_write(prof, obj.planned_payroll_monthly, new_company)
    if values.get("planned_payroll_monthly", 0) is None:
        values.pop("planned_payroll_monthly")
    key = {k: values.get(k, getattr(obj, k)) for k in ("year", "company_id", "department_id")}
    if any(key[k] != getattr(obj, k) for k in key):
        service.check_refs(db, key["company_id"], key["department_id"])
        service.ensure_unique(db, key["year"], key["company_id"], key["department_id"], exclude_id=obj.id)
    for k, v in values.items():
        setattr(obj, k, v)
    obj.updated_by = user.id
    db.flush()
    if get_scoped(db, HeadcountPlan, ENTITY, obj.id, user, prof, "write") is None:   # không đẩy dòng ra ngoài phạm vi
        db.rollback()
        raise HTTPException(403, "Kế hoạch nằm ngoài phạm vi dữ liệu của bạn")
    commit_or_conflict(db, "Đã có kế hoạch cho năm, pháp nhân và phòng này")
    record(db, user.id, ENTITY, oid, "update")
    return success(serialize_plans(db, [obj], prof)[0], "Đã cập nhật")


@router.delete("/{oid}")
def delete_plan(oid: int, db: Session = Depends(get_db), user=Depends(require(ENTITY, "delete"))):
    obj = get_scoped(db, HeadcountPlan, ENTITY, oid, user, get_perm_profile(db, user), "delete")
    if obj is None:
        raise HTTPException(404, "Không tìm thấy")
    db.delete(obj)
    db.commit()
    record(db, user.id, ENTITY, oid, "delete")
    return success(None, "Đã xóa")
