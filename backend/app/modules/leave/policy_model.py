"""CHÍNH SÁCH NGHỈ PHÉP + PHÂN BỔ CHÍNH SÁCH (duoc-CR-717) — kiểu Leave Policy / Leave Policy Assignment của ERPNext.

Gói chính sách = danh sách (loại nghỉ, số ngày/năm). Phân bổ = gán gói cho MỘT nhân sự trong `[từ, đến]`
(`effective_to` NULL = không thời hạn). Quỹ vẫn theo NĂM DƯƠNG LỊCH: phân bổ chỉ đổi cách tính `allocated_days`
(xem `policy_allocation_math`).

⚠️ `LeavePolicyAssignment` được lọc phạm vi bằng `apply_scope(..., "leave_balance")` nên PHẢI giữ đủ các cột mà
`SCOPE_FIELDS["leave_balance"]` đọc: `company_id` (chép từ hồ sơ lúc tạo) và `employee_id`. Thêm cột vào khai báo
phạm vi của `leave_balance` mà bảng này không có là chặn sạch (`false()`), không phải mở.
"""
from datetime import date

from sqlalchemy import BigInteger, Boolean, Date, Float, Index, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base


class LeavePolicy(Base, AuditMixin):
    """Gói chính sách nghỉ phép."""

    __tablename__ = "tab_leave_policy"

    code: Mapped[str] = mapped_column(String(30), unique=True)
    name: Mapped[str] = mapped_column(String(150))
    note: Mapped[str] = mapped_column(String(500), default="")
    #  Ngừng dùng chỉ chặn phân bổ MỚI; phân bổ đang có vẫn áp.
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("1"))


class LeavePolicyLine(Base, AuditMixin):
    """Một dòng của gói: loại nghỉ này được bao nhiêu ngày/năm."""

    __tablename__ = "tab_leave_policy_line"
    __table_args__ = (
        UniqueConstraint("policy_id", "leave_type_id", name="uq_leave_policy_line_type"),
    )

    policy_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    leave_type_id: Mapped[int] = mapped_column(BigInteger, default=0)
    annual_days: Mapped[float] = mapped_column(Float, default=0.0)


class LeavePolicyAssignment(Base, AuditMixin):
    """Gán một gói chính sách cho một nhân sự trong khoảng ngày."""

    __tablename__ = "tab_leave_policy_assignment"
    __table_args__ = (
        #  Chống bấm đúp; chồng ngày thật chặn ở service (khoảng ngày không diễn tả được bằng UNIQUE).
        UniqueConstraint("employee_id", "effective_from", name="uq_leave_policy_assign_emp_from"),
        Index("ix_leave_policy_assign_emp_dates", "employee_id", "effective_from", "effective_to"),
    )

    employee_id: Mapped[int] = mapped_column(BigInteger, default=0)
    #  Chép từ hồ sơ lúc tạo — để `apply_scope` lọc theo pháp nhân không phải JOIN.
    company_id: Mapped[int] = mapped_column(BigInteger, default=0)
    policy_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    effective_from: Mapped[date] = mapped_column(Date)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    note: Mapped[str] = mapped_column(String(500), default="")
