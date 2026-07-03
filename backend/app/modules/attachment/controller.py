import uuid

from fastapi import (APIRouter, Depends, File, Form, HTTPException, Query,
                     UploadFile)
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, user_has_permission
from app.core.database import get_db
from app.core.file_registry import ext_of, policy
from app.core.response import success
from app.core.storage import delete_key, upload_fileobj

from .model import Attachment

router = APIRouter(prefix="/api/attachments", tags=["attachment"])


def _out(a: Attachment) -> dict:
    return {"id": a.id, "filename": a.filename, "url": a.url, "content_type": a.content_type,
            "size": a.size, "entity": a.entity, "entity_id": a.entity_id}


def _policy_or_400(entity: str):
    pol = policy(entity)
    if not pol:
        raise HTTPException(400, f"Loại đính kèm không hợp lệ: {entity}")
    return pol


def _check(db: Session, user, entity: str, mode: str):
    """mode='read' → cần đọc phiếu cha; mode='manage' → cần write HOẶC create phiếu cha
       (để người TẠO phiếu, vd nhân viên, vẫn đính kèm được phiếu của mình)."""
    parent, exts, max_mb = _policy_or_400(entity)
    if parent == "__self__":          # avatar: chỉ cần đăng nhập
        return exts, max_mb
    if mode == "read":
        ok = user_has_permission(db, user, parent, "read")
    else:
        ok = user_has_permission(db, user, parent, "write") or user_has_permission(db, user, parent, "create")
    if not ok:
        raise HTTPException(403, "Không có quyền thao tác đính kèm cho phần này")
    return exts, max_mb


@router.get("")
def list_attachments(
    entity: str = Query(...), entity_id: int = Query(...),
    db: Session = Depends(get_db), user=Depends(get_current_user),
):
    _check(db, user, entity, "read")
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
    exts, max_mb = _check(db, user, entity, "manage")
    out = []
    for f in files:
        ext = ext_of(f.filename or "")
        if ext not in exts:
            raise HTTPException(400, f"Định dạng .{ext or '?'} không được phép (cho phép: {', '.join(sorted(exts))})")
        # đo dung lượng
        f.file.seek(0, 2)
        size = f.file.tell()
        f.file.seek(0)
        if size > max_mb * 1024 * 1024:
            raise HTTPException(400, f"File '{f.filename}' vượt {max_mb}MB")

        key = f"{entity}/{entity_id}/{uuid.uuid4().hex}_{f.filename}"
        try:
            url = upload_fileobj(f.file, key, f.content_type or "")
        except RuntimeError as e:
            raise HTTPException(400, str(e))
        a = Attachment(entity=entity, entity_id=entity_id, purchase_order_id=purchase_order_id,
                       filename=f.filename, file_key=key, url=url, content_type=f.content_type or "",
                       size=size, created_by=user.id, updated_by=user.id)
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
    _check(db, user, a.entity, "manage")
    delete_key(a.file_key)
    db.delete(a)
    db.commit()
    return success(None, "Đã xóa")
