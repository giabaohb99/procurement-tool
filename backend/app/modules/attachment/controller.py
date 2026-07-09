import uuid

from fastapi import (APIRouter, Depends, File, Form, HTTPException, Query,
                     UploadFile)
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, user_has_permission
from app.core.database import get_db
from app.core.file_registry import ext_of, policy
from app.core.response import success
from app.core.storage import delete_key, upload_fileobj

from .model import FileLink, StoredFile
from .service import _delete_file_if_orphan

router = APIRouter(prefix="/api/attachments", tags=["attachment"])


def _link_out(link: FileLink, f: StoredFile) -> dict:
    # id = LINK id (để DELETE tương thích FE cũ); kèm file_id + thông tin file
    return {"id": link.id, "file_id": f.id, "filename": f.filename, "url": f.url,
            "content_type": f.content_type, "size": f.size,
            "entity": link.entity, "entity_id": link.entity_id}


def _file_out(f: StoredFile) -> dict:
    return {"file_id": f.id, "filename": f.filename, "url": f.url,
            "content_type": f.content_type, "size": f.size}


def _policy_or_400(entity: str):
    pol = policy(entity)
    if not pol:
        raise HTTPException(400, f"Loại đính kèm không hợp lệ: {entity}")
    return pol


def _check(db: Session, user, entity: str, mode: str):
    """mode='read' → cần đọc phiếu cha; mode='manage' → write HOẶC create phiếu cha."""
    parent, exts, max_mb = _policy_or_400(entity)
    if parent == "__self__":
        return exts, max_mb
    if mode == "read":
        ok = user_has_permission(db, user, parent, "read")
    else:
        ok = user_has_permission(db, user, parent, "write") or user_has_permission(db, user, parent, "create")
    if not ok:
        raise HTTPException(403, "Không có quyền thao tác đính kèm cho phần này")
    return exts, max_mb


def _store_one(db: Session, f: UploadFile, exts: set, max_mb: int, user_id: int) -> StoredFile:
    """Upload 1 file lên storage + tạo dòng tab_file. Chưa gắn link."""
    ext = ext_of(f.filename or "")
    if ext not in exts:
        raise HTTPException(400, f"Định dạng .{ext or '?'} không được phép (cho phép: {', '.join(sorted(exts))})")
    f.file.seek(0, 2); size = f.file.tell(); f.file.seek(0)
    if size > max_mb * 1024 * 1024:
        raise HTTPException(400, f"File '{f.filename}' vượt {max_mb}MB")
    key = f"file/{uuid.uuid4().hex}_{f.filename}"
    try:
        url = upload_fileobj(f.file, key, f.content_type or "")
    except RuntimeError as e:
        raise HTTPException(400, str(e))
    sf = StoredFile(filename=f.filename, file_key=key, url=url,
                    content_type=f.content_type or "", size=size,
                    created_by=user_id, updated_by=user_id)
    db.add(sf); db.commit(); db.refresh(sf)
    return sf


@router.get("")
def list_attachments(
    entity: str = Query(...), entity_id: int = Query(...),
    db: Session = Depends(get_db), user=Depends(get_current_user),
):
    _check(db, user, entity, "read")
    rows = (db.query(FileLink, StoredFile)
            .join(StoredFile, StoredFile.id == FileLink.file_id)
            .filter(FileLink.entity == entity, FileLink.entity_id == entity_id)
            .order_by(FileLink.id.desc()).all())
    return success([_link_out(lk, f) for lk, f in rows])


@router.post("")
def upload(
    entity: str = Form(...), entity_id: int = Form(...),
    purchase_order_id: int = Form(0),
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db), user=Depends(get_current_user),
):
    """Upload + gắn luôn (record đã có id) — tương thích FE cũ."""
    exts, max_mb = _check(db, user, entity, "manage")
    out = []
    for f in files:
        sf = _store_one(db, f, exts, max_mb, user.id)
        lk = FileLink(file_id=sf.id, entity=entity, entity_id=entity_id,
                      purchase_order_id=purchase_order_id, created_by=user.id, updated_by=user.id)
        db.add(lk); db.commit(); db.refresh(lk)
        out.append(_link_out(lk, sf))
    return success(out, "Đã tải lên", 201)


@router.post("/upload-file")
def upload_file_only(
    entity: str = Form(...),
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db), user=Depends(get_current_user),
):
    """Upload file NGAY → tạo tab_file (chưa gắn link) → trả file_id để gắn khi Lưu record."""
    exts, max_mb = _check(db, user, entity, "manage")
    out = [_file_out(_store_one(db, f, exts, max_mb, user.id)) for f in files]
    return success(out, "Đã tải lên", 201)


class RegisterIn(BaseModel):
    entity: str
    entity_id: int
    purchase_order_id: int = 0
    file_ids: list[int] = []


@router.post("/register")
def register_files(data: RegisterIn, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Gắn các file ĐÃ upload (theo file_id) vào 1 record — khi record vừa có id."""
    _check(db, user, data.entity, "manage")
    out = []
    for fid in data.file_ids:
        f = db.get(StoredFile, fid)
        if not f:
            continue
        lk = FileLink(file_id=fid, entity=data.entity, entity_id=data.entity_id,
                      purchase_order_id=data.purchase_order_id, created_by=user.id, updated_by=user.id)
        db.add(lk); db.commit(); db.refresh(lk)
        out.append(_link_out(lk, f))
    return success(out, "Đã gắn file", 201)


@router.delete("/{link_id}")
def remove(link_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    lk = db.get(FileLink, link_id)
    if not lk:
        raise HTTPException(404, "Không tìm thấy file")
    _check(db, user, lk.entity, "manage")
    fid = lk.file_id
    db.delete(lk); db.flush()
    _delete_file_if_orphan(db, fid)      # còn dùng chỗ khác thì giữ file
    db.commit()
    return success(None, "Đã xóa")
