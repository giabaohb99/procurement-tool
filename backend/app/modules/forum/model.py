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

from sqlalchemy import BigInteger, DateTime, Index, SmallInteger, Text, UniqueConstraint
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
    )

    body: Mapped[str] = mapped_column(Text, default="")
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
