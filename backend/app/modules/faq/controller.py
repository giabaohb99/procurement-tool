from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import require
from app.core.database import get_db
from app.core.response import success

from . import service
from .schema import FaqCreate, FaqOut, FaqUpdate

# Câu hỏi thường gặp — cùng nhóm nội dung với Hướng dẫn sử dụng nên dùng chung
# quyền `help_article` (vai trò help_admin đã có sẵn), không thêm entity mới.
router = APIRouter(prefix="/api/v1/faq", tags=["faq"])


@router.get("")
def list_faqs(active_only: bool = False, db: Session = Depends(get_db)):
    """Danh sách câu hỏi. Trang người dùng gọi với active_only=true để bỏ câu đang ẩn."""
    items = service.list_faqs(db, active_only)
    return success([FaqOut.model_validate(i).model_dump() for i in items])


@router.get("/{faq_id}")
def get_faq(faq_id: int, db: Session = Depends(get_db)):
    return success(FaqOut.model_validate(service.get_faq(db, faq_id)).model_dump())


@router.post("")
def create_faq(data: FaqCreate, db: Session = Depends(get_db),
               user=Depends(require("help_article", "create"))):
    faq = service.create_faq(db, data, user.id)
    return success(FaqOut.model_validate(faq).model_dump(), "Đã tạo câu hỏi")


@router.put("/{faq_id}")
def update_faq(faq_id: int, data: FaqUpdate, db: Session = Depends(get_db),
               user=Depends(require("help_article", "write"))):
    faq = service.update_faq(db, faq_id, data, user.id)
    return success(FaqOut.model_validate(faq).model_dump(), "Đã cập nhật câu hỏi")


@router.delete("/{faq_id}")
def delete_faq(faq_id: int, db: Session = Depends(get_db),
               user=Depends(require("help_article", "delete"))):
    service.delete_faq(db, faq_id, user.id)
    return success(None, "Đã xóa câu hỏi")
