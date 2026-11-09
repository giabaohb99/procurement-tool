"""PHIẾU THANH TOÁN NGHỈ PHÉP (duoc-CR-719) — đổi ngày phép chưa nghỉ ra tiền: cuối năm hoặc khi nghỉ việc.

Phiếu CHỈ ghi SỐ NGÀY. Số tiền do người có quyền tài chính nhập ở YCTT sinh ra sau khi phiếu được duyệt, nên phiếu
không bao giờ lộ lương. Duyệt xong: `pending_days` -= days, `encashed_days` += days (bảng quỹ) và sinh YCTT nguồn
`leave_encashment` (liên kết bằng `payment_request_id` ở đây + `source_ref_id` bên YCTT).
"""
from datetime import date, datetime

from sqlalchemy import BigInteger, Boolean, Date, DateTime, Float, Index, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base

from .constants import LeaveEncashmentReason, LeaveEncashmentStatus


class LeaveEncashment(Base, AuditMixin):
    """Một phiếu thanh toán ngày phép của MỘT người, MỘT loại nghỉ, MỘT năm quỹ, MỘT lý do."""

    __tablename__ = "tab_leave_encashment"
    __table_args__ = (
        Index("ix_leave_encash_emp_year", "employee_id", "balance_year"),
        #  Chốt chặn THẬT của "một phiếu còn hiệu lực / (người, loại, năm, lý do)": `active_key` UNIQUE, NULL khi phiếu hết
        #  hiệu lực (từ chối / hủy / xóa) — nhiều NULL không đụng nhau. Câu kiểm ở service chỉ để có câu báo đẹp.
        Index("uq_leave_encash_active_key", "active_key", unique=True),
    )

    code: Mapped[str] = mapped_column(String(30), unique=True)          # TTP00001
    company_id: Mapped[int] = mapped_column(BigInteger, default=0)
    department_id: Mapped[int] = mapped_column(BigInteger, default=0)
    #  Người được nhận tiền. `created_by` có thể là Nhân sự lập hộ.
    employee_id: Mapped[int] = mapped_column(BigInteger, default=0)
    leave_type_id: Mapped[int] = mapped_column(BigInteger, default=0)
    #  Năm của dòng quỹ bị trừ (năm nay hoặc năm trước).
    balance_year: Mapped[int] = mapped_column(SmallInteger, default=0)
    reason_kind: Mapped[int] = mapped_column(SmallInteger, default=int(LeaveEncashmentReason.YEAR_END))
    encashment_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    days: Mapped[float] = mapped_column(Float, default=0.0)
    #  Phần của `days` lấy từ ngày mang sang, chốt lúc DUYỆT (0 khi chưa duyệt / lý do cuối năm) — để hủy phiếu trả đúng
    #  `encashed_carried_days` của dòng quỹ (duoc-CR-719 M1).
    carried_paid_days: Mapped[float] = mapped_column(Float, default=0.0, server_default="0")
    #  Ảnh chụp lúc gửi duyệt — số dùng được và số được phép thanh toán, để duyệt xong còn đối chiếu được.
    balance_snapshot: Mapped[float] = mapped_column(Float, default=0.0)
    encashable_snapshot: Mapped[float] = mapped_column(Float, default=0.0)
    note: Mapped[str] = mapped_column(String(1000), default="")
    status: Mapped[int] = mapped_column(SmallInteger, default=int(LeaveEncashmentStatus.DRAFT))
    approval_instance_id: Mapped[int] = mapped_column(BigInteger, default=0)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    #  Lý do từ chối / trả về / hủy.
    decision_note: Mapped[str] = mapped_column(String(500), default="")
    #  YCTT sinh ra khi duyệt; 0 = chưa sinh.
    payment_request_id: Mapped[int] = mapped_column(BigInteger, default=0)
    #  "<employee_id>:<leave_type_id>:<balance_year>" khi phiếu còn hiệu lực, NULL khi hết — xem `__table_args__`.
    active_key: Mapped[str | None] = mapped_column(String(60), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
