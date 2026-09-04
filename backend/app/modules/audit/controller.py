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
    #  Hai kết cục của bộ máy duyệt nhiều bước — xem `document/approval_bridge`.
    "returned": "Trả về",
    "withdrawn": "Rút phiếu",
    "dispatched": "Điều phối",
    "paid": "Ghi nhận đã chi",
    "cancelled": "Hủy",
    #  ⚠️ Dạng NGUYÊN THỂ của cùng những hành động trên. Bảng quyền của hệ dùng
    #  `approve` / `cancel` (xem `core/permissions.ACTIONS`), nên controller viết
    #  sau quen tay ghi dấu vết bằng đúng chữ đó — Nghỉ phép và Đặt phòng đều
    #  vậy. Thiếu mấy dòng này thì dòng dấu vết hiện mã Anh trần
    #  («Dego Admin — approve: Duyệt phiếu PH004»), thấy được ngày 04/09/2026.
    #  Nhận CẢ HAI dạng thay vì đi sửa lời gọi: dữ liệu đã ghi bằng dạng nguyên
    #  thể vẫn nằm trong bảng, sửa mã nguồn không làm nó đọc được.
    "submit": "Gửi duyệt",
    "approve": "Duyệt",
    "reject": "Từ chối",
    "return": "Trả về",
    "withdraw": "Rút phiếu",
    "cancel": "Hủy",
    #  Hai hành động còn lại của bảng quyền. Chưa chỗ nào ghi dấu vết bằng chúng,
    #  nhưng `require(entity, "print")` là hợp lệ ở mọi endpoint nên chỉ cần một
    #  người thêm `record(..., "print")` là dòng đó hiện mã trần.
    "print": "In",
    "export": "Xuất dữ liệu",
    #  Bảng quyền gọi việc sửa là `write`, dấu vết cũ gọi là `update` — hai chữ
    #  cho một việc, và cả hai đều đang được ghi ở đâu đó.
    "write": "Cập nhật",
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
