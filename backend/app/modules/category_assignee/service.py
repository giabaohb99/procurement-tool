from fastapi import HTTPException
from sqlalchemy.orm import Session

from .model import CategoryAssignee
from .schema import CategoryAssigneeCreate, CategoryAssigneeUpdate


def list_all(db: Session):
    return db.query(CategoryAssignee).order_by(CategoryAssignee.id.desc()).all()


def get(db: Session, cid: int) -> CategoryAssignee:
    obj = db.get(CategoryAssignee, cid)
    if not obj:
        raise HTTPException(404, "Không tìm thấy phân công")
    return obj


def create(db: Session, data: CategoryAssigneeCreate, user_id: int) -> CategoryAssignee:
    if db.query(CategoryAssignee).filter(CategoryAssignee.item_group_id == data.item_group_id).first():
        raise HTTPException(400, "Phân loại này đã được cấu hình phụ trách")
    obj = CategoryAssignee(**data.model_dump(), created_by=user_id, updated_by=user_id)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update(db: Session, cid: int, data: CategoryAssigneeUpdate, user_id: int) -> CategoryAssignee:
    obj = get(db, cid)
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    obj.updated_by = user_id
    db.commit()
    db.refresh(obj)
    return obj


def delete(db: Session, cid: int, user_id: int) -> None:
    db.delete(get(db, cid))
    db.commit()


def auto_assign_by_category(db: Session, pr) -> int:
    """Sau khi TRƯỞNG PHÒNG duyệt PYC: điền `assignee` (mã NV) cho các dòng CHƯA có người,
    theo phân loại của dòng. Ưu tiên người CHÍNH; người chính nghỉ (is_active=false) → DỰ PHÒNG.
    Tôn trọng gán tay: dòng đã có assignee thì bỏ qua. Trả số dòng được gán."""
    from app.modules.catalog.model import ItemGroup
    from app.modules.employee.model import Employee
    from app.modules.purchase_request.model import PurchaseRequestItem

    lines = db.query(PurchaseRequestItem).filter(PurchaseRequestItem.pr_id == pr.id).all()
    if not lines:
        return 0
    configs = {c.item_group_id: c for c in db.query(CategoryAssignee).all()}
    if not configs:
        return 0
    group_id_by_name = {g.name: g.id for g in db.query(ItemGroup).all()}
    emp_cache: dict = {}

    def emp(eid):
        if not eid:
            return None
        if eid not in emp_cache:
            emp_cache[eid] = db.get(Employee, eid)
        return emp_cache[eid]

    assigned = 0
    for ln in lines:
        if ln.assignee:                      # đã có (gán tay) → giữ nguyên
            continue
        gid = group_id_by_name.get(ln.item_group or "")
        cfg = configs.get(gid) if gid else None
        if not cfg:
            continue
        primary = emp(cfg.primary_employee_id)
        chosen = primary if (primary and primary.is_active) else emp(cfg.backup_employee_id)
        if chosen and chosen.code:
            ln.assignee = chosen.code
            assigned += 1
    if assigned:
        db.commit()
    return assigned
