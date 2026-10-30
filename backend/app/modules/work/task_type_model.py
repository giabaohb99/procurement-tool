"""Danh mục LOẠI VIỆC của phân hệ Dự án (duoc-CR-656, D1b).

Vì sao có danh mục này: `kind` TASK/MILESTONE không phải loại nghiệp vụ, còn trường tùy
biến (`tab_work_label_field`) khai theo TỪNG dự án nên không gom được toàn công ty. Muốn
trả lời "thời gian trọn vòng của loại việc X" thì phải có một cột thật, dùng chung.

Theo pháp nhân (`company_id`), tùy chọn gắn phòng ban (`department_id`; 0 = cả pháp nhân).
Quản trị khai (gác `setting.write`). Không xóa cứng khi đã có task dùng — chuyển `is_active = 0`.
"""
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base


class WorkTaskType(Base, AuditMixin):
    __tablename__ = "tab_work_task_type"
    __table_args__ = (
        UniqueConstraint("company_id", "code", name="uq_work_task_type_code"),
        Index("ix_work_task_type_company", "company_id", "is_active"),
    )

    company_id: Mapped[int] = mapped_column(BigInteger, default=0)
    department_id: Mapped[int] = mapped_column(BigInteger, default=0, server_default="0")
    code: Mapped[str] = mapped_column(String(30), default="")
    name: Mapped[str] = mapped_column(String(120), default="")
    default_estimate_hours: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
