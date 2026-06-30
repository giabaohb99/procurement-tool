"""Generic CRUD router factory — dùng cho các danh mục đơn giản (đỡ lặp code)."""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.auth import require
from app.core.base_controller import apply_filters, pagination
from app.core.database import get_db
from app.core.response import success


def make_crud_router(prefix, entity, Model, CreateSchema, UpdateSchema, OutSchema,
                     filterable, unique_field="code"):
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
        if unique_field and getattr(data, unique_field, None) is not None:
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

    return router
