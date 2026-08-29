"""Nghiệp vụ Đặt xe nội bộ (DEGO Booking Auto) — MVP lát dọc.

Đợt này khép phần tạo & theo dõi phiếu của người dùng: tạo phiếu 2 loại (công tác /
giao hàng), lưu nháp hoặc gửi duyệt, danh sách "Yêu cầu của tôi" (đã bó phạm vi ở
controller), xem chi tiết, sửa khi còn nháp / bị trả về. Điều phối & tài xế ở đợt sau.
"""

import json

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.utils import generate_code
from app.modules.employee.model import Employee

from .model import (
    BK_DRAFT,
    BK_PENDING,
    EDITABLE_STATUSES,
    TYPE_CAR,
    TYPE_DELIVERY,
    VehicleBooking,
)
from .schema import VehicleBookingCreate, VehicleBookingUpdate

# Bộ lọc cho danh sách (whitelist của apply_filters). Cột số (status/request_type/…) tự
# so khớp chính xác; `code` để ô tìm nhanh lo nên KHÔNG đưa vào đây (xem apply_filters).
FILTERABLE = ["status", "request_type", "company_id", "department_id", "requester_id"]

# Ô "Tìm nhanh" trên danh sách quét các trường này.
SEARCH_FIELDS = ("code", "purpose", "requester", "start_location", "end_location")


def apply_keyword_search(query, keyword: str | None):
    """Lọc OR LIKE theo từ khóa trên nhiều trường. Bỏ trống thì giữ nguyên."""
    kw = (keyword or "").strip()
    if not kw:
        return query
    like = f"%{kw}%"
    return query.filter(or_(*[getattr(VehicleBooking, f).like(like) for f in SEARCH_FIELDS]))


def _requester_context(db: Session, user) -> tuple[str, int, int]:
    """Suy ra (tên hiển thị, phòng ban, công ty) của người tạo từ hồ sơ nhân sự.

    Snapshot lúc tạo để phiếu vẫn đúng dù hồ sơ đổi sau. Không có hồ sơ nhân sự thì
    lấy email làm tên, phạm vi để 0.
    """
    emp = None
    if getattr(user, "employee_id", 0):
        emp = db.get(Employee, user.employee_id)
    name = (emp.full_name if emp and emp.full_name else "") or getattr(user, "email", "") or ""
    dept_id = emp.department_id if emp else 0
    company_id = emp.company_id if emp else 0
    return name, dept_id or 0, company_id or 0


def _normalize_type(value: int | None) -> int:
    """Chỉ nhận 1 (công tác) hoặc 2 (giao hàng); lạ thì về công tác."""
    return TYPE_DELIVERY if value == TYPE_DELIVERY else TYPE_CAR


def _dump_stops(stops) -> str:
    """StopItem[] → chuỗi JSON, bỏ điểm dừng KHÔNG có địa điểm, giữ thứ tự.

    Mỗi điểm giữ cả tên + SĐT người liên hệ tại điểm đó.
    """
    out = []
    for s in stops or []:
        location = (s.location or "").strip()
        if not location:
            continue
        out.append({
            "location": location,
            "contact_name": (s.contact_name or "").strip(),
            "contact_phone": (s.contact_phone or "").strip(),
        })
    return json.dumps(out, ensure_ascii=False)


def create_booking(db: Session, data: VehicleBookingCreate, user, submit: bool) -> VehicleBooking:
    """Tạo phiếu đặt xe. `submit=True` → gửi duyệt ngay (Chờ duyệt); ngược lại lưu Nháp.

    Phạm vi (phòng ban / công ty) auto-fill từ hồ sơ người tạo khi client bỏ trống, để
    `apply_scope` lọc đúng theo pháp nhân/bộ phận. Điểm dừng lưu chuỗi JSON, giữ thứ tự.
    """
    if not (data.purpose or "").strip():
        raise HTTPException(400, "Mục đích không được để trống")

    req_type = _normalize_type(data.request_type)
    name, dept_id, company_id = _requester_context(db, user)

    booking = VehicleBooking(
        request_type=req_type,
        purpose=data.purpose.strip(),
        start_location=data.start_location or "",
        end_location=data.end_location or "",
        stops=_dump_stops(data.stops),
        start_time=data.start_time or "",
        end_time=data.end_time or "",
        # Khối riêng đặt xe công tác
        passenger_count=data.passenger_count or 1,
        attendees=data.attendees or "",
        contact_phone=data.contact_phone or "",
        is_round_trip=bool(data.is_round_trip),
        # Khối riêng giao hàng
        goods_name=data.goods_name or "",
        goods_size=data.goods_size or "",
        sender_name=data.sender_name or "",
        sender_phone=data.sender_phone or "",
        receiver_name=data.receiver_name or "",
        receiver_phone=data.receiver_phone or "",
        special_instructions=data.special_instructions or "",
        # Người tạo + phạm vi
        requester=name,
        requester_id=getattr(user, "id", 0),
        department_id=data.department_id or dept_id,
        company_id=data.company_id or company_id,
        first_approver_id=data.first_approver_id or 0,
        status=BK_PENDING if submit else BK_DRAFT,
        note=data.note or "",
        created_by=getattr(user, "id", 0),
        updated_by=getattr(user, "id", 0),
    )
    db.add(booking)
    db.flush()  # có id để sinh mã
    booking.code = generate_code(db, VehicleBooking, "DX")
    db.commit()
    db.refresh(booking)
    return booking


def update_booking(db: Session, booking: VehicleBooking, data: VehicleBookingUpdate,
                   user, submit: bool) -> VehicleBooking:
    """Sửa phiếu — CHỈ khi còn Nháp hoặc bị trả về (A07). Sau khi vào luồng thì khóa.

    `submit=True` chuyển tiếp sang Chờ duyệt sau khi lưu.
    """
    if booking.status not in EDITABLE_STATUSES:
        raise HTTPException(400, "Phiếu đã vào luồng duyệt/điều phối — không sửa được nữa")

    patch = data.model_dump(exclude_unset=True)
    if "request_type" in patch:
        booking.request_type = _normalize_type(patch.pop("request_type"))
    if "stops" in patch:
        patch.pop("stops")  # dump từ đối tượng StopItem đã validate, không từ dict thô
        booking.stops = _dump_stops(data.stops or [])
    for field, value in patch.items():
        setattr(booking, field, value)

    if submit:
        booking.status = BK_PENDING
    booking.updated_by = getattr(user, "id", 0)
    db.commit()
    db.refresh(booking)
    return booking
