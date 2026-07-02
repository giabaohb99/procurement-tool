from fastapi import APIRouter, Depends, Query, Request, UploadFile, File
from sqlalchemy.orm import Session

from app.core.auth import get_perm_profile, require
from app.core.base_controller import apply_filters, pagination
from app.core.database import get_db
from app.core.response import success
from app.core.scoping import apply_scope

from . import service
from .schema import EmployeeCreate, EmployeeOut, EmployeeUpdate

router = APIRouter(prefix="/api/employees", tags=["employee"])


@router.get("")
def list_employees(
    request: Request,
    pg: dict = Depends(pagination),
    db: Session = Depends(get_db),
    user=Depends(require("employee", "read")),
):
    query = apply_filters(db.query(service.Employee), service.Employee, request, service.FILTERABLE)
    query = apply_scope(query, service.Employee, "employee", user, get_perm_profile(db, user))
    total, items = service.list_employees(db, query, pg)
    return success({
        "total": total,
        "items": [EmployeeOut.model_validate(i).model_dump() for i in items],
    })


@router.get("/{eid}")
def get_employee(eid: int, db: Session = Depends(get_db), user=Depends(require("employee", "read"))):
    return success(EmployeeOut.model_validate(service.get_employee(db, eid)).model_dump())


@router.post("")
def create_employee(
    data: EmployeeCreate, db: Session = Depends(get_db),
    user=Depends(require("employee", "create")),
):
    obj = service.create_employee(db, data, user.id)
    return success(EmployeeOut.model_validate(obj).model_dump(), "Đã tạo nhân viên", 201)


@router.patch("/{eid}")
def update_employee(
    eid: int, data: EmployeeUpdate, db: Session = Depends(get_db),
    user=Depends(require("employee", "write")),
):
    obj = service.update_employee(db, eid, data, user.id)
    return success(EmployeeOut.model_validate(obj).model_dump(), "Đã cập nhật")


@router.delete("/{eid}")
def delete_employee(
    eid: int, db: Session = Depends(get_db), user=Depends(require("employee", "delete"))
):
    service.delete_employee(db, eid, user.id)
    return success(None, "Đã xóa")

@router.get("/export/csv")
def export_employees_csv(
    ids: str | None = Query(None),
    request: Request = None,
    db: Session = Depends(get_db),
    user=Depends(require("employee", "read")),
):
    from app.core.csv_utils import export_csv_response
    from .model import Employee
    
    query = apply_filters(db.query(Employee), Employee, request, service.FILTERABLE)
    if ids:
        id_list = [int(i.strip()) for i in ids.split(",") if i.strip().isdigit()]
        if id_list:
            query = query.filter(Employee.id.in_(id_list))
            
    items = query.order_by(Employee.id.desc()).all()
    headers_map = {
        "code": "Mã NV",
        "full_name": "Họ tên",
        "email": "Email",
        "phone": "Số điện thoại",
        "department_name": "Phòng ban",
        "role_name": "Vai trò",
        "status": "Trạng thái NS",
    }
    return export_csv_response(items, headers_map, "employees")

@router.post("/import/csv")
def import_employees_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(require("employee", "write")),
):
    import csv
    from io import StringIO
    from fastapi import HTTPException
    from app.core.utils import generate_code
    from .model import Employee
    
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
        action = (row.get("Hành động") or "").strip().lower()
        is_active = action not in ["xóa", "delete", "ngừng"]
        
        code = (row.get("Mã NV") or row.get("ID") or "").strip()
        full_name = (row.get("Họ tên") or "").strip()
        email = (row.get("Email") or "").strip()
        phone = (row.get("Số điện thoại") or row.get("SĐT") or "").strip()
        department_name = (row.get("Phòng ban") or "").strip()
        role_name = (row.get("Vai trò") or "").strip()
        status = (row.get("Trạng thái NS") or row.get("Trạng thái") or "Chính thức").strip()
        
        if not code and not full_name:
            continue
            
        # Try mapping department_name to department_id
        department_id = 0
        if department_name:
            from .model import Employee
            from app.modules.department.model import Department
            dept = db.query(Department).filter(Department.name.like(f"%{department_name}%")).first()
            if dept:
                department_id = dept.id

        existing = db.query(Employee).filter(Employee.code == code).first() if code else None
        if existing:
            if action in ["xóa", "delete"]:
                db.delete(existing)
                deleted += 1
            else:
                if full_name: existing.full_name = full_name
                existing.email = email
                existing.phone = phone
                if department_id: existing.department_id = department_id
                existing.role_name = role_name
                existing.status = status
                existing.is_active = is_active
                existing.updated_by = user.id
                if not is_active: deleted += 1
                else: updated += 1
        else:
            if not is_active or not full_name: continue
            if not code: code = generate_code(db, Employee, "NSU")
            new_obj = Employee(
                code=code, full_name=full_name, email=email, phone=phone,
                department_id=department_id, role_name=role_name, status=status,
                is_active=is_active, created_by=user.id, updated_by=user.id
            )
            db.add(new_obj)
            db.flush()
            created += 1
            
    db.commit()
    return success(None, f"Nhập file thành công. Thêm mới {created}, cập nhật {updated}, ẩn {deleted}.")
