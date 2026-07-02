from fastapi import APIRouter, Depends, Request, Query, UploadFile, File
from sqlalchemy.orm import Session

from app.core.auth import require
from app.core.base_controller import apply_filters, pagination
from app.core.database import get_db
from app.core.response import success

from . import service
from .model import Product
from .schema import ProductCreate, ProductOut, ProductUpdate

router = APIRouter(prefix="/api/products", tags=["product"])


@router.get("")
def list_products(
    request: Request,
    search: str = Query("", description="Tìm theo Mã hoặc Tên (LIKE)"),
    pg: dict = Depends(pagination),
    db: Session = Depends(get_db),
    user=Depends(require("product", "read")),
):
    query = apply_filters(db.query(Product), Product, request, service.FILTERABLE)
    if search.strip():
        from sqlalchemy import or_
        kw = f"%{search.strip()}%"
        query = query.filter(or_(Product.code.like(kw), Product.name.like(kw)))
    total, items = service.list_products(db, query, pg)
    return success({
        "total": total,
        "items": [ProductOut.model_validate(i).model_dump() for i in items],
    })


@router.get("/{pid}")
def get_product(pid: int, db: Session = Depends(get_db), user=Depends(require("product", "read"))):
    return success(ProductOut.model_validate(service.get_product(db, pid)).model_dump())


@router.post("")
def create_product(
    data: ProductCreate, db: Session = Depends(get_db), user=Depends(require("product", "create"))
):
    obj = service.create_product(db, data, user.id)
    return success(ProductOut.model_validate(obj).model_dump(), "Đã tạo sản phẩm", 201)


@router.patch("/{pid}")
def update_product(
    pid: int, data: ProductUpdate, db: Session = Depends(get_db),
    user=Depends(require("product", "write")),
):
    obj = service.update_product(db, pid, data, user.id)
    return success(ProductOut.model_validate(obj).model_dump(), "Đã cập nhật")


@router.delete("/{pid}")
def delete_product(
    pid: int, db: Session = Depends(get_db), user=Depends(require("product", "delete"))
):
    service.delete_product(db, pid, user.id)
    return success(None, "Đã xóa")


@router.delete("")
def bulk_delete_products(ids: str, db: Session = Depends(get_db), user=Depends(require("product", "delete"))):
    id_list = [int(i.strip()) for i in ids.split(",") if i.strip().isdigit()]
    from fastapi import HTTPException
    if not id_list:
        raise HTTPException(400, "Không có ID hợp lệ")
    from .model import Product
    db.query(Product).filter(Product.id.in_(id_list)).delete(synchronize_session=False)
    db.commit()
    from app.core.audit import record
    for oid in id_list:
        record(db, user.id, "product", oid, "delete")
    return success(None, f"Đã xóa {len(id_list)} bản ghi")

@router.get("/export/csv")
def export_products_csv(
    ids: str | None = Query(None),
    request: Request = None,
    db: Session = Depends(get_db),
    user=Depends(require("product", "read")),
):
    from app.core.csv_utils import export_csv_response
    from .model import Product
    
    query = apply_filters(db.query(Product), Product, request, service.FILTERABLE)
    if ids:
        id_list = [int(i.strip()) for i in ids.split(",") if i.strip().isdigit()]
        if id_list:
            query = query.filter(Product.id.in_(id_list))
            
    items = query.order_by(Product.id.desc()).all()
    headers_map = {
        "id": "ID",
        "code": "Mã",
        "name": "Tên",
        "invoice_name": "Tên trên HĐ",
        "legal_name": "Tên pháp lý",
        "item_group": "Phân loại",
        "unit": "ĐVT",
    }
    return export_csv_response(items, headers_map, "products")

@router.post("/import/csv")
def import_products_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(require("product", "write")),
):
    import csv
    from io import StringIO
    from fastapi import HTTPException
    from app.core.utils import generate_code
    from .model import Product
    
    content = file.file.read().decode("utf-8")
    reader = csv.DictReader(StringIO(content))
    if not reader.fieldnames:
        raise HTTPException(400, "File CSV trống")
        
    created, updated, deleted = 0, 0, 0
    for row in reader:
        action = row.get("Hành động", "").strip().lower()
        is_active = action not in ["xóa", "delete", "ngừng"]
        
        db_id = row.get("ID", "").strip()
        code = row.get("Mã", "").strip()
        name = row.get("Tên", "").strip()
        invoice_name = row.get("Tên trên HĐ", "").strip()
        legal_name = row.get("Tên pháp lý", "").strip()
        item_group = row.get("Phân loại", "").strip()
        unit = row.get("ĐVT", "").strip()
        
        if not db_id and not code and not name:
            continue
            
        existing = None
        if db_id and db_id.isdigit():
            existing = db.query(Product).filter(Product.id == int(db_id)).first()
        if not existing and code:
            existing = db.query(Product).filter(Product.code == code).first()
        if existing:
            if action in ["xóa", "delete"]:
                db.delete(existing)
                deleted += 1
            else:
                if name: existing.name = name
                existing.invoice_name = invoice_name
                existing.legal_name = legal_name
                existing.item_group = item_group
                existing.unit = unit
                existing.is_active = is_active
                existing.updated_by = user.id
                if not is_active: deleted += 1
                else: updated += 1
        else:
            if not is_active or not name or not code: continue
            new_obj = Product(
                code=code, name=name, invoice_name=invoice_name,
                legal_name=legal_name,
                item_group=item_group, unit=unit, is_active=is_active,
                created_by=user.id, updated_by=user.id
            )
            db.add(new_obj)
            created += 1
            
    db.commit()
    return success(None, f"Nhập file thành công. Thêm mới {created}, cập nhật {updated}, ẩn {deleted}.")
