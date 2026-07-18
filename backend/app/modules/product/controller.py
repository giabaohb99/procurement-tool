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
        query = query.filter(or_(Product.code.like(kw), Product.name.like(kw),
                                 Product.hh_code.like(kw), Product.hh_name.like(kw)))
    total, items = service.list_products(db, query, pg)
    rows = [ProductOut.model_validate(i).model_dump() for i in items]
    # Gắn thumbnail_url = ảnh sort_order nhỏ nhất mỗi SP (batch 1 query/trang, không N+1)
    from app.modules.attachment.model import FileLink, StoredFile
    ids = [r["id"] for r in rows]
    thumb: dict[int, str] = {}
    if ids:
        q = (db.query(FileLink.entity_id, StoredFile.url)
             .join(StoredFile, StoredFile.id == FileLink.file_id)
             .filter(FileLink.entity == "product", FileLink.entity_id.in_(ids))
             .order_by(FileLink.entity_id, FileLink.sort_order.asc(), FileLink.id.desc()))
        for eid, url in q:
            thumb.setdefault(eid, url)   # dòng đầu mỗi SP = ảnh sort_order nhỏ nhất
    for r in rows:
        r["thumbnail_url"] = thumb.get(r["id"], "")
    return success({"total": total, "items": rows})


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
        "item_group": "Phân Loại",
        "code": "Mã VTBB/NL",
        "name": "Tên VTBB/NL",
        "invoice_name": "Tên Trên Hóa Đơn VTBB/NL",
        "legal_name": "Tên pháp lý",
        "unit": "ĐVT",
        "hh_code": "Mã HH",
        "hh_name": "Tên Sản phẩm (HH)",
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
    from .model import Product

    content = file.file.read().decode("utf-8-sig")   # bỏ BOM nếu có
    lines = content.splitlines()
    # Bỏ qua dòng tiêu đề/ghi chú phía trên của sheet — tìm đúng DÒNG HEADER
    hdr_idx = 0
    for i, ln in enumerate(lines):
        low = ln.lower()
        if ("mã vtbb" in low) or ("mã hh" in low) or ("phân loại" in low) or ln.strip().startswith("Mã") or (",Mã," in ln):
            hdr_idx = i
            break
    reader = csv.DictReader(StringIO("\n".join(lines[hdr_idx:])))
    if not reader.fieldnames:
        raise HTTPException(400, "File CSV trống hoặc không tìm thấy dòng tiêu đề")

    def clean(v):
        s = (v or "").strip()
        return "" if s.upper() in ("#N/A", "N/A", "NA", "-", "NULL") else s

    # Chuẩn hóa Phân loại: bỏ ngoặc vuông + gộp hoa/thường về 1 nhóm chuẩn
    import re
    _GROUP_CANON = {
        "thùng": "Thùng", "hộp": "Hộp", "chai": "Chai", "nắp": "Nắp", "túi": "Túi",
        "xô": "Xô", "can": "Can", "bao": "Bao", "cóc": "Cóc", "lon": "Lon",
        "seal": "Seal", "băng keo": "Băng keo", "tem": "Tem", "nhãn": "Nhãn",
        "nhãn thùng": "Nhãn thùng", "nhãn phụ": "Nhãn phụ",
        "nl": "NL", "nguyên liệu": "NL", "vt": "VT", "ndt": "NDT", "icare": "ICARE",
    }

    def norm_group(v):
        s = clean(v)
        if s.startswith("[") and s.endswith("]"):
            s = s[1:-1].strip()           # bỏ ngoặc vuông [Nhãn] -> Nhãn
        s = re.sub(r"\s+", " ", s).strip()
        return _GROUP_CANON.get(s.lower(), s)  # gộp biến thể hoa/thường; acronym (NL, VT...) giữ nguyên

    def pick(row, *keys):
        for k in keys:                       # khớp header chính xác trước
            if k in row and clean(row[k]):
                return clean(row[k])
        return ""

    def pick_has(row, *frags):
        for k, v in row.items():             # fallback: header CHỨA các từ khóa
            kl = (k or "").lower()
            if all(f in kl for f in frags) and clean(v):
                return clean(v)
        return ""

    # Nạp sẵn toàn bộ mã hiện có -> tránh query từng dòng (nhanh) + gộp mã trùng trong file
    by_code = {p.code: p for p in db.query(Product).all()}
    by_id = {p.id: p for p in by_code.values()}

    created = updated = deleted = skipped = 0
    seen = set()                              # mã đã xử lý trong lần chạy này (chống đếm trùng)
    for raw in reader:
        row = {(k or "").strip(): v for k, v in raw.items()}
        action = clean(row.get("Hành động", "")).lower()
        is_active = action not in ["xóa", "delete", "ngừng", "ẩn"]

        db_id = pick(row, "ID")
        code = pick(row, "Mã VTBB/NL", "Mã VTBB", "Mã") or pick_has(row, "mã", "vtbb")
        name = pick(row, "Tên VTBB/NL", "Tên") or pick_has(row, "tên", "vtbb")
        invoice_name = pick(row, "Tên Trên Hóa Đơn VTBB/NL", "Tên trên HĐ") or pick_has(row, "hóa đơn")
        legal_name = pick(row, "Tên pháp lý") or pick_has(row, "pháp lý")
        item_group = norm_group(pick(row, "Phân Loại", "Phân loại"))
        unit = pick(row, "ĐVT", "Đơn vị tính")
        hh_code = pick(row, "Mã HH") or pick_has(row, "mã", "hh")
        hh_name = pick(row, "Tên Sản phẩm (HH)", "Tên Sản phẩm HH", "Tên HH") or pick_has(row, "sản phẩm", "hh")

        if not db_id and not code:
            continue                          # dòng rỗng
        if code.upper().startswith("TEST") or name.lower() in ("kiểm tra hệ thống", "kiem tra he thong"):
            skipped += 1
            continue                          # dòng test

        dup_in_file = code in seen            # dòng trùng mã trong cùng file -> không đếm lại
        if code:
            seen.add(code)

        existing = None
        if db_id and db_id.isdigit():
            existing = by_id.get(int(db_id))
        if not existing and code:
            existing = by_code.get(code)      # gồm cả bản ghi vừa tạo trong lần chạy này -> gộp dòng trùng

        if existing:
            if action in ["xóa", "delete"]:
                db.delete(existing)
                by_code.pop(existing.code, None)
                if not dup_in_file: deleted += 1
            else:
                # chỉ ghi đè cột có trong file (tránh xóa nhầm dữ liệu cột không sync)
                if name: existing.name = name
                if invoice_name: existing.invoice_name = invoice_name
                if legal_name: existing.legal_name = legal_name
                if item_group: existing.item_group = item_group
                if unit: existing.unit = unit
                if hh_code: existing.hh_code = hh_code
                if hh_name: existing.hh_name = hh_name
                existing.is_active = is_active
                existing.updated_by = user.id
                if dup_in_file:
                    pass                       # đã đếm ở lần xuất hiện đầu
                elif not is_active:
                    deleted += 1
                else:
                    updated += 1
        else:
            if not is_active or not name or not code:
                continue
            obj = Product(
                code=code, name=name, invoice_name=invoice_name, legal_name=legal_name,
                item_group=item_group, unit=unit, hh_code=hh_code, hh_name=hh_name,
                is_active=is_active, created_by=user.id, updated_by=user.id)
            db.add(obj)
            by_code[code] = obj               # đăng ký để dòng trùng sau gộp vào đây
            created += 1

    db.commit()
    return success(None, f"Đồng bộ xong. Thêm {created}, cập nhật {updated}, ẩn/xóa {deleted}, bỏ qua {skipped} dòng test/rỗng.")
