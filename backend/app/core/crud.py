"""Generic CRUD router factory — dùng cho các danh mục đơn giản (đỡ lặp code)."""
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.auth import require
from app.core.base_controller import apply_filters, pagination
from app.core.database import get_db
from app.core.response import success


def make_crud_router(prefix, entity, Model, CreateSchema, UpdateSchema, OutSchema,
                     filterable, unique_field="code", code_prefix=None, csv_headers=None):
    router = APIRouter(prefix=prefix, tags=[entity])

    def out(o):
        return OutSchema.model_validate(o).model_dump()

    @router.get("")
    def list_items(request: Request, pg: dict = Depends(pagination),
                   db: Session = Depends(get_db), user=Depends(require(entity, "read"))):
        q = apply_filters(db.query(Model), Model, request, filterable)
        total = q.count()
        items = q.order_by(Model.id.desc()).offset(pg["offset"]).limit(pg["limit"]).all()
        return success({"total": total, "items": [out(i) for i in items]})

    @router.get("/{oid}")
    def get_item(oid: int, db: Session = Depends(get_db), user=Depends(require(entity, "read"))):
        o = db.get(Model, oid)
        if not o:
            raise HTTPException(404, "Không tìm thấy")
        return success(out(o))

    @router.post("")
    def create_item(data: CreateSchema, db: Session = Depends(get_db),
                    user=Depends(require(entity, "create"))):
        if code_prefix and hasattr(data, "code") and not data.code:
            from app.core.utils import generate_code
            data.code = generate_code(db, Model, code_prefix)

        if unique_field and getattr(data, unique_field, None):
            val = getattr(data, unique_field)
            if db.query(Model).filter(getattr(Model, unique_field) == val).first():
                raise HTTPException(400, f"{unique_field} đã tồn tại")
        o = Model(**data.model_dump(), created_by=user.id, updated_by=user.id)
        db.add(o)
        db.commit()
        db.refresh(o)
        record(db, user.id, entity, o.id, "create")
        return success(out(o), "Đã tạo", 201)

    @router.patch("/{oid}")
    def update_item(oid: int, data: UpdateSchema, db: Session = Depends(get_db),
                    user=Depends(require(entity, "write"))):
        o = db.get(Model, oid)
        if not o:
            raise HTTPException(404, "Không tìm thấy")
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(o, k, v)
        o.updated_by = user.id
        db.commit()
        db.refresh(o)
        record(db, user.id, entity, oid, "update")
        return success(out(o), "Đã cập nhật")

    @router.delete("/{oid}")
    def delete_item(oid: int, db: Session = Depends(get_db),
                    user=Depends(require(entity, "delete"))):
        o = db.get(Model, oid)
        if not o:
            raise HTTPException(404, "Không tìm thấy")
        db.delete(o)
        db.commit()
        record(db, user.id, entity, oid, "delete")
        return success(None, "Đã xóa")

    if csv_headers:
        @router.get("/export/csv")
        def export_csv(
            ids: str | None = None,
            request: Request = None,
            db: Session = Depends(get_db),
            user=Depends(require(entity, "read")),
        ):
            from app.core.csv_utils import export_csv_response
            q = apply_filters(db.query(Model), Model, request, filterable)
            if ids:
                id_list = [int(i.strip()) for i in ids.split(",") if i.strip().isdigit()]
                if id_list:
                    q = q.filter(Model.id.in_(id_list))
            items = q.order_by(Model.id.desc()).all()
            return export_csv_response(items, csv_headers, entity)

        @router.post("/import/csv")
        def import_csv(
            file: UploadFile = File(...),
            db: Session = Depends(get_db),
            user=Depends(require(entity, "write")),
        ):
            import csv
            from io import StringIO
            content = file.file.read().decode("utf-8")
            reader = csv.DictReader(StringIO(content))
            if not reader.fieldnames:
                raise HTTPException(400, "File CSV trống")
                
            created, updated, deleted = 0, 0, 0
            for row in reader:
                action = row.get("Hành động", "").strip().lower()
                is_active = action not in ["xóa", "delete", "ngừng"]
                
                data = {}
                for model_key, csv_header in csv_headers.items():
                    if csv_header in row:
                        data[model_key] = row[csv_header].strip()
                        
                code = data.get("code", "")
                if not code and not data.get("name", ""):
                    continue # Skip empty rows
                    
                existing = db.query(Model).filter(Model.code == code).first() if code else None
                if not existing and getattr(Model, "name", None) is not None and "name" in data and data["name"]:
                    existing = db.query(Model).filter(Model.name == data["name"]).first()
                    
                if existing:
                    if action in ["xóa", "delete"]:
                        db.delete(existing)
                        deleted += 1
                    else:
                        for k, v in data.items():
                            if k != "code" and v:
                                setattr(existing, k, v)
                        existing.is_active = is_active
                        existing.updated_by = user.id
                        if not is_active: deleted += 1
                        else: updated += 1
                else:
                    if not is_active: continue
                    if not code and code_prefix:
                        data["code"] = generate_code(db, Model, code_prefix)
                    
                    new_obj = Model(**data, is_active=is_active, created_by=user.id, updated_by=user.id)
                    db.add(new_obj)
                    created += 1
                    
            db.commit()
            return success(None, f"Nhập file thành công. Thêm mới {created}, cập nhật {updated}, ẩn {deleted}.")
            
    return router
