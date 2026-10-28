"""Kế hoạch nhân sự theo kỳ `/api/headcount-plans` (duoc-CR-690, entity `headcount_plan`; thiết kế `doc/erp/hrm/06`).

Viết tay (không dùng `make_crud_router`): khóa duy nhất là (năm, loại kỳ, kỳ, pháp nhân, phòng), có khoản / dòng con, và phải
CHE tiền theo pháp nhân. Mọi đường qua `require` + `apply_scope` / `get_scoped`; xuất dùng phạm vi `export`.
Đường cố định (`/compute`, `/position-stats`, `/export/csv`) khai TRƯỚC `/{oid}`.
"""
from contextlib import contextmanager
from datetime import date

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.auth import require
from app.core.base_controller import pagination
from app.core.crud import commit_or_conflict
from app.core.database import get_db
from app.core.response import success
from app.core.scoping import apply_scope, get_perm_profile, get_scoped
from app.core.vn_time import vn_today
from app.modules.attachment.model import FileLink

from . import catalog_service, csv_service, export_service, plan_save_service, service
from .cost_model import HeadcountPlanCostItem
from .costing import PlanCalcError
from .detail_serializer import load_children, serialize_detail
from .model import HeadcountPlan, HeadcountPlanDocument, HeadcountPlanLine
from .position_stats import get_position_stats
from .schema import HeadcountPlanCreate, HeadcountPlanSave, PlanDraft
from .serializer import can_see_payroll, compute_from, mask_computed, serialize_plans

ENTITY = "headcount_plan"
router = APIRouter(prefix="/api/headcount-plans", tags=[ENTITY])

_ORDER = (HeadcountPlan.year.desc(), HeadcountPlan.period_type, HeadcountPlan.period_no,
          HeadcountPlan.company_id, HeadcountPlan.department_id)
_OUT_OF_SCOPE = "Kế hoạch nằm ngoài phạm vi dữ liệu của bạn"


def _filtered(db: Session, user, year, period_type, company_id, department_id, action: str = "read"):
    q = db.query(HeadcountPlan)
    for col, val in ((HeadcountPlan.year, year), (HeadcountPlan.period_type, period_type),
                     (HeadcountPlan.company_id, company_id), (HeadcountPlan.department_id, department_id)):
        if val is not None:
            q = q.filter(col == val)
    return apply_scope(q, HeadcountPlan, ENTITY, user, get_perm_profile(db, user), action)


def _get_or_404(db: Session, user, prof: dict, oid: int, action: str = "read") -> HeadcountPlan:
    obj = get_scoped(db, HeadcountPlan, ENTITY, oid, user, prof, action)
    if obj is None:
        raise HTTPException(404, "Không tìm thấy")
    return obj


@contextmanager
def _atomic(db: Session):
    """Mọi lỗi nghiệp vụ giữa chừng (422/403…) hoàn tác cả những gì đã flush — không để lại kế hoạch nửa vời."""
    try:
        yield
    except Exception:
        db.rollback()
        raise


def _check_in_scope(db: Session, user, prof: dict, plan: HeadcountPlan, action: str) -> None:
    """Dòng vừa ghi phải còn nằm trong phạm vi của người ghi — không thì hoàn tác cả giao dịch."""
    db.flush()
    if get_scoped(db, HeadcountPlan, ENTITY, plan.id, user, prof, action) is None:
        db.rollback()
        raise HTTPException(403, _OUT_OF_SCOPE)


@router.get("")
def list_plans(year: int | None = None, period_type: int | None = None, company_id: int | None = None,
               department_id: int | None = None, pg: dict = Depends(pagination), db: Session = Depends(get_db),
               user=Depends(require(ENTITY, "read"))):
    q = _filtered(db, user, year, period_type, company_id, department_id)
    items = q.order_by(*_ORDER).offset(pg["offset"]).limit(pg["limit"]).all()
    return success({"total": q.count(), "items": serialize_plans(db, items, get_perm_profile(db, user), user)})


@router.get("/export/csv")
def export_csv(year: int | None = None, period_type: int | None = None, company_id: int | None = None,
               department_id: int | None = None, db: Session = Depends(get_db), user=Depends(require(ENTITY, "export"))):
    plans = _filtered(db, user, year, period_type, company_id, department_id, "export").order_by(*_ORDER).all()
    body = csv_service.to_csv(csv_service.export_rows(db, serialize_plans(db, plans, get_perm_profile(db, user), user)))
    return Response(content=body, media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": "attachment; filename=ke-hoach-nhan-su.csv"})


@router.post("/compute")
def compute_draft(data: PlanDraft, db: Session = Depends(get_db), user=Depends(require(ENTITY, "read"))):
    """Xem trước số tự tính của bản NHÁP (không lưu). Tiền chỉ trả khi được xem tiền của `company_id` trong bản nháp."""
    prof = get_perm_profile(db, user)
    items = [HeadcountPlanCostItem(**i.model_dump(exclude={"cap_amount", "amount"}),
                                   cap_amount=i.cap_amount or 0, amount=i.amount or 0) for i in data.cost_items]
    lines = [HeadcountPlanLine(position_id=ln.position_id, headcounts=ln.headcounts, amounts=ln.amounts or {})
             for ln in data.lines]
    try:
        computed = compute_from(db, data.year, data.period_type, data.period_no, items, lines)
    except PlanCalcError as e:
        raise HTTPException(422, str(e))
    return success(computed if can_see_payroll(prof, data.company_id, data.department_id) else mask_computed(computed))


@router.get("/position-stats")
def position_stats(company_id: int, department_id: int = 0, as_of: date | None = None, db: Session = Depends(get_db),
                   user=Depends(require(ENTITY, "read"))):
    prof = get_perm_profile(db, user)
    return success(get_position_stats(db, user, prof, company_id, department_id, as_of or vn_today()))


@router.get("/{oid}")
def get_plan(oid: int, db: Session = Depends(get_db), user=Depends(require(ENTITY, "read"))):
    prof = get_perm_profile(db, user)
    return success(serialize_detail(db, _get_or_404(db, user, prof, oid), user, prof))


@router.get("/{oid}/export")
def export_plan(oid: int, db: Session = Depends(get_db), user=Depends(require(ENTITY, "export"))):
    prof = get_perm_profile(db, user)
    plan = _get_or_404(db, user, prof, oid, "export")
    try:
        return export_service.xlsx_response(db, plan, prof)
    except PlanCalcError as e:
        raise HTTPException(422, str(e))


@router.post("")
def create_plan(data: HeadcountPlanCreate, db: Session = Depends(get_db), user=Depends(require(ENTITY, "create"))):
    prof = get_perm_profile(db, user)
    with _atomic(db):
        return _create_plan(data, db, user, prof)


def _create_plan(data: HeadcountPlanCreate, db: Session, user, prof: dict):
    service.check_refs(db, data.company_id, data.department_id)
    service.check_approver(db, user, prof, data.approver_employee_id)
    service.ensure_unique(db, data.year, data.period_type, data.period_no, data.company_id, data.department_id)
    plan = HeadcountPlan(**data.model_dump(include={"year", "period_type", "period_no", "company_id", "department_id",
                                                    "basis_no", "basis_date", "approver_employee_id", "note",
                                                    "template_id"}), created_by=user.id, updated_by=user.id)
    db.add(plan)
    db.flush()
    skipped: list[str] = []
    if data.cost_items is not None:
        catalog_service.ensure_groups_exist(db, [i.group_id for i in data.cost_items])
        items = plan_save_service.build_items(db, plan, data.cost_items, prof)
    elif data.template_id:
        items, skipped = plan_save_service.copy_template_items(db, data.template_id, plan.period_type, plan.period_no)
    else:
        items = []
    plan_save_service.replace_children(db, plan, items, data.lines, data.document_ids, user, prof)
    _check_in_scope(db, user, prof, plan, "create")   # dòng mới phải nằm trong phạm vi
    commit_or_conflict(db, service.DUPLICATE_MESSAGE)
    record(db, user.id, ENTITY, plan.id, "create")
    return success(serialize_detail(db, plan, user, prof) | {"skipped_items": skipped}, "Đã tạo", 201)


@router.put("/{oid}")
def update_plan(oid: int, data: HeadcountPlanSave, db: Session = Depends(get_db), user=Depends(require(ENTITY, "write"))):
    prof = get_perm_profile(db, user)
    plan = _get_or_404(db, user, prof, oid, "write")
    with _atomic(db):
        return _update_plan(plan, data, db, user, prof)


def _update_plan(plan: HeadcountPlan, data: HeadcountPlanSave, db: Session, user, prof: dict):
    oid = plan.id
    key = ("year", "period_type", "period_no", "company_id", "department_id")
    if any(getattr(data, k) != getattr(plan, k) for k in key):
        service.check_refs(db, data.company_id, data.department_id)
        service.ensure_unique(db, data.year, data.period_type, data.period_no, data.company_id, data.department_id,
                              exclude_id=plan.id)
    if data.approver_employee_id != (plan.approver_employee_id or 0):
        service.check_approver(db, user, prof, data.approver_employee_id)   # người duyệt cũ giữ nguyên thì không soi lại
    moved = (data.company_id, data.department_id) != (plan.company_id, plan.department_id or 0)
    if moved and (not can_see_payroll(prof, plan.company_id, plan.department_id or 0)
                  or not can_see_payroll(prof, data.company_id, data.department_id)):
        #  Dời kế hoạch sang pháp nhân / phòng khác khi không xem được tiền ở MỘT trong hai bên: hoặc đọc ra số của bên kia,
        #  hoặc gán số của mình cho bên kia. Cả hai đều lộ / sửa tiền ngoài quyền.
        if db.query(HeadcountPlanCostItem.id).filter(HeadcountPlanCostItem.plan_id == plan.id).first() is not None:
            raise HTTPException(403, service.PAYROLL_DENIED)
    for k in (*key, "basis_no", "basis_date", "approver_employee_id", "note"):
        setattr(plan, k, getattr(data, k))
    plan.updated_by = user.id
    catalog_service.ensure_groups_exist(db, [i.group_id for i in data.cost_items])
    items = plan_save_service.build_items(db, plan, data.cost_items, prof, restrict_structure=True)
    try:
        plan_save_service.replace_children(db, plan, items, data.lines, data.document_ids, user, prof)
        _check_in_scope(db, user, prof, plan, "write")   # không đẩy dòng ra ngoài phạm vi
    except IntegrityError:   # hai người cùng thay khoản / dòng: người đến sau đụng ràng buộc duy nhất
        db.rollback()
        raise HTTPException(409, service.CONFLICT_MESSAGE)
    commit_or_conflict(db, service.DUPLICATE_MESSAGE)
    record(db, user.id, ENTITY, oid, "update")
    return success(serialize_detail(db, plan, user, prof), "Đã cập nhật")


@router.post("/{oid}/import/csv")
def import_lines_csv(oid: int, file: UploadFile = File(...), db: Session = Depends(get_db),
                     user=Depends(require(ENTITY, "write"))):
    prof = get_perm_profile(db, user)
    plan = _get_or_404(db, user, prof, oid, "write")
    result = csv_service.import_lines(db, plan, file.file.read(csv_service.MAX_BYTES + 1), prof, user.id)
    try:
        db.flush()
    except IntegrityError:   # hai người cùng thêm một vị trí
        db.rollback()
        raise HTTPException(409, service.CONFLICT_MESSAGE)
    items, lines = load_children(db, plan.id)
    try:   # sau khi trộn dòng mới vào, cả kế hoạch vẫn phải đúng luật tính (đủ số kỳ con, khoản nhập theo vị trí…)
        compute_from(db, plan.year, plan.period_type, plan.period_no, items, lines)
    except PlanCalcError as e:
        db.rollback()
        raise HTTPException(422, str(e))
    plan.updated_by = user.id
    commit_or_conflict(db, service.CONFLICT_MESSAGE)
    record(db, user.id, ENTITY, oid, "import", f"Thêm {result['created']}, cập nhật {result['updated']}")
    return success(result, f"Đã nhập: thêm {result['created']}, cập nhật {result['updated']}")


@router.delete("/{oid}")
def delete_plan(oid: int, db: Session = Depends(get_db), user=Depends(require(ENTITY, "delete"))):
    plan = _get_or_404(db, user, get_perm_profile(db, user), oid, "delete")
    for model in (HeadcountPlanCostItem, HeadcountPlanLine, HeadcountPlanDocument):
        db.query(model).filter(model.plan_id == oid).delete(synchronize_session=False)
    db.query(FileLink).filter(FileLink.entity == "headcount_plan", FileLink.entity_id == oid).delete(
        synchronize_session=False)   # chỉ gỡ liên kết; tệp thật vẫn nằm trong kho (dọn tệp mồ côi là việc chung)
    db.delete(plan)
    db.commit()
    record(db, user.id, ENTITY, oid, "delete")
    return success(None, "Đã xóa")
