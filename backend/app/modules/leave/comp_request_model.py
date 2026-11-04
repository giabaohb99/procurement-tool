"""PHIẾU XIN NGHỈ BÙ (duoc-CR-715 giai đoạn C) — nhân sự đi làm vào ngày lễ / ngày nghỉ theo lịch thì xin nghỉ bù.

Duyệt xong, `days` được cộng vào `tab_leave_balance.comp_days` của năm `work_date`, loại nghỉ bật
`is_compensatory` — từ đó đơn nghỉ phép trừ quỹ như mọi loại khác.
"""
from datetime import date, datetime

from sqlalchemy import BigInteger, Boolean, Date, DateTime, Float, Index, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base

from .constants import LeaveCompStatus


class LeaveCompRequest(Base, AuditMixin):
    """Một phiếu xin nghỉ bù cho MỘT ngày đã đi làm."""

    __tablename__ = "tab_leave_comp_request"
    __table_args__ = (
        #  Luật "một ngày một phiếu" và lọc theo người + ngày.
        Index("ix_leave_comp_emp_date", "employee_id", "work_date"),
        #  Chốt chặn THẬT của "một ngày một phiếu còn hiệu lực": `active_key` UNIQUE, NULL khi phiếu hết hiệu lực
        #  (từ chối / hủy / xóa) — nhiều NULL không đụng nhau. Câu kiểm ở service chỉ để có câu báo đẹp.
        Index("uq_leave_comp_active_key", "active_key", unique=True),
    )

    code: Mapped[str] = mapped_column(String(30), unique=True)
    company_id: Mapped[int] = mapped_column(BigInteger, default=0)
    department_id: Mapped[int] = mapped_column(BigInteger, default=0)
    #  Người đi làm (được nhận ngày bù). `created_by` có thể là người lập hộ.
    employee_id: Mapped[int] = mapped_column(BigInteger, default=0)
    work_date: Mapped[date] = mapped_column(Date)
    #  0.5 hoặc 1 — số ngày nghỉ bù xin nhận.
    days: Mapped[float] = mapped_column(Float, default=1.0)
    reason: Mapped[str] = mapped_column(String(1000), default="")
    #  Loại nghỉ NHẬN ngày bù, chốt lúc GỬI duyệt — duyệt / hủy cộng trừ đúng loại này, không dò lại danh mục.
    comp_leave_type_id: Mapped[int] = mapped_column(BigInteger, default=0)
    #  Năm quỹ được cộng, chốt lúc DUYỆT: max(năm đi làm, năm hôm nay) — năm đã kết sổ không nhận thêm ngày.
    balance_year: Mapped[int] = mapped_column(SmallInteger, default=0)
    #  "<employee_id>:<work_date>" khi phiếu còn hiệu lực, NULL khi hết — xem `__table_args__`.
    active_key: Mapped[str | None] = mapped_column(String(40), nullable=True)
    status: Mapped[int] = mapped_column(SmallInteger, default=int(LeaveCompStatus.DRAFT))
    approval_instance_id: Mapped[int] = mapped_column(BigInteger, default=0)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    #  Lý do từ chối / trả về / hủy.
    decision_note: Mapped[str] = mapped_column(String(500), default="")
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
