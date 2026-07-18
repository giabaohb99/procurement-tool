"""API bình luận đa hình /api/comments (gắn (entity, entity_id)). Guard = quyền đọc survey."""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.auth import get_perm_profile, require, user_has_permission
from app.core.database import get_db
from app.core.response import success
from app.core.scoping import apply_scope

from . import service
from .model import Comment
from .schema import CommentCreate, CommentUpdate

router = APIRouter(prefix="/api/comments", tags=["comment"])


def _assert_visible(db: Session, user, survey_id: int | None) -> int:
    """Chặn thao tác trên comment của phiếu ngoài PHẠM VI DỮ LIỆU của user
    (tái dùng apply_scope — 'ai xem được phiếu mới được bình luận'). Trả survey_id."""
    from app.modules.survey.model import Survey

    if not survey_id:
        raise HTTPException(404, "Không tìm thấy phiếu khảo sát")
    q = apply_scope(db.query(Survey).filter(Survey.id == survey_id),
                    Survey, "survey", user, get_perm_profile(db, user))
    if not q.first():
        raise HTTPException(403, "Ngoài phạm vi được phép xem")
    return survey_id


def _out(c: Comment, names: dict) -> dict:
    return {
        "id": c.id, "entity": c.entity, "entity_id": c.entity_id, "body": c.body,
        "parent_id": c.parent_id, "mention_user_ids": c.mention_user_ids or [],
        "by": names.get(c.created_by, "Hệ thống"), "by_id": c.created_by,
        "at": c.created_at,
    }


@router.get("")
def list_(entity: str = Query(...), entity_id: int = Query(...),
          db: Session = Depends(get_db), user=Depends(require("survey", "read"))):
    if entity not in service.ALLOWED_ENTITIES:
        raise HTTPException(400, "entity không hợp lệ")
    _assert_visible(db, user, service.resolve_survey_id(db, entity, entity_id))
    items = service.list_comments(db, entity, entity_id)
    names = service.resolve_names(db, {c.created_by for c in items})
    return success([_out(c, names) for c in items])


@router.get("/counts")
def counts_(entity: str = Query(...), entity_ids: str = Query(...),
            db: Session = Depends(get_db), user=Depends(require("survey", "read"))):
    """Đếm số bình luận theo nhiều entity_id (badge cấp dòng) — 1 query, tránh N+1."""
    if entity not in service.ALLOWED_ENTITIES:
        raise HTTPException(400, "entity không hợp lệ")
    ids = [int(x) for x in entity_ids.split(",") if x.strip().isdigit()]
    if not ids:
        return success({})
    # Kiểm phạm vi: mọi entity_id phải thuộc phiếu user được xem
    survey_ids = {service.resolve_survey_id(db, entity, i) for i in ids}
    for sid in survey_ids:
        _assert_visible(db, user, sid)
    rows = (
        db.query(Comment.entity_id, func.count(Comment.id))
        .filter(Comment.entity == entity, Comment.entity_id.in_(ids))
        .group_by(Comment.entity_id).all()
    )
    return success({str(eid): n for eid, n in rows})


@router.post("")
def create_(data: CommentCreate, background_tasks: BackgroundTasks,
            db: Session = Depends(get_db), user=Depends(require("survey", "read"))):
    if data.entity not in service.ALLOWED_ENTITIES:
        raise HTTPException(400, "entity không hợp lệ")
    # Suy survey_id ở server (tin cậy) → kiểm phạm vi + dùng luôn cho thông báo
    survey_id = _assert_visible(db, user, service.resolve_survey_id(db, data.entity, data.entity_id))
    try:
        service.check_parent(db, data.entity, data.entity_id, data.parent_id)
    except ValueError as ex:
        raise HTTPException(400, str(ex))
    c = Comment(
        entity=data.entity, entity_id=data.entity_id, body=data.body.strip(),
        parent_id=data.parent_id, mention_user_ids=service.valid_mention_ids(db, data.mention_user_ids),
        created_by=user.id, updated_by=user.id,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    service.notify_comment(db, c, background_tasks, survey_id)
    names = service.resolve_names(db, {c.created_by})
    return success(_out(c, names), "Đã bình luận", 201)


@router.patch("/{cid}")
def update_(cid: int, data: CommentUpdate, db: Session = Depends(get_db),
            user=Depends(require("survey", "read"))):
    c = db.get(Comment, cid)
    if not c:
        raise HTTPException(404, "Không tìm thấy bình luận")
    _assert_visible(db, user, service.resolve_survey_id(db, c.entity, c.entity_id))
    if c.created_by != user.id:
        raise HTTPException(403, "Chỉ sửa được bình luận của mình")
    c.body = data.body.strip()
    c.mention_user_ids = service.valid_mention_ids(db, data.mention_user_ids)
    c.updated_by = user.id
    db.commit()
    names = service.resolve_names(db, {c.created_by})
    return success(_out(c, names), "Đã cập nhật")


@router.delete("/{cid}")
def delete_(cid: int, db: Session = Depends(get_db), user=Depends(require("survey", "read"))):
    c = db.get(Comment, cid)
    if not c:
        raise HTTPException(404, "Không tìm thấy bình luận")
    _assert_visible(db, user, service.resolve_survey_id(db, c.entity, c.entity_id))
    # Chủ bình luận, hoặc người có quyền cao (delete trên survey) → xóa được
    if c.created_by != user.id and not user_has_permission(db, user, "survey", "delete"):
        raise HTTPException(403, "Không có quyền xóa bình luận này")
    # Xóa luôn các reply con (threading 1 cấp)
    db.query(Comment).filter(Comment.parent_id == cid).delete(synchronize_session=False)
    db.delete(c)
    db.commit()
    return success(None, "Đã xóa")
