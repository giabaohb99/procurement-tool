"""LOẠI TRỪ EMAIL — không gửi email thông báo cho một số người.

Chặn theo 3 mức, đọc thông tin từ hồ sơ nhân sự (`tab_employee`):
  · `employee`  — đúng một người (theo `employee_id`);
  · `department`— cả một phòng ban (mọi người có `department_id` này);
  · `company`   — cả một pháp nhân (mọi người có `company_id` này).

CHỈ chặn EMAIL — chuông trong ứng dụng vẫn gửi. `label` lưu sẵn tên để hiển thị,
khỏi tra ngược mỗi lần liệt kê.
"""
from sqlalchemy import BigInteger, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base


class EmailExclusion(Base, AuditMixin):
    __tablename__ = "tab_email_exclusion"
    __table_args__ = (
        UniqueConstraint("scope", "ref_id", "event", name="uq_email_exclusion_scope_ref_event"),
    )

    #  employee | department | company
    scope: Mapped[str] = mapped_column(String(20), index=True)
    ref_id: Mapped[int] = mapped_column(BigInteger, index=True)
    label: Mapped[str] = mapped_column(String(255), default="")
    #  Áp cho MẪU EMAIL nào: "" = mọi mẫu; hoặc mã event (vd "dx_approved_dispatcher").
    event: Mapped[str] = mapped_column(String(50), default="", index=True)
