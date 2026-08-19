from sqlalchemy import BigInteger, Boolean, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, AuditMixin


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
    purpose: Mapped[str] = mapped_column(Text, default="")
    
    start_location: Mapped[str] = mapped_column(String(255), default="")
    end_location: Mapped[str] = mapped_column(String(255), default="")
    start_time: Mapped[str] = mapped_column(String(20), default="") # ISO string
    end_time: Mapped[str] = mapped_column(String(20), default="") # ISO string
    
    passenger_count: Mapped[int] = mapped_column(Integer, default=1)
    attendees: Mapped[str] = mapped_column(Text, default="")
    contact_phone: Mapped[str] = mapped_column(String(20), default="")
    is_round_trip: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Nguoi tao
    requester: Mapped[str] = mapped_column(String(255), default="")
    requester_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    department_id: Mapped[int] = mapped_column(BigInteger, default=0)
    company_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    
    first_approver_id: Mapped[int] = mapped_column(BigInteger, default=0)
    
    status: Mapped[str] = mapped_column(String(30), default="draft")
    note: Mapped[str] = mapped_column(Text, default="")
    
    # Dispatch Info
    assigned_vehicle_id: Mapped[int] = mapped_column(BigInteger, nullable=True)
    assigned_driver_id: Mapped[int] = mapped_column(BigInteger, nullable=True)
    dispatched_by: Mapped[int] = mapped_column(BigInteger, nullable=True)
    dispatched_at: Mapped[str] = mapped_column(String(20), default="")
    driver_status: Mapped[str] = mapped_column(String(30), default="") # ACCEPTED, REJECTED, COMPLETED
    
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
