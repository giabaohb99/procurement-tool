from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.audit import resolve_actor
from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.response import success

from .model import AuditLog

router = APIRouter(prefix="/api/audit-logs", tags=["audit"])

ACTION_LABEL = {
    "create": "Tạo mới", "update": "Cập nhật", "delete": "Xóa",
    "submitted": "Gửi duyệt", "approved": "Duyệt", "rejected": "Từ chối",
    "paid": "Ghi nhận đã chi", "cancelled": "Hủy",
}


@router.get("")
def list_logs(
    entity: str = Query(...),
    entity_id: int | None = Query(None, description="Bỏ trống = lấy log của MỌI bản ghi thuộc entity"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    q = db.query(AuditLog).filter(AuditLog.entity == entity)
    if entity_id is not None:
        q = q.filter(AuditLog.entity_id == entity_id)

    logs = q.order_by(AuditLog.id.desc()).limit(limit).all()
    return success([
        {
            "action": l.action,
            "action_label": ACTION_LABEL.get(l.action, l.action),
            "message": l.message,
            "entity_id": l.entity_id,
            "by": resolve_actor(db, l.created_by),
            "at": l.created_at,
        }
        for l in logs
    ])
