# -*- coding: utf-8 -*-
"""Quy tắc chuyển một DÒNG Excel hệ cũ → bộ trường `VehicleBooking`.

Tách khỏi runner (`import_datxe_legacy.py`) để phần quy tắc thuần hàm, kiểm được
mà không cần DB. Mọi tra cứu danh mục đi qua đối tượng `Lookups` do runner dựng.

Nguồn: 2 tệp xuất từ app cũ (`app.degoholding.vn`), cột tiếng Việt:
  - `import-yeu-cau-dat-xe-cong-tac.xlsx` → TYPE_CAR
  - `import-yeu-cau-giao-hang.xlsx`       → TYPE_DELIVERY
"""
import json
import re
import unicodedata
from datetime import datetime

from app.modules.vehicle_booking.model import (
    BK_APPROVED, BK_CANCELLED, BK_COMPLETED, BK_DISPATCHED, BK_DRAFT,
    BK_PENDING, BK_REJECTED, BK_RETURNED, DRV_ACCEPTED, DRV_COMPLETED,
    DRV_NONE, DRV_ONGOING, DRV_REJECTED, DRV_WAITING, TYPE_CAR, TYPE_DELIVERY,
)

# --- Bộ mã: chữ tiếng Việt hệ cũ → SMALLINT của module (R2/QĐ-11) ------------
# Hệ cũ không có khái niệm "Nháp" nên bản đồ này không sinh BK_DRAFT; giữ khóa
# để ai dọn dữ liệu tay sau này vẫn khớp.
STATUS_MAP = {
    "Nháp": BK_DRAFT,
    "Chờ duyệt": BK_PENDING,
    "Đã duyệt": BK_APPROVED,
    "Điều phối": BK_DISPATCHED,
    "Hoàn thành": BK_COMPLETED,
    "Từ chối": BK_REJECTED,
    "Hủy yêu cầu": BK_CANCELLED,
    "Yêu cầu chỉnh sửa": BK_RETURNED,
}
DRIVER_STATUS_MAP = {
    "": DRV_NONE,
    "Chờ tài xế": DRV_WAITING,
    "Đã nhận": DRV_ACCEPTED,
    "Đang đi": DRV_ONGOING,
    "Hoàn thành": DRV_COMPLETED,
    "Tài xế từ chối": DRV_REJECTED,
}

# Định dạng mốc thời gian hệ cũ dùng thống nhất ở cả 2 tệp.
_LEGACY_DT = "%H:%M:%S %d/%m/%Y"


def loose(value) -> str:
    """Bỏ dấu + bỏ mọi ký tự không phải chữ/số → khóa so khớp bền.

    Cần vì dữ liệu hai bên lệch nhau đúng mấy chỗ đó: `Thuỳ` vs `Thùy` (dấu đặt
    khác vị trí), `DR.XANH` vs `DR XANH` (dấu chấm), `Mai Thị Hiểu` vs
    `Mai Thi Hiểu` (hồ sơ gõ thiếu dấu).
    """
    text = unicodedata.normalize("NFD", str(value or ""))
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = text.replace("đ", "d").replace("Đ", "D")
    return re.sub(r"[^a-z0-9]", "", text.lower())


def digits(value) -> str:
    """Chỉ giữ chữ số — SĐT hệ cũ lẫn dấu cách/gạch (`0909 805 009`)."""
    return re.sub(r"\D", "", str(value or ""))


def parse_legacy_dt(value) -> datetime | None:
    """`'14:21:15 2/7/2026'` → datetime. Không đúng khuôn thì trả None."""
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.strptime(text, _LEGACY_DT)
    except ValueError:
        return None


def to_iso(value) -> str:
    """→ chuỗi ISO tới phút, cùng khuôn `service._now()` đang lưu trong DB."""
    parsed = parse_legacy_dt(value)
    return parsed.isoformat(timespec="minutes") if parsed else ""


def split_route(value) -> tuple[str, str]:
    """`'A -> B'` → (A, B). Cả 355 dòng nguồn đều đúng một dấu `->`.

    Không có dấu phân cách thì coi cả chuỗi là điểm đi, điểm đến để trống — thà
    mất điểm đến còn hơn nhét cả lộ trình vào một ô rồi báo là đã nhập đủ.
    """
    text = str(value or "").strip()
    if "->" not in text:
        return text[:255], ""
    head, _, tail = text.partition("->")
    return head.strip()[:255], tail.strip()[:255]


def first_phone(value) -> str:
    """Rút SĐT ĐẦU TIÊN trong ô chữ tự do, để vừa `contact_phone String(20)`.

    Ô `SĐT người tham gia` hệ cũ là văn bản: `'0899651779 - Chị Huỳnh,
    0946141028 - Chị Ly, ...'` (dài tới 70 ký tự). Cắt cứng 20 ký tự là ghi
    xuống DB một số điện thoại SAI (dính đuôi tên); còn String(20) mà nhồi 70
    ký tự thì MySQL chặn → lỗi 500 chứ không phải 422 (duoc-CR-316). Nên rút số
    đầu, và nguyên văn ô được runner giữ lại vào `note`.
    """
    text = str(value or "")
    match = re.search(r"0\d[\d\s.\-]{7,}", text)
    if not match:
        return ""
    phone = digits(match.group(0))
    return phone[:20]


def _int_or(value, default: int) -> int:
    try:
        return int(str(value or "").strip())
    except (TypeError, ValueError):
        return default


class Lookups:
    """Danh mục tra cứu dựng một lần từ DB (tránh truy vấn trong vòng lặp)."""

    def __init__(self, employees, users, companies, vehicles, drivers):
        self.emp_by_name: dict[str, list] = {}
        for emp in employees:
            self.emp_by_name.setdefault(loose(emp.full_name), []).append(emp)
        # Trùng tên → chốt theo id nhỏ nhất cho KẾT QUẢ ỔN ĐỊNH giữa các lần chạy.
        for bucket in self.emp_by_name.values():
            bucket.sort(key=lambda e: e.id)

        self.user_by_emp = {u.employee_id: u for u in users if u.employee_id}

        self.comp_by_name: dict[str, list] = {}
        for comp in companies:
            self.comp_by_name.setdefault(loose(comp.name), []).append(comp)
        for bucket in self.comp_by_name.values():
            bucket.sort(key=lambda c: c.id)  # `DEGO HOLDING` bị trùng 2 bản ghi

        self.veh_by_plate = {loose(v.license_plate): v for v in vehicles}

        self.drv_by_phone: dict[str, list] = {}
        for drv in drivers:
            self.drv_by_phone.setdefault(digits(drv.phone), []).append(drv)
        for bucket in self.drv_by_phone.values():
            bucket.sort(key=lambda d: d.id)

    def employee(self, name):
        return (self.emp_by_name.get(loose(name)) or [None])[0]

    def user_of(self, employee):
        return self.user_by_emp.get(employee.id) if employee else None

    def company(self, cell):
        """Ô `Công ty` → bản ghi công ty.

        Ô có thể chứa NHIỀU công ty (`'A - mst, B - mst'`, 2 dòng ở tệp giao
        hàng) → lấy cái đầu. Đuôi ` - <MST>` bị cắt trước khi so tên: MST hệ cũ
        lệch hẳn MST trong DB ở 2 pháp nhân DR.XANH nên so theo tên bền hơn.
        """
        head = str(cell or "").split(",")[0].strip()
        base = head.rsplit(" - ", 1)[0].strip() if " - " in head else head
        return (self.comp_by_name.get(loose(base)) or [None])[0]

    def vehicle(self, plate):
        return self.veh_by_plate.get(loose(plate))

    def driver(self, phone):
        return (self.drv_by_phone.get(digits(phone)) or [None])[0]


def build_kwargs(row: dict, is_delivery: bool, look: Lookups) -> tuple[dict, list[str]]:
    """DÒNG Excel → (bộ trường `VehicleBooking`, danh sách cảnh báo).

    Không ghi DB, không sinh mã — runner lo hai việc đó. Người tạo không tra
    được hồ sơ nhân sự thì trả `{}` để runner bỏ dòng (quyết định 15/09/2026).
    """
    warnings: list[str] = []
    employee = look.employee(row.get("Tên người tạo"))
    if not employee:
        return {}, [f"bỏ dòng — không có hồ sơ nhân sự: {row.get('Tên người tạo')!r}"]

    user = look.user_of(employee)
    company = look.company(row.get("Công ty"))
    if not company:
        warnings.append(f"không khớp công ty: {str(row.get('Công ty'))[:48]!r}")

    start_key = "Thời gian lấy hàng" if is_delivery else "Thời gian đi"
    end_key = "Thời gian giao (dự kiến)" if is_delivery else "Thời gian về"
    start_location, end_location = split_route(row.get("Lộ trình"))

    # --- Xe: chữ tự do (`xe thuê`, `xe thê`, `XE THUÊ NGOÀI`) không khớp danh
    # mục → để trống khóa, giữ nguyên văn vào ghi chú (quyết định 15/09/2026).
    plate = str(row.get("Biển số xe") or "").strip()
    vehicle = look.vehicle(plate) if plate else None
    notes = [str(row.get("Ghi chú") or "").strip()]
    if plate and not vehicle:
        notes.append(f"[nhập từ hệ cũ] Xe ghi tay: {plate}")

    driver = look.driver(row.get("SĐT tài xế"))

    kwargs = {
        "request_type": TYPE_DELIVERY if is_delivery else TYPE_CAR,
        "purpose": str(row.get("Tiêu đề") or "").strip(),
        "start_location": start_location,
        "end_location": end_location,
        "stops": json.dumps([], ensure_ascii=False),
        "start_time": to_iso(row.get(start_key)),
        "end_time": to_iso(row.get(end_key)),
        "requester": employee.full_name,
        "requester_id": user.id if user else 0,
        "requester_email": employee.email or "",
        "requester_phone": (employee.phone or "")[:30],
        "requester_role": (employee.position or "")[:255],
        "department_id": employee.department_id or 0,
        "company_id": company.id if company else 0,
        "status": STATUS_MAP.get(str(row.get("Trạng thái chung") or "").strip(), BK_PENDING),
        "assigned_vehicle_id": vehicle.id if vehicle else None,
        "assigned_driver_id": driver.id if driver else None,
        "dispatched_at": to_iso(row.get("Thời gian điều phối")),
        "driver_status": DRIVER_STATUS_MAP.get(
            str(row.get("Trạng thái tài xế") or "").strip(), DRV_NONE),
        "actual_start_time": to_iso(row.get("Bắt đầu thực tế")),
        "actual_end_time": to_iso(row.get("Kết thúc thực tế")),
        "created_by": user.id if user else 0,
        "updated_by": user.id if user else 0,
    }

    if is_delivery:
        kwargs.update({
            "goods_name": str(row.get("Tên hàng hóa") or "").strip()[:255],
            "goods_size": str(row.get("Kích thước/KL") or "").strip()[:255],
            "sender_name": str(row.get("Tên người gửi") or "").strip()[:255],
            "sender_phone": digits(row.get("SĐT người gửi"))[:30],
            "receiver_name": str(row.get("Tên người nhận") or "").strip()[:255],
            "receiver_phone": digits(row.get("SĐT người nhận"))[:30],
            "special_instructions": str(row.get("Chi dẫn đặc biệt") or "").strip(),
        })
    else:
        raw_contact = str(row.get("SĐT người tham gia") or "").strip()
        contact = first_phone(raw_contact)
        # Cột chỉ giữ được MỘT số, nên lưu nguyên văn ô khi ô nói nhiều hơn thế:
        # nhiều số (`'0899… - Chị Huỳnh, 0946… - Chị Ly'`) hoặc có chữ kèm theo
        # (`'0946141028 - Mai Thị Yến Ly'`). So theo chữ số là KHÔNG đủ — ô một
        # số kèm tên có cùng bộ chữ số nên lọt qua, và tên người rơi mất im lặng.
        # Ô chỉ khác dấu cách (`'0865 808 322'`) thì không mất gì, bỏ qua.
        if raw_contact and (digits(raw_contact) != contact
                            or re.search(r"[^\d\s.\-()]", raw_contact)):
            notes.append(f"[nhập từ hệ cũ] SĐT người tham gia: {raw_contact}")
        kwargs.update({
            "passenger_count": _int_or(row.get("Số hành khách"), 1),
            "attendees": str(row.get("Người tham gia") or "").strip(),
            "contact_phone": contact,
            "is_round_trip": str(row.get("Khứ hồi") or "").strip() == "Có",
        })

    kwargs["note"] = "\n".join(p for p in notes if p)

    # `created_at` KHÔNG có trong nguồn (cả 2 tệp đều thiếu cột ngày tạo). Lấy
    # mốc thật sớm nhất đã biết làm XẤP XỈ — phiếu chắc chắn được tạo trước khi
    # điều phối và trước giờ khởi hành. Để mặc định `func.now()` thì cả 337
    # phiếu mang ngày nhập, và mọi báo cáo theo tháng dồn hết vào tháng 9/2026.
    anchors = [d for d in (parse_legacy_dt(row.get("Thời gian điều phối")),
                           parse_legacy_dt(row.get(start_key))) if d]
    if anchors:
        kwargs["created_at"] = min(anchors)

    return kwargs, warnings
