"""Nhóm chi phí + mẫu khoản chi phí (duoc-CR-690): kiểm tên duy nhất, kiểm cấu trúc khoản, thay nguyên danh sách khoản,
sao chép mẫu, chặn xóa nhóm đang dùng. Danh mục KHÔNG chứa lương ai nên không có phạm vi dữ liệu theo pháp nhân."""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from .cost_model import HeadcountPlanCostItem, HrCostGroup, HrCostTemplate, HrCostTemplateItem
from .costing import PlanCalcError, validate_plan
from .constants import PlanPeriodType
from .schema import CostItemIn
from .serializer import to_cost_item

ITEM_FIELDS = ("code", "name", "group_id", "calc_method", "rate", "factor", "cap_amount", "amount", "base_codes",
               "applies_to", "position_ids", "months", "actual_source", "sort_order")


def ensure_unique_name(db: Session, model, name: str, exclude_id: int = 0) -> None:
    q = db.query(model.id).filter(model.name == name)
    if exclude_id:
        q = q.filter(model.id != exclude_id)
    if q.first() is not None:
        raise HTTPException(400, f"Tên «{name}» đã được dùng")


def ensure_groups_exist(db: Session, group_ids) -> None:
    ids = {g for g in group_ids if g}
    found = {i for (i,) in db.query(HrCostGroup.id).filter(HrCostGroup.id.in_(ids or {0})).all()}
    if ids - found:
        raise HTTPException(422, "Nhóm chi phí không tồn tại")


def check_group_not_in_use(db: Session, group_id: int) -> None:
    used = (db.query(HrCostTemplateItem.id).filter(HrCostTemplateItem.group_id == group_id).first()
            or db.query(HeadcountPlanCostItem.id).filter(HeadcountPlanCostItem.group_id == group_id).first())
    if used is not None:
        raise HTTPException(400, "Nhóm chi phí đang được mẫu hoặc kế hoạch dùng — hãy ngừng dùng thay vì xóa")


def validate_template_items(db: Session, items: list[CostItemIn]) -> None:
    """Cấu trúc khoản của mẫu kiểm như kế hoạch Năm (đủ 12 tháng): trùng mã, vòng tham chiếu, tháng sai… → 422."""
    ensure_groups_exist(db, [i.group_id for i in items])
    try:
        validate_plan(PlanPeriodType.YEAR, 1, [to_cost_item(i) for i in items], [])
    except PlanCalcError as e:
        raise HTTPException(422, str(e))


def replace_template_items(db: Session, template_id: int, items: list[CostItemIn], actor_id: int) -> None:
    db.query(HrCostTemplateItem).filter(HrCostTemplateItem.template_id == template_id).delete(synchronize_session=False)
    db.add_all(HrCostTemplateItem(template_id=template_id, created_by=actor_id, updated_by=actor_id, **i.model_dump())
               for i in items)


def duplicate_template(db: Session, src: HrCostTemplate, actor_id: int) -> HrCostTemplate:
    base, n = f"{src.name} (bản sao)", 1
    name = base
    while db.query(HrCostTemplate.id).filter(HrCostTemplate.name == name).first() is not None:
        n += 1
        name = f"{base} {n}"
    copy = HrCostTemplate(name=name[:150], note=src.note, is_active=src.is_active, created_by=actor_id, updated_by=actor_id)
    db.add(copy)
    db.flush()
    for it in db.query(HrCostTemplateItem).filter(HrCostTemplateItem.template_id == src.id).all():
        db.add(HrCostTemplateItem(template_id=copy.id, created_by=actor_id, updated_by=actor_id,
                                  **{f: getattr(it, f) for f in ITEM_FIELDS}))
    return copy
