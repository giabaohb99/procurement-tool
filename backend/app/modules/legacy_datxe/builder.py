"""Dựng hàng ERP từ một bản ghi phiếu của app đặt xe cũ.

MỘT BẢN DUY NHẤT, HAI NGƯỜI GỌI. Toàn bộ mã trong tệp này trước nằm trong
`scripts/legacy_sync/import_tickets.py` và đã chạy thật trên 1313 phiếu ngày
16/09/2026. Đồng bộ thường trực cần đúng phép dựng ấy — cái móc bên app cũ đẩy
sang một phiếu, ERP phải ra cùng một hàng như đợt nạp đã ra. Mà tầng API không
import được `scripts/`, nên để nguyên chỗ cũ thì buộc chép logic ra lần hai.

Hai bản chép của cùng một phép dựng là thứ hỏng im lặng nhất: hôm nay giống
nhau, mai ai đó vá một bên, và từ đó phiếu nạp hàng loạt khác phiếu đồng bộ
thường ngày ở vài ô — không lỗi, không cảnh báo, chỉ là số liệu lệch. Nên mã
dời sang đây nguyên văn, KHÔNG sửa một dòng nghiệp vụ nào; `import_tickets.py`
giữ phần điều phối (đọc tệp kết xuất, đối chiếu bảng tay, đếm, in tổng kết) rồi
import ngược về đây.

HAI ĐỒNG HỒ TRONG CÙNG MỘT HÀNG — không phải lỗi, là chép đúng nếp ERP:

- `created_at` và mọi mốc do MÁY CHỦ đóng (`approved_at`, `completed_at`,
  `dispatched_at`, `actual_*`) ghi theo **UTC**, vì container ERP chạy UTC và
  `service._now()` lấy `datetime.now()` của container.
- `start_time` / `end_time` là giờ NGƯỜI DÙNG gõ trên trình duyệt nên ERP đang
  giữ **giờ Việt Nam (+7)**. Nạp theo UTC thì phiếu cũ hiện lệch 7 tiếng so với
  phiếu ERP tạo cùng màn hình.

CÁI GÌ Ở ĐÂY CỐ Ý KHÔNG LÀM: không ghi xuống DB, không sinh mã phiếu, không
quyết định tạo mới hay cập nhật. Mấy việc đó là của người gọi, vì luật khác
nhau — đợt nạp thì "đã có thì bỏ qua", còn đồng bộ thường trực thì "đã có thì
cập nhật, nhưng CHỈ những ô app cũ làm chủ" (§9.4 bản thiết kế).
"""

import collections
import json
import re
from datetime import datetime, timedelta, timezone

from sqlalchemy import String, inspect as sa_inspect, select

from app.modules.employee.model import Employee
from app.modules.seal_request.model import (
    SEAL_APPROVED,
    SEAL_CANCELLED,
    SEAL_COMPLETED,
    SEAL_PENDING,
    SEAL_REJECTED,
    SEAL_RETURNED,
    SealRequest,
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
    VehicleBooking,
)
from app.modules.legacy_datxe.mapping import USER_MANUAL_MAP

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
    """Mốc epoch (ms) hoặc chuỗi ISO -> `datetime` KHÔNG múi giờ, theo UTC.

    Dùng cho cột `DateTime` và cho mốc do máy chủ đóng — xem ghi chú "hai đồng
    hồ" ở đầu tệp.
    """
    if not ms:
        return None
    try:
        num = float(ms)
        s = num / 1000 if num > 1e11 else num
        return datetime.fromtimestamp(s, tz=timezone.utc).replace(tzinfo=None)
    except (TypeError, ValueError):
        pass
    val_str = str(ms).strip()
    if not val_str:
        return None
    try:
        dt = datetime.fromisoformat(val_str.replace("Z", "+00:00"))
        return dt.replace(tzinfo=None)
    except ValueError:
        for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(val_str, fmt)
            except ValueError:
                pass
        return None


def _utc_iso(ms) -> str:
    """Mốc epoch (ms) -> chuỗi ISO phút theo UTC, khớp `service._now()`."""
    dt = _utc_dt(ms)
    return dt.isoformat(timespec="minutes") if dt else ""


def _local_iso(ms) -> str:
    """Mốc epoch (ms) hoặc chuỗi ISO -> chuỗi ISO phút theo GIỜ VIỆT NAM.

    Chỉ dùng cho `start_time` / `end_time`: đó là giờ người dùng gõ, ERP đang
    lưu nguyên văn chuỗi trình duyệt gửi lên nên nó là giờ địa phương.
    """
    if not ms:
        return ""
    if isinstance(ms, str) and ("T" in ms or "- " in ms or "-" in ms) and not ms.replace(".", "").isdigit():
        return ms.strip()[:16]
    try:
        num = float(ms)
        s = num / 1000 if num > 1e11 else num
        return (datetime.fromtimestamp(s, tz=VN_OFFSET)
                .replace(tzinfo=None).isoformat(timespec="minutes"))
    except (TypeError, ValueError):
        return str(ms).strip()[:16]


def _safe_int(val, default: int = 1, max_val: int = 999) -> int:
    try:
        n = int(val or default)
        return max(0, min(n, max_val))
    except (TypeError, ValueError):
        return default



# ---------------------------------------------------------------------------
# Tra danh mục (công ty / phòng ban)
# ---------------------------------------------------------------------------

def legacy_index(db, model) -> dict[str, int]:
    """`{khóa app cũ: id ERP}` đọc thẳng từ cột `legacy_id` dưới DB."""
    return {row.legacy_id: row.id
            for row in db.execute(select(model).where(model.legacy_id != "")).scalars()}


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
# Dựng phiếu
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
        passenger_count=_safe_int(details.get("passengerCount"), default=1, max_val=999),
        attendees=(details.get("attendees") or "").strip()[:500],
        contact_phone=(details.get("contactPhone") or "").strip()[:50],
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


# ---------------------------------------------------------------------------
# Cập nhật phiếu đã có: ô nào app cũ được phép ghi đè
# ---------------------------------------------------------------------------

#  Ô app cũ KHÔNG BAO GIỜ được đụng, dù chế độ là ghi đè hết.
#
#  Danh sách cố ý ngắn. Bản thiết kế §9.4 cấm thêm sáu ô điều phối
#  (`status`, `assigned_vehicle_id`, `assigned_driver_id`, `driver_status`,
#  `distance_km`, `cost`) vì nó giả định điều phối viên bấm gán xe BÊN ERP.
#  Giai đoạn này chưa đúng: chiều ERP -> app cũ chưa làm, người ta vẫn gán xe
#  bên app cũ, ERP mới chỉ là cái gương. Cấm ghi đè lúc này thì gương đứng hình
#  ngay lần đầu, phiếu mãi mãi không có xe. Đại ca chốt 17/09/2026: ghi đè hết.
#
#  NGÀY NÀO ĐIỀU PHỐI CHUYỂN HẲN SANG ERP thì thêm sáu tên đó vào đây. Một chỗ
#  duy nhất, không phải đi lục lại mã.
#
#  Bốn ô dưới thì không bao giờ mở: đổi `code` là mọi bản in và email đã gửi
#  trỏ sai; `created_at` là mốc đối soát; `id` và `legacy_id` là dây nối giữa
#  hai hệ, đứt là mồ côi. `updated_at` / `updated_by` nằm đây vì lý do khác:
#  không phải cấm, mà là người gọi tự đóng dấu (bộ dựng đang để bằng `createdAt`,
#  chép sang thì mốc sửa cuối đứng im từ ngày phiếu ra đời).
LEGACY_READONLY_FIELDS = frozenset({
    "id", "code", "legacy_id", "created_at", "created_by",
    "updated_at", "updated_by",
})


def _is_blank(value) -> bool:
    """Giá trị này có phải là "không có gì" không.

    `False` KHÔNG tính là trống — bỏ tick "khứ hồi" là một ý định thật, khác
    hẳn với "không biết". Số 0 thì tính, vì mọi cột số ở đây là khóa ngoại hoặc
    mã trạng thái, 0 nghĩa là tra không ra.
    """
    if value is None or value == "":
        return True
    return isinstance(value, int) and not isinstance(value, bool) and value == 0


def copy_legacy_fields(target, source, stats: collections.Counter) -> list[str]:
    """Chép ô app cũ làm chủ từ bản vừa dựng (`source`) sang hàng ERP đang có.

    LUẬT MỘT CÂU: **ghi đè hết, trừ ghi rỗng đè lên đang có.**

    Vế sau mới là chỗ quan trọng, và nó chống một đường mất dữ liệu rất khó
    nhìn ra. `assigned_driver_id` không chép thẳng — nó là `driver_index.get(khóa, 0)`.
    Hôm nào đội xe mua xe mới, app cũ gán liền, ERP chưa kịp có dấu `legacy_id`
    cho xe đó, thì bộ dựng trả về 0. Ghi đè thẳng là **xóa xe khỏi phiếu**, trong
    khi bên app cũ vẫn ghi đủ — mất dữ liệu vì tra không ra, không phải vì ai bỏ,
    và không có một dòng lỗi nào. Nên ô trống thì giữ nguyên bản ERP và đếm lại
    để sổ đồng bộ còn kêu lên.

    Trả về tên những ô đã thực sự đổi, để người gọi ghi xuống sổ. Rỗng nghĩa là
    phiếu không có gì khác — đừng đụng vào DB nữa.
    """
    changed: list[str] = []
    for col in sa_inspect(type(target)).columns:
        field = col.key
        if field in LEGACY_READONLY_FIELDS:
            continue
        new = getattr(source, field, None)
        old = getattr(target, field, None)
        if _is_blank(new):
            if not _is_blank(old):
                stats[f"giu nguyen vi app cu khong tra ra: {field}"] += 1
            continue
        if new == old:
            continue
        setattr(target, field, new)
        changed.append(field)
    return changed
