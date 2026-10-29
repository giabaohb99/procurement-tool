"""Danh mục của kế hoạch nhân sự: `/api/hr-cost-groups` (nhóm chi phí) và `/api/hr-cost-templates` (mẫu khoản).

Đọc theo `headcount_plan.read`, ghi theo `headcount_plan.write` (chốt 28/10: chỉ trưởng phòng Nhân sự + admin ghi).
Viết tay thay vì `make_crud_router`: bộ sinh đó lọc theo phạm vi cột `company_id` / `department_id` mà hai bảng này không có.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.auth import require
from app.core.base_controller import pagination
from app.core.crud import commit_or_conflict
from app.core.database import get_db
from app.core.response import success

from . import catalog_service as svc
from .cost_model import HrCostGroup, HrCostTemplate, HrCostTemplateItem
from .detail_serializer import cost_item_out
from .schema import CostGroupIn, CostGroupPatch, CostTemplateIn, CostTemplatePatch

ENTITY = "headcount_plan"
groups_router = APIRouter(prefix="/api/hr-cost-groups", tags=["hr_cost_group"])
templates_router = APIRouter(prefix="/api/hr-cost-templates", tags=["hr_cost_template"])


def _group_out(g: HrCostGroup) -> dict:
    return {"id": g.id, "name": g.name, "sort_order": g.sort_order or 0, "is_active": bool(g.is_active)}


def _get_or_404(db: Session, model, oid: int):
    obj = db.get(model, oid)
    if obj is None:
        raise HTTPException(404, "Không tìm thấy")
    return obj


@groups_router.get("")
def list_groups(is_active: bool | None = None, pg: dict = Depends(pagination), db: Session = Depends(get_db),
                user=Depends(require(ENTITY, "read"))):
    q = db.query(HrCostGroup)
    if is_active is not None:
        q = q.filter(HrCostGroup.is_active == is_active)
    rows = q.order_by(HrCostGroup.sort_order, HrCostGroup.id).offset(pg["offset"]).limit(pg["limit"]).all()
    return success({"total": q.count(), "items": [_group_out(g) for g in rows]})


@groups_router.get("/{oid}")
def get_group(oid: int, db: Session = Depends(get_db), user=Depends(require(ENTITY, "read"))):
    return success(_group_out(_get_or_404(db, HrCostGroup, oid)))


@groups_router.post("")
def create_group(data: CostGroupIn, db: Session = Depends(get_db), user=Depends(require(ENTITY, "create"))):
    svc.ensure_unique_name(db, HrCostGroup, data.name)
    g = HrCostGroup(**data.model_dump(), created_by=user.id, updated_by=user.id)
    db.add(g)
    commit_or_conflict(db, "Tên nhóm chi phí đã được dùng")
    record(db, user.id, "hr_cost_group", g.id, "create")
    return success(_group_out(g), "Đã tạo", 201)


@groups_router.patch("/{oid}")
def update_group(oid: int, data: CostGroupPatch, db: Session = Depends(get_db), user=Depends(require(ENTITY, "write"))):
    g = _get_or_404(db, HrCostGroup, oid)
    values = data.model_dump(exclude_unset=True)
    if any(v is None for v in values.values()):
        raise HTTPException(422, "Trường không được để trống")
    if "name" in values:
        svc.ensure_unique_name(db, HrCostGroup, values["name"], exclude_id=oid)
    for k, v in values.items():
        setattr(g, k, v)
    g.updated_by = user.id
    commit_or_conflict(db, "Tên nhóm chi phí đã được dùng")
    record(db, user.id, "hr_cost_group", oid, "update")
    return success(_group_out(g), "Đã cập nhật")


@groups_router.delete("/{oid}")
def delete_group(oid: int, db: Session = Depends(get_db), user=Depends(require(ENTITY, "delete"))):
    g = _get_or_404(db, HrCostGroup, oid)
    svc.check_group_not_in_use(db, oid)
    db.delete(g)
    db.commit()
    record(db, user.id, "hr_cost_group", oid, "delete")
    return success(None, "Đã xóa")


# ---- Mẫu khoản chi phí ----------------------------------------------------------------------------
def _template_out(db: Session, t: HrCostTemplate, with_items: bool = True) -> dict:
    items = db.query(HrCostTemplateItem).filter(HrCostTemplateItem.template_id == t.id).order_by(
        HrCostTemplateItem.sort_order, HrCostTemplateItem.id).all()
    out = {"id": t.id, "name": t.name, "note": t.note or "", "is_active": bool(t.is_active),
           "item_count": len(items), "updated_at": t.updated_at}
    if with_items:
        out["items"] = [cost_item_out(i, True) for i in items]
    return out


@templates_router.get("")
def list_templates(is_active: bool | None = None, pg: dict = Depends(pagination), db: Session = Depends(get_db),
                   user=Depends(require(ENTITY, "read"))):
    q = db.query(HrCostTemplate)
    if is_active is not None:
        q = q.filter(HrCostTemplate.is_active == is_active)
    rows = q.order_by(HrCostTemplate.name).offset(pg["offset"]).limit(pg["limit"]).all()
    #  Đếm khoản của cả trang bằng MỘT câu GROUP BY (không mở danh sách khoản từng mẫu)
    counts = dict(db.query(HrCostTemplateItem.template_id, func.count(HrCostTemplateItem.id)).filter(
        HrCostTemplateItem.template_id.in_([t.id for t in rows] or [0])).group_by(HrCostTemplateItem.template_id).all())
    return success({"total": q.count(), "items": [
        {"id": t.id, "name": t.name, "note": t.note or "", "is_active": bool(t.is_active),
         "item_count": counts.get(t.id, 0), "updated_at": t.updated_at} for t in rows]})


@templates_router.get("/{oid}")
def get_template(oid: int, db: Session = Depends(get_db), user=Depends(require(ENTITY, "read"))):
    return success(_template_out(db, _get_or_404(db, HrCostTemplate, oid)))


@templates_router.post("")
def create_template(data: CostTemplateIn, db: Session = Depends(get_db), user=Depends(require(ENTITY, "create"))):
    svc.ensure_unique_name(db, HrCostTemplate, data.name)
    svc.validate_template_items(db, data.items)
    t = HrCostTemplate(name=data.name, note=data.note, is_active=data.is_active, created_by=user.id, updated_by=user.id)
    db.add(t)
    db.flush()
    svc.replace_template_items(db, t.id, data.items, user.id)
    commit_or_conflict(db, "Tên mẫu đã được dùng")
    record(db, user.id, "hr_cost_template", t.id, "create")
    return success(_template_out(db, t), "Đã tạo", 201)


@templates_router.patch("/{oid}")
def update_template(oid: int, data: CostTemplatePatch, db: Session = Depends(get_db),
                    user=Depends(require(ENTITY, "write"))):
    t = _get_or_404(db, HrCostTemplate, oid)
    values = data.model_dump(exclude_unset=True, exclude={"items"})
    if any(v is None for v in values.values()):
        raise HTTPException(422, "Trường không được để trống")
    if "name" in values:
        svc.ensure_unique_name(db, HrCostTemplate, values["name"], exclude_id=oid)
    if data.items is not None:
        svc.validate_template_items(db, data.items)
        svc.replace_template_items(db, oid, data.items, user.id)
    for k, v in values.items():
        setattr(t, k, v)
    t.updated_by = user.id
    commit_or_conflict(db, "Tên mẫu đã được dùng")
    record(db, user.id, "hr_cost_template", oid, "update")
    return success(_template_out(db, t), "Đã cập nhật")


@templates_router.post("/{oid}/duplicate")
def duplicate_template(oid: int, db: Session = Depends(get_db), user=Depends(require(ENTITY, "create"))):
    copy = svc.duplicate_template(db, _get_or_404(db, HrCostTemplate, oid), user.id)
    commit_or_conflict(db, "Tên mẫu đã được dùng")
    record(db, user.id, "hr_cost_template", copy.id, "create", f"Sao chép từ mẫu {oid}")
    return success(_template_out(db, copy), "Đã sao chép", 201)


@templates_router.delete("/{oid}")
def delete_template(oid: int, db: Session = Depends(get_db), user=Depends(require(ENTITY, "delete"))):
    t = _get_or_404(db, HrCostTemplate, oid)   # kế hoạch đã lập giữ BẢN CHỤP khoản nên xóa mẫu không ảnh hưởng chúng
    db.query(HrCostTemplateItem).filter(HrCostTemplateItem.template_id == oid).delete(synchronize_session=False)
    db.delete(t)
    db.commit()
    record(db, user.id, "hr_cost_template", oid, "delete")
    return success(None, "Đã xóa")
