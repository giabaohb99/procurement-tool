from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Request
from sqlalchemy.orm import Session

from app.core.auth import require
from app.core.base_controller import pagination
from app.core.database import get_db
from app.core.response import success
from app.core.scoping import get_perm_profile, get_scoped, scope_condition

from . import service
from .schema import (DepartmentCompanyOut, DepartmentCompanyReplace,
                     DepartmentCreate, DepartmentOut, DepartmentUpdate)

router = APIRouter(prefix="/api/departments", tags=["department"])


def _scope_filter(db, user, action: str = "read"):
    from .model import Department
    return scope_condition(Department, "department", user, get_perm_profile(db, user), action)


def _department_in_scope(db, did: int, user, action: str):
    """Phòng ban #did nếu nằm trong phạm vi, không thì 404 — B-07."""
    from .model import Department
    obj = get_scoped(db, Department, "department", did, user, get_perm_profile(db, user), action)
    if not obj:
        from fastapi import HTTPException
        raise HTTPException(404, "Không tìm thấy phòng ban")
    return obj


@router.get("")
def list_departments(
    request: Request,
    q: str | None = Query(None),
    is_active: bool | None = Query(None),
    kind: int | None = Query(None, description="1 phòng chức năng · 2 đơn vị kinh doanh · 3 ban dự án"),
    company_id: int | None = Query(None, description="Phòng ban HIỆN DIỆN ở pháp nhân này"),
    sort_by: str = Query(""),
    sort_dir: str = Query("asc"),
    pg: dict = Depends(pagination),
    db: Session = Depends(get_db),
    user=Depends(require("department", "read")),
):
    # request đi kèm để service gắn BỘ LỌC ĐIỀU KIỆN (`<field>__<op>`), xem core/filter_operators.py
    total, items = service.list_departments(db, q, pg, is_active, sort_by, sort_dir, request,
                                            scope_cond=_scope_filter(db, user),
                                            kind=kind, company_id=company_id)
    # manager_id (chọn cứng) + manager_name (property của model) tự lấy qua model_validate
    res = [DepartmentOut.model_validate(i).model_dump() for i in items]
    return success({
        "total": total,
        "items": res,
    })


@router.get("/by-companies")
def list_by_companies(
    company_ids: str = Query("", description="Danh sách id pháp nhân, ngăn bằng dấu phẩy"),
    db: Session = Depends(get_db),
    user=Depends(require("department", "read")),
):
    """Các CẶP (phòng ban × pháp nhân) của những pháp nhân được hỏi.

    ⚠️ Phải khai TRƯỚC `/{did}`, không thì FastAPI khớp `by-companies` vào tham
    số `did` và trả 422.

    Trả về cặp chứ không phải danh sách phòng ban: một phòng có mặt ở nhiều pháp
    nhân, mà ô chọn phạm vi áp dụng cần đúng cặp (phòng nào ở công ty nào).
    """
    ids = [int(row) for row in company_ids.split(",") if row.strip().isdigit()]
    return success(service.departments_of_companies(db, ids))


@router.get("/{did}")
def get_department(did: int, db: Session = Depends(get_db), user=Depends(require("department", "read"))):
    obj = _department_in_scope(db, did, user, "read")
    return success(DepartmentOut.model_validate(obj).model_dump())


@router.post("")
def create_department(
    data: DepartmentCreate, db: Session = Depends(get_db),
    user=Depends(require("department", "create")),
):
    obj = service.create_department(db, data, user.id)
    return success(DepartmentOut.model_validate(obj).model_dump(), "Đã tạo phòng ban", 201)


@router.patch("/{did}")
def update_department(
    did: int, data: DepartmentUpdate, db: Session = Depends(get_db),
    user=Depends(require("department", "write")),
):
    _department_in_scope(db, did, user, "write")
    obj = service.update_department(db, did, data, user.id)
    return success(DepartmentOut.model_validate(obj).model_dump(), "Đã cập nhật")


@router.delete("/{did}")
def delete_department(
    did: int, db: Session = Depends(get_db), user=Depends(require("department", "delete"))
):
    _department_in_scope(db, did, user, "delete")
    service.delete_department(db, did, user.id)
    return success(None, "Đã xóa")


@router.get("/{did}/companies")
def list_department_companies(
    did: int,
    db: Session = Depends(get_db),
    user=Depends(require("department", "read")),
):
    _department_in_scope(db, did, user, "read")
    rows = service.list_department_companies(db, did)
    return success([DepartmentCompanyOut.model_validate(row).model_dump() for row in rows])


@router.put("/{did}/companies")
def replace_department_companies(
    did: int,
    data: DepartmentCompanyReplace,
    db: Session = Depends(get_db),
    user=Depends(require("department", "write")),
):
    _department_in_scope(db, did, user, "write")
    rows = service.replace_department_companies(db, did, data.items, user.id)
    return success(
        [DepartmentCompanyOut.model_validate(row).model_dump() for row in rows],
        "Đã cập nhật pháp nhân áp dụng",
    )

@router.get("/export/csv")
def export_departments_csv(
    ids: str | None = Query(None),
    q: str | None = Query(None),
    db: Session = Depends(get_db),
    user=Depends(require("department", "export")),   # duoc-CR-660: trước đây `read`
):
    from app.core.csv_utils import export_csv_response
    from .model import Department
    
    query = db.query(Department)
    cond = _scope_filter(db, user, "export")   # xuất file phải cùng phạm vi với danh sách
    if cond is not None:
        query = query.filter(cond)
    if q:
        query = query.filter(Department.name.like(f"%{q}%"))
    if ids:
        id_list = [int(i.strip()) for i in ids.split(",") if i.strip().isdigit()]
        if id_list:
            query = query.filter(Department.id.in_(id_list))
            
    items = query.order_by(Department.id.desc()).all()
    headers_map = {
        "code": "Mã PB",
        "name": "Tên phòng ban",
        "company_id": "Mã công ty",
        "parent": "Mã PB cha",
    }
    return export_csv_response(items, headers_map, "departments")

@router.post("/import/csv")
def import_departments_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(require("department", "import")),
):
    """duoc-CR-628: Nhập CSV phòng ban đã NGỪNG (ghi thẳng cột, xóa hàng loạt, không chạy thử).
    Thay bằng "Quản trị → Quản lý Import → Phòng ban" (Excel, có chạy thử + hoàn tác)."""
    raise HTTPException(
        410, "Nhập CSV phòng ban đã ngừng. Dùng \"Quản trị → Quản lý Import → Phòng ban\" "
             "(Excel, có chạy thử và hoàn tác).")
