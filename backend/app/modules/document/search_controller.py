"""API TÌM KIẾM TOÀN VĂN văn bản — `GET /api/documents/search` (phase 07,
duoc-CR-477).

Router RIÊNG (không thêm route vào `document/controller.py`): tệp đó có agent
khác chỉnh song song (phase 01/02/03/04 của cùng kế hoạch), và endpoint này đủ
khác biệt về hình dạng tham số để đứng module riêng. Tái dùng
`document.controller._list_query` để không chép lại luật lọc/quyền/thư mục —
xem `search_service.search`.

⚠️ Đăng ký router này TRƯỚC `document_router` (có `/{document_id}`) trong
`app/main.py` — cùng lý do `export_xlsx` phải khai trước route đó trong
`document/controller.py`: nếu không, FastAPI đọc "search" thành `document_id`.
"""
from datetime import date

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.auth import get_perm_profile, require
from app.core.database import get_db
from app.core.response import success

from . import search_service

router = APIRouter(prefix="/api/documents", tags=["document"])


@router.get("/search")
def search_documents(
    request: Request,
    q: str = Query("", description='Câu tìm — cụm trong ngoặc kép ("..."), loại trừ bằng -từ'),
    effective_from: date | None = Query(None, description="Hiệu lực từ ngày"),
    effective_to: date | None = Query(None, description="Hiệu lực đến ngày"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user=Depends(require("document", "read")),
):
    """Tìm trên siêu dữ liệu + nội dung soạn thảo + chữ trong tệp đính kèm.

    Kết hợp được với mọi bộ lọc của danh sách văn bản qua CHÍNH request này —
    `doc_type_id`, `company_id`, `status`, `folder_id`, `include_subfolders`...
    đọc lại từ `request.query_params` bên trong `_list_query`, không cần khai
    tham số riêng ở đây (xem whitelist `FILTERABLE` của `document/controller.py`).
    """
    profile = get_perm_profile(db, user)
    result = search_service.search(db, request, user, profile, q,
                                   effective_from, effective_to, page, page_size)
    return success(result)
