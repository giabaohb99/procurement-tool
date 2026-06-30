from fastapi import APIRouter, Depends, Request, UploadFile, File
from sqlalchemy.orm import Session

from app.core.auth import require
from app.core.base_controller import apply_filters, pagination
from app.core.database import get_db
from app.core.response import success

from . import service
from .model import Supplier
from .schema import SupplierCreate, SupplierOut, SupplierUpdate

router = APIRouter(prefix="/api/suppliers", tags=["supplier"])


@router.get("")
def list_suppliers(
    request: Request,
    pg: dict = Depends(pagination),
    db: Session = Depends(get_db),
    user=Depends(require("supplier", "read")),
):
    query = apply_filters(db.query(Supplier), Supplier, request, service.FILTERABLE)
    total, items = service.list_suppliers(db, query, pg)
    return success({
        "total": total,
        "items": [SupplierOut.model_validate(i).model_dump() for i in items],
    })


@router.get("/{sid}")
def get_supplier(sid: int, db: Session = Depends(get_db), user=Depends(require("supplier", "read"))):
    return success(SupplierOut.model_validate(service.get_supplier(db, sid)).model_dump())


@router.post("")
def create_supplier(
    data: SupplierCreate, db: Session = Depends(get_db),
    user=Depends(require("supplier", "create")),
):
    obj = service.create_supplier(db, data, user.id)
    return success(SupplierOut.model_validate(obj).model_dump(), "Đã tạo NCC", 201)


@router.patch("/{sid}")
def update_supplier(
    sid: int, data: SupplierUpdate, db: Session = Depends(get_db),
    user=Depends(require("supplier", "write")),
):
    obj = service.update_supplier(db, sid, data, user.id)
    return success(SupplierOut.model_validate(obj).model_dump(), "Đã cập nhật")


@router.delete("/{sid}")
def delete_supplier(
    sid: int, db: Session = Depends(get_db), user=Depends(require("supplier", "delete"))
):
    service.delete_supplier(db, sid, user.id)
    return success(None, "Đã xóa")


@router.get("/export/csv")
def export_suppliers_csv(
    ids: str | None = None,
    request: Request = None,
    db: Session = Depends(get_db),
    user=Depends(require("supplier", "read")),
):
    from app.core.csv_utils import export_csv_response

    query = apply_filters(db.query(Supplier), Supplier, request, service.FILTERABLE)
    if ids:
        id_list = [int(i.strip()) for i in ids.split(",") if i.strip().isdigit()]
        if id_list:
            query = query.filter(Supplier.id.in_(id_list))
    items = query.order_by(Supplier.id.desc()).all()

    headers_map = {
        "code": "ID",
        "name": "Tên pháp lý",
        "tax_code": "MST",
        "address": "Địa chỉ",
        "supplier_type": "Loại",
        "payment_terms": "Hình thức thanh toán",
        "vat": "VAT"
    }
    return export_csv_response(items, headers_map, "suppliers")


@router.post("/import/csv")
def import_suppliers_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(require("supplier", "write")),
):
    import csv
    from io import StringIO
    from fastapi import HTTPException

    from app.core.utils import generate_code

    content = file.file.read().decode("utf-8")
    reader = csv.DictReader(StringIO(content))

    if not reader.fieldnames or "Tên pháp lý" not in reader.fieldnames:
        raise HTTPException(400, "File CSV không đúng định dạng. Cần có cột 'Tên pháp lý'.")

    created = 0
    updated = 0
    deleted = 0

    for row in reader:
        action = row.get("Hành động", "").strip().lower()
        is_active = action not in ["xóa", "delete", "ngừng"]

        code = row.get("ID", "").strip()
        name = row.get("Tên pháp lý", "").strip()
        if not code or not name:
            continue
        
        tax_code = row.get("MST", "").strip()
        address = row.get("Địa chỉ", "").strip()
        supplier_type = row.get("Loại", "").strip()
        if supplier_type not in ["goods", "transport"]:
            supplier_type = "goods"
        payment_terms = row.get("Hình thức thanh toán", "").strip()
        
        try:
            vat = float(row.get("VAT", 0.08))
        except ValueError:
            vat = 0.08

        existing = db.query(Supplier).filter(Supplier.code == code).first()
        if existing:
            existing.name = name
            existing.tax_code = tax_code
            existing.address = address
            existing.supplier_type = supplier_type
            existing.payment_terms = payment_terms
            existing.vat = vat
            existing.is_active = is_active
            existing.updated_by = user.id
            if not is_active: deleted += 1
            else: updated += 1
        else:
            if not is_active or not name: continue
            if not code: code = generate_code(db, Supplier, "NCC")
            new_sup = Supplier(
                code=code, name=name, tax_code=tax_code, address=address,
                supplier_type=supplier_type, payment_terms=payment_terms,
                vat=vat, is_active=is_active, created_by=user.id, updated_by=user.id
            )
            db.add(new_sup)
            created += 1

    db.commit()
    return success(None, f"Nhập file thành công. Thêm mới {created}, cập nhật {updated}, ẩn {deleted}.")
