"""Sổ của Agent Hub — bốn bảng. Thiết kế: doc/agent-hub/01-thiet-ke-ky-thuat.md §5.

Bộ mã số khai ở `constants.py` (R2/QĐ-11). Không cột trạng thái nào lưu chữ tiếng Việt.
"""
from datetime import datetime

from sqlalchemy import (
    Boolean,
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
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import Mapped, mapped_column, synonym

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
    #  ai-CR-057: 0 = làn đầy đủ, 1 = đường tắt việc nhỏ (không rà soát, tự duyệt kế hoạch gọn).
    lane: Mapped[int] = mapped_column(SmallInteger, default=0)

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
    #  ai-CR-054: máy sửa mã đang giữ việc này (dính từ lượt đầu; 0 = hàng đợi cũ / chưa giao).
    runner_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
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
    #  ai-CR-053: tài khoản ERP có khóa Gemini đã trả tiền cho lượt này (0 = khóa `.env` của máy bot).
    owner_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    #  ai-CR-098: dòng `tab_ai_key` đã trả lời lượt này (0 = khóa `.env` / không rõ) — để áp `daily_cap` từng khóa.
    key_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
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
    #  ai-CR-095 (C-06): 0 chưa phân · 1 việc công ty · 2 việc cá nhân — bộ phân loại ý định gán.
    scope: Mapped[int] = mapped_column(SmallInteger, default=0)

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
    #  ai-CR-059: chuông ERP chuyển sang chat này — 0 tắt · 1 việc của tôi (mặc định) · 2 tất cả.
    notify_mode: Mapped[int] = mapped_column(SmallInteger, default=1)


class AgentGrant(Base, AuditMixin):
    """Ai được ra lệnh SỬA MÃ qua bot, ở cấp nào (ai-CR-051, K-01 «cách 3»).

    Cấp bằng CÂU NHẮN của đại ca trên Telegram, không lên web, không build, không khởi động lại.
    Gắn với TÀI KHOẢN ERP (`user_id`), không gắn với chat: người đó đăng nhập bot bằng chat nào cũng
    mang theo cấp của mình. Gỡ = đóng dấu `revoked_at`, dòng cũ giữ lại làm sổ.
    Cấp: 1 = duyệt kế hoạch (duyệt, sửa kế hoạch, làm tiếp, hỏi tình trạng), 2 = gộp dev (thêm gộp,
    deploy dev, thu hồi). Prod không cấp cho ai; chat của đại ca không cần dòng nào.
    """

    __tablename__ = "tab_agent_grant"

    user_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    level: Mapped[int] = mapped_column(SmallInteger, default=0)
    #  Chat đã cấp (chỉ có thể là chat đại ca) — để sổ trả lời «ai cấp, lúc nào».
    granted_by_chat: Mapped[str] = mapped_column(String(50), default="")
    note: Mapped[str] = mapped_column(String(255), default="")
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, default=None, nullable=True)


class AiKey(Base, AuditMixin):
    """Sổ khóa AI MỘT BẢNG cho công ty lẫn cá nhân (ai-CR-053 D-01 → ai-CR-098 C-04, đại ca chốt 07/10/2026).

    `owner_type` 1 công ty (`owner_id` 0) · 2 cá nhân (`owner_id` = user_id). `provider` gemini · claude · openai ·
    openrouter. `priority` 1 = khóa chính, 2, 3… dự phòng (hỏng vì hết tiền / hạn mức / khóa sai thì tự nhảy).
    `model` mặc định cho khóa đó (trống = mặc định của hãng); `daily_cap` trần lượt/ngày riêng (0 = trần chung).
    Khóa lưu mã hóa Fernet (cùng khóa suy từ `JWT_SECRET` như cấu hình hệ thống), chỉ giữ 4 ký tự cuối; gỡ = `revoked_at`
    giữ lịch sử; nghỉ việc thì đóng cùng lúc khóa phiên. Bot không bao giờ in khóa thô ra chat hay log.
    Đọc/ghi chỉ qua `ai_keys.py` (sổ) và `user_keys.py` (ngữ cảnh lượt gọi).
    """

    __tablename__ = "tab_ai_key"

    owner_type: Mapped[int] = mapped_column(SmallInteger, default=2)
    owner_id: Mapped[int] = mapped_column(BigInteger, default=0)
    provider: Mapped[str] = mapped_column(String(30), default="gemini")
    model: Mapped[str] = mapped_column(String(80), default="")
    #  ai-CR-108: địa chỉ trạm cho hãng «tùy chỉnh» (https, tên miền công khai); trống với hãng có sẵn.
    base_url: Mapped[str] = mapped_column(String(200), default="")
    priority: Mapped[int] = mapped_column(SmallInteger, default=1)
    daily_cap: Mapped[int] = mapped_column(Integer, default=0)
    key_enc: Mapped[str] = mapped_column(Text, default="")
    key_hint: Mapped[str] = mapped_column(String(8), default="")
    verified_at: Mapped[datetime | None] = mapped_column(DateTime, default=None, nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, default=None, nullable=True)
    #  Tên cũ (ai-CR-053): mã cũ và bài kiểm còn gọi `user_id` — với dòng cá nhân nó chính là `owner_id`.
    user_id = synonym("owner_id")

    __table_args__ = (Index("ix_tab_ai_key_owner", "owner_type", "owner_id"),)


#  Bí danh tương thích (ai-CR-053): chỗ cũ import `AgentUserKey`.
AgentUserKey = AiKey


class AgentRunner(Base, AuditMixin):
    """Một MÁY SỬA MÃ đã đăng ký (ai-CR-054, D-03): tên máy, chủ máy, mã máy (băm), cờ deploy, nhịp tim.

    Đăng ký/gỡ bằng câu nhắn ở chat đại ca. Mã máy thô chỉ hiện đúng một lần lúc đăng ký; máy ghi vào
    `.env` runner (`AGENT_RUNNER_NAME` + `AGENT_RUNNER_TOKEN`). Gỡ = `revoked_at`, máy bị từ chối ở lượt kế.
    """

    __tablename__ = "tab_agent_runner"

    name: Mapped[str] = mapped_column(String(40), index=True)
    owner_user_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), default="")
    can_deploy: Mapped[bool] = mapped_column(Boolean, default=False)
    note: Mapped[str] = mapped_column(String(255), default="")
    version: Mapped[str] = mapped_column(String(50), default="")
    registered_by_chat: Mapped[str] = mapped_column(String(50), default="")
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime, default=None, nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, default=None, nullable=True)


class AgentMemory(Base, AuditMixin):
    """Sổ ghi nhớ cá nhân — tầng LÕI (ai-CR-095, C-02): MỖI NGƯỜI MỘT DÒNG, `text` Markdown bốn mục, trần 8.000 ký tự,
    nạp nguyên văn vào mọi câu hỏi của người đó. Đọc/ghi chỉ qua `personal_memory`."""

    __tablename__ = "tab_agent_memory"

    user_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True, unique=True)
    text: Mapped[str] = mapped_column(Text, default="")


class AgentNote(Base, AuditMixin):
    """Sổ ghi nhớ cá nhân — tầng KHO (ai-CR-095, C-02): ghi chú dài của từng người, không trần; vector ở collection
    `agent_personal` của Qdrant (payload `user_id`). «Quên» = `revoked_at`, giữ lịch sử."""

    __tablename__ = "tab_agent_note"

    user_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    title: Mapped[str] = mapped_column(String(200), default="")
    text: Mapped[str] = mapped_column(Text, default="")
    chars: Mapped[int] = mapped_column(Integer, default=0)
    indexed_at: Mapped[datetime | None] = mapped_column(DateTime, default=None, nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, default=None, nullable=True)


class AgentPersonalItem(Base, AuditMixin):
    """Thẻ cá nhân (ai-CR-103, C-05): lịch trình / việc riêng, chi tiêu, món cần mua — của TỪNG người, không phải ERP.

    `kind` 1 lịch trình · 2 chi tiêu · 3 mua sắm; `status` 1 còn · 2 xong · 3 đã bỏ (SMALLINT + IntEnum ở
    `personal_items.py`). `at` = giờ hẹn (lịch trình) hoặc lúc chi (chi tiêu), giờ Việt Nam. `amount` đồng.
    """

    __tablename__ = "tab_agent_personal_item"

    user_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    kind: Mapped[int] = mapped_column(SmallInteger, default=1)
    status: Mapped[int] = mapped_column(SmallInteger, default=1)
    title: Mapped[str] = mapped_column(String(300), default="")
    amount: Mapped[int] = mapped_column(BigInteger, default=0)
    category: Mapped[str] = mapped_column(String(60), default="")
    at: Mapped[datetime | None] = mapped_column(DateTime, default=None, nullable=True)
    note: Mapped[str] = mapped_column(String(500), default="")

    __table_args__ = (Index("ix_agent_personal_item_user_kind", "user_id", "kind", "status"),)


class AgentMeeting(Base, AuditMixin):
    """Một phiên biên bản họp (ai-CR-104, phase 10): nguồn tệp, trạng thái, bản chép, biên bản. Chỉ người gửi xem.

    `source_kind` 1 Telegram (`source_ref` = file_id) · 2 Google Drive (id tệp). `status` 1 chờ · 2 đang chép ·
    3 đang viết · 4 xong · 5 hỏng (SMALLINT + IntEnum ở `meetings.py`). Tệp âm thanh KHÔNG giữ trên máy chủ.
    """

    __tablename__ = "tab_agent_meeting"

    user_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    chat_id: Mapped[str] = mapped_column(String(50), default="")
    source_kind: Mapped[int] = mapped_column(SmallInteger, default=1)
    source_ref: Mapped[str] = mapped_column(String(300), default="")
    title: Mapped[str] = mapped_column(String(200), default="")
    mime: Mapped[str] = mapped_column(String(80), default="")
    status: Mapped[int] = mapped_column(SmallInteger, default=1)
    template: Mapped[str] = mapped_column(String(40), default="")
    #  ai-CR-112: mẫu đã dùng — nhãn + lời dặn (mẫu riêng / lời dặn tại chỗ). Mẫu sẵn để trống lời dặn.
    template_label: Mapped[str] = mapped_column(String(80), default="")
    template_prompt: Mapped[str] = mapped_column(Text, default="")
    #  ai-CR-114: việc + lịch rút từ biên bản, đánh số cho thẻ duyệt; mỗi mục ghi trạng thái (ActionState) và chỗ đã tạo.
    actions: Mapped[list | None] = mapped_column(JSON, default=None, nullable=True)
    duration_sec: Mapped[int] = mapped_column(Integer, default=0)
    transcript: Mapped[str] = mapped_column(Text().with_variant(mysql.MEDIUMTEXT(), "mysql"), default="")
    recap: Mapped[str] = mapped_column(Text, default="")
    note_id: Mapped[int] = mapped_column(BigInteger, default=0)
    drive_file_id: Mapped[str] = mapped_column(String(120), default="")
    error: Mapped[str] = mapped_column(String(500), default="")
    started_at: Mapped[datetime | None] = mapped_column(DateTime, default=None, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, default=None, nullable=True)


class AgentGroup(Base, AuditMixin):
    """Nhóm bot đang ở (ai-CR-105 Telegram, ai-CR-122 Zalo `zg:`). Chủ = người đã thêm bot (`owner_user_id` tài khoản
    ERP, 0 nếu chưa rõ). `members` = id Zalo các thành viên (chỉ nhóm Zalo — Telegram hỏi thẳng `getChatMember`)."""

    __tablename__ = "tab_agent_group"

    chat_id: Mapped[str] = mapped_column(String(50), default="", index=True, unique=True)
    title: Mapped[str] = mapped_column(String(200), default="")
    owner_user_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    owner_tg_id: Mapped[int] = mapped_column(BigInteger, default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    joined_at: Mapped[datetime | None] = mapped_column(DateTime, default=None, nullable=True)
    left_at: Mapped[datetime | None] = mapped_column(DateTime, default=None, nullable=True)
    members: Mapped[list | None] = mapped_column(JSON, default=None, nullable=True)
    #  ai-CR-123: loại nhóm (`constants.GROUP_CAT_*`) + ngừng ghi (người quản lý bot AI tắt một nhóm mà bot vẫn ở).
    category: Mapped[int] = mapped_column(SmallInteger, default=0)
    paused: Mapped[bool] = mapped_column(Boolean, default=False)


class AgentGroupMessage(Base, AuditMixin):
    """Một tin trong nhóm bot đang ở (ai-CR-105) — giữ AGENT_GROUP_RETENTION_DAYS ngày. `file` = siêu dữ liệu tệp
    (chưa tải), đọc khi người dùng nhờ. `sent_at` giờ UTC."""

    __tablename__ = "tab_agent_group_message"

    group_id: Mapped[int] = mapped_column(BigInteger, default=0)
    tg_message_id: Mapped[int] = mapped_column(BigInteger, default=0)
    from_tg_id: Mapped[int] = mapped_column(BigInteger, default=0)
    from_name: Mapped[str] = mapped_column(String(120), default="")
    text: Mapped[str] = mapped_column(Text, default="")
    file: Mapped[dict | None] = mapped_column(JSON, default=None, nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, default=None, nullable=True)

    __table_args__ = (Index("ix_agent_group_msg_group_sent", "group_id", "sent_at"),)


class AgentGroupSummary(Base, AuditMixin):
    """Bản tóm tắt / câu trả lời về một nhóm mà bot hoặc Trợ lý AI đã viết (ai-CR-123) — để xem lại trên web.
    `user_id` = người hỏi (tài khoản ERP); `source` = 1 bot nhắn riêng / Trợ lý web, 2 nút «Tóm tắt» trên màn nhóm."""

    __tablename__ = "tab_agent_group_summary"

    group_id: Mapped[int] = mapped_column(BigInteger, default=0)
    user_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    source: Mapped[int] = mapped_column(SmallInteger, default=1)
    hours: Mapped[int] = mapped_column(Integer, default=24)
    question: Mapped[str] = mapped_column(String(500), default="")
    text: Mapped[str] = mapped_column(Text, default="")

    __table_args__ = (Index("ix_agent_group_sum_group", "group_id", "id"),)


class AgentGroupView(Base, AuditMixin):
    """Nhật ký người quản lý bot AI mở NỘI DUNG một nhóm mà họ không phải thành viên (ai-CR-123, đại ca chốt 08/10:
    quản lý AI thấy hết, nhưng có dấu vết)."""

    __tablename__ = "tab_agent_group_view"

    group_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, default=0)
    what: Mapped[str] = mapped_column(String(40), default="")


class AgentReminder(Base, AuditMixin):
    """Lời nhắc đặt bằng câu nói (ai-CR-060, T-10): tới `due_at` (UTC) thì bot nhắn lại đúng `chat_id`."""

    __tablename__ = "tab_agent_reminder"

    chat_id: Mapped[str] = mapped_column(String(50), default="", index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    text: Mapped[str] = mapped_column(String(500), default="")
    due_at: Mapped[datetime | None] = mapped_column(DateTime, default=None, nullable=True, index=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, default=None, nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime, default=None, nullable=True)


class AgentMcpKey(Base, AuditMixin):
    """Khóa kết nối MCP cá nhân (ai-CR-063, M-02): chỉ giữ băm, có hạn, hai mức chỉ đọc / được ghi."""

    __tablename__ = "tab_agent_mcp_key"

    user_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    name: Mapped[str] = mapped_column(String(80), default="")
    token_hash: Mapped[str] = mapped_column(String(64), default="", index=True)
    key_hint: Mapped[str] = mapped_column(String(8), default="")
    scope: Mapped[int] = mapped_column(SmallInteger, default=0)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, default=None, nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime, default=None, nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, default=None, nullable=True)


class AgentGoogleLink(Base, AuditMixin):
    """Google CÁ NHÂN của một tài khoản ERP (ai-CR-064, M-06): refresh token mã hóa Fernet, dùng cho tool Lịch + Drive."""

    __tablename__ = "tab_agent_google_link"

    user_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    email: Mapped[str] = mapped_column(String(255), default="")
    scopes: Mapped[str] = mapped_column(String(500), default="")
    refresh_token_enc: Mapped[str] = mapped_column(Text, default="")
    access_token_enc: Mapped[str] = mapped_column(Text, default="")
    access_expires_at: Mapped[datetime | None] = mapped_column(DateTime, default=None, nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, default=None, nullable=True)


class AgentEnv(Base, AuditMixin):
    """SỔ MÔI TRƯỜNG (ai-CR-067, V-01): mỗi dòng = một nơi bot được deploy / xem / thao tác.

    Khai bằng câu nhắn ở chat đại ca («thêm môi trường …»), migration nạp sẵn `dev` và `prod`. Ô máy chủ để
    trống = máy trong .env của runner (`AGENT_VPS_HOST`…) — dev và prod hiện chung một VPS. Thêm VPS mới =
    thêm một dòng có host riêng, không sửa mã. `kind` = 1 dev · 2 prod · 3 preview (constants.ENV_*).
    Ba cột sức khỏe cuối do vòng theo dõi mỗi phút ghi (O-01).
    """

    __tablename__ = "tab_agent_env"

    name: Mapped[str] = mapped_column(String(40), index=True)
    kind: Mapped[int] = mapped_column(SmallInteger, default=1)
    host: Mapped[str] = mapped_column(String(255), default="")
    port: Mapped[int] = mapped_column(Integer, default=0)
    ssh_user: Mapped[str] = mapped_column(String(60), default="")
    dir: Mapped[str] = mapped_column(String(255), default="")
    compose_args: Mapped[str] = mapped_column(String(255), default="")
    branch: Mapped[str] = mapped_column(String(80), default="")
    health_url: Mapped[str] = mapped_column(String(255), default="")
    db_name: Mapped[str] = mapped_column(String(64), default="")
    #  Tự chữa khi sự cố (O-03). Prod KHÔNG BAO GIỜ tự chữa dù cột này bật — mã chặn theo `kind`.
    auto_heal: Mapped[bool] = mapped_column(Boolean, default=False)
    note: Mapped[str] = mapped_column(String(255), default="")
    last_health_code: Mapped[int] = mapped_column(Integer, default=0)
    last_health_at: Mapped[datetime | None] = mapped_column(DateTime, default=None, nullable=True)
    fail_streak: Mapped[int] = mapped_column(Integer, default=0)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, default=None, nullable=True)


class AgentOp(Base, AuditMixin):
    """NHẬT KÝ THAO TÁC trên VPS (ai-CR-068, V-02 + V-03): mỗi lệnh bot chạy trên một môi trường = một dòng.

    Ghi TRƯỚC khi chạy (thẻ «đúng» hiện nguyên văn `command`), nên dòng sổ là bằng chứng ai cho phép cái gì.
    Thao tác sửa có `backup_ref` (tệp sao lưu trên VPS) và `undo_params` (cách hoàn tác) — «hoàn tác thao tác
    #n» đẻ ra một dòng MỚI trỏ `undo_of_op_id` về dòng cũ, không sửa dòng cũ ngoài `undone_by_op_id`.
    `output` đã qua `guardrails.mask_secrets` — không bao giờ có bí mật thô ở đây.
    """

    __tablename__ = "tab_agent_op"

    env_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    kind: Mapped[int] = mapped_column(SmallInteger, default=1)
    status: Mapped[int] = mapped_column(SmallInteger, default=1, index=True)
    title: Mapped[str] = mapped_column(String(255), default="")
    command: Mapped[str] = mapped_column(Text, default="")
    params: Mapped[dict] = mapped_column(JSON, default=dict)
    backup_ref: Mapped[str] = mapped_column(String(255), default="")
    undo_params: Mapped[dict] = mapped_column(JSON, default=dict)
    undo_of_op_id: Mapped[int] = mapped_column(BigInteger, default=0)
    undone_by_op_id: Mapped[int] = mapped_column(BigInteger, default=0)
    incident_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    chat_id: Mapped[str] = mapped_column(String(50), default="")
    #  Bot tự chạy (tự chữa, báo tài nguyên) thì 0 / rỗng; đại ca ra lệnh thì là chat của đại ca.
    auto: Mapped[bool] = mapped_column(Boolean, default=False)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, default=None, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, default=None, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, default=None, nullable=True)
    output: Mapped[str] = mapped_column(Text, default="")
    error: Mapped[str] = mapped_column(String(1000), default="")


class AgentIncident(Base, AuditMixin):
    """SỔ SỰ CỐ (ai-CR-069/070, O-05): một lần một môi trường hỏng health liên tiếp, từ lúc phát hiện tới lúc xanh lại.

    `signature` = khóa gom các lần giống nhau (môi trường + nguyên nhân rút gọn) để O-06 đếm lặp lại và đề xuất
    một việc sửa gốc rễ (`task_id`). Thời gian gián đoạn = `resolved_at - started_at`.
    """

    __tablename__ = "tab_agent_incident"

    env_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    status: Mapped[int] = mapped_column(SmallInteger, default=1, index=True)
    symptom: Mapped[str] = mapped_column(String(255), default="")
    signature: Mapped[str] = mapped_column(String(120), default="", index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, default=None, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, default=None, nullable=True)
    diagnosis: Mapped[str] = mapped_column(Text, default="")
    cause: Mapped[str] = mapped_column(String(255), default="")
    action: Mapped[str] = mapped_column(String(40), default="")
    heal_op_id: Mapped[int] = mapped_column(BigInteger, default=0)
    task_id: Mapped[int] = mapped_column(BigInteger, default=0)
