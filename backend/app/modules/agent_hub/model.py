"""Sổ của Agent Hub — bốn bảng. Thiết kế: doc/agent-hub/01-thiet-ke-ky-thuat.md §5.

Bộ mã số khai ở `constants.py` (R2/QĐ-11). Không cột trạng thái nào lưu chữ tiếng Việt.
"""
from datetime import datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    DateTime,
    Float,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base

from .constants import DIR_IN, RISK_MEDIUM, RUN_RUNNING, SRC_TELEGRAM, ST_INBOX


class AgentTask(Base, AuditMixin):
    """Một đầu việc: gom từ một hoặc nhiều tin nhắn / phiếu hỗ trợ cùng loại."""

    __tablename__ = "tab_agent_task"

    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255), default="")
    source: Mapped[int] = mapped_column(SmallInteger, default=SRC_TELEGRAM)
    #  Không gắn `index=True` ở đây: index ghép `(status, created_at)` bên dưới đã phủ
    #  luôn phần `status` đứng đầu, thêm index đơn nữa chỉ tốn thêm một lần ghi mỗi lần
    #  task đổi trạm.
    status: Mapped[int] = mapped_column(SmallInteger, default=ST_INBOX)

    summary: Mapped[str] = mapped_column(Text, default="")
    plan: Mapped[str] = mapped_column(Text, default="")

    #  CỘT QUAN TRỌNG NHẤT BẢNG NÀY. Danh sách đường dẫn tệp mà bản đề xuất nói sẽ
    #  đụng tới, vd ["backend/app/modules/leave/service.py"]. Ở bậc 2 nó là PHANH TAY:
    #  runner so danh sách tệp bot thật sự sửa với danh sách này, lệch quá ngưỡng thì
    #  dừng và không commit. Rỗng nghĩa là Gemini không viết nổi phạm vi cụ thể, và
    #  task đó KHÔNG được sang CODE (luật B2) — cái rỗng ở đây là một chốt chặn, không
    #  phải một ô chưa ai điền.
    plan_files: Mapped[list] = mapped_column(JSON, default=list)
    #  Bài kiểm dự kiến, Gemini viết ở PLAN. Bậc 2 nối thẳng vào task brief.
    test_plan: Mapped[str] = mapped_column(Text, default="")
    #  Tài liệu / CR cũ mà Gemini viện dẫn: [{"title", "source", "score"}]. Luật B4 —
    #  phải lấy từ Qdrant, cấm bịa mã CR.
    related_docs: Mapped[list] = mapped_column(JSON, default=list)
    #  Câu Gemini hỏi lại khi đề bài mơ hồ. Có câu ở đây = task đứng ở NEEDS_INPUT.
    questions: Mapped[list] = mapped_column(JSON, default=list)

    risk_level: Mapped[int] = mapped_column(SmallInteger, default=RISK_MEDIUM)

    #  Bốn cột dưới đây BẬC 1 KHÔNG BAO GIỜ ĐIỀN — bậc 1 dừng ở PLAN. Khai sẵn vì
    #  chúng là cùng một tờ phiếu, thêm cột sau tốn một migration trên bảng đang chạy.
    branch_name: Mapped[str] = mapped_column(String(120), default="")
    pr_url: Mapped[str] = mapped_column(String(255), default="")
    deployed_dev_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    deployed_prod_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)

    #  Đại ca duyệt bản đề xuất lúc nào. `approved_by` là chat_id Telegram chứ KHÔNG
    #  phải id người dùng ERP: bậc 1 không đi qua đăng nhập ERP, và ghi một id người
    #  dùng mà không ai đăng nhập thì đó là một dấu vết giả.
    approved_by_chat: Mapped[str] = mapped_column(String(50), default="")
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)

    #  Vì sao task dừng: câu lỗi hoặc lý do đại ca bỏ. Để đọc sổ sáu tháng sau.
    note: Mapped[str] = mapped_column(Text, default="")

    __table_args__ = (
        #  Vòng gom tìm "task còn sống" rất nhiều lần; không có index này thì mỗi lượt
        #  quét cả bảng.
        Index("ix_agent_task_status_created", "status", "created_at"),
    )


class AgentTaskItem(Base, AuditMixin):
    """Nối NHIỀU đầu vào vào MỘT task — đây là chỗ việc "gom nhiều ticket cùng loại
    vào một lần" được ghi lại.

    ⚠️ Lệch một chút so với bản thiết kế §5 (QĐ-AI-8, xem change-log-ai.md). Thiết kế
    ghi bảng `tab_agent_task_ticket` với đúng một cột `ticket_id` trỏ `tab_ticket`.
    Nhưng bậc 1 KHÔNG có `tab_ticket` nào cả — nguồn duy nhất là tin nhắn Telegram —
    nên một bảng chỉ trỏ được sang `tab_ticket` sẽ rỗng suốt bậc 1, tức là chức năng
    gom nhóm không chạy thật, mà "bot có gom được không" lại đúng là một trong hai câu
    bậc 1 sinh ra để trả lời.

    Nên bảng này mang một CẶP `(source, ref_id)`:
      - `source = SRC_TELEGRAM`  -> `ref_id` = `tab_agent_message.id`
      - `source = SRC_ERP_TICKET`-> `ref_id` = `tab_ticket.id`   (bậc sau, AN-005)
    Bậc sau nối `tab_ticket` vào là thêm dòng, không phải sửa bảng.
    """

    __tablename__ = "tab_agent_task_item"

    task_id: Mapped[int] = mapped_column(BigInteger, index=True)
    source: Mapped[int] = mapped_column(SmallInteger, default=SRC_TELEGRAM)
    ref_id: Mapped[int] = mapped_column(BigInteger, default=0)
    merged_by: Mapped[int] = mapped_column(SmallInteger, default=1)

    __table_args__ = (
        #  Một đầu vào chỉ được thuộc MỘT task. Không có ràng buộc này thì một tin
        #  nhắn lỡ chạy qua hai vòng gom sẽ đẻ ra hai task giống hệt nhau, và đại ca
        #  nhận hai thẻ Telegram cho cùng một việc.
        Index("uq_agent_task_item_ref", "source", "ref_id", unique=True),
    )


class AgentRun(Base, AuditMixin):
    """Mỗi lần gọi model (bậc 1) hoặc chạy bot code (bậc 2) là một dòng.

    Không có bảng này thì không ai biết con bot đốt bao nhiêu và làm gì.
    """

    __tablename__ = "tab_agent_run"

    task_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    stage: Mapped[int] = mapped_column(SmallInteger, default=0)
    provider: Mapped[str] = mapped_column(String(30), default="")
    model: Mapped[str] = mapped_column(String(80), default="")
    status: Mapped[int] = mapped_column(SmallInteger, default=RUN_RUNNING)

    started_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)

    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    #  ĐÃ CỘNG token "suy nghĩ" vào đây — Gemini tính giá chúng như output, tách ra
    #  hai cột thì mọi chỗ cộng chi phí đều phải nhớ cộng cả hai, và sẽ có chỗ quên.
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)

    error: Mapped[str] = mapped_column(Text, default="")
    #  Bậc 1: câu trả lời thô của model (để dò khi nó trả JSON hỏng).
    #  Bậc 2: danh sách tệp đã đụng, lệnh đã chạy, kết quả cổng kiểm.
    artifact: Mapped[dict] = mapped_column(JSON, default=dict)


class AgentMessage(Base, AuditMixin):
    """Mọi lượt Telegram, CẢ HAI CHIỀU.

    Lưu cả chiều bot gửi để sáu tháng sau còn truy được *vì sao hồi đó chốt vậy* —
    đúng thứ `nhat-ky-task.md` đang làm cho việc tay (luật F3).
    """

    __tablename__ = "tab_agent_message"

    #  0 = chưa thuộc task nào. Tin nhắn ĐẾN nằm ở 0 cho tới khi vòng gom xếp nó vào
    #  một task — chính cái 0 này là hàng đợi INBOX, không cần bảng riêng.
    task_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    direction: Mapped[int] = mapped_column(SmallInteger, default=DIR_IN)
    chat_id: Mapped[str] = mapped_column(String(50), default="")
    tg_message_id: Mapped[int] = mapped_column(BigInteger, default=0)
    body: Mapped[str] = mapped_column(Text, default="")
    #  Nút đã bấm, vd "plan" / "approve" / "cancel". Rỗng = tin nhắn chữ thường.
    action: Mapped[str] = mapped_column(String(50), default="")
    #  ai-CR-035: tệp đính kèm đã lưu, [{"path": "/agent-files/…", "kind": "photo", "group": "…"}].
    #  `group` = media_group_id của Telegram (album nhiều ảnh), để ghép các ảnh cùng album vào một tin.
    files: Mapped[list | None] = mapped_column(JSON, default=list, nullable=True)

    __table_args__ = (
        #  Vòng gom hỏi "tin ĐẾN nào chưa thuộc task nào, cũ hơn N giây" mỗi phút.
        Index("ix_agent_msg_pending", "direction", "task_id", "created_at"),
    )


class AgentCursor(Base, AuditMixin):
    """Con trỏ `getUpdates` của Telegram — đúng một dòng, `name = "telegram_offset"`.

    Telegram giữ tin chưa xác nhận tối đa 24h rồi bỏ. Không lưu con trỏ xuống DB thì
    mỗi lần restart api là bot đọc lại toàn bộ tin cũ và đẻ lại một loạt task trùng.
    """

    __tablename__ = "tab_agent_cursor"

    name: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    value: Mapped[int] = mapped_column(BigInteger, default=0)


class AgentChatLink(Base, AuditMixin):
    """Liên kết một chat Telegram với một tài khoản ERP (ai-CR-038).

    Một dòng đi qua ba mốc: người dùng LẤY MÃ ở trang cá nhân ERP (`code_hash` + `code_expires_at`,
    `chat_id` rỗng) -> nhắn `/dangnhap <mã>` cho bot (`chat_id` + `linked_at` + `expires_at`, xóa mã)
    -> hết hạn hoặc `/dangxuat` / gỡ ở web (`revoked_at`). Không bao giờ hỏi mật khẩu trong chat:
    Telegram giữ lịch sử vĩnh viễn. Mã chỉ lưu dạng băm.
    """

    __tablename__ = "tab_agent_chat_link"

    user_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    chat_id: Mapped[str] = mapped_column(String(50), default="", index=True)
    #  Tên hiển thị Telegram lúc liên kết — để trang cá nhân nói «đang nối với ‹tên›».
    tg_name: Mapped[str] = mapped_column(String(255), default="")
    code_hash: Mapped[str] = mapped_column(String(64), default="", index=True)
    code_expires_at: Mapped[datetime | None] = mapped_column(DateTime, default=None, nullable=True)
    linked_at: Mapped[datetime | None] = mapped_column(DateTime, default=None, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, default=None, nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, default=None, nullable=True)
