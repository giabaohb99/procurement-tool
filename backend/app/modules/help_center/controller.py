import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, require
from app.core.database import get_db
from app.core.file_registry import ext_of
from app.core.response import success
from app.core.storage import dated_key, upload_fileobj

from . import service
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
