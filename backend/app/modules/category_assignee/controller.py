from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session, aliased

from app.core.auth import require
from app.core.base_controller import pagination
from app.core.filter_operators import apply_operator_filters
from app.core.database import get_db
from app.core.response import success

from . import service
from .model import CategoryAssignee
from .schema import CategoryAssigneeBulk, CategoryAssigneeCreate, CategoryAssigneeOut, CategoryAssigneeUpdate

router = APIRouter(prefix="/api/category-assignees", tags=["category_assignee"])


def _out(db: Session, obj) -> dict:
    from app.modules.catalog.model import ItemGroup
    from app.modules.employee.model import Employee
    d = CategoryAssigneeOut.model_validate(obj).model_dump()
    g = db.get(ItemGroup, obj.item_group_id) if obj.item_group_id else None
    p = db.get(Employee, obj.primary_employee_id) if obj.primary_employee_id else None
    b = db.get(Employee, obj.backup_employee_id) if obj.backup_employee_id else None
    d["item_group_name"] = g.name if g else None
    d["primary_name"] = p.full_name if p else None
    d["primary_code"] = p.code if p else None
    d["backup_name"] = b.full_name if b else None
    d["backup_code"] = b.code if b else None
    return d


FILTERABLE = ["item_group_id", "primary_employee_id", "backup_employee_id"]


@router.get("")
def list_(
    request: Request,
    sort: str = Query("item_group_name"),
    order: str = Query("asc"),
    sort_by: str = Query(""),
    sort_dir: str = Query(""),
    pg: dict = Depends(pagination),
    db: Session = Depends(get_db),
    user=Depends(require("category_assignee", "read")),
):
    """Danh sách phân công NSTM — 1 query JOIN (hết N+1), phân trang + sort tại DB."""
    # CrudList gửi sort_by/sort_dir; giữ tương thích tham số cũ sort/order
    if sort_by:
        sort = sort_by
    if sort_dir:
        order = sort_dir
    from app.modules.catalog.model import ItemGroup
    from app.modules.employee.model import Employee

    Pr = aliased(Employee)   # NSTM chính
    Bk = aliased(Employee)   # NSTM dự phòng
    q = (
        db.query(
            CategoryAssignee,
            ItemGroup.name.label("item_group_name"),
            Pr.full_name.label("primary_name"), Pr.code.label("primary_code"),
            Bk.full_name.label("backup_name"), Bk.code.label("backup_code"),
        )
        .outerjoin(ItemGroup, ItemGroup.id == CategoryAssignee.item_group_id)
        .outerjoin(Pr, Pr.id == CategoryAssignee.primary_employee_id)
        .outerjoin(Bk, Bk.id == CategoryAssignee.backup_employee_id)
    )
    # Bộ lọc điều kiện theo phân loại / NSTM chính / NSTM dự phòng (xem core/filter_operators.py)
    q = apply_operator_filters(q, CategoryAssignee, request, FILTERABLE)

    sort_map = {
        "id": CategoryAssignee.id,
        "item_group_name": ItemGroup.name,
        "primary_name": Pr.full_name,
        "backup_name": Bk.full_name,
    }
    col = sort_map.get(sort, ItemGroup.name)
    q = q.order_by(col.desc() if order == "desc" else col.asc())

    total = q.count()
    rows = q.offset(pg["offset"]).limit(pg["limit"]).all()

    items = []
    for obj, ig_name, p_name, p_code, b_name, b_code in rows:
        d = CategoryAssigneeOut.model_validate(obj).model_dump()
        d["item_group_name"] = ig_name
        d["primary_name"] = p_name
        d["primary_code"] = p_code
        d["backup_name"] = b_name
        d["backup_code"] = b_code
        items.append(d)
    return success({"total": total, "items": items})


@router.get("/{cid}")
def get_(cid: int, db: Session = Depends(get_db), user=Depends(require("category_assignee", "read"))):
    return success(_out(db, service.get(db, cid)))


@router.post("")
def create_(data: CategoryAssigneeCreate, db: Session = Depends(get_db),
            user=Depends(require("category_assignee", "create"))):
    return success(_out(db, service.create(db, data, user.id)), "Đã tạo phân công", 201)


@router.post("/bulk")
def bulk_(data: CategoryAssigneeBulk, db: Session = Depends(get_db),
          user=Depends(require("category_assignee", "create"))):
    n = service.bulk_upsert(db, data.item_group_ids, data.primary_employee_id, data.backup_employee_id, user.id)
    return success({"count": n}, f"Đã gán cho {n} phân loại")


@router.patch("/{cid}")
def update_(cid: int, data: CategoryAssigneeUpdate, db: Session = Depends(get_db),
            user=Depends(require("category_assignee", "write"))):
    return success(_out(db, service.update(db, cid, data, user.id)), "Đã cập nhật")


@router.delete("/{cid}")
def delete_(cid: int, db: Session = Depends(get_db),
            user=Depends(require("category_assignee", "delete"))):
    service.delete(db, cid, user.id)
    return success(None, "Đã xóa")
