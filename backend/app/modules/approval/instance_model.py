"""PHIÊN CHẠY, VIỆC và DẤU VẾT của một lần duyệt (I17, I20, I21).

Ba bảng, ba nhiệm vụ tách bạch:
  · `tab_approval_instance` — một phiếu đang đi qua một luồng;
  · `tab_approval_task`     — một người phải làm gì ở một bước;
  · `tab_approval_action`   — chuyện đã xảy ra, **chỉ ghi thêm**.
"""
from datetime import datetime

from sqlalchemy import (BigInteger, DateTime, Index, Integer, SmallInteger,
                        String, Text)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base

# ── Trạng thái phiên chạy ───────────────────────────────────────────────────
INSTANCE_RUNNING = 1
INSTANCE_APPROVED = 2
INSTANCE_REJECTED = 3
INSTANCE_RETURNED = 4   # trả lại người nộp, còn sửa và gửi lại được
INSTANCE_WITHDRAWN = 5  # người nộp tự rút
INSTANCE_BLOCKED = 6    # không tìm được người duyệt, chờ quản trị xử lý

INSTANCE_STATUS_LABELS = {
    INSTANCE_RUNNING: "Đang chạy",
    INSTANCE_APPROVED: "Đã duyệt",
    INSTANCE_REJECTED: "Từ chối",
    INSTANCE_RETURNED: "Trả lại",
    INSTANCE_WITHDRAWN: "Đã rút",
    INSTANCE_BLOCKED: "Kẹt — không có người duyệt",
}

INSTANCE_OPEN_STATUSES = (INSTANCE_RUNNING, INSTANCE_BLOCKED)

# ── Trạng thái một việc ─────────────────────────────────────────────────────
TASK_WAITING = 1   # chưa tới lượt (bước lần lượt)
TASK_PENDING = 2   # đang chờ người này
TASK_APPROVED = 3
TASK_REJECTED = 4
#  ⚠️ TRẠNG THÁI RIÊNG, không được ghi thành "đã duyệt". Bản in dấu vết phải
#  phân biệt *người này đã ký* với *bước này tự qua vì trùng người* — gộp làm
#  một là bản in nói dối rằng có thêm một người đã xem xét.
TASK_SKIPPED_DUPLICATE = 5
TASK_CANCELLED = 6  # phiếu bị rút / bị trả lại nên việc không còn nghĩa

TASK_STATUS_LABELS = {
    TASK_WAITING: "Chưa tới lượt",
    TASK_PENDING: "Đang chờ",
    TASK_APPROVED: "Đã duyệt",
    TASK_REJECTED: "Từ chối",
    TASK_SKIPPED_DUPLICATE: "Tự qua vì trùng người duyệt",
    TASK_CANCELLED: "Đã hủy",
}

TASK_OPEN_STATUSES = (TASK_WAITING, TASK_PENDING)

# ── Hành động đã xảy ra ─────────────────────────────────────────────────────
ACTION_START = 1
ACTION_APPROVE = 2
ACTION_REJECT = 3
ACTION_RETURN = 4
ACTION_WITHDRAW = 5
ACTION_SKIP_DUPLICATE = 6
ACTION_REASSIGN = 7   # đổi người xử lý (nghỉ việc, bàn giao)
ACTION_COMMENT = 8
ACTION_ESCALATE = 9   # quá hạn, đẩy lên cấp trên
ACTION_FINISH = 10

ACTION_LABELS = {
    ACTION_START: "Bắt đầu trình duyệt",
    ACTION_APPROVE: "Duyệt",
    ACTION_REJECT: "Từ chối",
    ACTION_RETURN: "Trả lại",
    ACTION_WITHDRAW: "Rút lại",
    ACTION_SKIP_DUPLICATE: "Tự qua vì trùng người duyệt",
    ACTION_REASSIGN: "Chuyển người xử lý",
    ACTION_COMMENT: "Ý kiến",
    ACTION_ESCALATE: "Quá hạn — đẩy lên cấp trên",
    ACTION_FINISH: "Kết thúc",
}

#  Ba hành động BẮT BUỘC nhập lý do (I09/I10/I11). Không có lý do thì người nộp
#  không biết phải sửa gì, và lần gửi sau y hệt lần trước.
ACTIONS_REQUIRE_REASON = (ACTION_REJECT, ACTION_RETURN, ACTION_WITHDRAW)


class ApprovalInstance(Base, AuditMixin):
    """Một phiếu đang đi qua một luồng (I21)."""

    __tablename__ = "tab_approval_instance"
    __table_args__ = (
        #  Tra ngược từ chứng từ sang phiên chạy — mỗi lần mở một phiếu ra xem.
        Index("ix_approval_instance_entity", "entity", "entity_id", "status"),
    )

    entity: Mapped[str] = mapped_column(String(50))
    entity_id: Mapped[int] = mapped_column(BigInteger)
    #  Nhãn để hiện trên màn "Việc của tôi" mà không phải nạp bảng gốc lên.
    entity_code: Mapped[str] = mapped_column(String(100), default="")
    entity_title: Mapped[str] = mapped_column(String(500), default="")

    flow_id: Mapped[int] = mapped_column(BigInteger, index=True)
    flow_version: Mapped[int] = mapped_column(Integer, default=1)
    #  ⚠️ BẢN CHỤP của luồng lúc phiếu bắt đầu chạy, dạng JSON.
    #
    #  Phiếu chạy theo bản chụp của CHÍNH NÓ, không tham chiếu tới bản luồng
    #  đang sống. Đây là cách duy nhất để "sửa luồng khi có 5 phiếu đang chạy"
    #  không làm hỏng 5 phiếu đó: đọc bảng `tab_approval_node` lúc chạy thì
    #  người quản trị xóa một bước là phiếu đang ở bước đó mất đích tới.
    flow_snapshot: Mapped[str] = mapped_column(Text, default="")

    status: Mapped[int] = mapped_column(SmallInteger, default=INSTANCE_RUNNING)
    current_seq: Mapped[int] = mapped_column(Integer, default=1)

    started_by_employee_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    #  Lý do của hành động kết thúc phiếu — hiện ngay trên phiếu, không bắt
    #  người ta mở nhật ký ra tìm.
    finish_reason: Mapped[str] = mapped_column(String(1000), default="")


class ApprovalTask(Base, AuditMixin):
    """Một người phải xử lý một bước (I17)."""

    __tablename__ = "tab_approval_task"
    __table_args__ = (
        #  ⚠️ CHỈ MỤC QUAN TRỌNG NHẤT CỦA CẢ BỘ MÁY. Đây là truy vấn của màn
        #  "Việc của tôi" — màn được mở nhiều nhất trong hệ, chạy mỗi lần có
        #  người mở trang chủ. Thiếu chỉ mục này là quét cả bảng việc mỗi lần.
        Index("ix_approval_task_assignee", "assignee_employee_id", "status"),
        Index("ix_approval_task_instance", "instance_id", "node_seq"),
    )

    instance_id: Mapped[int] = mapped_column(BigInteger)
    node_seq: Mapped[int] = mapped_column(Integer, default=1)
    node_name: Mapped[str] = mapped_column(String(200), default="")
    #  Thứ tự trong bước, dùng cho `multi_mode = lần lượt`.
    order_no: Mapped[int] = mapped_column(Integer, default=1)

    assignee_employee_id: Mapped[int] = mapped_column(BigInteger)
    status: Mapped[int] = mapped_column(SmallInteger, default=TASK_WAITING)

    due_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    #  Đã nhắc quá hạn lần nào chưa — để không nhắc lại mỗi lần chạy tác vụ nền.
    reminded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    escalated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class ApprovalAction(Base, AuditMixin):
    """Dấu vết duyệt — **chỉ ghi thêm, không sửa, không xóa** (I20).

    Ba cột danh tính chứ không phải một: bản in phải ghi đúng câu *"ông B duyệt
    thay ông A theo ủy quyền số 12"*. Ghi mỗi một người là sau này không phân
    biệt được ai chịu trách nhiệm, mà đó chính là câu kiểm toán sẽ hỏi.
    """

    __tablename__ = "tab_approval_action"
    __table_args__ = (Index("ix_approval_action_instance", "instance_id", "id"),)

    instance_id: Mapped[int] = mapped_column(BigInteger)
    task_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    node_seq: Mapped[int] = mapped_column(Integer, default=0)
    node_name: Mapped[str] = mapped_column(String(200), default="")

    action: Mapped[int] = mapped_column(SmallInteger, default=ACTION_APPROVE)
    #  Người thật sự bấm nút.
    actor_employee_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    #  Người mà việc đó vốn là của họ (khi duyệt thay).
    on_behalf_of_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    delegation_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    comment: Mapped[str] = mapped_column(Text, default="")
