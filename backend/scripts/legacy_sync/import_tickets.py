"""Nạp 1313 phiếu app đặt xe cũ vào ERP.

    946 SEAL_REQUEST -> tab_seal_request
    321 CAR_BOOKING  -> tab_vehicle_booking (request_type = TYPE_CAR)
     46 DELIVERY     -> tab_vehicle_booking (request_type = TYPE_DELIVERY)

CHẠY ĐƯỢC NHIỀU LẦN: tra `legacy_id` trước, đã có thì bỏ qua, không tạo bản thứ
hai. Mặc định chỉ xem trước, `--apply` mới ghi.

    python -m scripts.legacy_sync.import_tickets --export /tmp/fb-export.json
    python -m scripts.legacy_sync.import_tickets --export /tmp/fb-export.json --apply

MÃ PHIẾU — đại ca chốt 16/09/2026: "prefix + 000 + id, ví dụ DD000789, còn đặt
xe là DX000789". Nên mã sinh sau khi `flush()` vì lúc đó mới có id. Lưu ý mã này
KHÁC nếp ERP đang tự sinh (`DD001` ba chữ số, xem `_next_seal_code`): sáu chữ số
không bao giờ đụng ba chữ số, và bộ sinh của ERP đọc `DD(\\d+)` nên vẫn chạy tiếp
đúng sau khi nạp — nhưng nhìn bảng sẽ thấy hai dạng mã, đó là cố ý để phân biệt
phiếu nhập từ app cũ với phiếu ERP tự tạo.

HAI ĐỒNG HỒ TRONG CÙNG MỘT HÀNG — không phải lỗi, là chép đúng nếp ERP:

- `created_at` và mọi mốc do MÁY CHỦ đóng (`approved_at`, `completed_at`,
  `dispatched_at`, `actual_*`) ghi theo **UTC**, vì container ERP chạy UTC và
  `service._now()` lấy `datetime.now()` của container.
- `start_time` / `end_time` là giờ NGƯỜI DÙNG gõ trên trình duyệt nên ERP đang
  giữ **giờ Việt Nam (+7)**. Nạp theo UTC thì phiếu cũ hiện lệch 7 tiếng so với
  phiếu ERP tạo cùng màn hình.

NHỮNG THỨ BỘ NẠP NÀY CỐ Ý KHÔNG LÀM (việc riêng, đừng tưởng là sót):

- KHÔNG nạp lịch sử duyệt. 5095 dòng `approval.history` đi theo §P1.1 của
  TIEN-DO.md, vào `tab_approval_instance` + `tab_approval_action`, và phải chạy
  SAU bước này vì `ApprovalInstance.entity_id` trỏ vào chính phiếu ERP.
- KHÔNG nạp tệp đính kèm. Cả 946 phiếu dấu đều có `attachedFileIds`; tệp nằm ở
  nhánh `files` bên Firebase, dời tệp là một việc riêng.
- KHÔNG mở phiên duyệt thật cho 34 phiếu còn `pending_approval`.
"""

import argparse
import collections
import json
import re
import sys
from datetime import datetime, timedelta, timezone

from sqlalchemy import String, inspect as sa_inspect, select

import app.core.all_models  # noqa: F401  nạp đủ model để SQLAlchemy dựng xong quan hệ
from app.core.database import SessionLocal
from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.seal_request.model import (
    SEAL_APPROVED,
    SEAL_CANCELLED,
    SEAL_COMPLETED,
    SEAL_PENDING,
    SEAL_REJECTED,
    SEAL_RETURNED,
    SealRequest,
    SealRequestCompany,
    SealType,
)
from app.modules.user.model import User
from app.modules.vehicle_booking.model import (
    BK_APPROVED,
    BK_CANCELLED,
    BK_COMPLETED,
    BK_DISPATCHED,
    BK_PENDING,
    BK_REJECTED,
    BK_RETURNED,
    DRV_ACCEPTED,
    DRV_COMPLETED,
    DRV_NONE,
    DRV_ONGOING,
    DRV_WAITING,
    TYPE_CAR,
    TYPE_DELIVERY,
    Driver,
    Vehicle,
    VehicleBooking,
)
from scripts.legacy_sync.mapping import (
    BRAND_TO_COMPANY_ID,
    DEPARTMENT_TO_ERP_ID,
    DRIVER_TO_ERP_ID,
    USER_MANUAL_MAP,
    VEHICLE_TO_ERP_ID,
)

SYSTEM_ACTOR_ID = 0

#  Giờ Việt Nam. Không có quy ước giờ mùa hè nên một hằng số cố định là đủ.
VN_OFFSET = timezone(timedelta(hours=7))

#  Bên app cũ "Tự lái" là một HỒ SƠ TÀI XẾ; bên ERP nó là cờ `is_self_drive`.
#  Phiếu gán đúng tài xế này nghĩa là người yêu cầu tự cầm lái.
SELF_DRIVE_DRIVER_KEY = "vRKAfizJgj_fdJFkSLWrL"

#  Tên loại con dấu gom chung. Cả 946 phiếu bên app cũ mang đúng một giá trị
#  `sealTypeId` là chuỗi "Phê duyệt dấu" (không phải khóa, là nhãn gõ cứng), và
#  `tab_seal_type` bên ERP đang TRỐNG. Đại ca chốt 16/09: gom hết về một loại,
#  tạo trước rồi gắn sau. Giữ nguyên chữ của app cũ để còn lần ngược được.
LEGACY_SEAL_TYPE_NAME = "Phê duyệt dấu"
LEGACY_SEAL_TYPE_DESC = ("Gom từ app đặt xe cũ — toàn bộ phiếu bên đó dùng chung "
                         "một loại này, app cũ không cho chọn loại con dấu")

SEAL_STATUS_FROM_LEGACY = {
    "completed": SEAL_COMPLETED,
    "fully_approved": SEAL_APPROVED,    # duyệt xong, chờ Văn thư đóng dấu
    "pending_approval": SEAL_PENDING,
    "rejected": SEAL_REJECTED,
    "canceled": SEAL_CANCELLED,
    "needs_correction": SEAL_RETURNED,
}

BOOKING_STATUS_FROM_LEGACY = {
    "completed": BK_COMPLETED,
    "dispatched": BK_DISPATCHED,
    "fully_approved": BK_APPROVED,      # duyệt xong, chờ điều phối
    "pending_approval": BK_PENDING,
    "rejected": BK_REJECTED,
    "canceled": BK_CANCELLED,
    "needs_correction": BK_RETURNED,
}

DRIVER_STATUS_FROM_LEGACY = {
    "completed": DRV_COMPLETED,
    "on_trip": DRV_ONGOING,
    "accepted": DRV_ACCEPTED,
    "pending_acceptance": DRV_WAITING,
}


# ---------------------------------------------------------------------------
# Đổi mốc thời gian
# ---------------------------------------------------------------------------

def _utc_dt(ms) -> datetime | None:
    """Mốc epoch (ms) -> `datetime` KHÔNG múi giờ, theo UTC.

    Dùng cho cột `DateTime` và cho mốc do máy chủ đóng — xem ghi chú "hai đồng
    hồ" ở đầu tệp.
    """
    if not ms:
        return None
    return datetime.fromtimestamp(int(ms) / 1000, tz=timezone.utc).replace(tzinfo=None)


def _utc_iso(ms) -> str:
    """Mốc epoch (ms) -> chuỗi ISO phút theo UTC, khớp `service._now()`."""
    dt = _utc_dt(ms)
    return dt.isoformat(timespec="minutes") if dt else ""


def _local_iso(ms) -> str:
    """Mốc epoch (ms) -> chuỗi ISO phút theo GIỜ VIỆT NAM.

    Chỉ dùng cho `start_time` / `end_time`: đó là giờ người dùng gõ, ERP đang
    lưu nguyên văn chuỗi trình duyệt gửi lên nên nó là giờ địa phương.
    """
    if not ms:
        return ""
    return (datetime.fromtimestamp(int(ms) / 1000, tz=VN_OFFSET)
            .replace(tzinfo=None).isoformat(timespec="minutes"))


# ---------------------------------------------------------------------------
# Tra danh mục (công ty / phòng ban)
# ---------------------------------------------------------------------------

def legacy_index(db, model) -> dict[str, int]:
    """`{khóa app cũ: id ERP}` đọc thẳng từ cột `legacy_id` dưới DB."""
    return {row.legacy_id: row.id
            for row in db.execute(select(model).where(model.legacy_id != "")).scalars()}


def check_against_hand_table(title: str, from_db: dict[str, int],
                             hand: dict[str, int]) -> bool:
    """Đối chiếu bảng tra khai tay với dấu `legacy_id` dưới DB.

    DB là nguồn dùng để nạp, KHÔNG phải bảng tay — vì `sync_master_data` còn
    TẠO THÊM hàng ERP cho những khóa app cũ chưa có bên này rồi đóng dấu cho
    chúng, và những hàng đó không bao giờ có mặt trong bảng tay. Riêng phòng
    ban: bảng tay có 14 dòng, dưới DB có 22 dấu — đọc mỗi bảng tay thì 92 phiếu
    dấu rơi mất phòng ban và lặng lẽ lùi về phòng của người tạo.

    Bảng tay vẫn giữ vai trò cái chốt: nó là hồ sơ của những cặp do NGƯỜI chốt
    (bốn phòng gộp tay), nên hai bên nói khác nhau là có chuyện, phải dừng.
    """
    ok = True
    for key, hand_id in hand.items():
        db_id = from_db.get(key)
        if db_id is None:
            print(f"  LOI    {title}: bang tay co {key!r} -> {hand_id} ma duoi DB "
                  f"khong hang nao mang dau do")
            ok = False
        elif db_id != hand_id:
            print(f"  LOI    {title}: {key!r} bang tay tro {hand_id}, duoi DB "
                  f"la {db_id}")
            ok = False
    thua = set(from_db) - set(hand)
    if thua:
        print(f"  ghi chu {title}: {len(thua)} khoa chi co duoi DB (do "
              f"sync_master_data tao them), van dung binh thuong")
    return ok


# ---------------------------------------------------------------------------
# Tra người
# ---------------------------------------------------------------------------

class PeopleResolver:
    """UID Firebase -> hồ sơ nhân sự ERP -> tài khoản ERP.

    THỨ TỰ TRA BẮT BUỘC: `USER_MANUAL_MAP` TRƯỚC, `legacy_id` sau. Ba UID cùng
    trỏ về hồ sơ 221 mà `legacy_id` chỉ đeo được một, nên tra mỗi `legacy_id`
    thì phiếu của hai UID kia rơi mất (xem ghi chú ở `mapping.py`).

    Bốn hồ sơ nhân sự CÓ `legacy_id` mà KHÔNG có tài khoản ERP: app cũ đã khóa
    họ từ trước nên `create_missing_employees` cố ý không cấp tài khoản. Phiếu
    của họ vẫn nạp, chỉ là `requester_id` / `created_by` để 0 — ghi một id tài
    khoản bịa ra thì tệ hơn nhiều so với để trống. Tên và email người tạo vẫn
    được chụp lại vào phiếu nên bản in không mất chữ nào.
    """

    def __init__(self, db):
        self.db = db
        self._emp_by_uid: dict[str, Employee] = {}
        self._user_by_emp: dict[int, int] = {}
        self.no_account: collections.Counter = collections.Counter()
        self.unknown_uid: collections.Counter = collections.Counter()

        for emp in db.execute(select(Employee).where(Employee.legacy_id != "")).scalars():
            self._emp_by_uid[emp.legacy_id] = emp
        for uid, emp_id in USER_MANUAL_MAP.items():
            emp = db.get(Employee, emp_id)
            if emp is not None:
                self._emp_by_uid[uid] = emp

        #  Một hồ sơ có thể đeo nhiều tài khoản. Ưu tiên tài khoản ĐANG HOẠT
        #  ĐỘNG, rồi mới tới id nhỏ nhất — đúng luật đại ca chốt cho `dedupe`.
        for user in db.execute(select(User).order_by(User.id)).scalars():
            if not user.employee_id:
                continue
            cur = self._user_by_emp.get(user.employee_id)
            if cur is None:
                self._user_by_emp[user.employee_id] = user.id
            elif user.is_active and not self._is_active(cur):
                self._user_by_emp[user.employee_id] = user.id

    def _is_active(self, user_id: int) -> bool:
        user = self.db.get(User, user_id)
        return bool(user and user.is_active)

    def employee(self, uid: str) -> Employee | None:
        emp = self._emp_by_uid.get(uid or "")
        if emp is None and uid:
            self.unknown_uid[uid] += 1
        return emp

    def user_id(self, uid: str) -> int:
        emp = self.employee(uid)
        if emp is None:
            return 0
        user_id = self._user_by_emp.get(emp.id, 0)
        if not user_id:
            self.no_account[f"{emp.code} {emp.full_name}"] += 1
        return user_id


def _requester_snapshot(db, emp: Employee | None) -> dict:
    """Chụp tên / email / SĐT / chức danh người tạo, giống `_requester_context`.

    QĐ-K: hồ sơ ERP là bản chính, KHÔNG lấy tên hay email bên app cũ đè lên.
    """
    from app.modules.department.model import Department

    if emp is None:
        return {"requester": "", "requester_email": "", "requester_phone": "",
                "requester_role": "", "department_id": 0, "company_id": 0}
    dept = db.get(Department, emp.department_id) if emp.department_id else None
    role = " · ".join(x for x in [(emp.position or ""), (dept.name if dept else "")] if x)
    return {
        "requester": emp.full_name or "",
        "requester_email": emp.email or "",
        "requester_phone": getattr(emp, "phone", "") or "",
        "requester_role": role,
        "department_id": emp.department_id or 0,
        "company_id": emp.company_id or 0,
    }


# ---------------------------------------------------------------------------
# Đọc lịch sử duyệt (chỉ lấy mốc duyệt, không nạp cả sổ)
# ---------------------------------------------------------------------------

def _approvals(node: dict) -> list[dict]:
    hist = (node.get("approval") or {}).get("history") or []
    return [h for h in hist if h.get("action") == "approved"]


def _first_approval(node: dict, level: int | None = None) -> dict | None:
    for h in _approvals(node):
        if level is None or h.get("level") == level:
            return h
    return None


def _last_approval(node: dict, level: int | None = None) -> dict | None:
    found = None
    for h in _approvals(node):
        if level is None or h.get("level") == level:
            found = h
    return found


# ---------------------------------------------------------------------------
# Loại con dấu
# ---------------------------------------------------------------------------

def ensure_seal_type(db, apply: bool) -> int:
    """Lấy (hoặc tạo) loại con dấu gom chung. Trả về id, 0 nếu mới xem trước."""
    row = db.execute(select(SealType)
                     .where(SealType.name == LEGACY_SEAL_TYPE_NAME)).scalar_one_or_none()
    if row is not None:
        print(f"  = da co loai con dau id {row.id}: {LEGACY_SEAL_TYPE_NAME}")
        return row.id
    print(f"  + tao loai con dau: {LEGACY_SEAL_TYPE_NAME}")
    if not apply:
        return 0
    row = SealType(name=LEGACY_SEAL_TYPE_NAME, description=LEGACY_SEAL_TYPE_DESC,
                   is_active=True, created_by=SYSTEM_ACTOR_ID, updated_by=SYSTEM_ACTOR_ID)
    db.add(row)
    db.flush()
    print(f"         id {row.id}")
    return row.id


# ---------------------------------------------------------------------------
# Nạp phiếu
# ---------------------------------------------------------------------------

def _companies_of(details: dict, company_index: dict[str, int],
                  stats: collections.Counter) -> list[int]:
    """`brandId` (LUÔN là danh sách bên app cũ) -> danh sách id công ty ERP."""
    out = []
    for key in details.get("brandId") or []:
        cid = company_index.get(key)
        if cid is None:
            stats["cong ty la"] += 1
            continue
        if cid not in out:
            out.append(cid)
    return out


def build_seal(db, key: str, node: dict, people: PeopleResolver, seal_type_id: int,
               company_index: dict[str, int], dept_index: dict[str, int],
               stats: collections.Counter) -> tuple[SealRequest, list[int]]:
    details = node.get("details") or {}
    emp = people.employee(node.get("createdBy") or "")
    snap = _requester_snapshot(db, emp)
    company_ids = _companies_of(details, company_index, stats)
    if len(company_ids) > 1:
        stats["phieu dau nhieu cong ty"] += 1

    #  Phòng ban: phiếu dấu bên app cũ CÓ khai `departmentId`, ưu tiên nó; phòng
    #  của hồ sơ nhân sự chỉ là đường lùi (người có thể đã chuyển phòng từ đó).
    dept_id = dept_index.get(details.get("departmentId") or "")
    if dept_id is None:
        dept_id = snap["department_id"]
        stats["phieu dau phong ban lui ve ho so"] += 1

    #  Luồng app cũ: cấp 1 "Trưởng bộ phận", cấp 2 "GĐ thương hiệu (tùy chọn)",
    #  cấp 3 "Pháp lý kiểm tra". Luồng ERP: cổng 1 Trưởng bộ phận -> `approved_*`,
    #  cổng 2 Văn thư đóng dấu -> `completed_*`. Cấp 3 KHÔNG phải Văn thư, nhưng
    #  nó là CỔNG CUỐI của cả hai luồng nên đổ vào `completed_*` — chỗ lệch nghĩa
    #  này ghi ở §P1.1 TIEN-DO.md, đừng đọc `completed_by` là "người đóng dấu".
    gate1 = _first_approval(node, level=1)
    gate_last = _last_approval(node, level=3)
    if gate1 is None and gate_last is not None:
        stats["phieu dau bo qua cap 1 (skip approval)"] += 1

    req = SealRequest(
        legacy_id=key,
        purpose=(details.get("purpose") or "").strip(),
        seal_type_id=seal_type_id,
        department_id=dept_id,
        company_id=company_ids[0] if company_ids else 0,
        copies=1,                       # app cũ không có ô số bản
        first_approver_id=people.user_id(details.get("firstApproverUid") or ""),
        approved_by=people.user_id((gate1 or {}).get("userId") or ""),
        approved_at=_utc_iso((gate1 or {}).get("timestamp")),
        completed_by=people.user_id((gate_last or {}).get("userId") or ""),
        completed_at=_utc_iso((gate_last or {}).get("timestamp")),
        status=SEAL_STATUS_FROM_LEGACY[(node.get("approval") or {})["overallStatus"]],
        note=(details.get("notes") or "").strip(),
        requester=snap["requester"],
        requester_id=people.user_id(node.get("createdBy") or ""),
        requester_email=snap["requester_email"],
        requester_phone=snap["requester_phone"],
        requester_role=snap["requester_role"],
        created_at=_utc_dt(node.get("createdAt")),
        updated_at=_utc_dt(node.get("createdAt")),
        created_by=people.user_id(node.get("createdBy") or ""),
        updated_by=people.user_id(node.get("createdBy") or ""),
    )
    return req, company_ids


def build_booking(db, key: str, node: dict, people: PeopleResolver,
                  company_index: dict[str, int], vehicle_index: dict[str, int],
                  driver_index: dict[str, int],
                  stats: collections.Counter) -> VehicleBooking:
    details = node.get("details") or {}
    is_delivery = node.get("type") == "DELIVERY"
    emp = people.employee(node.get("createdBy") or "")
    snap = _requester_snapshot(db, emp)
    company_ids = _companies_of(details, company_index, stats)

    note = (details.get("notes") or "").strip()
    if len(company_ids) > 1:
        #  `tab_vehicle_booking` chỉ có MỘT cột công ty (khác phiếu dấu, bên đó
        #  có bảng nối). Hai phiếu giao hàng khai hai công ty — giữ công ty đầu
        #  rồi nói rõ phần còn lại ra ghi chú, đừng vứt im lặng.
        extra = ", ".join(str(c) for c in company_ids[1:])
        note = (note + "\n" if note else "") + f"[App cũ] Phiếu khai nhiều công ty, id ERP: {extra}"
        stats["phieu xe nhieu cong ty"] += 1

    dispatch = details.get("dispatch") or {}
    driver_key = dispatch.get("assignedDriverId") or ""
    vehicle_key = dispatch.get("assignedVehicleId") or ""
    if driver_key and driver_key not in driver_index:
        #  Khóa tài xế này KHÔNG còn ở bất kỳ đâu trong bản kết xuất — không ở
        #  nhánh `drivers`, không ở `users`. Hồ sơ đã bị xóa bên app cũ mà phiếu
        #  vẫn trỏ vào. Không có gì để tra ra tên, nên nói thẳng ra ghi chú: một
        #  chuyến đã hoàn thành mà ô tài xế trống thì người đọc sẽ tưởng là lỗi
        #  nạp, trong khi sự thật là dữ liệu gốc đã mất.
        note = (note + "\n" if note else "") + (
            f"[App cũ] Tài xế được điều phối đã bị xóa khỏi app cũ, khóa {driver_key}")
        stats["tai xe da bi xoa ben app cu"] += 1
    if vehicle_key and vehicle_key not in vehicle_index:
        stats["xe la"] += 1

    gate = _last_approval(node)
    stops = [
        {"location": (s.get("address") or "").strip(),
         "contact_name": (s.get("contactName") or "").strip(),
         "contact_phone": (s.get("contactPhone") or "").strip(),
         "notes": (s.get("notes") or "").strip()}
        for s in (details.get("intermediateStops") or [])
        if isinstance(s, dict) and (s.get("address") or "").strip()
    ]

    return VehicleBooking(
        legacy_id=key,
        request_type=TYPE_DELIVERY if is_delivery else TYPE_CAR,
        purpose=(details.get("purpose") or "").strip(),
        is_self_drive=(driver_key == SELF_DRIVE_DRIVER_KEY),
        start_location=(details.get("pickupLocation") if is_delivery
                        else details.get("startLocation")) or "",
        end_location=(details.get("dropoffLocation") if is_delivery
                      else details.get("endLocation")) or "",
        stops=json.dumps(stops, ensure_ascii=False),
        start_time=_local_iso(details.get("startTime")),
        end_time=_local_iso(details.get("endTime")),
        # --- riêng đặt xe công tác ---
        passenger_count=int(details.get("passengerCount") or 1),
        attendees=(details.get("attendees") or "").strip(),
        contact_phone=(details.get("contactPhone") or "").strip(),
        is_round_trip=bool(details.get("isRoundTrip")),
        # --- riêng giao hàng ---
        goods_name=(details.get("itemName") or "").strip(),
        goods_size=(details.get("dimensions") or "").strip(),
        sender_name=(details.get("senderName") or "").strip(),
        sender_phone=(details.get("senderPhone") or "").strip(),
        receiver_name=(details.get("recipientName") or "").strip(),
        receiver_phone=(details.get("recipientPhone") or "").strip(),
        special_instructions=(details.get("specialInstructions") or "").strip(),
        # --- người tạo + phạm vi ---
        requester=snap["requester"],
        requester_id=people.user_id(node.get("createdBy") or ""),
        requester_email=snap["requester_email"],
        requester_phone=snap["requester_phone"],
        requester_role=snap["requester_role"],
        #  Phiếu đặt xe bên app cũ KHÔNG khai phòng ban (khác phiếu dấu), nên
        #  phòng ban chỉ có một nguồn: hồ sơ nhân sự người tạo.
        department_id=snap["department_id"],
        company_id=company_ids[0] if company_ids else 0,
        first_approver_id=people.user_id(details.get("firstApproverUid") or ""),
        approved_by=people.user_id((gate or {}).get("userId") or ""),
        approved_at=_utc_iso((gate or {}).get("timestamp")),
        status=BOOKING_STATUS_FROM_LEGACY[(node.get("approval") or {})["overallStatus"]],
        note=note,
        # --- điều phối ---
        assigned_vehicle_id=vehicle_index.get(vehicle_key, 0),
        assigned_driver_id=driver_index.get(driver_key, 0),
        dispatched_by=people.user_id(dispatch.get("dispatchedBy") or ""),
        dispatched_at=_utc_iso(dispatch.get("dispatchedAt")),
        driver_status=DRIVER_STATUS_FROM_LEGACY.get(dispatch.get("driverStatus"), DRV_NONE),
        actual_start_time=_utc_iso(dispatch.get("actualStartTime")),
        actual_end_time=_utc_iso(dispatch.get("actualEndTime")),
        created_at=_utc_dt(node.get("createdAt")),
        updated_at=_utc_dt(node.get("createdAt")),
        created_by=people.user_id(node.get("createdBy") or ""),
        updated_by=people.user_id(node.get("createdBy") or ""),
    )


def _existing_keys(db, model) -> set[str]:
    return set(db.execute(select(model.legacy_id)
                          .where(model.legacy_id != "")).scalars())


#  Trần độ dài đọc THẲNG từ model, không chép tay — chép tay thì đổi `String(n)`
#  bên model là bảng số bên này lệch ngay mà không ai biết.
def _string_limits(model) -> dict[str, int]:
    return {col.key: col.type.length for col in sa_inspect(model).columns
            if isinstance(col.type, String) and col.type.length}


#  Cụm số điện thoại ở ĐẦU chuỗi: "0787936664 - Mỹ Giang" → "0787936664".
PHONE_HEAD = re.compile(r"^[\d+][\d\s.\-()]*")


def fit_to_columns(obj, stats: collections.Counter) -> None:
    """Ép mọi ô chữ vừa trần cột mà KHÔNG làm mất chữ người ta đã gõ.

    App cũ để người dùng gõ tự do vào ô mà bên ERP khai `String(n)` — ô "SĐT
    liên hệ" có người gõ "0787936664 - Mỹ Giang" (21 ký tự, cột 20). MySQL
    không cắt hộ: nó ném lỗi 1406 và cả mẻ nạp chết ngang. Ở đây cắt cho vừa
    cột rồi chép NGUYÊN VĂN giá trị gốc xuống `note` (cột Text), nên không có
    chữ nào biến mất — chỉ đổi chỗ.
    """
    for field, limit in _string_limits(type(obj)).items():
        value = getattr(obj, field, None)
        if not isinstance(value, str) or len(value) <= limit:
            continue
        #  Ô điện thoại cắt tại ranh giới CÓ NGHĨA: phần đầu là số, phần đuôi là
        #  tên người ta gõ thêm. Cắt thô ra "0787936664 - Mỹ Gia" thì ô đọc như
        #  dữ liệu hỏng và bấm gọi cũng không được; giữ đúng cụm số thì ô vẫn dùng
        #  được, còn tên đã nằm đủ dưới ghi chú.
        cut = ""
        if field.endswith("phone"):
            head = PHONE_HEAD.match(value)
            if head:
                cut = head.group(0).strip(" .-")[:limit]
        setattr(obj, field, cut or value[:limit])
        note = getattr(obj, "note", "") or ""
        obj.note = (note + "\n" if note else "") + f"[App cũ] {field}: {value}"
        stats[f"o qua dai, chep xuong ghi chu: {field}"] += 1


def run(db, data: dict, apply: bool) -> collections.Counter:
    stats: collections.Counter = collections.Counter()
    people = PeopleResolver(db)
    requests = data["requests"]

    print("\n=== DANH MUC ===")
    company_index = legacy_index(db, Company)
    dept_index = legacy_index(db, Department)
    vehicle_index = legacy_index(db, Vehicle)
    driver_index = legacy_index(db, Driver)
    clean = check_against_hand_table("cong ty", company_index, BRAND_TO_COMPANY_ID)
    clean &= check_against_hand_table("phong ban", dept_index, DEPARTMENT_TO_ERP_ID)
    clean &= check_against_hand_table("xe", vehicle_index, VEHICLE_TO_ERP_ID)
    clean &= check_against_hand_table("tai xe", driver_index, DRIVER_TO_ERP_ID)
    if not clean:
        raise SystemExit("  DUNG: dau legacy_id duoi DB lech bang tra tay, "
                         "chay lai sync_master_data truoc.")
    print(f"  cong ty {len(company_index)} dau · phong ban {len(dept_index)} dau · "
          f"xe {len(vehicle_index)} dau · tai xe {len(driver_index)} dau")

    print("\n=== LOAI CON DAU ===")
    seal_type_id = ensure_seal_type(db, apply)

    seal_done = _existing_keys(db, SealRequest)
    booking_done = _existing_keys(db, VehicleBooking)
    print(f"\n=== NAP PHIEU === (da co san: {len(seal_done)} phieu dau, "
          f"{len(booking_done)} phieu xe)")

    #  Xếp theo mốc tạo để id ERP tăng dần đúng thứ tự thời gian bên app cũ —
    #  mã phiếu sinh từ id nên nhờ vậy mã cũng chạy đúng dòng thời gian.
    ordered = sorted(requests.items(), key=lambda kv: kv[1].get("createdAt") or 0)

    for key, node in ordered:
        typ = node.get("type")
        if typ == "SEAL_REQUEST":
            if key in seal_done:
                stats["phieu dau bo qua (da nap)"] += 1
                continue
            req, company_ids = build_seal(db, key, node, people, seal_type_id,
                                          company_index, dept_index, stats)
            fit_to_columns(req, stats)
            stats["phieu dau"] += 1
            if not apply:
                continue
            db.add(req)
            db.flush()
            req.code = f"DD{req.id:06d}"
            for cid in company_ids:
                db.add(SealRequestCompany(seal_request_id=req.id, company_id=cid,
                                          created_by=SYSTEM_ACTOR_ID,
                                          updated_by=SYSTEM_ACTOR_ID))
        elif typ in ("CAR_BOOKING", "DELIVERY"):
            if key in booking_done:
                stats["phieu xe bo qua (da nap)"] += 1
                continue
            booking = build_booking(db, key, node, people, company_index,
                                    vehicle_index, driver_index, stats)
            fit_to_columns(booking, stats)
            stats["phieu xe cong tac" if typ == "CAR_BOOKING" else "phieu giao hang"] += 1
            if not apply:
                continue
            db.add(booking)
            db.flush()
            booking.code = f"DX{booking.id:06d}"
        else:
            stats[f"loai la: {typ}"] += 1

    if people.unknown_uid:
        print("\n  LOI: UID khong tra ra ho so nao (phieu se mat nguoi tao):")
        for uid, n in people.unknown_uid.most_common():
            print(f"    {uid}  x{n}")
    if people.no_account:
        print("\n  CANH BAO: ho so KHONG co tai khoan ERP — app cu da khoa ho tu "
              "truoc nen khong duoc cap tai khoan. Phieu van nap, ten nguoi tao "
              "van con, chi de trong id tai khoan:")
        for who, n in people.no_account.most_common():
            print(f"    {who}  x{n}")
    return stats


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export", required=True,
                        help="duong dan ban ket xuat JSON tu Firebase")
    parser.add_argument("--apply", action="store_true",
                        help="ghi that; bo qua thi chi xem truoc")
    args = parser.parse_args()

    with open(args.export, encoding="utf-8") as fh:
        data = json.load(fh)
    for node in ("requests", "users", "brands", "departments"):
        if node not in data:
            print(f"LOI: ban ket xuat thieu nhanh {node!r}")
            return 1

    db = SessionLocal()
    try:
        stats = run(db, data, args.apply)
        if args.apply:
            db.commit()
        else:
            db.rollback()
        print("\n=== TONG KET ===")
        for name, n in sorted(stats.items()):
            print(f"  {name:42} {n}")
        print("\n  " + ("DA GHI VAO DB." if args.apply
                        else "MOI CHI XEM TRUOC — them --apply de ghi that."))
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
