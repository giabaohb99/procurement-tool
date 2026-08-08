import json
import re
import unicodedata

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.audit import record

from .model import HelpArticle, HelpArticleSlide
from .schema import (HelpArticleCreate, HelpArticleSlideCreate,
                     HelpArticleSlideUpdate, HelpArticleUpdate)

AUDIT_ENTITY = "help_article"


# ---------- Bài viết ----------

def get_tree(db: Session):
    """Danh sách phẳng (client tự dựng cây). Bỏ cột content cho API nhẹ.

    Trả kèm summary/icon để trang chủ portal dựng thẻ danh mục mà không cần gọi thêm N+1 request.
    """
    items = (
        db.query(
            HelpArticle.id, HelpArticle.parent_id, HelpArticle.title, HelpArticle.sort_order,
            HelpArticle.summary, HelpArticle.icon,
        )
        .order_by(HelpArticle.sort_order.asc(), HelpArticle.id.asc())
        .all()
    )
    return [
        {
            "id": i.id, "parent_id": i.parent_id, "title": i.title, "sort_order": i.sort_order,
            "summary": i.summary, "icon": i.icon,
        }
        for i in items
    ]


def get_article(db: Session, article_id: int) -> HelpArticle:
    article = db.get(HelpArticle, article_id)
    if not article:
        raise HTTPException(404, "Không tìm thấy bài viết")
    return article


def find_by_title(db: Session, title: str) -> HelpArticle | None:
    """Tìm bài theo ĐÚNG tiêu đề — dùng cho nhập file ở chế độ ghi đè bài trùng."""
    return db.query(HelpArticle).filter(HelpArticle.title == title).first()


def next_sort_order(db: Session, parent_id: int | None) -> int:
    """Thứ tự kế tiếp trong cùng một mục — để bài nhập vào nằm cuối danh sách, không chen giữa."""
    q = db.query(func.max(HelpArticle.sort_order))
    q = q.filter(HelpArticle.parent_id.is_(None) if parent_id is None
                 else HelpArticle.parent_id == parent_id)
    return int((q.scalar() or 0) + 1)


def create_article(db: Session, data: HelpArticleCreate, user_id: int) -> HelpArticle:
    if data.parent_id is not None:
        get_article(db, data.parent_id)  # chặn parent_id rác
    article = HelpArticle(
        title=data.title,
        parent_id=data.parent_id,
        content=data.content,
        sort_order=data.sort_order,
        summary=data.summary,
        icon=data.icon,
        created_by=user_id,
        updated_by=user_id,
    )
    db.add(article)
    db.commit()
    db.refresh(article)
    record(db, user_id, AUDIT_ENTITY, article.id, "create", f"Tạo bài viết {data.title}")
    return article


def _validate_new_parent(db: Session, article: HelpArticle, new_parent_id: int | None):
    """Chặn chuyển bài vào chính nó hoặc vào một bài CON/CHÁU của nó (sẽ tạo vòng lặp cây)."""
    if new_parent_id is None:
        return  # đưa về mục gốc — luôn hợp lệ
    if new_parent_id == article.id:
        raise HTTPException(400, "Không thể đặt bài viết làm thư mục cha của chính nó")

    parent = db.get(HelpArticle, new_parent_id)
    if not parent:
        raise HTTPException(404, "Không tìm thấy thư mục cha")

    # Đi ngược lên gốc từ cha mới: gặp lại chính bài này nghĩa là cha mới nằm trong nhánh con
    seen = set()
    cursor = parent
    while cursor is not None:
        if cursor.id == article.id:
            raise HTTPException(400, "Không thể chuyển bài viết vào bên trong bài con của chính nó")
        if cursor.id in seen:
            break  # dữ liệu cũ lỡ có vòng lặp — dừng để không lặp vô hạn
        seen.add(cursor.id)
        cursor = db.get(HelpArticle, cursor.parent_id) if cursor.parent_id else None


def update_article(db: Session, article_id: int, data: HelpArticleUpdate, user_id: int) -> HelpArticle:
    article = get_article(db, article_id)
    changes = {}

    if data.title is not None and article.title != data.title:
        changes["Tiêu đề"] = data.title
        article.title = data.title
    # "parent_id" phải kiểm bằng model_fields_set: gửi null = ĐƯA VỀ MỤC GỐC,
    # còn không gửi = giữ nguyên. Nếu chỉ so `is not None` thì không đưa về gốc được.
    if "parent_id" in data.model_fields_set and article.parent_id != data.parent_id:
        _validate_new_parent(db, article, data.parent_id)
        new_parent = db.get(HelpArticle, data.parent_id) if data.parent_id else None
        changes["Thư mục cha"] = new_parent.title if new_parent else "Mục gốc"
        article.parent_id = data.parent_id
    if data.content is not None and article.content != data.content:
        changes["Nội dung bài viết"] = "Đã cập nhật nội dung mới"
        article.content = data.content
    if data.sort_order is not None and article.sort_order != data.sort_order:
        changes["Thứ tự hiển thị"] = data.sort_order
        article.sort_order = data.sort_order
    # "summary"/"icon" phải kiểm bằng model_fields_set: gửi null = XÓA mô tả/icon,
    # còn không gửi = giữ nguyên. Nếu chỉ so `is not None` thì không xóa được.
    if "summary" in data.model_fields_set and article.summary != data.summary:
        changes["Mô tả ngắn"] = data.summary
        article.summary = data.summary
    if "icon" in data.model_fields_set and article.icon != data.icon:
        changes["Icon"] = data.icon
        article.icon = data.icon

    article.updated_by = user_id
    db.commit()
    db.refresh(article)

    if changes:
        record(db, user_id, AUDIT_ENTITY, article.id, "update",
               json.dumps(changes, ensure_ascii=False))
    return article


def count_branch(db: Session, article_id: int) -> int:
    """Tổng số bài trong nhánh, tính cả chính nó — dùng để cảnh báo trước khi xóa."""
    total = 1
    for child in db.query(HelpArticle.id).filter(HelpArticle.parent_id == article_id).all():
        total += count_branch(db, child.id)
    return total


def _delete_branch(db: Session, article: HelpArticle):
    """Xóa đệ quy từ lá lên gốc — FK parent_id không có ON DELETE CASCADE.

    Phải flush sau MỖI lần xóa: nếu để dồn tới commit, SQLAlchemy gom các lệnh DELETE
    thành một batch theo thứ tự id (cha trước con) và MySQL sẽ báo lỗi khóa ngoại 1451.
    """
    for child in db.query(HelpArticle).filter(HelpArticle.parent_id == article.id).all():
        _delete_branch(db, child)
    db.delete(article)
    db.flush()


def delete_article(db: Session, article_id: int, user_id: int):
    """Xóa bài viết CÙNG toàn bộ bài con/cháu bên trong."""
    article = get_article(db, article_id)
    title = article.title
    total = count_branch(db, article.id)

    _delete_branch(db, article)
    db.commit()

    message = (f"Xóa bài viết {title} cùng {total - 1} bài viết con"
               if total > 1 else f"Xóa bài viết {title}")
    record(db, user_id, AUDIT_ENTITY, article_id, "delete", message)


SEARCH_LIMIT = 20
SNIPPET_BEFORE = 60      # số ký tự lấy trước từ khóa
SNIPPET_AFTER = 130      # số ký tự lấy sau từ khóa


def _strip_html(html: str) -> str:
    """Bỏ thẻ HTML, gộp khoảng trắng — để trích đoạn hiển thị được ở dropdown."""
    text = re.sub(r"<[^>]+>", " ", html or "")
    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
    return re.sub(r"\s+", " ", text).strip()


def _fold_char(ch: str) -> str:
    """Bỏ dấu 1 ký tự, giữ ĐÚNG 1 ký tự để chỉ số vẫn ánh xạ được về chuỗi gốc."""
    if ch in "đĐ":
        return "d"
    base = "".join(c for c in unicodedata.normalize("NFD", ch) if not unicodedata.combining(c))
    return (base or ch).lower()


def _fold(text: str) -> str:
    """Chuẩn hóa không dấu + chữ thường (khớp cách so sánh của MySQL utf8mb4_general_ci)."""
    return "".join(_fold_char(c) for c in text)


def _snippet(content: str, kw: str) -> tuple[str, int, int]:
    """Đoạn trích quanh từ khóa trong nội dung.

    Trả (đoạn trích, vị trí khớp trong đoạn, độ dài khớp).
    Vị trí = -1 nếu từ khóa không nằm trong nội dung (chỉ khớp tiêu đề).
    """
    text = _strip_html(content)
    if not text:
        return "", -1, 0

    pos = _fold(text).find(_fold(kw))
    if pos < 0:
        head = text[:SNIPPET_AFTER]
        return (head + "…" if len(text) > SNIPPET_AFTER else head), -1, 0

    start = max(0, pos - SNIPPET_BEFORE)
    end = min(len(text), pos + len(kw) + SNIPPET_AFTER)
    piece = text[start:end]

    prefix = "…" if start > 0 else ""
    suffix = "…" if end < len(text) else ""
    return prefix + piece + suffix, pos - start + len(prefix), len(kw)


def search_articles(db: Session, keyword: str):
    """Tìm theo tiêu đề HOẶC nội dung. Bài khớp tiêu đề xếp trước, kèm đoạn trích quanh từ khóa."""
    kw = (keyword or "").strip()
    if not kw:
        return []

    like = f"%{kw}%"
    rows = (
        db.query(HelpArticle.id, HelpArticle.title, HelpArticle.content, HelpArticle.parent_id)
        .filter(HelpArticle.title.ilike(like) | HelpArticle.content.ilike(like))
        .limit(SEARCH_LIMIT)
        .all()
    )

    folded_kw = _fold(kw)
    results = []
    for row in rows:
        in_title = folded_kw in _fold(row.title or "")
        snippet, match_at, match_len = _snippet(row.content or "", kw)
        results.append({
            "id": row.id,
            "title": row.title,
            "parent_id": row.parent_id,
            "in_title": in_title,
            "snippet": snippet,
            "match_at": match_at,
            "match_len": match_len,
        })

    # Khớp tiêu đề lên trước, rồi tới khớp nội dung
    results.sort(key=lambda r: (not r["in_title"], r["title"]))
    return results


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
