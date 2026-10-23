"""YÊU CẦU SỬA HỒ SƠ do nhân viên tự khai, nhân sự duyệt — `tab_employee_change_request` (duoc-CR-676, C6).

Nhóm LIÊN HỆ vẫn tự sửa áp ngay (`self_contact_service`, bao-CR-508). Bốn nhóm còn lại — cá nhân ·
ngân hàng · giấy tờ · hộ gia đình — nhân viên chỉ GỬI, phòng Nhân sự duyệt rồi mới ghi vào hồ sơ.

⚠️ FK MỀM `employee_id` (khuôn `tab_employee_work_history`): xóa hồ sơ thì dọn ở `contact_service.delete_all_of`.
⚠️ Hai cột JSON chứa giá trị NHẠY CẢM (số TK, CCCD, người thân) — `core/change_tracker` che nội dung
(`TABLE_FIELD_ALLOWLIST`), chỉ giữ dấu vết ở mức dòng.
⚠️ Mỗi nhân sự chỉ có TỐI ĐA MỘT yêu cầu đang chờ — chốt bằng cột `pending_employee_id` UNIQUE (= employee_id khi
đang chờ, NULL khi đã xử lý/rút; MySQL cho nhiều NULL trong chỉ mục duy nhất). Service bắt IntegrityError → 409.
"""
from datetime import datetime

from sqlalchemy import JSON, BigInteger, DateTime, Index, SmallInteger, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base


class EmployeeChangeRequest(Base, AuditMixin):
    __tablename__ = "tab_employee_change_request"
    __table_args__ = (
        Index("ix_employee_change_request_status", "status"),
        UniqueConstraint("pending_employee_id", name="uq_employee_change_request_pending"),
    )

    employee_id: Mapped[int] = mapped_column(BigInteger, index=True)
    pending_employee_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    #  `EmployeeChangeRequestStatus` (core/hr_change_request_codes.py).
    status: Mapped[int] = mapped_column(SmallInteger, default=1)
    #  [{group, field, before, after}] — giá trị đã chuẩn hóa JSON (ngày = ISO).
    changes: Mapped[list] = mapped_column(JSON)
    #  {before: [...], after: [...]} hoặc NULL nếu không đụng hộ gia đình.
    families: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    note: Mapped[str] = mapped_column(String(500), default="")
    reject_reason: Mapped[str] = mapped_column(String(500), default="")
    decided_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    decided_by: Mapped[int] = mapped_column(BigInteger, default=0)
