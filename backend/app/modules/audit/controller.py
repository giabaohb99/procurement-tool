from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.audit import resolve_actor
from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.response import success

from .model import AuditLog

router = APIRouter(prefix="/api/audit-logs", tags=["audit"])

ACTION_LABEL = {"create": "Tạo mới", "update": "Cập nhật", "delete": "Xóa"}


@router.get("")
def list_logs(
    entity: str = Query(...),
    entity_id: int = Query(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    logs = (
        db.query(AuditLog)
        .filter(AuditLog.entity == entity, AuditLog.entity_id == entity_id)
        .order_by(AuditLog.id.desc())
        .limit(100)
        .all()
    )
    return success([
        {
            "action": l.action,
            "action_label": ACTION_LABEL.get(l.action, l.action),
            "message": l.message,
            "by": resolve_actor(db, l.created_by),
            "at": l.created_at,
        }
        for l in logs
    ])
