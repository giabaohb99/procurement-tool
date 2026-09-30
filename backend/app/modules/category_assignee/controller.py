from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import BigInteger, func, type_coerce
from sqlalchemy.orm import Session, aliased

from app.core.auth import require
from app.core.base_controller import pagination
from app.core.central_purchasing import get_central_dept_id
from app.core.filter_operators import apply_operator_filters_map
from app.core.database import get_db
from app.core.response import success

from . import service
from .model import CategoryAssignee
from .schema import CategoryAssigneeBulk, CategoryAssigneeCreate, CategoryAssigneeOut, CategoryAssigneeUpdate

router = APIRouter(prefix="/api/category-assignees", tags=["category_assignee"])


def _effective_dept_expr(db: Session):
    """Phòng áp dụng THẬT của dòng phân công — bao-CR-524: dòng `0` cũ («Thu mua chung», chưa
    chạy backfill) đọc là phòng thu mua mặc định. Dùng cho cả JOIN lấy tên, sắp xếp lẫn ô lọc,
    để dòng cũ và dòng mới của cùng phòng đi chung một nhóm."""
    return type_coerce(func.coalesce(func.nullif(CategoryAssignee.department_id, 0),
                                     get_central_dept_id(db)), BigInteger)


def _primary_flags(emp) -> dict:
    """Tình trạng HIỆN TẠI của NSTM chính để màn danh sách gắn cảnh báo — bao-CR-527."""
    if not emp:
        return {"primary_status": None, "primary_status_label": None, "primary_is_active": None,
                "primary_not_official": True}
    return {"primary_status": emp.status or "", "primary_status_label": emp.status_label or "",
            "primary_is_active": bool(emp.is_active),
            "primary_not_official": not service.is_official_employee(emp)}


def _out(db: Session, obj) -> dict:
    from app.modules.catalog.model import ItemGroup
    from app.modules.department.model import Department
    from app.modules.employee.model import Employee
    d = CategoryAssigneeOut.model_validate(obj).model_dump()
    g = db.get(ItemGroup, obj.item_group_id) if obj.item_group_id else None
    p = db.get(Employee, obj.primary_employee_id) if obj.primary_employee_id else None
    b = db.get(Employee, obj.backup_employee_id) if obj.backup_employee_id else None
    # bao-CR-524: dòng `0` cũ trả về đúng phòng thu mua mặc định (id + tên thật) — màn hình không
    # còn mục «Thu mua chung» để hiện số 0.
    dept_id = int(obj.department_id or 0) or get_central_dept_id(db)
    dept = db.get(Department, dept_id) if dept_id else None
    d["department_id"] = dept_id
    d["item_group_name"] = g.name if g else None
    d["primary_name"] = p.full_name if p else None
    d["primary_code"] = p.code if p else None
    d["backup_name"] = b.full_name if b else None
    d["backup_code"] = b.code if b else None
    d["department_name"] = dept.name if dept else None
    d.update(_primary_flags(p))
    return d


# bao-CR-414: lọc thêm theo phòng. bao-CR-524: `department_id` lọc theo phòng THẬT (dòng `0` cũ
# tính là phòng thu mua mặc định), xem `_effective_dept_expr`.
FILTERABLE = ["item_group_id", "primary_employee_id", "backup_employee_id", "department_id"]


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
    from app.modules.department.model import Department
    from app.modules.employee.model import Employee

    Pr = aliased(Employee)   # NSTM chính
    Bk = aliased(Employee)   # NSTM dự phòng
    dept_expr = _effective_dept_expr(db)
    q = (
        db.query(
            CategoryAssignee,
            ItemGroup.name.label("item_group_name"),
            Pr,
            Bk.full_name.label("backup_name"), Bk.code.label("backup_code"),
            dept_expr.label("effective_department_id"),
            Department.name.label("department_name"),
        )
        .outerjoin(ItemGroup, ItemGroup.id == CategoryAssignee.item_group_id)
        .outerjoin(Pr, Pr.id == CategoryAssignee.primary_employee_id)
        .outerjoin(Bk, Bk.id == CategoryAssignee.backup_employee_id)
        .outerjoin(Department, Department.id == dept_expr)
    )
    # Bộ lọc điều kiện theo phân loại / NSTM chính / NSTM dự phòng / phòng (xem core/filter_operators.py)
    colmap = {f: getattr(CategoryAssignee, f) for f in FILTERABLE}
    colmap["department_id"] = dept_expr
    q = apply_operator_filters_map(q, colmap, request)

    sort_map = {
        "id": CategoryAssignee.id,
        "item_group_name": ItemGroup.name,
        "primary_name": Pr.full_name,
        "backup_name": Bk.full_name,
        "department_name": Department.name,
    }
    col = sort_map.get(sort, ItemGroup.name)
    if sort == "department_name":
        # bao-CR-524: phòng thu mua mặc định là phòng thật — xếp theo tên cùng các phòng khác.
        q = q.order_by(col.desc() if order == "desc" else col.asc(), ItemGroup.name.asc())
    else:
        q = q.order_by(col.desc() if order == "desc" else col.asc(), dept_expr.asc())

    total = q.count()
    rows = q.offset(pg["offset"]).limit(pg["limit"]).all()

    items = []
    for obj, ig_name, primary, b_name, b_code, dept_id, dept_name in rows:
        d = CategoryAssigneeOut.model_validate(obj).model_dump()
        d["department_id"] = int(dept_id or 0)
        d["item_group_name"] = ig_name
        d["primary_name"] = primary.full_name if primary else None
        d["primary_code"] = primary.code if primary else None
        d["backup_name"] = b_name
        d["backup_code"] = b_code
        d["department_name"] = dept_name
        d.update(_primary_flags(primary))   # bao-CR-527: cờ cảnh báo NSTM chính
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
    n = service.bulk_upsert(db, data.item_group_ids, data.primary_employee_id, data.backup_employee_id,
                            user.id, department_id=data.department_id)
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
