import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, require
from app.core.database import get_db
from app.core.file_registry import ext_of
from app.core.response import success
from app.core.storage import dated_key, upload_fileobj

from . import home_service, service
from .home_schema import HelpHomeItemCreate, HelpHomeItemUpdate, HelpHomeSectionUpdate
from .schema import (HelpArticleCreate, HelpArticleOut, HelpArticleSlideCreate,
                     HelpArticleSlideOut, HelpArticleSlideUpdate,
                     HelpArticleUpdate)

router = APIRouter(prefix="/api/v1/help-center", tags=["help_center"])

IMAGE_EXTS = {"jpg", "jpeg", "png", "gif", "webp", "svg"}
MAX_IMAGE_SIZE = 10 * 1024 * 1024


# ---------- Đọc: mọi user đã đăng nhập đều xem được HDSD ----------

@router.get("/tree")
def get_help_tree(db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Danh sách phẳng bài viết để client dựng cây thư mục."""
    return success(service.get_tree(db))


@router.get("/search")
def search_help_articles(q: str = "", db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Tìm kiếm bài viết theo tiêu đề HOẶC nội dung, kèm đoạn trích quanh từ khóa."""
    return success(service.search_articles(db, q))


@router.get("/home")
def get_help_home_sections(db: Session = Depends(get_db),
                           user=Depends(require("help_article", "read"))):
    """Danh sách 4 khung trang chủ sắp theo sort_order, kèm bài viết đã gắn (nếu có).

    PHẢI khai báo TRƯỚC route "/{article_id}" bên dưới — nếu không, "/home" (1 segment)
    sẽ khớp với "/{article_id}" trước và FastAPI trả 422 vì không convert được "home" sang int.
    """
    return success(home_service.get_home_sections(db))


@router.get("/{article_id}")
def get_help_article(article_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Chi tiết 1 bài viết gồm nội dung HTML và danh sách slide."""
    article = service.get_article(db, article_id)
    return success(HelpArticleOut.model_validate(article).model_dump())


# ---------- Ghi: cần quyền trên entity help_article (vai trò "Quản trị HDSD" / admin) ----------

@router.post("")
def create_help_article(data: HelpArticleCreate, db: Session = Depends(get_db),
                        user=Depends(require("help_article", "create"))):
    article = service.create_article(db, data, user.id)
    return success(HelpArticleOut.model_validate(article).model_dump(), "Đã tạo bài viết")


@router.put("/{article_id}")
def update_help_article(article_id: int, data: HelpArticleUpdate, db: Session = Depends(get_db),
                        user=Depends(require("help_article", "write"))):
    article = service.update_article(db, article_id, data, user.id)
    return success(HelpArticleOut.model_validate(article).model_dump(), "Đã cập nhật bài viết")


@router.delete("/{article_id}")
def delete_help_article(article_id: int, db: Session = Depends(get_db),
                        user=Depends(require("help_article", "delete"))):
    service.delete_article(db, article_id, user.id)
    return success(None, "Đã xóa bài viết")


@router.post("/upload-image")
def upload_image(file: UploadFile = File(...), db: Session = Depends(get_db),
                 user=Depends(require("help_article", "write"))):
    """Upload ảnh (chèn vào trình soạn thảo hoặc làm slide) và trả về URL."""
    if ext_of(file.filename or "") not in IMAGE_EXTS:
        raise HTTPException(400, "Chỉ cho phép upload hình ảnh (jpg, png, gif, webp, svg)")

    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    if size > MAX_IMAGE_SIZE:
        raise HTTPException(400, "Kích thước ảnh tối đa 10MB")

    key = dated_key("help_center", file.filename or "image", uuid.uuid4().hex[:12])
    try:
        url = upload_fileobj(file.file, key, file.content_type or "")
    except Exception as e:
        raise HTTPException(400, f"Lỗi tải ảnh: {e}")
    return success({"url": url}, "Tải ảnh thành công")


@router.post("/{article_id}/slides")
def add_article_slide(article_id: int, data: HelpArticleSlideCreate, db: Session = Depends(get_db),
                      user=Depends(require("help_article", "write"))):
    slide = service.add_slide(db, article_id, data, user.id)
    return success(HelpArticleSlideOut.model_validate(slide).model_dump(), "Đã thêm slide")


@router.put("/slides/{slide_id}")
def update_article_slide(slide_id: int, data: HelpArticleSlideUpdate, db: Session = Depends(get_db),
                         user=Depends(require("help_article", "write"))):
    slide = service.update_slide(db, slide_id, data, user.id)
    return success(HelpArticleSlideOut.model_validate(slide).model_dump(), "Đã cập nhật slide")


@router.delete("/slides/{slide_id}")
def delete_article_slide(slide_id: int, db: Session = Depends(get_db),
                         user=Depends(require("help_article", "delete"))):
    service.delete_slide(db, slide_id, user.id)
    return success(None, "Đã xóa slide")


# ---------- Cấu hình hiển thị trang chủ (4 khung cố định: quick_start/categories/faq/tips) ----------

@router.put("/home/sections/{section_id}")
def update_help_home_section(section_id: int, data: HelpHomeSectionUpdate, db: Session = Depends(get_db),
                             user=Depends(require("help_article", "write"))):
    section = home_service.update_home_section(db, section_id, data, user.id)
    return success(section, "Đã cập nhật khung trang chủ")


@router.post("/home/sections/{section_id}/items")
def add_help_home_item(section_id: int, data: HelpHomeItemCreate, db: Session = Depends(get_db),
                       user=Depends(require("help_article", "write"))):
    item = home_service.add_home_item(db, section_id, data, user.id)
    return success(item, "Đã thêm bài viết vào khung")


@router.put("/home/items/{item_id}")
def update_help_home_item(item_id: int, data: HelpHomeItemUpdate, db: Session = Depends(get_db),
                          user=Depends(require("help_article", "write"))):
    item = home_service.update_home_item(db, item_id, data, user.id)
    return success(item, "Đã cập nhật bài viết trong khung")


@router.delete("/home/items/{item_id}")
def delete_help_home_item(item_id: int, db: Session = Depends(get_db),
                          user=Depends(require("help_article", "write"))):
    home_service.delete_home_item(db, item_id, user.id)
    return success(None, "Đã bỏ bài viết khỏi khung")
