from sqlalchemy import BigInteger, Boolean, Float, Index, Integer, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, AuditMixin

# ---------------------------------------------------------------------------
# Bộ mã (R2/QĐ-11): cột nghĩa loại / trạng thái lưu SMALLINT + hằng số nguyên;
# tiếng Việt chỉ ở tầng hiển thị (dict nhãn), API trả kèm số + nhãn. Cùng khuôn
# với module `document`. KHÔNG lưu chữ tiếng Việt vào các cột này.
# ---------------------------------------------------------------------------

# Loại yêu cầu — quyết định bộ trường của form.
TYPE_CAR = 1       # Đặt xe công tác (chở người)
TYPE_DELIVERY = 2  # Đặt xe giao hàng (chở hàng)
REQUEST_TYPE_LABELS = {
    TYPE_CAR: "Đặt xe công tác",
    TYPE_DELIVERY: "Đặt xe giao hàng",
}

# Trạng thái chung của phiếu.
BK_DRAFT = 1       # Nháp — người tạo còn sửa, chưa vào luồng duyệt
BK_PENDING = 2     # Chờ duyệt
BK_APPROVED = 3    # Đã duyệt — chờ điều phối
BK_DISPATCHED = 4  # Điều phối — đã phân xe/tài xế, chờ tài xế
BK_COMPLETED = 5   # Hoàn thành
BK_REJECTED = 6    # Từ chối (người duyệt) — khóa
BK_CANCELLED = 7   # Đã hủy — kết thúc
BK_RETURNED = 8    # Yêu cầu chỉnh sửa — trả người tạo sửa rồi gửi lại
BOOKING_STATUS_LABELS = {
    BK_DRAFT: "Nháp",
    BK_PENDING: "Chờ duyệt",
    BK_APPROVED: "Đã duyệt",
    BK_DISPATCHED: "Điều phối",
    BK_COMPLETED: "Hoàn thành",
    BK_REJECTED: "Từ chối",
    BK_CANCELLED: "Đã hủy",
    BK_RETURNED: "Yêu cầu chỉnh sửa",
}
# Chỉ sửa được khi phiếu chưa vào luồng hoặc bị trả về (A07).
EDITABLE_STATUSES = (BK_DRAFT, BK_RETURNED)

# Trạng thái tài xế — tách riêng khỏi trạng thái chung.
DRV_NONE = 0       # Chưa phân tài xế
DRV_WAITING = 1    # Chờ tài xế phản hồi
DRV_ACCEPTED = 2   # Đã nhận
DRV_ONGOING = 3    # Đang đi
DRV_COMPLETED = 4  # Hoàn thành
DRV_REJECTED = 5   # Tài xế từ chối — quay về điều phối
DRIVER_STATUS_LABELS = {
    DRV_NONE: "",
    DRV_WAITING: "Chờ tài xế",
    DRV_ACCEPTED: "Đã nhận",
    DRV_ONGOING: "Đang đi",
    DRV_COMPLETED: "Hoàn thành",
    DRV_REJECTED: "Tài xế từ chối",
}


class Vehicle(Base, AuditMixin):
    """Quản lý xe."""
    __tablename__ = "tab_vehicle"

    license_plate: Mapped[str] = mapped_column(String(50), unique=True)
    model: Mapped[str] = mapped_column(String(100), default="")
    type: Mapped[str] = mapped_column(String(50), default="")
    capacity: Mapped[int] = mapped_column(Integer, default=4)
    status: Mapped[str] = mapped_column(String(30), default="available")  # available, on_trip, maintenance
    is_external: Mapped[bool] = mapped_column(Boolean, default=False)
    external_company: Mapped[str] = mapped_column(String(255), default="")


class Driver(Base, AuditMixin):
    """Quản lý tài xế."""
    __tablename__ = "tab_driver"

    user_id: Mapped[int] = mapped_column(BigInteger, nullable=True)  # Liêk kết với tab_user
    name: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str] = mapped_column(String(20), default="")
    license_number: Mapped[str] = mapped_column(String(50), default="")
    status: Mapped[str] = mapped_column(String(30), default="available")
    is_external: Mapped[bool] = mapped_column(Boolean, default=False)
    external_company: Mapped[str] = mapped_column(String(255), default="")


class VehicleBooking(Base, AuditMixin):
    """Yêu cầu đặt xe."""
    __tablename__ = "tab_vehicle_booking"

    __table_args__ = (Index("ix_vbooking_created_by", "created_by"),)

    code: Mapped[str] = mapped_column(String(50), unique=True, default="")
    # TYPE_CAR = đặt xe công tác · TYPE_DELIVERY = giao hàng (xem hằng số ở đầu tệp)
    request_type: Mapped[int] = mapped_column(SmallInteger, default=TYPE_CAR)
    purpose: Mapped[str] = mapped_column(Text, default="")

    start_location: Mapped[str] = mapped_column(String(255), default="")
    end_location: Mapped[str] = mapped_column(String(255), default="")
    # Điểm dừng trung gian (kiểu Google Maps) — JSON danh sách chuỗi, giữ thứ tự.
    stops: Mapped[str] = mapped_column(Text, default="")
    start_time: Mapped[str] = mapped_column(String(20), default="")  # ISO string
    end_time: Mapped[str] = mapped_column(String(20), default="")  # ISO string

    # --- Riêng ĐẶT XE CÔNG TÁC ---
    passenger_count: Mapped[int] = mapped_column(Integer, default=1)
    attendees: Mapped[str] = mapped_column(Text, default="")
    contact_phone: Mapped[str] = mapped_column(String(20), default="")
    is_round_trip: Mapped[bool] = mapped_column(Boolean, default=False)

    # --- Riêng ĐẶT XE GIAO HÀNG ---
    goods_name: Mapped[str] = mapped_column(String(255), default="")
    goods_size: Mapped[str] = mapped_column(String(255), default="")
    sender_name: Mapped[str] = mapped_column(String(255), default="")
    sender_phone: Mapped[str] = mapped_column(String(30), default="")
    receiver_name: Mapped[str] = mapped_column(String(255), default="")
    receiver_phone: Mapped[str] = mapped_column(String(30), default="")
    special_instructions: Mapped[str] = mapped_column(Text, default="")

    # Nguoi tao
    requester: Mapped[str] = mapped_column(String(255), default="")
    requester_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    department_id: Mapped[int] = mapped_column(BigInteger, default=0)
    company_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    
    first_approver_id: Mapped[int] = mapped_column(BigInteger, default=0)

    status: Mapped[int] = mapped_column(SmallInteger, default=BK_DRAFT, index=True)
    note: Mapped[str] = mapped_column(Text, default="")
    
    # Dispatch Info
    assigned_vehicle_id: Mapped[int] = mapped_column(BigInteger, nullable=True)
    assigned_driver_id: Mapped[int] = mapped_column(BigInteger, nullable=True)
    dispatched_by: Mapped[int] = mapped_column(BigInteger, nullable=True)
    dispatched_at: Mapped[str] = mapped_column(String(20), default="")
    driver_status: Mapped[int] = mapped_column(SmallInteger, default=DRV_NONE)

    # Chạy chuyến thực tế (tài xế ghi khi hoàn thành) — để thống kê theo tài xế/điều phối
    actual_start_time: Mapped[str] = mapped_column(String(20), default="")
    actual_end_time: Mapped[str] = mapped_column(String(20), default="")
    distance_km: Mapped[float] = mapped_column(Float, default=0)
    cost: Mapped[int] = mapped_column(BigInteger, default=0)

    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    @property
    def request_type_label(self) -> str:
        return REQUEST_TYPE_LABELS.get(self.request_type, "")

    @property
    def status_label(self) -> str:
        return BOOKING_STATUS_LABELS.get(self.status, "")

    @property
    def driver_status_label(self) -> str:
        return DRIVER_STATUS_LABELS.get(self.driver_status, "")
