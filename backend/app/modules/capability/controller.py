"""API năng lực — `prefix=/api/work-capability` (duoc-CR-656). Chỉ QUẢN TRỊ (cùng khóa `setting` như hồ sơ cách làm việc).

Phase 08 sẽ gác thêm khóa báo cáo số 16 và gắn các đường tổng hợp theo loại việc / theo người; ở đây chỉ có đường
đọc TẢI ĐANG ÔM (D1c). Admin xem tất cả — không `apply_scope` (khóa `setting` không có bảng để lọc).
Mỗi lần mở để lại dòng `tab_request_log` (GET không bị loại): đủ trả lời «ai đã xem tải của ai».
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.auth import require
from app.core.database import get_db
from app.core.response import success
from app.modules.capability import workload_service

router = APIRouter(prefix="/api/work-capability", tags=["work-capability"])

MAX_IDS = 200


@router.get("/load")
def get_current_load(company_id: int | None = Query(None, ge=1),
                     department_id: list[int] | None = Query(None, max_length=50),
                     employee_id: list[int] | None = Query(None, max_length=MAX_IDS),
                     horizon_days: int = Query(14, ge=1, le=workload_service.MAX_HORIZON_DAYS),
                     db: Session = Depends(get_db), user=Depends(require("setting", "read"))):
    """Tải đang ôm từng người, tính lúc gọi. Phải truyền ít nhất một trong `company_id` / `department_id` / `employee_id`."""
    if not (company_id or department_id or employee_id):
        raise HTTPException(422, "Cần chọn pháp nhân, phòng ban hoặc nhân sự — không trả cả công ty khi không nói rõ")
    rows = workload_service.current_load(db, company_id=company_id, department_ids=department_id,
                                         employee_ids=employee_id, horizon_days=horizon_days)
    return success({"items": rows, "count": len(rows), "horizon_days": horizon_days})
