import uuid

from fastapi import (APIRouter, Depends, File, Form, HTTPException, Query,
                     UploadFile)
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.response import success
from app.core.storage import delete_key, upload_fileobj

from .model import Attachment

router = APIRouter(prefix="/api/attachments", tags=["attachment"])


def _out(a: Attachment) -> dict:
    return {"id": a.id, "filename": a.filename, "url": a.url, "content_type": a.content_type,
            "size": a.size, "entity": a.entity, "entity_id": a.entity_id}


@router.get("")
def list_attachments(
    entity: str = Query(...), entity_id: int = Query(...),
    db: Session = Depends(get_db), user=Depends(get_current_user),
):
    rows = (db.query(Attachment)
            .filter(Attachment.entity == entity, Attachment.entity_id == entity_id)
            .order_by(Attachment.id.desc()).all())
    return success([_out(a) for a in rows])


@router.post("")
def upload(
    entity: str = Form(...), entity_id: int = Form(...),
    purchase_order_id: int = Form(0),
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db), user=Depends(get_current_user),
):
    out = []
    for f in files:
        key = f"{entity}/{entity_id}/{uuid.uuid4().hex}_{f.filename}"
        try:
            url = upload_fileobj(f.file, key, f.content_type or "")
        except RuntimeError as e:
            raise HTTPException(400, str(e))
        a = Attachment(entity=entity, entity_id=entity_id, purchase_order_id=purchase_order_id,
                       filename=f.filename, file_key=key, url=url, content_type=f.content_type or "",
                       created_by=user.id, updated_by=user.id)
        db.add(a)
        db.commit()
        db.refresh(a)
        out.append(_out(a))
    return success(out, "Đã tải lên", 201)


@router.delete("/{aid}")
def remove(aid: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    a = db.get(Attachment, aid)
    if not a:
        raise HTTPException(404, "Không tìm thấy file")
    delete_key(a.file_key)
    db.delete(a)
    db.commit()
    return success(None, "Đã xóa")
