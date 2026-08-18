"""API TRANG TỔNG QUAN VĂN THƯ.

⚠️ Router này phải đăng ký TRƯỚC `document_router` trong `app/main.py` — đường
dẫn `/api/documents/dashboard` là TĨNH và sẽ bị route động `/{document_id}`
nuốt nếu xếp sau. Xem `test_thu_tu_route_van_ban.py`.
"""
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.auth import get_perm_profile, require
from app.core.database import get_db
from app.core.response import success

from . import dashboard_service
from .dashboard_service import DashboardFilters

router = APIRouter(prefix="/api/documents", tags=["document-dashboard"])


@router.get("/dashboard")
def dashboard(
    company_id: int | None = Query(default=None),
    department_id: int | None = Query(default=None),
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
    user=Depends(require("document", "read")),
):
    """Đủ số liệu cho cả trang trong MỘT lần gọi.

    Mọi câu đếm đi qua cùng bộ lọc phạm vi với danh sách văn bản — nếu không thì
    trang tổng quan nói một con số mà bấm vào danh sách lại ra con số khác.

    Bốn tham số lọc là của thanh trên cùng trang; bỏ trống hết = toàn bộ phạm vi
    người này xem được. Chúng CỘNG THÊM vào phạm vi quyền chứ không thay thế —
    khai `company_id` của pháp nhân mình không được xem thì vẫn ra rỗng.
    """
    filters = DashboardFilters(
        company_id=company_id,
        department_id=department_id,
        from_date=from_date,
        to_date=to_date,
    )
    return success(
        dashboard_service.overview(db, user, get_perm_profile(db, user), filters)
    )
