"""Phân hệ Công việc — cụm việc: cột kanban · task · người phụ trách.

Quy ước chung của phân hệ (employee_id, ngày dạng chuỗi, IntEnum) nằm ở đầu
`model.py` — đọc trước. Thiết kế: `doc/erp/cong-viec/02-bang-du-lieu.md` §3.
"""
from datetime import datetime

from sqlalchemy import (BigInteger, DateTime, ForeignKey, Index, SmallInteger,
                        String, Text, UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base
from app.modules.work.model import WorkAssigneeKind, WorkTaskStatus


class WorkSection(Base, AuditMixin):
    """Cột kanban của MỘT list ("Cần làm", "Đang làm"…).

    Đây là NHÃN NGƯỜI DÙNG TỰ ĐẶT, không phải trạng thái — trạng thái hệ thống
    nằm ở `WorkTask.status` (Q2). Tạo list là seed sẵn ba cột mặc định; xóa cột
    còn task thì bắt chọn cột nhận trước, không để task mồ côi.
    """

    __tablename__ = "tab_work_section"

    company_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    list_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tab_work_list.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(100), default="")
    color: Mapped[str] = mapped_column(String(20), default="")
    sort_order: Mapped[int] = mapped_column(BigInteger, default=0)


class WorkTask(Base, AuditMixin):
    """Task VÀ việc con — chung một bảng, phân biệt bằng `parent_id`.

    - Việc con mang `list_id` CỦA CHA và `section_id = NULL`: không nằm cột nào
      nên không bao giờ lọt ra kanban (C-05, Q10 chốt "bản đầu tuyệt đối ẩn").
    - **Chặn cấp 3 là việc của service**: cha đã có `parent_id` thì không nhận
      con. DB không giữ hộ được ràng buộc này.
    - Đếm việc của list/cột và tiến độ chỉ tính TASK CHA (`parent_id IS NULL`);
      việc con chỉ đóng góp vào `n/m` của thẻ cha (C-02).
    - Xóa là XÓA MỀM (`deleted_at`) cho thùng rác B-09 — mọi query thường phải
      tự lọc `deleted_at IS NULL`, không có bộ lọc toàn cục nào làm hộ.

    `creator_employee_id` là trục NHÂN SỰ của người tạo, dùng cho luật "MEMBER
    chỉ xóa được task mình tạo" (`04-phan-quyen.md` §3). Cố ý KHÔNG mượn
    `created_by` của `AuditMixin`: cột đó là user_id ở toàn hệ, đổi nghĩa riêng
    một bảng là cái bẫy cho người đọc sau.
    """

    __tablename__ = "tab_work_task"
    __table_args__ = (
        #  Query chính của kanban và màn danh sách: lấy task cha còn sống của
        #  một list. Ba cột đi cùng nhau trong đúng một mệnh đề WHERE.
        Index("ix_work_task_list_parent", "list_id", "parent_id", "deleted_at"),
        #  Job nhắc hạn Celery quét theo hạn + trạng thái (F-03).
        Index("ix_work_task_due_status", "due_date", "status"),
    )

    company_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    list_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tab_work_list.id", ondelete="CASCADE"), index=True
    )
    section_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("tab_work_section.id", ondelete="SET NULL"), nullable=True
    )
    parent_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("tab_work_task.id", ondelete="CASCADE"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(500), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[int] = mapped_column(SmallInteger, default=int(WorkTaskStatus.OPEN))
    #  Ngày dạng chuỗi "YYYY-MM-DD" — xem quy ước 2 ở đầu `model.py`.
    start_date: Mapped[str] = mapped_column(String(10), default="")
    due_date: Mapped[str] = mapped_column(String(10), default="")
    #  Thứ tự tay trong cột (B-07); với việc con là thứ tự trong danh sách con.
    sort_order: Mapped[int] = mapped_column(BigInteger, default=0)
    creator_employee_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class WorkTaskAssignee(Base, AuditMixin):
    """Người phụ trách (PIC) và người theo dõi của một task.

    Nhiều PIC được, đúng như Lark (Q5) — giao diện khuyến khích một người chính
    chứ dữ liệu không chặn. Unique `(task_id, employee_id)`: một người một vai
    trên một task, PIC thắng follower khi trùng.

    Index `employee_id` phục vụ hai chỗ đọc nặng: màn "Việc của tôi" (G-03) và
    khóa `job:{id}` đổ vào tab Việc cần làm (F-02).
    """

    __tablename__ = "tab_work_task_assignee"
    __table_args__ = (
        UniqueConstraint("task_id", "employee_id", name="uq_work_task_assignee"),
        Index("ix_work_task_assignee_emp", "employee_id"),
    )

    task_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tab_work_task.id", ondelete="CASCADE"), index=True
    )
    employee_id: Mapped[int] = mapped_column(BigInteger, default=0)
    kind: Mapped[int] = mapped_column(SmallInteger, default=int(WorkAssigneeKind.PIC))
