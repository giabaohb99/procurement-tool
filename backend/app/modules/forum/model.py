"""Diễn đàn nội bộ — bài viết, lượt thích, nhật ký kiểm duyệt (F0).

Thiết kế chốt ở `doc/erp/dien-dan/` (QĐ-D1..D5, 26/08/2026). Trạng thái và
đối tượng xem lưu SMALLINT + IntEnum theo luật R2/QĐ-11 — tiếng Việt chỉ nằm
ở tầng hiển thị.

Trục TÁC GIẢ là `created_by` = **user_id** (AuditMixin), KHÔNG phải employee_id
như cột người trên chứng từ thu mua — chốt rõ từ đầu để khỏi lặp lại sự mơ hồ đó
(xem `00-pham-vi-va-ke-hoach.md` mục 4). Muốn ra hồ sơ nhân sự thì đi đường
`tab_user.employee_id`.
"""
from datetime import datetime
from enum import IntEnum

from sqlalchemy import (BigInteger, DateTime, Index, SmallInteger, String, Text,
                        UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base


class ForumPostStatus(IntEnum):
    """Trạng thái bài viết.

    `PENDING_REVIEW` chừa sẵn theo QĐ-D2: trước mắt KHÔNG duyệt bài, nhưng sau
    này bật duyệt chỉ là thêm cấu hình + màn hàng chờ, không phải sửa dữ liệu.
    """

    PENDING_REVIEW = 0   # chờ duyệt — đợt 1 chưa dùng, chừa sẵn (QĐ-D2)
    PUBLISHED = 1        # đã đăng, hiện trên feed
    HIDDEN = 2           # quản trị ẩn — tác giả vẫn thấy kèm lý do (QĐ-D1)
    REMOVED = 3          # quản trị xóa — biến khỏi mọi feed, giữ dòng để đối soát


class ForumAudience(IntEnum):
    """Đối tượng xem của MỘT bài (QĐ-D3) — mỗi bài tự chọn khi đăng."""

    DEPT = 1      # phòng ban của tác giả
    COMPANY = 2   # pháp nhân của tác giả
    PUBLIC = 3    # toàn tập đoàn


class ForumPostKind(IntEnum):
    """Loại bài (F10) — bài thường hay bài sinh theo SỰ KIỆN.

    Bài sự kiện vẫn do CHÍNH CHỦ bấm đăng (hỏi trước, không ép); `kind` chỉ để
    thẻ bài vẽ dòng hệ thống ("vừa cập nhật ảnh đại diện") tách khỏi caption.
    Sự kiện mới sau này (thăng chức, sinh nhật...) = thêm giá trị, không thêm bảng.
    """

    NORMAL = 0         # bài thường
    AVATAR_UPDATE = 1  # đổi ảnh đại diện — đúng 1 ảnh là chính avatar mới


class ForumBodyFormat(IntEnum):
    """Định dạng nội dung bài (CR-261) — chữ trơn hay HTML đã soạn thảo.

    RICH_HTML lưu HTML từ `RichTextField` (bộ mở rộng CHUNG với văn thư),
    ĐÃ qua `sanitize_html` của help_center ngay tại cửa ghi — một bộ lọc
    duy nhất cho cả hệ, không viết bộ lọc thứ hai. Bài cũ giữ PLAIN, FE
    vẫn vẽ theo đường chữ trơn như trước.
    """

    PLAIN = 0      # chữ trơn — bài cũ + bình luận
    RICH_HTML = 1  # HTML đã lọc — bài đăng từ hộp soạn có định dạng


class ForumModerationAction(IntEnum):
    """Hành động của quản trị viên trên một bài (QĐ-D1)."""

    HIDE = 1      # ẩn bài
    REMOVE = 2    # xóa bài
    RESTORE = 3   # khôi phục bài đã ẩn


class ForumReactionKind(IntEnum):
    """Dải cảm xúc kiểu Facebook (CR-206) — giá trị nằm xuống cột `kind`.

    LIKE=1 giữ nguyên từ đợt 1 nên dữ liệu like cũ tự thành cảm xúc "Thích",
    không cần migration. WOW dùng nhãn "Tuyệt vời" (icon ngôi sao) vì lucide
    không có mặt ngạc nhiên — FE map nhãn/icon ở `FORUM_REACTION_META`.
    """

    LIKE = 1     # Thích
    LOVE = 2     # Yêu thích
    HAHA = 3     # Haha
    WOW = 4      # Tuyệt vời
    SAD = 5      # Buồn
    ANGRY = 6    # Phẫn nộ


class ForumBoardStatus(IntEnum):
    """Trạng thái box/nhóm chuyên mục (F13a). Ẩn là RÚT KHỎI MẮT chứ không xóa:
    box ẩn không nhận bài mới, không hiện trên cây, bài cũ giữ nguyên."""

    ACTIVE = 1   # đang mở
    HIDDEN = 2   # admin ẩn — chờ dọn hoặc ngưng hẳn


class ForumPrefix(IntEnum):
    """Prefix của chủ đề trong box (F13a) — nhãn màu đầu tiêu đề kiểu VOZ.

    Nhãn tiếng Việt khai ở `app/core/forum_codes.py` (bộ `forum_prefix`) để
    `gen_status_ts.py` sinh cho FE — hai nơi phải cùng dải giá trị, có test giữ.
    """

    NONE = 0        # không prefix
    DISCUSSION = 1  # thảo luận
    QUESTION = 2    # thắc mắc
    KNOWLEDGE = 3   # kiến thức
    SHOWCASE = 4    # khoe
    REVIEW = 5      # đánh giá


class ForumBoard(Base, AuditMixin):
    """Nhóm/box chuyên mục kiểu VOZ (F13a, QĐ-D7) — MỘT bảng cho cả hai tầng.

    `parent_id` NULL = NHÓM chỉ làm tiêu đề (không chứa bài trực tiếp);
    có `parent_id` = BOX nhận bài. Đúng hai tầng, không đệ quy sâu hơn —
    service chặn từ lúc tạo. Cấu trúc do `forum_admin` quyết thủ công
    (nguyên tắc kiểm duyệt chốt 03/09/2026), bài trong box KHÔNG duyệt trước.
    """

    __tablename__ = "tab_forum_board"

    parent_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    name: Mapped[str] = mapped_column(String(255), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    # Tên icon lucide hoặc 1 emoji do admin chọn lúc tạo box — FE tự vẽ.
    icon: Mapped[str] = mapped_column(String(50), default="")
    sort_order: Mapped[int] = mapped_column(SmallInteger, default=0)
    status: Mapped[int] = mapped_column(
        SmallInteger, default=int(ForumBoardStatus.ACTIVE)
    )
    # Đợt đầu ÉP PUBLIC (QĐ-D7a) — cột chừa sẵn cho box theo phòng/pháp nhân sau.
    audience: Mapped[int] = mapped_column(
        SmallInteger, default=int(ForumAudience.PUBLIC)
    )


class ForumPost(Base, AuditMixin):
    """Bài viết trên diễn đàn. Tác giả = `created_by` (user_id).

    `dept_id` / `company_id` ĐÓNG BĂNG theo hồ sơ tác giả tại thời điểm đăng:
    chuyển phòng sau này không làm bài cũ đổi đối tượng xem (mục 4.2 của `01`).
    Ảnh đính kèm đi qua FileLink entity `forum_post`; comment đi qua CR-033.
    """

    __tablename__ = "tab_forum_post"
    # Hai index phục vụ đúng hai câu hỏi của feed (mục 4.3 của `01`):
    #   (status, id)     — feed chung: WHERE status=1 ORDER BY id DESC
    #   (created_by, id) — trang cá nhân: WHERE created_by=? ORDER BY id DESC
    # KHÔNG đánh index theo audience/dept/company: lọc audience là OR nhiều vế,
    # index đơn lẻ không ăn, còn dữ liệu thì nhỏ (~15k bài/năm).
    __table_args__ = (
        Index("ix_forum_post_status_id", "status", "id"),
        Index("ix_forum_post_author_id", "created_by", "id"),
        # (board_id, id) — danh sách thread của một box (F13a):
        #   WHERE board_id=? AND status=1, sắp theo hoạt động cuối
        Index("ix_forum_post_board_id", "board_id", "id"),
    )

    body: Mapped[str] = mapped_column(Text, default="")
    # CR-261: 0 = chữ trơn (bài cũ), 1 = HTML đã qua sanitize ở service —
    # FE dựa cột này chọn đường vẽ, KHÔNG đoán bằng cách ngửi chuỗi.
    body_format: Mapped[int] = mapped_column(
        SmallInteger, default=int(ForumBodyFormat.PLAIN), server_default="0"
    )
    status: Mapped[int] = mapped_column(
        SmallInteger, default=int(ForumPostStatus.PUBLISHED)
    )
    audience: Mapped[int] = mapped_column(
        SmallInteger, default=int(ForumAudience.PUBLIC)
    )
    kind: Mapped[int] = mapped_column(
        SmallInteger, default=int(ForumPostKind.NORMAL), server_default="0"
    )
    dept_id: Mapped[int] = mapped_column(BigInteger, default=0)
    company_id: Mapped[int] = mapped_column(BigInteger, default=0)
    # Ghim bài (F9a/CR-199): CÓ MỐC = đang ghim, NULL = bài thường — một cột
    # kiêm luôn thứ tự dải ghim (mới ghim lên đầu). Không cột boolean riêng,
    # không index: số bài ghim đếm trên đầu ngón tay.
    pinned_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # F13a — chuyên mục kiểu VOZ. NULL = bài Bảng tin thuần như cũ; có board_id
    # thì bài là một THREAD trong box: `title` bắt buộc (service chặn 400),
    # `prefix` theo `ForumPrefix`. Bài box vẫn ra feed (QĐ-D7b).
    board_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    prefix: Mapped[int] = mapped_column(
        SmallInteger, default=int(ForumPrefix.NONE), server_default="0"
    )


class ForumReaction(Base, AuditMixin):
    """Cảm xúc của một người với một BÀI VIẾT — tối đa 1 dòng/(bài, người).

    Khuôn `tab_comment_reaction`. Unique theo (bài, người) nên đổi cảm xúc là
    UPDATE `kind` (CR-206: dải 6 cảm xúc `ForumReactionKind`), bấm lại cùng
    cảm xúc là xóa dòng. Không sinh chuông (D-Q6).
    """

    KIND_LIKE = int(ForumReactionKind.LIKE)   # giữ tên cũ — test F0 và code cũ còn gọi

    __tablename__ = "tab_forum_reaction"
    __table_args__ = (UniqueConstraint("post_id", "user_id", name="uq_forum_reaction"),)

    post_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    kind: Mapped[int] = mapped_column(SmallInteger, default=KIND_LIKE)


class ForumModerationLog(Base, AuditMixin):
    """Nhật ký kiểm duyệt (QĐ-D1) — KHÔNG có đường "ẩn lặng lẽ".

    Quản trị viên = `created_by`. `reason` bắt buộc ở tầng service (ẩn/xóa
    không lý do phải bị 400 — điều kiện đủ của F5); `notified_at` ghi lúc đã
    bắn thông báo cho tác giả, để đối soát "đã báo chưa" tách khỏi "đã ẩn chưa".
    """

    __tablename__ = "tab_forum_moderation_log"

    post_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    action: Mapped[int] = mapped_column(
        SmallInteger, default=int(ForumModerationAction.HIDE)
    )
    reason: Mapped[str] = mapped_column(Text, default="")
    notified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
