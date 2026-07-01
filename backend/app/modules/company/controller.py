from fastapi import APIRouter, Depends, Query, Request, UploadFile, File
from sqlalchemy.orm import Session

from app.core.auth import require
from app.core.base_controller import apply_filters, pagination
from app.core.database import get_db
from app.core.response import success

from . import service
from .schema import CompanyCreate, CompanyOut, CompanyUpdate

router = APIRouter(prefix="/api/companies", tags=["company"])


@router.get("")
def list_companies(
    request: Request,
    pg: dict = Depends(pagination),
    db: Session = Depends(get_db),
    user=Depends(require("company", "read")),
):
    from sqlalchemy.orm import joinedload
    query = apply_filters(db.query(service.Company), service.Company, request, service.FILTERABLE)
    query = query.options(joinedload(service.Company.legal_rep))
    total, items = service.list_companies(db, query, pg)
    return success({
        "total": total,
        "items": [CompanyOut.model_validate(i).model_dump() for i in items],
    })


@router.get("/{cid}")
def get_company(cid: int, db: Session = Depends(get_db), user=Depends(require("company", "read"))):
    return success(CompanyOut.model_validate(service.get_company(db, cid)).model_dump())


@router.post("")
def create_company(
    data: CompanyCreate, db: Session = Depends(get_db), user=Depends(require("company", "create"))
):
    obj = service.create_company(db, data, user.id)
    return success(CompanyOut.model_validate(obj).model_dump(), "Đã tạo công ty", 201)


@router.patch("/{cid}")
def update_company(
    cid: int, data: CompanyUpdate, db: Session = Depends(get_db),
    user=Depends(require("company", "write")),
):
    obj = service.update_company(db, cid, data, user.id)
    return success(CompanyOut.model_validate(obj).model_dump(), "Đã cập nhật")


@router.delete("/{cid}")
def delete_company(cid: int, db: Session = Depends(get_db), user=Depends(require("company", "delete"))):
    service.delete_company(db, cid, user.id)
    return success(None, "Đã xóa")


@router.delete("")
def bulk_delete_companies(ids: str, db: Session = Depends(get_db), user=Depends(require("company", "delete"))):
    id_list = [int(i.strip()) for i in ids.split(",") if i.strip().isdigit()]
    from fastapi import HTTPException
    if not id_list:
        raise HTTPException(400, "Không có ID hợp lệ")
    from .model import Company
    db.query(Company).filter(Company.id.in_(id_list)).delete(synchronize_session=False)
    db.commit()
    from app.core.audit import record
    for oid in id_list:
        record(db, user.id, "company", oid, "delete")
    return success(None, f"Đã xóa {len(id_list)} bản ghi")

@router.get("/export/csv")
def export_companies_csv(
    ids: str | None = Query(None),
    request: Request = None,
    db: Session = Depends(get_db),
    user=Depends(require("company", "read")),
):
    from app.core.csv_utils import export_csv_response
    from .model import Company
    
    query = apply_filters(db.query(Company), Company, request, service.FILTERABLE)
    if ids:
        id_list = [int(i.strip()) for i in ids.split(",") if i.strip().isdigit()]
        if id_list:
            query = query.filter(Company.id.in_(id_list))
            
    items = query.order_by(Company.id.desc()).all()
    headers_map = {
        "id": "ID",
        "code": "Mã",
        "name": "Tên pháp nhân",
        "export_tax_code": "MST",
        "address": "Địa chỉ",
        "invoice_email": "Email hóa đơn",
        "parent": "Thuộc công ty",
        "legal_rep_name": "Người đại diện",
        "legal_rep_title": "Chức danh",
    }
    return export_csv_response(items, headers_map, "companies")

@router.post("/import/csv")
def import_companies_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(require("company", "write")),
):
    import csv
    from io import StringIO
    from fastapi import HTTPException
    from app.core.utils import generate_code
    from .model import Company
    
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
        
        db_id = row.get("ID", "").strip()
        code = row.get("Mã", "").strip()
        name = (row.get("Tên pháp nhân") or row.get("Tên") or "").strip()
        tax_code = row.get("MST", "").strip()
        if tax_code.startswith("'"):
            tax_code = tax_code[1:]
        address = row.get("Địa chỉ", "").strip()
        invoice_email = row.get("Email hóa đơn", "").strip()
        
        if not db_id and not code and not name:
            continue
            
        existing = None
        if db_id and db_id.isdigit():
            existing = db.query(Company).filter(Company.id == int(db_id)).first()
        if not existing and code:
            existing = db.query(Company).filter(Company.code == code).first()
        if existing:
            if status_str in ["xóa", "delete"]:
                db.delete(existing)
                deleted += 1
            else:
                if name: existing.name = name
                existing.tax_code = tax_code
                existing.address = address
                existing.invoice_email = invoice_email
                existing.is_active = is_active
                existing.updated_by = user.id
                if not is_active: deleted += 1
                else: updated += 1
        else:
            if not is_active or not name: continue
            if not code: code = generate_code(db, Company, "CTY")
            new_obj = Company(
                code=code, name=name, tax_code=tax_code, address=address,
                invoice_email=invoice_email, is_active=is_active,
                created_by=user.id, updated_by=user.id
            )
            db.add(new_obj)
            db.flush()
            created += 1
            
    db.commit()
    return success(None, f"Nhập file thành công. Thêm mới {created}, cập nhật {updated}, ẩn {deleted}.")
