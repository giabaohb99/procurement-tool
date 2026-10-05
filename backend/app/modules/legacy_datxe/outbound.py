"""Chiều ERP -> app đặt xe cũ (P3, bao-CR-596). Bản dựng: doc/dong-bo-dat-xe-duyet-dau/p3-erp-sang-app-cu.md.

Tệp này làm hai việc, cố ý tách khỏi bộ nghe ORM (`outbound_listener.py`):

1. `build_payload` — dựng ẢNH CHỤP phiếu hiện tại theo đúng tên trường app cũ. Không đọc
   lịch sử thao tác, chỉ đọc trạng thái đang có: gửi lại bao nhiêu lần cũng ra cùng kết
   quả, tới lệch thứ tự cũng không hỏng.
2. `push_outbound` — gửi một phiếu: van chặn, bỏ qua khi không có gì đổi, ghi sổ, ký,
   gọi Worker, ghi ngược `legacy_id` cho phiếu ERP vừa được tạo bên app cũ.

Ánh xạ trạng thái là ĐÚNG BẢNG NGƯỢC của chiều nhận (`builder.*_FROM_LEGACY`), để một trạng
thái đi sang rồi đồng bộ về vẫn ra y như cũ — hai bảng chép tay là kiểu gì cũng có ngày lệch.
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timedelta, timezone

import requests
from sqlalchemy import func, select

from app.core import app_settings
from app.core.sync_signature import HEADER_SOURCE, sign_headers
from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.legacy_datxe.builder import (
    BOOKING_STATUS_FROM_LEGACY,
    DRIVER_STATUS_FROM_LEGACY,
    SEAL_STATUS_FROM_LEGACY,
    SELF_DRIVE_DRIVER_KEY,
)
from app.modules.legacy_datxe.mapping import (
    BRAND_TO_COMPANY_ID,
    DEPARTMENT_TO_ERP_ID,
    DRIVER_TO_ERP_ID,
    USER_MANUAL_MAP,
    VEHICLE_TO_ERP_ID,
)
from app.modules.seal_request.model import (
    SEAL_DRAFT,
    SealRequest,
    SealRequestCompany,
    SealType,
)
from app.modules.sync_log.constants import SyncAction, SyncDirection, SyncStatus
from app.modules.sync_log.model import SyncLog
from app.modules.sync_log.registry import SOURCE_DATXE, get_source
from app.modules.sync_log.service import (
    compute_hash,
    finish_failed,
    finish_ok,
    mark_running,
    open_entry,
    suppress_outbound,
)
from app.modules.user.model import User
from app.modules.vehicle_booking.model import (
    BK_DRAFT,
    DRV_REJECTED,
    TYPE_DELIVERY,
    Driver,
    Vehicle,
    VehicleBooking,
)

LOGGER = logging.getLogger(__name__)

#: Đường nhận bên Worker. KHÔNG có tiền tố `/api`: Worker phục vụ đường ở gốc tên miền
#: (`dev-api.degoholding.vn/v1/...`). Chữ ký ký kèm chuỗi này nên phải khớp từng ký tự.
OUTBOUND_PATH = "/v1/sync/erp-events"

#: Phiên bản hình dạng gói. Đổi hình dạng thì tăng số, bên nhận từ chối số lạ.
PAYLOAD_SCHEMA = 1

#: Van chặn (§14 bản vẽ): một phiếu sinh quá ngần này dòng sổ gửi đi trong một giờ thì
#: dừng gửi phiếu đó. Vòng lặp vô hạn là lỗi phá nhanh nhất — mỗi vòng đều ghi sổ.
VALVE_MAX_PER_HOUR = 20

#: Trần chờ Worker: (nối, đọc). Chạy trong Celery nên không có người đứng đợi, nhưng
#: vẫn phải có trần để một Worker treo không giữ chân tiến trình mãi.
HTTP_TIMEOUT = (5, 20)

MODEL = {"vehicle_booking": VehicleBooking, "seal_request": SealRequest}

BOOKING_STATUS_TO_LEGACY = {v: k for k, v in BOOKING_STATUS_FROM_LEGACY.items()}
SEAL_STATUS_TO_LEGACY = {v: k for k, v in SEAL_STATUS_FROM_LEGACY.items()}
DRIVER_STATUS_TO_LEGACY = {v: k for k, v in DRIVER_STATUS_FROM_LEGACY.items()}
DRIVER_STATUS_TO_LEGACY[DRV_REJECTED] = "rejected"   # chiều nhận không có, chiều gửi cần

#: Trạng thái app cũ -> kết cục duyệt (§15.1: chỉ đồng bộ KẾT CỤC, không đồng bộ chặng).
OUTCOME_OF_STATUS = {
    "pending_approval": "pending",
    "fully_approved": "approved",
    "dispatched": "approved",
    "completed": "approved",
    "rejected": "rejected",
    "needs_correction": "needs_correction",
    "canceled": "canceled",
}

#: Dòng ghi chú do CHIỀU NHẬN chèn vào (`[App cũ] ...`). Gửi ngược sang là app cũ nhận lại
#: chính chữ của nó kèm nhãn lạ, lần sau lại về ERP thêm một nhãn nữa.
_LEGACY_NOTE_LINE = re.compile(r"^\[App cũ\].*$", re.M)

VN_TZ = timezone(timedelta(hours=7))


# ---------------------------------------------------------------------------
# Công tắc
# ---------------------------------------------------------------------------

def is_outbound_enabled() -> bool:
    """Đủ điều kiện gửi chưa: cầu dao tổng + công tắc chiều gửi + địa chỉ + khóa."""
    source = get_source(SOURCE_DATXE)
    if source is None or not source.is_enabled():
        return False
    if not app_settings.get("sync_datxe_outbound_enabled"):
        return False
    if not (app_settings.get("sync_legacy_api_base") or "").strip():
        return False
    return bool(source.secret())


# ---------------------------------------------------------------------------
# Đổi giờ
# ---------------------------------------------------------------------------

def _parse_iso(text: str) -> datetime | None:
    text = (text or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def _ms_from_utc_text(text: str) -> int:
    """Mốc do MÁY CHỦ đóng (`approved_at`, `dispatched_at`, `actual_*`…) — lưu theo UTC."""
    dt = _parse_iso(text)
    if dt is None:
        return 0
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def _ms_from_local_text(text: str) -> int:
    """`start_time`/`end_time` — giờ NGƯỜI DÙNG gõ, ERP giữ giờ Việt Nam."""
    dt = _parse_iso(text)
    if dt is None:
        return 0
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=VN_TZ)
    return int(dt.timestamp() * 1000)


def _ms_from_dt(value) -> int:
    """Cột `DateTime` của `AuditMixin` — UTC không múi."""
    if not value:
        return 0
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return int(value.timestamp() * 1000)


# ---------------------------------------------------------------------------
# Tra ngược khóa app cũ
# ---------------------------------------------------------------------------

def _reverse(table: dict[str, int]) -> dict[int, str]:
    """{id ERP: khóa app cũ}. Nhiều khóa trỏ một id thì giữ khóa ĐẦU TIÊN khai trong bảng."""
    out: dict[int, str] = {}
    for key, erp_id in table.items():
        out.setdefault(int(erp_id), key)
    return out


_COMPANY_KEY = _reverse(BRAND_TO_COMPANY_ID)
_DEPARTMENT_KEY = _reverse(DEPARTMENT_TO_ERP_ID)
_VEHICLE_KEY = _reverse(VEHICLE_TO_ERP_ID)
_DRIVER_KEY = _reverse(DRIVER_TO_ERP_ID)
_EMPLOYEE_UID = _reverse(USER_MANUAL_MAP)


def _key_of(db, model, row_id, fallback: dict[int, str]) -> str:
    """Cột `legacy_id` trước, bảng gán tay sau — chiều nhận tra theo đúng hai nguồn đó."""
    if not row_id:
        return ""
    row = db.get(model, int(row_id))
    if row is not None and (getattr(row, "legacy_id", "") or ""):
        return row.legacy_id
    return fallback.get(int(row_id), "")


class _People:
    """Tài khoản ERP -> (tên, email, UID app cũ). Nhớ trong một lượt dựng."""

    def __init__(self, db):
        self.db = db
        self._cache: dict[int, dict] = {}

    def of_user(self, user_id) -> dict:
        user_id = int(user_id or 0)
        if user_id in self._cache:
            return self._cache[user_id]
        info = {"uid": "", "name": "", "email": ""}
        user = self.db.get(User, user_id) if user_id else None
        if user is not None:
            info["email"] = user.email or ""
            emp = self.db.get(Employee, user.employee_id) if user.employee_id else None
            if emp is not None:
                info["name"] = emp.full_name or ""
                info["uid"] = (emp.legacy_id or "") or _EMPLOYEE_UID.get(emp.id, "")
                info["email"] = info["email"] or (emp.email or "")
        self._cache[user_id] = info
        return info


# ---------------------------------------------------------------------------
# Dựng ảnh chụp
# ---------------------------------------------------------------------------

def _clean_note(note: str) -> str:
    return _LEGACY_NOTE_LINE.sub("", note or "").strip()


def _stops_of(row: VehicleBooking) -> list[dict]:
    try:
        stops = json.loads(row.stops or "[]")
    except (TypeError, ValueError):
        return []
    out = []
    for stop in stops if isinstance(stops, list) else []:
        if not isinstance(stop, dict) or not (stop.get("location") or "").strip():
            continue
        out.append({"address": stop.get("location", "").strip(),
                    "contactName": (stop.get("contact_name") or "").strip(),
                    "contactPhone": (stop.get("contact_phone") or "").strip(),
                    "notes": (stop.get("notes") or "").strip()})
    return out


def _approval_block(status_text: str, row, people: _People) -> dict:
    """Kết cục duyệt kèm người ký. Duyệt thì lấy người duyệt; kết cục khác lấy người sửa cuối."""
    outcome = OUTCOME_OF_STATUS.get(status_text, "pending")
    if outcome == "approved" and row.approved_by:
        who, at = people.of_user(row.approved_by), _ms_from_utc_text(row.approved_at)
    else:
        who, at = people.of_user(row.updated_by), _ms_from_dt(row.updated_at)
    return {"outcome": outcome, "by_name": who["name"], "by_email": who["email"],
            "by_uid": who["uid"], "at": at}


def _booking_data(db, row: VehicleBooking, people: _People) -> dict:
    is_delivery = row.request_type == TYPE_DELIVERY
    status_text = BOOKING_STATUS_TO_LEGACY.get(row.status, "pending_approval")
    company_key = _key_of(db, Company, row.company_id, _COMPANY_KEY)
    details = {
        "purpose": row.purpose or "",
        "startTime": _ms_from_local_text(row.start_time),
        "endTime": _ms_from_local_text(row.end_time),
        "intermediateStops": _stops_of(row),
        "notes": _clean_note(row.note),
        "brandId": [company_key] if company_key else [],
        "firstApproverUid": people.of_user(row.first_approver_id)["uid"],
    }
    if is_delivery:
        details.update({
            "pickupLocation": row.start_location or "",
            "dropoffLocation": row.end_location or "",
            "itemName": row.goods_name or "",
            "dimensions": row.goods_size or "",
            "senderName": row.sender_name or "",
            "senderPhone": row.sender_phone or "",
            "recipientName": row.receiver_name or "",
            "recipientPhone": row.receiver_phone or "",
            "specialInstructions": row.special_instructions or "",
        })
    else:
        details.update({
            "startLocation": row.start_location or "",
            "endLocation": row.end_location or "",
            "passengerCount": int(row.passenger_count or 0),
            "attendees": row.attendees or "",
            "contactPhone": row.contact_phone or "",
            "isRoundTrip": bool(row.is_round_trip),
        })

    vehicle = db.get(Vehicle, row.assigned_vehicle_id) if row.assigned_vehicle_id else None
    driver = db.get(Driver, row.assigned_driver_id) if row.assigned_driver_id else None
    driver_key = (SELF_DRIVE_DRIVER_KEY if row.is_self_drive
                  else _key_of(db, Driver, row.assigned_driver_id, _DRIVER_KEY))
    dispatcher = people.of_user(row.dispatched_by)
    dispatch = {
        "assignedVehicleId": _key_of(db, Vehicle, row.assigned_vehicle_id, _VEHICLE_KEY),
        "assignedDriverId": driver_key,
        #  Kèm CHỮ để app cũ vẫn hiển thị được khi xe / tài xế không có khóa bên đó.
        "vehicle": ({"license_plate": vehicle.license_plate or "", "model": vehicle.model or "",
                     "type": vehicle.type or ""} if vehicle is not None else {}),
        "driver": ({"name": driver.name or "", "phone": driver.phone or ""}
                   if driver is not None else {}),
        "dispatchedAt": _ms_from_utc_text(row.dispatched_at),
        "dispatchedBy": dispatcher["uid"],
        "dispatchedByName": dispatcher["name"],
        "driverStatus": DRIVER_STATUS_TO_LEGACY.get(row.driver_status, ""),
        "actualStartTime": _ms_from_utc_text(row.actual_start_time),
        "actualEndTime": _ms_from_utc_text(row.actual_end_time),
        "distanceKm": float(row.distance_km or 0),
        "cost": int(row.cost or 0),
    }
    return {
        "type": "DELIVERY" if is_delivery else "CAR_BOOKING",
        "status": status_text,
        "details": details,
        "dispatch": dispatch,
        "approval": _approval_block(status_text, row, people),
        "seal": {},
    }


def _seal_data(db, row: SealRequest, people: _People) -> dict:
    status_text = SEAL_STATUS_TO_LEGACY.get(row.status, "pending_approval")
    company_ids = [c for (c,) in db.execute(
        select(SealRequestCompany.company_id)
        .where(SealRequestCompany.seal_request_id == row.id)
        .order_by(SealRequestCompany.id))] or ([row.company_id] if row.company_id else [])
    brand_keys = [k for k in (_key_of(db, Company, cid, _COMPANY_KEY) for cid in company_ids) if k]
    seal_type = db.get(SealType, row.seal_type_id) if row.seal_type_id else None
    clerk = people.of_user(row.completed_by)
    details = {
        "purpose": row.purpose or "",
        #  App cũ không cho chọn loại con dấu: ô này là NHÃN gõ cứng ("Phê duyệt dấu"),
        #  không phải khóa — xem `builder.LEGACY_SEAL_TYPE_NAME`.
        "sealTypeId": (seal_type.name if seal_type is not None else ""),
        "title": row.title or "",
        "attachedFileIds": [],
        "departmentId": _key_of(db, Department, row.department_id, _DEPARTMENT_KEY),
        "brandId": brand_keys,
        "firstApproverUid": people.of_user(row.first_approver_id)["uid"],
        "notes": _clean_note(row.note),
    }
    return {
        "type": "SEAL_REQUEST",
        "status": status_text,
        "details": details,
        "dispatch": {},
        "approval": _approval_block(status_text, row, people),
        "seal": {"completed_at": _ms_from_utc_text(row.completed_at),
                 "completed_by_name": clerk["name"]},
    }


def build_payload(db, entity: str, row) -> dict:
    """Ảnh chụp đầy đủ của một phiếu, đúng hợp đồng `schema: 1` (p3-erp-sang-app-cu.md §4)."""
    people = _People(db)
    data = (_booking_data(db, row, people) if entity == "vehicle_booking"
            else _seal_data(db, row, people))
    requester = people.of_user(row.requester_id or row.created_by)
    data.update({
        "created_by_uid": requester["uid"],
        "created_at": _ms_from_dt(row.created_at),
        "requester": {"name": row.requester or requester["name"],
                      "email": row.requester_email or requester["email"],
                      "phone": row.requester_phone or ""},
    })
    return {
        "schema": PAYLOAD_SCHEMA,
        "entity": entity,
        "erp_id": int(row.id),
        "erp_code": row.code or "",
        "legacy_id": row.legacy_id or "",
        "occurred_at": _ms_from_dt(row.updated_at) or _ms_from_dt(row.created_at),
        "data": data,
    }


# ---------------------------------------------------------------------------
# Gửi
# ---------------------------------------------------------------------------

def _is_sendable(row, entity: str) -> bool:
    """Nháp không gửi (app cũ không có nháp); phiếu đã xóa mềm cũng không."""
    if row is None or getattr(row, "is_deleted", False):
        return False
    draft = BK_DRAFT if entity == "vehicle_booking" else SEAL_DRAFT
    return row.status != draft


def _recent_count(db, entity: str, local_id: int) -> int:
    since = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=1)
    return db.execute(
        select(func.count(SyncLog.id)).where(
            SyncLog.source == SOURCE_DATXE,
            SyncLog.direction == int(SyncDirection.OUTBOUND),
            SyncLog.entity == entity,
            SyncLog.local_id == local_id,
            SyncLog.created_at >= since,
        )
    ).scalar() or 0


def last_sent_hash(db, entity: str, local_id: int) -> str:
    """Băm của lần gửi THÀNH CÔNG gần nhất — trùng thì không có gì phải gửi."""
    return db.execute(
        select(SyncLog.content_hash).where(
            SyncLog.source == SOURCE_DATXE,
            SyncLog.direction == int(SyncDirection.OUTBOUND),
            SyncLog.entity == entity,
            SyncLog.local_id == local_id,
            SyncLog.status == int(SyncStatus.SUCCESS),
        ).order_by(SyncLog.id.desc()).limit(1)
    ).scalar_one_or_none() or ""


def _content_hash(payload: dict) -> str:
    """Băm phần NGHIỆP VỤ: bỏ `occurred_at` (mốc sửa cuối đổi cả khi chỉ đổi `updated_by`)."""
    return compute_hash({"legacy_id": payload["legacy_id"], "data": payload["data"]})


def _post(body: str) -> requests.Response:
    base = (app_settings.get("sync_legacy_api_base") or "").rstrip("/")
    headers = sign_headers(SOURCE_DATXE, OUTBOUND_PATH, body)
    #  Chữ ký không ký tên nguồn, nên đổi nhãn này không làm hỏng chữ ký. Bên nhận đọc nó
    #  để biết gói đến từ ERP (§5.2 bản vẽ).
    headers[HEADER_SOURCE] = "erp"
    headers["Content-Type"] = "application/json"
    return requests.post(f"{base}{OUTBOUND_PATH}", data=body.encode("utf-8"),
                         headers=headers, timeout=HTTP_TIMEOUT)


def push_outbound(db, entity: str, local_id: int, *, user_id: int = 0,
                  force: bool = False, check_switch: bool = True, poster=None) -> dict:
    """Gửi MỘT phiếu sang app cũ. Trả `{status, ...}` để vòng gọi đếm.

    `force` bỏ qua phép so băm (nút gửi lại tay) nhưng KHÔNG bỏ qua công tắc: công tắc tắt
    là khóa cứng (đại ca chốt 05/10/2026). `check_switch` / `poster` chỉ để bài kiểm chạy
    không cần cấu hình và không cần mạng.
    """
    if entity not in MODEL:
        return {"status": "bad_entity"}
    if check_switch and not is_outbound_enabled():
        return {"status": "off"}
    row = db.get(MODEL[entity], int(local_id))
    if not _is_sendable(row, entity):
        return {"status": "not_sendable"}

    payload = build_payload(db, entity, row)
    content_hash = _content_hash(payload)
    if not force and last_sent_hash(db, entity, row.id) == content_hash:
        return {"status": "unchanged"}

    action = SyncAction.UPDATE if row.legacy_id else SyncAction.CREATE
    over_valve = _recent_count(db, entity, row.id) >= VALVE_MAX_PER_HOUR
    entry = open_entry(db, source=SOURCE_DATXE, entity=entity,
                       direction=int(SyncDirection.OUTBOUND), action=int(action),
                       legacy_id=row.legacy_id or "", local_id=row.id,
                       payload=payload, content_hash=content_hash, user_id=user_id)
    if entry is None:
        return {"status": "duplicate"}
    payload["event_id"] = entry.event_id
    if over_valve:
        finish_failed(db, entry, f"Van chặn: quá {VALVE_MAX_PER_HOUR} lần gửi trong một giờ — "
                                 "nghi vòng lặp, dừng gửi phiếu này")
        LOGGER.warning("datxe outbound: van chặn %s#%s", entity, row.id)
        return {"status": "valve"}

    mark_running(db, entry)
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    try:
        response = (poster or _post)(body)
    except Exception as exc:  # noqa: BLE001 — mạng hỏng là chuyện thường, ghi sổ rồi để vòng sau gửi lại
        finish_failed(db, entry, f"Không gọi được app cũ: {str(exc)[:400]}")
        return {"status": "failed"}

    text = (getattr(response, "text", "") or "")[:500]
    if not 200 <= int(getattr(response, "status_code", 0)) < 300:
        finish_failed(db, entry, f"HTTP {response.status_code} {text}".strip())
        return {"status": "failed", "http": response.status_code}

    try:
        data = (response.json() or {}).get("data") or {}
    except ValueError:
        data = {}
    new_key = str(data.get("legacy_id") or "").strip()[:64]
    if new_key and not row.legacy_id:
        #  Phiếu ERP vừa được TẠO bên app cũ. Ghi khóa trong `suppress_outbound` để chính cú
        #  ghi này không đẻ thêm một lượt gửi.
        with suppress_outbound():
            row.legacy_id = new_key
            db.commit()
        entry.legacy_id = new_key
    finish_ok(db, entry, text or "Đã gửi", local_id=row.id)
    return {"status": "sent", "legacy_id": row.legacy_id or ""}
