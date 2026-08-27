from fastapi import APIRouter, Depends, Query, UploadFile, File, Request
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
    user=Depends(require("department", "read")),
):
    from app.core.csv_utils import export_csv_response
    from .model import Department
    
    query = db.query(Department)
    cond = _scope_filter(db, user)   # xuất file phải cùng phạm vi với danh sách
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
    user=Depends(require("department", "write")),
):
    import csv
    from io import StringIO
    from fastapi import HTTPException
    from app.core.utils import generate_code
    from .model import Department
    
    try:
        content = file.file.read().decode("utf-8-sig").replace("\r\n", "\n")
        if content.lower().startswith("sep="):
            content = content.split("\n", 1)[-1]
    except UnicodeDecodeError:
        raise HTTPException(400, "Lỗi định dạng file. Vui lòng lưu file CSV với encoding UTF-8.")
        
    reader = csv.DictReader(StringIO(content))
    if not reader.fieldnames:
        raise HTTPException(400, "File CSV trống")
        
    # Nhập file sửa/xóa được bản ghi bằng mã → phải chịu đúng phạm vi như nút sửa.
    scope_cond = _scope_filter(db, user, "write")
    created, updated, deleted, skipped = 0, 0, 0, 0
    for row in reader:
        status_str = (row.get("Trạng thái") or row.get("Hành động") or "").strip().lower()
        is_active = status_str not in ["xóa", "delete", "ngừng", "đã ẩn", "ẩn", "false"]
        
        code = (row.get("Mã PB") or row.get("ID") or "").strip()
        name = (row.get("Tên phòng ban") or row.get("Tên") or "").strip()
        
        company_id_str = (row.get("Mã công ty") or "0").strip()
        parent_str = (row.get("Mã PB cha") or "0").strip()
        company_id = int(company_id_str) if company_id_str.isdigit() else 0
        parent = int(parent_str) if parent_str.isdigit() else 0
        
        if not code and not name:
            continue
            
        existing = db.query(Department).filter(Department.code == code).first() if code else None
        if existing is not None and scope_cond is not None:
            if db.query(Department.id).filter(Department.id == existing.id,
                                              scope_cond).first() is None:
                skipped += 1
                continue
        if existing:
            if status_str in ["xóa", "delete"]:
                db.delete(existing)
                deleted += 1
            else:
                if name: existing.name = name
                existing.company_id = company_id
                existing.parent = parent
                existing.is_active = is_active
                existing.updated_by = user.id
                if not is_active: deleted += 1
                else: updated += 1
        else:
            if not is_active or not name: continue
            if not code: code = generate_code(db, Department, "PBA")
            new_obj = Department(
                code=code, name=name, company_id=company_id, parent=parent,
                is_active=is_active,
                created_by=user.id, updated_by=user.id
            )
            db.add(new_obj)
            db.flush()
            created += 1
            
    db.commit()
    msg = f"Nhập file thành công. Thêm mới {created}, cập nhật {updated}, ẩn {deleted}."
    if skipped:
        msg += f" Bỏ qua {skipped} dòng ngoài phạm vi của bạn."
    return success(None, msg)
