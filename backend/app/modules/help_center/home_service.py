"""Business logic cấu hình hiển thị trang chủ khu người dùng (4 khung cố định).

Tách riêng khỏi service.py (bài viết HDSD) để giữ mỗi file dưới ~200 dòng.
"""
import json

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record

from .home_schema import HelpHomeItemCreate, HelpHomeItemUpdate, HelpHomeSectionUpdate
from .model import HelpArticle, HelpHomeItem, HelpHomeSection
from .service import AUDIT_ENTITY, get_article

# 2 khung chỉ có tiêu đề tĩnh + ẩn/hiện, KHÔNG gắn được bài viết
NO_ITEM_SECTION_KEYS = {"faq", "tips"}


def _get_home_section(db: Session, section_id: int) -> HelpHomeSection:
    section = db.get(HelpHomeSection, section_id)
    if not section:
        raise HTTPException(404, "Không tìm thấy khung trang chủ")
    return section


def _get_home_item(db: Session, item_id: int) -> HelpHomeItem:
    item = db.get(HelpHomeItem, item_id)
    if not item:
        raise HTTPException(404, "Không tìm thấy bài viết trong khung")
    return item


def _serialize_item(item: HelpHomeItem, article: HelpArticle | None) -> dict:
    return {
        "id": item.id,
        "article_id": item.article_id,
        "article_title": article.title if article else None,
        "article_summary": article.summary if article else None,
        "article_icon": article.icon if article else None,
        "background_image": item.background_image,
        "gradient": item.gradient,
        "sort_order": item.sort_order,
    }


def _serialize_section(db: Session, section: HelpHomeSection) -> dict:
    """Kèm items sắp theo sort_order, JOIN dữ liệu bài viết. Item trỏ tới bài đã xóa (hiếm khi
    xảy ra nhờ FK CASCADE) sẽ bị loại khỏi kết quả thay vì trả article rỗng."""
    items = (
        db.query(HelpHomeItem)
        .filter(HelpHomeItem.section_id == section.id)
        .order_by(HelpHomeItem.sort_order.asc(), HelpHomeItem.id.asc())
        .all()
    )
    article_ids = [i.article_id for i in items]
    articles: dict[int, HelpArticle] = {}
    if article_ids:
        articles = {
            a.id: a for a in db.query(HelpArticle).filter(HelpArticle.id.in_(article_ids)).all()
        }
    return {
        "id": section.id,
        "key": section.key,
        "title": section.title,
        "is_visible": section.is_visible,
        "sort_order": section.sort_order,
        "items": [
            _serialize_item(i, articles[i.article_id])
            for i in items if i.article_id in articles
        ],
    }


def get_home_sections(db: Session) -> list[dict]:
    sections = (
        db.query(HelpHomeSection)
        .order_by(HelpHomeSection.sort_order.asc(), HelpHomeSection.id.asc())
        .all()
    )
    return [_serialize_section(db, s) for s in sections]


def update_home_section(db: Session, section_id: int, data: HelpHomeSectionUpdate, user_id: int) -> dict:
    section = _get_home_section(db, section_id)
    changes = {}

    if data.title is not None and section.title != data.title:
        changes["Tiêu đề"] = data.title
        section.title = data.title
    if data.is_visible is not None and section.is_visible != data.is_visible:
        changes["Hiển thị"] = data.is_visible
        section.is_visible = data.is_visible
    if data.sort_order is not None and section.sort_order != data.sort_order:
        changes["Thứ tự"] = data.sort_order
        section.sort_order = data.sort_order

    section.updated_by = user_id
    db.commit()
    db.refresh(section)

    if changes:
        record(db, user_id, AUDIT_ENTITY, section.id, "update",
               f"Đổi cấu hình khung trang chủ '{section.key}': " +
               json.dumps(changes, ensure_ascii=False))
    return _serialize_section(db, section)


def add_home_item(db: Session, section_id: int, data: HelpHomeItemCreate, user_id: int) -> dict:
    section = _get_home_section(db, section_id)
    if section.key in NO_ITEM_SECTION_KEYS:
        raise HTTPException(400, "Khung này không gắn bài viết")
    article = get_article(db, data.article_id)

    exists = (
        db.query(HelpHomeItem)
        .filter(HelpHomeItem.section_id == section.id, HelpHomeItem.article_id == article.id)
        .first()
    )
    if exists:
        raise HTTPException(400, "Bài viết đã có trong khung này, không thể thêm trùng")

    item = HelpHomeItem(
        section_id=section.id,
        article_id=article.id,
        background_image=data.background_image,
        gradient=data.gradient,
        sort_order=data.sort_order,
        created_by=user_id,
        updated_by=user_id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    record(db, user_id, AUDIT_ENTITY, section.id, "update",
           f"Thêm bài viết '{article.title}' vào khung '{section.title}'")
    return _serialize_item(item, article)


def update_home_item(db: Session, item_id: int, data: HelpHomeItemUpdate, user_id: int) -> dict:
    item = _get_home_item(db, item_id)
    # "background_image"/"gradient" phải kiểm bằng model_fields_set: gửi null = XÓA ảnh/gradient,
    # còn không gửi = giữ nguyên. Nếu chỉ so `is not None` thì không xóa được (giống update_article).
    if "background_image" in data.model_fields_set:
        item.background_image = data.background_image
    if "gradient" in data.model_fields_set:
        item.gradient = data.gradient
    if data.sort_order is not None:
        item.sort_order = data.sort_order

    item.updated_by = user_id
    db.commit()
    db.refresh(item)

    article = db.get(HelpArticle, item.article_id)
    record(db, user_id, AUDIT_ENTITY, item.section_id, "update",
           f"Cập nhật bài viết '{article.title if article else item.article_id}' trong khung trang chủ")
    return _serialize_item(item, article)


def delete_home_item(db: Session, item_id: int, user_id: int):
    item = _get_home_item(db, item_id)
    section_id = item.section_id
    article = db.get(HelpArticle, item.article_id)

    db.delete(item)
    db.commit()
    record(db, user_id, AUDIT_ENTITY, section_id, "update",
           f"Bỏ bài viết '{article.title if article else item.article_id}' khỏi khung trang chủ")
