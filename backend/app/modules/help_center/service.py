import json

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record

from .model import HelpArticle, HelpArticleSlide
from .schema import (HelpArticleCreate, HelpArticleSlideCreate,
                     HelpArticleSlideUpdate, HelpArticleUpdate)

AUDIT_ENTITY = "help_article"


# ---------- Bài viết ----------

def get_tree(db: Session):
    """Danh sách phẳng (client tự dựng cây). Bỏ cột content cho API nhẹ."""
    items = (
        db.query(HelpArticle.id, HelpArticle.parent_id, HelpArticle.title, HelpArticle.sort_order)
        .order_by(HelpArticle.sort_order.asc(), HelpArticle.id.asc())
        .all()
    )
    return [
        {"id": i.id, "parent_id": i.parent_id, "title": i.title, "sort_order": i.sort_order}
        for i in items
    ]


def get_article(db: Session, article_id: int) -> HelpArticle:
    article = db.get(HelpArticle, article_id)
    if not article:
        raise HTTPException(404, "Không tìm thấy bài viết")
    return article


def create_article(db: Session, data: HelpArticleCreate, user_id: int) -> HelpArticle:
    if data.parent_id is not None:
        get_article(db, data.parent_id)  # chặn parent_id rác
    article = HelpArticle(
        title=data.title,
        parent_id=data.parent_id,
        content=data.content,
        sort_order=data.sort_order,
        created_by=user_id,
        updated_by=user_id,
    )
    db.add(article)
    db.commit()
    db.refresh(article)
    record(db, user_id, AUDIT_ENTITY, article.id, "create", f"Tạo bài viết {data.title}")
    return article


def update_article(db: Session, article_id: int, data: HelpArticleUpdate, user_id: int) -> HelpArticle:
    article = get_article(db, article_id)
    changes = {}

    if data.title is not None and article.title != data.title:
        changes["Tiêu đề"] = data.title
        article.title = data.title
    if data.parent_id is not None and article.parent_id != data.parent_id:
        if data.parent_id == article.id:
            raise HTTPException(400, "Không thể đặt bài viết làm thư mục cha của chính nó")
        changes["Thư mục cha"] = data.parent_id
        article.parent_id = data.parent_id
    if data.content is not None and article.content != data.content:
        changes["Nội dung bài viết"] = "Đã cập nhật nội dung mới"
        article.content = data.content
    if data.sort_order is not None and article.sort_order != data.sort_order:
        changes["Thứ tự hiển thị"] = data.sort_order
        article.sort_order = data.sort_order

    article.updated_by = user_id
    db.commit()
    db.refresh(article)

    if changes:
        record(db, user_id, AUDIT_ENTITY, article.id, "update",
               json.dumps(changes, ensure_ascii=False))
    return article


def delete_article(db: Session, article_id: int, user_id: int):
    article = get_article(db, article_id)
    has_child = db.query(HelpArticle).filter(HelpArticle.parent_id == article.id).count()
    if has_child:
        raise HTTPException(400, "Không thể xóa thư mục đang có chứa bài viết con.")

    title = article.title
    db.delete(article)
    db.commit()
    record(db, user_id, AUDIT_ENTITY, article_id, "delete", f"Xóa bài viết {title}")


def search_articles(db: Session, keyword: str):
    kw = (keyword or "").strip()
    if not kw:
        return []
    return (
        db.query(HelpArticle.id, HelpArticle.title)
        .filter(HelpArticle.title.ilike(f"%{kw}%") | HelpArticle.content.ilike(f"%{kw}%"))
        .limit(10)
        .all()
    )


# ---------- Slide ảnh hướng dẫn ----------

def add_slide(db: Session, article_id: int, data: HelpArticleSlideCreate, user_id: int) -> HelpArticleSlide:
    article = get_article(db, article_id)
    slide = HelpArticleSlide(
        article_id=article.id,
        image_url=data.image_url,
        caption=data.caption,
        step_order=data.step_order,
        created_by=user_id,
        updated_by=user_id,
    )
    db.add(slide)
    db.commit()
    db.refresh(slide)
    record(db, user_id, AUDIT_ENTITY, article.id, "update",
           f"Thêm ảnh hướng dẫn (Slide #{slide.step_order})")
    return slide


def _get_slide(db: Session, slide_id: int) -> HelpArticleSlide:
    slide = db.get(HelpArticleSlide, slide_id)
    if not slide:
        raise HTTPException(404, "Không tìm thấy slide")
    return slide


def update_slide(db: Session, slide_id: int, data: HelpArticleSlideUpdate, user_id: int) -> HelpArticleSlide:
    slide = _get_slide(db, slide_id)
    if data.image_url is not None:
        slide.image_url = data.image_url
    if data.caption is not None:
        slide.caption = data.caption
    if data.step_order is not None:
        slide.step_order = data.step_order
    slide.updated_by = user_id
    db.commit()
    db.refresh(slide)
    record(db, user_id, AUDIT_ENTITY, slide.article_id, "update",
           f"Cập nhật nội dung ảnh hướng dẫn (Slide #{slide.step_order})")
    return slide


def delete_slide(db: Session, slide_id: int, user_id: int):
    slide = _get_slide(db, slide_id)
    article_id, step_order = slide.article_id, slide.step_order
    db.delete(slide)
    db.commit()
    record(db, user_id, AUDIT_ENTITY, article_id, "update",
           f"Xóa ảnh hướng dẫn (Slide #{step_order})")
