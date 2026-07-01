from fastapi import APIRouter, Depends, Query, UploadFile, File, Request
from sqlalchemy.orm import Session

from app.core.auth import require
from app.core.base_controller import pagination
from app.core.database import get_db
from app.core.response import success

from . import service
from .schema import DepartmentCreate, DepartmentOut, DepartmentUpdate

router = APIRouter(prefix="/api/departments", tags=["department"])


@router.get("")
def list_departments(
    q: str | None = Query(None),
    pg: dict = Depends(pagination),
    db: Session = Depends(get_db),
    user=Depends(require("department", "read")),
):
    total, items = service.list_departments(db, q, pg)
    
    # Auto-resolve managers
    from app.modules.employee.model import Employee
    managers = db.query(Employee).filter(
        Employee.role_name.in_(["Trưởng bộ phận", "Administrator", "ADMIN", "MANAGER", "ADMINISTRATOR"]),
        Employee.is_active == True
    ).all()
    manager_map = {m.department_id: m for m in managers if m.department_id}

    res = []
    for i in items:
        out = DepartmentOut.model_validate(i).model_dump()
        mgr = manager_map.get(i.id)
        if mgr:
            out["manager_id"] = mgr.id
            out["manager_name"] = mgr.full_name
        res.append(out)

    return success({
        "total": total,
        "items": res,
    })


@router.get("/{did}")
def get_department(did: int, db: Session = Depends(get_db), user=Depends(require("department", "read"))):
    obj = service.get_department(db, did)
    out = DepartmentOut.model_validate(obj).model_dump()
    
    from app.modules.employee.model import Employee
    mgr = db.query(Employee).filter(
        Employee.department_id == did,
        Employee.role_name.in_(["Trưởng bộ phận", "Administrator", "ADMIN", "MANAGER", "ADMINISTRATOR"]),
        Employee.is_active == True
    ).first()
    if mgr:
        out["manager_id"] = mgr.id
        out["manager_name"] = mgr.full_name

    return success(out)


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
    obj = service.update_department(db, did, data, user.id)
    return success(DepartmentOut.model_validate(obj).model_dump(), "Đã cập nhật")


@router.delete("/{did}")
def delete_department(
    did: int, db: Session = Depends(get_db), user=Depends(require("department", "delete"))
):
    service.delete_department(db, did, user.id)
    return success(None, "Đã xóa")

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
        
    created, updated, deleted = 0, 0, 0
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
    return success(None, f"Nhập file thành công. Thêm mới {created}, cập nhật {updated}, ẩn {deleted}.")
