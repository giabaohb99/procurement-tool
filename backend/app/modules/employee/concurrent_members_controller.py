"""API "Kiêm nhiệm tại phòng này" — `prefix=/api/employee-concurrents` (duoc-CR-755, giai đoạn 05).

Đặt đường RIÊNG (không lồng `/api/employees/...`) để khỏi đụng thứ tự route `/{eid}` của hồ sơ nhân sự.
Logic nằm ở `concurrent_members_service`; ở đây chỉ gác quyền + đọc tham số.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.auth import get_perm_profile, require
from app.core.database import get_db
from app.core.response import success

from . import concurrent_members_service

router = APIRouter(prefix="/api/employee-concurrents", tags=["employee"])


@router.get("")
def list_concurrent_members(
    department_id: int = Query(..., gt=0, description="Phòng ban cần xem người kiêm nhiệm"),
    company_id: int | None = Query(None, gt=0, description="Chỉ lấy kiêm nhiệm ở công ty này (phòng dùng chung)"),
    include_ended: int = Query(0, ge=0, le=1, description="1 = lấy cả dòng đã hết hạn"),
    db: Session = Depends(get_db), user=Depends(require("employee", "read")),
):
    """Người đang kiêm nhiệm ở một phòng ban (trang chi tiết phòng ban, bảng "Kiêm nhiệm tại phòng này").

    Quyền `employee.read`. Chỉ trả dòng mà phạm vi xem hồ sơ của người gọi phủ cặp (phòng, công ty) của
    dòng; nhân sự đã nghỉ việc và dòng đã hết hạn (trừ khi `include_ended=1`) không có. Mỗi dòng là bản
    tóm tắt: mã, họ tên, chức vụ kiêm nhiệm, ngày, trạng thái, công ty + phòng kiêm nhiệm, công ty + phòng
    chính, `counts_scope`, `can_open` (mở được hồ sơ đầy đủ hay chỉ xem tên) — không điện thoại, email,
    ngày sinh. Xếp theo họ tên; trần 200 dòng.
    """
    profile = get_perm_profile(db, user)
    cap = concurrent_members_service.MAX_ROWS
    items = concurrent_members_service.list_visible_members(
        db, user, profile, department_id=department_id, company_id=company_id,
        include_ended=bool(include_ended), limit=cap + 1)   # lấy dư 1 dòng để biết có bị cắt không
    return success({"items": items[:cap], "total": min(len(items), cap), "truncated": len(items) > cap})
