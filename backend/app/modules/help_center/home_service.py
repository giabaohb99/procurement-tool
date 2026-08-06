"""Business logic cấu hình hiển thị trang chủ khu người dùng (4 khung cố định).

Tách riêng khỏi service.py (bài viết HDSD) để giữ mỗi file dưới ~200 dòng.
"""
import json

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record
from app.modules.faq.model import Faq

from .home_schema import HelpHomeItemCreate, HelpHomeItemUpdate, HelpHomeSectionUpdate
from .model import HelpArticle, HelpHomeItem, HelpHomeSection
from .service import AUDIT_ENTITY, get_article

# Mỗi khung chỉ nhận đúng MỘT loại phần tử:
#   article -> trỏ tới bài viết HDSD
#   faq     -> trỏ tới câu hỏi thường gặp
#   custom  -> thẻ tự do, nội dung nhập tay
SECTION_ITEM_KIND = {
    "quick_start": "article",
    "categories": "article",
    "faq": "faq",
    "tips": "custom",
}

DEFAULT_ITEM_KIND = "article"


def item_kind(section: HelpHomeSection) -> str:
    return SECTION_ITEM_KIND.get(section.key, DEFAULT_ITEM_KIND)


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


def _serialize_item(item: HelpHomeItem, article: HelpArticle | None, faq: Faq | None) -> dict:
    return {
        "id": item.id,
        "article_id": item.article_id,
        "article_title": article.title if article else None,
        "article_summary": article.summary if article else None,
        "article_icon": article.icon if article else None,
        "faq_id": item.faq_id,
        "faq_question": faq.question if faq else None,
        "title": item.title,
        "description": item.description,
        "icon": item.icon,
        "background_image": item.background_image,
        "gradient": item.gradient,
        "sort_order": item.sort_order,
    }


def _serialize_section(db: Session, section: HelpHomeSection) -> dict:
    """Kèm items sắp theo sort_order, JOIN dữ liệu bài viết / câu hỏi.

    Item trỏ tới bài (hoặc câu hỏi) đã xóa — hiếm khi xảy ra nhờ FK CASCADE — bị loại khỏi kết
    quả thay vì trả về phần tử rỗng. Thẻ tự do không tham chiếu gì nên luôn được giữ.
    """
    items = (
        db.query(HelpHomeItem)
        .filter(HelpHomeItem.section_id == section.id)
        .order_by(HelpHomeItem.sort_order.asc(), HelpHomeItem.id.asc())
        .all()
    )

    article_ids = [i.article_id for i in items if i.article_id]
    articles: dict[int, HelpArticle] = {}
    if article_ids:
        articles = {
            a.id: a for a in db.query(HelpArticle).filter(HelpArticle.id.in_(article_ids)).all()
        }

    faq_ids = [i.faq_id for i in items if i.faq_id]
    faqs: dict[int, Faq] = {}
    if faq_ids:
        faqs = {f.id: f for f in db.query(Faq).filter(Faq.id.in_(faq_ids)).all()}

    def keep(item: HelpHomeItem) -> bool:
        if item.article_id:
            return item.article_id in articles
        if item.faq_id:
            return item.faq_id in faqs
        return True  # thẻ tự do

    return {
        "id": section.id,
        "key": section.key,
        "title": section.title,
        "is_visible": section.is_visible,
        "sort_order": section.sort_order,
        "item_kind": item_kind(section),
        "items": [
            _serialize_item(i, articles.get(i.article_id), faqs.get(i.faq_id))
            for i in items if keep(i)
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
    kind = item_kind(section)

    article: HelpArticle | None = None
    faq: Faq | None = None
    label = ""

    if kind == "article":
        if not data.article_id:
            raise HTTPException(400, "Khung này cần chọn bài viết")
        article = get_article(db, data.article_id)
        label = article.title
        if _has_duplicate(db, section.id, HelpHomeItem.article_id, article.id):
            raise HTTPException(400, "Bài viết đã có trong khung này, không thể thêm trùng")

    elif kind == "faq":
        if not data.faq_id:
            raise HTTPException(400, "Khung này cần chọn câu hỏi thường gặp")
        faq = db.get(Faq, data.faq_id)
        if not faq:
            raise HTTPException(404, "Không tìm thấy câu hỏi thường gặp")
        label = faq.question
        if _has_duplicate(db, section.id, HelpHomeItem.faq_id, faq.id):
            raise HTTPException(400, "Câu hỏi đã có trong khung này, không thể thêm trùng")

    else:  # custom — thẻ tự do
        if not (data.title or "").strip():
            raise HTTPException(400, "Thẻ tự do phải có tiêu đề")
        label = data.title.strip()

    item = HelpHomeItem(
        section_id=section.id,
        article_id=article.id if article else None,
        faq_id=faq.id if faq else None,
        title=(data.title or "").strip() or None,
        description=(data.description or "").strip() or None,
        icon=data.icon,
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
           f"Thêm '{label}' vào khung '{section.title}'")
    return _serialize_item(item, article, faq)


def _has_duplicate(db: Session, section_id: int, column, value: int) -> bool:
    return (
        db.query(HelpHomeItem)
        .filter(HelpHomeItem.section_id == section_id, column == value)
        .first()
        is not None
    )


def update_home_item(db: Session, item_id: int, data: HelpHomeItemUpdate, user_id: int) -> dict:
    item = _get_home_item(db, item_id)
    # Các cột này phải kiểm bằng model_fields_set: gửi null = XÓA giá trị, không gửi = giữ nguyên.
    # Chỉ so `is not None` thì không xóa được (giống update_article).
    for field in ("background_image", "gradient", "title", "description", "icon"):
        if field in data.model_fields_set:
            setattr(item, field, getattr(data, field))
    if data.sort_order is not None:
        item.sort_order = data.sort_order

    item.updated_by = user_id
    db.commit()
    db.refresh(item)

    article = db.get(HelpArticle, item.article_id) if item.article_id else None
    faq = db.get(Faq, item.faq_id) if item.faq_id else None
    record(db, user_id, AUDIT_ENTITY, item.section_id, "update",
           f"Cập nhật '{_item_label(item, article, faq)}' trong khung trang chủ")
    return _serialize_item(item, article, faq)


def delete_home_item(db: Session, item_id: int, user_id: int):
    item = _get_home_item(db, item_id)
    section_id = item.section_id
    article = db.get(HelpArticle, item.article_id) if item.article_id else None
    faq = db.get(Faq, item.faq_id) if item.faq_id else None
    label = _item_label(item, article, faq)

    db.delete(item)
    db.commit()
    record(db, user_id, AUDIT_ENTITY, section_id, "update",
           f"Bỏ '{label}' khỏi khung trang chủ")


def _item_label(item: HelpHomeItem, article: HelpArticle | None, faq: Faq | None) -> str:
    """Tên gọi của phần tử để ghi nhật ký, dùng chung cho cả 3 loại khung."""
    if article:
        return article.title
    if faq:
        return faq.question
    return item.title or f"#{item.id}"
