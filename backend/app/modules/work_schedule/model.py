"""LỊCH LÀM VIỆC — mẫu lịch tuần + gán theo hệ thống / pháp nhân / phòng ban / nhân sự.

Ba bảng; FK MỀM (không `ForeignKey`) theo quy ước `department_id`/`manager_id` của
repo — id có thật được kiểm ở service. Bộ mã: `app/core/work_schedule_codes.py`.
"""
from datetime import date, time

from sqlalchemy import (BigInteger, Boolean, Date, Index, SmallInteger, String, Time,
                        UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base


class WorkSchedule(Base, AuditMixin):
    """Mẫu lịch tuần (đủ 7 dòng ở `WorkScheduleDay`)."""

    __tablename__ = "tab_work_schedule"
    __table_args__ = (UniqueConstraint("name", name="uq_work_schedule_name"),)

    name: Mapped[str] = mapped_column(String(150))
    note: Mapped[str] = mapped_column(String(500), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class WorkScheduleDay(Base, AuditMixin):
    """Một ngày trong tuần của mẫu. `weekday`: 0 = Thứ hai … 6 = Chủ nhật (= `date.weekday()`)."""

    __tablename__ = "tab_work_schedule_day"
    __table_args__ = (
        UniqueConstraint("schedule_id", "weekday", name="uq_work_schedule_day"),
    )

    schedule_id: Mapped[int] = mapped_column(BigInteger)
    weekday: Mapped[int] = mapped_column(SmallInteger)
    day_kind: Mapped[int] = mapped_column(SmallInteger)   # WorkDayKind
    start_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    end_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    lunch_start: Mapped[time | None] = mapped_column(Time, nullable=True)
    lunch_end: Mapped[time | None] = mapped_column(Time, nullable=True)


class WorkScheduleAssignment(Base, AuditMixin):
    """Gán một mẫu cho một đối tượng trong khoảng ngày hiệu lực."""

    __tablename__ = "tab_work_schedule_assignment"
    __table_args__ = (
        #  Chốt DB chống bấm đúp / hai người cùng tạo: cùng đối tượng không có hai dòng cùng ngày bắt đầu.
        UniqueConstraint("target_level", "target_id", "effective_from", name="uq_wsa_target_from"),
        Index("ix_wsa_target", "target_level", "target_id", "effective_from"),
        Index("ix_wsa_schedule", "schedule_id"),
    )

    target_level: Mapped[int] = mapped_column(SmallInteger)   # WorkScheduleLevel
    target_id: Mapped[int] = mapped_column(BigInteger, default=0)  # 0 khi SYSTEM
    schedule_id: Mapped[int] = mapped_column(BigInteger)
    effective_from: Mapped[date] = mapped_column(Date)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)  # NULL = không thời hạn
    note: Mapped[str] = mapped_column(String(500), default="")
    #  Dòng gán GỐC đã kích hoạt việc tự đóng / tự nối dòng này (xóa dòng gốc thì mở lại, M4).
    linked_assignment_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
