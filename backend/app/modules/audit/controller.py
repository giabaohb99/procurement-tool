from datetime import datetime, time
from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.audit import resolve_actor
from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.response import success

from .model import AuditLog

router = APIRouter(prefix="/api/audit-logs", tags=["audit"])

ACTION_LABEL = {
    "create": "Tạo mới",
    "update": "Cập nhật",
    "delete": "Xóa",
    "submitted": "Gửi duyệt",
    "approved": "Duyệt",
    "rejected": "Từ chối",
    "dispatched": "Điều phối",
    "paid": "Ghi nhận đã chi",
    "cancelled": "Hủy",
}


@router.get("")
def list_logs(
    entity: str | None = Query(None, description="Tên entity (vd product, contract). Bỏ trống = tất cả"),
    entity_id: int | None = Query(None, description="ID của bản ghi"),
    action: str | None = Query(None, description="Hành động (vd create, update, delete)"),
    search: str | None = Query(None, description="Từ khóa tìm kiếm trong ghi chú hoặc entity"),
    created_by: int | None = Query(None, description="ID người thao tác"),
    from_date: str | None = Query(None, description="Từ ngày (YYYY-MM-DD)"),
    to_date: str | None = Query(None, description="Đến ngày (YYYY-MM-DD)"),
    page: int | None = Query(None, ge=1, description="Số trang (bỏ trống = trả về mảng đơn)"),
    page_size: int = Query(20, ge=1, le=500),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    q = db.query(AuditLog)
    if entity:
        q = q.filter(AuditLog.entity == entity)
    if entity_id is not None:
        q = q.filter(AuditLog.entity_id == entity_id)
    if action:
        q = q.filter(AuditLog.action == action)
    if created_by:
        q = q.filter(AuditLog.created_by == created_by)
    if search and search.strip():
        k = f"%{search.strip()}%"
        q = q.filter(or_(AuditLog.message.like(k), AuditLog.entity.like(k)))

    if from_date:
        try:
            fd = datetime.strptime(from_date[:10], "%Y-%m-%d")
            q = q.filter(AuditLog.created_at >= fd)
        except Exception:
            pass
    if to_date:
        try:
            td = datetime.strptime(to_date[:10], "%Y-%m-%d")
            td_end = datetime.combine(td.date(), time.max)
            q = q.filter(AuditLog.created_at <= td_end)
        except Exception:
            pass

    q = q.order_by(AuditLog.id.desc())

    def _format(l: AuditLog):
        return {
            "id": l.id,
            "entity": l.entity,
            "entity_id": l.entity_id,
            "action": l.action,
            "action_label": ACTION_LABEL.get(l.action, l.action),
            "message": l.message,
            "by": resolve_actor(db, l.created_by),
            "by_id": l.created_by,
            "at": l.created_at,
        }

    # Nếu truyền `page`: trả về dạng phân trang cho màn hình Nhật ký hệ thống
    if page is not None:
        total = q.count()
        items = q.offset((page - 1) * page_size).limit(page_size).all()
        return success({"total": total, "items": [_format(l) for l in items], "page": page, "page_size": page_size})

    # Nếu không truyền `page`: trả về mảng đơn cho các widget lịch sử chi tiết
    logs = q.limit(limit).all()
    return success([_format(l) for l in logs])
