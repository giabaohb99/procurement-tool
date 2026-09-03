"""API DANH MỤC NỀN của Nghỉ phép — loại nghỉ, bậc thâm niên, lịch ngày lễ.

Ba danh mục, ba khóa quyền khác nhau (`leave_type` và `holiday`; bậc thâm niên
đi theo `leave_type` vì nó là bảng con của loại nghỉ — tách khóa riêng cho một
bảng chỉ có bốn cột là đẻ thêm ô ma trận không ai hiểu).

Dựng bằng `make_crud_router` ở chỗ nào chuẩn CRUD, viết tay ở chỗ có chốt chặn
riêng. Hai chốt đáng kể:
  · KHÔNG xóa được loại nghỉ đang có đơn hoặc có quỹ — xóa là để lại dữ liệu mồ
    côi trỏ vào một `leave_type_id` không còn tồn tại;
  · KHÔNG sửa `code` của loại nghỉ — nó là mối nối sang giấy GNP đã phát hành.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.audit import record as audit_record
from app.core.auth import require
from app.core.crud import make_crud_router
from app.core.database import get_db
from app.core.response import success

from .balance_model import LeaveBalance
from .catalog_model import Holiday, LeaveType, LeaveTypeSeniority
from .request_model import LeaveRequest
from .schema import (HolidayCreate, HolidayResponse, HolidayUpdate,
                     LeaveTypeCreate, LeaveTypeResponse, LeaveTypeUpdate,
                     SeniorityTierCreate, SeniorityTierResponse,
                     SeniorityTierUpdate)


def _block_delete_used_type(db: Session, obj: LeaveType) -> None:
    """Chốt `before_delete` — xem đầu tệp về dữ liệu mồ côi."""
    if db.query(LeaveRequest).filter(LeaveRequest.leave_type_id == obj.id).count():
        raise HTTPException(
            400, f"«{obj.name}» đang có đơn nghỉ phép nên không xóa được. "
                 "Bỏ tick «Đang dùng» để ẩn khỏi ô chọn thay vì xóa.")
    if db.query(LeaveBalance).filter(LeaveBalance.leave_type_id == obj.id).count():
        raise HTTPException(
            400, f"«{obj.name}» đang có quỹ phép đã cấp nên không xóa được.")


def _block_code_change(db: Session, obj: LeaveType, values: dict) -> None:
    """Chốt `before_update` — `LeaveTypeUpdate` đã không có `code`, đây là lớp thứ hai.

    Hai lớp vì hai đường vào: schema chặn client gửi lên, còn hàm này chặn cả
    những chỗ gọi thẳng service sau này. Đổi mã là mọi giấy GNP đã phát hành trỏ
    vào một loại không còn tồn tại.
    """
    new_code = values.get("code")
    if new_code and new_code != obj.code:
        raise HTTPException(400, "Không đổi được «Mã loại nghỉ» sau khi đã tạo.")


leave_type_router = make_crud_router(
    "/api/leave-types", "leave_type", LeaveType,
    LeaveTypeCreate, LeaveTypeUpdate, LeaveTypeResponse,
    filterable=["code", "name", "is_active", "counts_balance", "gender"],
    unique_field="code",
    before_update=_block_code_change,
    before_delete=_block_delete_used_type,
)

holiday_router = make_crud_router(
    "/api/holidays", "holiday", Holiday,
    HolidayCreate, HolidayUpdate, HolidayResponse,
    filterable=["company_id", "name", "is_recurring", "is_active"],
    #  Lịch lễ KHÔNG có cột `code`. Bộ sinh dùng `unique_field` để báo trùng cho
    #  đẹp; ràng buộc thật là `uq_holiday_company_date` dưới CSDL, nên để `None`
    #  ở đây và để MySQL chặn — chứ khai bừa một cột không tồn tại thì nổ lúc
    #  chạy chứ không lúc nạp.
    unique_field=None,
)


# ── Bậc thâm niên: viết tay, vì nó luôn đọc/ghi theo LOẠI NGHỈ ─────────────────

seniority_router = APIRouter(prefix="/api/leave-seniority-tiers", tags=["leave"])

#  Gác bằng khóa của loại nghỉ — đây là bảng con của nó, xem đầu tệp.
ENTITY = "leave_type"


@seniority_router.get("")
def list_tiers(leave_type_id: int = Query(0, description="0 = mọi loại"),
               db: Session = Depends(get_db),
               user=Depends(require(ENTITY, "read"))):
    """Bậc thâm niên, thường hỏi theo một loại nghỉ. KHÔNG phân trang.

    Một loại nghỉ có tối đa vài bậc (5 năm, 10 năm, 20 năm) — phân trang một
    danh sách bốn dòng chỉ làm màn hình phải ghép lại.
    """
    query = db.query(LeaveTypeSeniority)
    if leave_type_id:
        query = query.filter(LeaveTypeSeniority.leave_type_id == leave_type_id)
    rows = query.order_by(LeaveTypeSeniority.leave_type_id,
                          LeaveTypeSeniority.years_from).all()
    return success({"total": len(rows),
                    "items": [SeniorityTierResponse.model_validate(r).model_dump()
                              for r in rows]})


def _check_tier(db: Session, leave_type_id: int, years_from: int, years_to: int,
                exclude_id: int = 0) -> None:
    """Khoảng phải hợp lệ và không CHỒNG lên bậc khác của cùng loại.

    Chồng nhau thì `seniority_days` lấy bậc cao nhất khớp được — vẫn ra một con
    số, nhưng không phải con số người khai định. Chặn ở cửa ghi rẻ hơn nhiều so
    với đi tìm vì sao một người được cộng nhầm ngày.
    """
    if db.get(LeaveType, leave_type_id) is None:
        raise HTTPException(400, "Loại nghỉ không tồn tại")
    if years_to and years_to <= years_from:
        raise HTTPException(400, "«Đến năm» phải lớn hơn «Từ năm» (để 0 nếu không có trần)")

    query = (db.query(LeaveTypeSeniority)
             .filter(LeaveTypeSeniority.leave_type_id == leave_type_id))
    if exclude_id:
        query = query.filter(LeaveTypeSeniority.id != exclude_id)
    for other in query.all():
        #  `years_to = 0` nghĩa là vô hạn — quy về một số đủ lớn để so khoảng.
        a_to = years_to or 9999
        b_to = other.years_to or 9999
        if years_from < b_to and other.years_from < a_to:
            raise HTTPException(
                400, f"Bậc này chồng lên bậc «từ {other.years_from} năm» đã khai.")


@seniority_router.post("")
def create_tier(data: SeniorityTierCreate, db: Session = Depends(get_db),
                user=Depends(require(ENTITY, "create"))):
    _check_tier(db, data.leave_type_id, data.years_from, data.years_to)
    obj = LeaveTypeSeniority(**data.model_dump(), created_by=user.id, updated_by=user.id)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    audit_record(db, user.id, ENTITY, obj.id, "create",
                 f"Thêm bậc thâm niên từ {obj.years_from} năm")
    return success(SeniorityTierResponse.model_validate(obj).model_dump(), "Đã thêm bậc")


@seniority_router.patch("/{tid}")
def update_tier(tid: int, data: SeniorityTierUpdate, db: Session = Depends(get_db),
                user=Depends(require(ENTITY, "write"))):
    obj = db.get(LeaveTypeSeniority, tid)
    if obj is None:
        raise HTTPException(404, "Không tìm thấy bậc thâm niên")
    values = data.model_dump(exclude_unset=True)
    _check_tier(db, obj.leave_type_id,
                values.get("years_from", obj.years_from),
                values.get("years_to", obj.years_to), exclude_id=obj.id)
    for key, value in values.items():
        setattr(obj, key, value)
    obj.updated_by = user.id
    db.commit()
    db.refresh(obj)
    return success(SeniorityTierResponse.model_validate(obj).model_dump(), "Đã cập nhật")


@seniority_router.delete("/{tid}")
def delete_tier(tid: int, db: Session = Depends(get_db),
                user=Depends(require(ENTITY, "delete"))):
    obj = db.get(LeaveTypeSeniority, tid)
    if obj is None:
        raise HTTPException(404, "Không tìm thấy bậc thâm niên")
    db.delete(obj)
    db.commit()
    audit_record(db, user.id, ENTITY, tid, "delete", "Xóa bậc thâm niên")
    return success(None, "Đã xóa bậc")
