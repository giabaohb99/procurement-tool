"""API "Kiêm nhiệm tại phòng / công ty này" — `prefix=/api/employee-concurrents` (duoc-CR-755, giai đoạn 05).

Đặt đường RIÊNG (không lồng `/api/employees/...`) để khỏi đụng thứ tự route `/{eid}` của hồ sơ nhân sự.
Logic nằm ở `concurrent_members_service`; ở đây chỉ gác quyền + đọc tham số.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.auth import get_perm_profile, require
from app.core.database import get_db
from app.core.response import success

from . import concurrent_members_service

router = APIRouter(prefix="/api/employee-concurrents", tags=["employee"])


@router.get("")
def list_concurrent_members(
    department_id: int | None = Query(None, gt=0, description="Phòng ban cần xem người kiêm nhiệm (loại Phòng ban)"),
    company_id: int | None = Query(None, gt=0, description="Công ty cần xem người kiêm nhiệm (trang công ty, hoặc "
                                                          "thu hẹp phòng dùng chung)"),
    kind: int | None = Query(None, ge=1, le=2, description="1 = loại Phòng ban, 2 = loại Công ty; bỏ trống = cả hai"),
    include_ended: int = Query(0, ge=0, le=1, description="1 = lấy cả dòng đã hết hạn"),
    db: Session = Depends(get_db), user=Depends(require("employee", "read")),
):
    """Người đang kiêm nhiệm ở một phòng ban hoặc một công ty (bảng "Kiêm nhiệm" của trang phòng ban và trang công ty).

    Quyền `employee.read`. Cần ít nhất một trong `department_id` / `company_id` (thiếu cả hai: 422). `kind=1`
    chỉ dòng loại Phòng ban, `kind=2` chỉ dòng loại Công ty (kiêm nhiệm cả công ty, `department_id = 0`). Chỉ trả dòng
    mà phạm vi xem hồ sơ của người gọi phủ "chỗ ngồi" của dòng (loại Phòng ban: phòng của dòng ở công ty chính; loại
    Công ty B: các phòng của người đó ở B); nhân sự đã nghỉ việc và dòng đã hết hạn (trừ khi `include_ended=1`) không
    có. Mỗi dòng là bản tóm tắt: mã, họ tên, loại (`kind`, `kind_label`), chức vụ kiêm nhiệm, ngày, trạng thái, công ty
    + phòng kiêm nhiệm, công ty + phòng chính, `counts_scope`, `can_open` (mở được hồ sơ đầy đủ hay chỉ xem tên) —
    không điện thoại, email, ngày sinh. Xếp theo họ tên; trần 200 dòng.
    """
    if department_id is None and company_id is None:
        raise HTTPException(422, "Cần truyền phòng ban (department_id) hoặc công ty (company_id) cần xem")
    profile = get_perm_profile(db, user)
    cap = concurrent_members_service.MAX_ROWS
    items = concurrent_members_service.list_visible_members(
        db, user, profile, department_id=department_id, company_id=company_id, kind=kind,
        include_ended=bool(include_ended), limit=cap + 1)   # lấy dư 1 dòng để biết có bị cắt không
    return success({"items": items[:cap], "total": min(len(items), cap), "truncated": len(items) > cap})
