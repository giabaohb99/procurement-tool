"""`tab_work_cycle` — vòng đời phiếu ĐÃ TÍNH SẴN, nguồn của số liệu năng lực (duoc-CR-656, D1a).

Một dòng / (phiếu, vai, người). Vì sao lưu kết quả thay vì tính lại từ nhật ký mỗi lần hỏi:
`tab_change_log` chỉ giữ 16 tháng, còn câu hỏi «chị A làm một YCMH trung bình mấy ngày» cần
nhìn xa hơn; và đọc từ bảng này là một truy vấn gom, không phải quét nhật ký.

Không AuditMixin (bảng dẫn xuất, dựng lại được), giữ 3 năm. Chỉ chứa mã + id + số — KHÔNG nội dung phiếu.
"""
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (BigInteger, Boolean, Date, DateTime, Float, Index, Numeric,
                        SmallInteger, UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base


class WorkCycle(Base):
    __tablename__ = "tab_work_cycle"
    __table_args__ = (
        UniqueConstraint("kind", "entity_id", "role", "employee_id", name="uq_work_cycle_key"),
        Index("ix_work_cycle_done", "done_at", "kind"),
        Index("ix_work_cycle_emp", "employee_id", "kind", "done_at"),
        Index("ix_work_cycle_type", "task_type_id", "done_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    kind: Mapped[int] = mapped_column(SmallInteger)                     # CycleKind
    entity_id: Mapped[int] = mapped_column(BigInteger)
    role: Mapped[int] = mapped_column(SmallInteger)                     # CycleRole
    employee_id: Mapped[int] = mapped_column(BigInteger)
    company_id: Mapped[int] = mapped_column(BigInteger, default=0)
    department_id: Mapped[int] = mapped_column(BigInteger, default=0)   # của nhân sự LÚC TÍNH
    task_type_id: Mapped[int] = mapped_column(BigInteger, default=0)    # chỉ task Dự án
    started_at: Mapped[datetime] = mapped_column(DateTime)              # UTC naive như mọi DateTime của hệ
    done_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    outcome: Mapped[int] = mapped_column(SmallInteger)                  # CycleOutcome
    #  Giờ trôi qua giữa `started_at` và `done_at` (ngày lịch — Q12); NULL khi chưa xong / mốc lệch.
    cycle_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    rework_count: Mapped[int] = mapped_column(SmallInteger, default=0)
    #  True = `done_at` KHÔNG lấy từ lịch sử trạng thái mà ước từ cột mốc của chính bảng (`completed_at`,
    #  `decided_at`…) hoặc `updated_at`. Báo cáo nên cho người xem biết hoặc loại ra.
    is_estimated: Mapped[bool] = mapped_column(Boolean, default=False)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)  # chỉ task có hạn
    is_late: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    estimate_hours: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    actual_hours: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    review_outcome: Mapped[int] = mapped_column(SmallInteger, default=0)  # WorkTaskOutcome của task
    computed_at: Mapped[datetime] = mapped_column(DateTime)
