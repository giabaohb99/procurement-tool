from sqlalchemy import BigInteger, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base


class Comment(Base, AuditMixin):
    """Bình luận gắn vào MỘT chứng từ bất kỳ theo cặp (entity, entity_id).

    Một bảng dùng chung cho mọi loại chứng từ — đúng khuôn `tab_file_link` của đính kèm,
    thay vì mỗi phân hệ đẻ một bảng riêng. Danh sách entity được phép nằm ở
    `app/core/comment_registry.py`.

    created_by = tài khoản người viết (AuditMixin), created_at = thời điểm gõ.
    """

    __tablename__ = "tab_comment"

    entity: Mapped[str] = mapped_column(String(50), default="", index=True)
    entity_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    body: Mapped[str] = mapped_column(Text, default="")

    # CR-030 — luồng CHỈ 2 CẤP (kiểu YouTube):
    #   parent_id = 0  -> bình luận gốc
    #   parent_id > 0  -> phản hồi, luôn treo vào một bình luận GỐC
    # Trả lời một phản hồi cũng ra cấp 2 (service tự kéo về gốc), nên cây không bao giờ sâu quá 2 tầng.
    parent_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    # Người được nhắc trong phản hồi. Lưu ID người, KHÔNG dò chữ "@Tên" trong nội dung:
    # tên tiếng Việt hay trùng và người viết sửa chữ được, dò text sẽ nhắc nhầm.
    reply_to_user_id: Mapped[int] = mapped_column(BigInteger, default=0)


class CommentMention(Base, AuditMixin):
    """Người được nhắc bằng `@` trong một bình luận (CR-031) — mỗi người 1 dòng.

    Vì sao tách bảng chứ không nhét thêm cột: một bình luận nhắc được NHIỀU người
    (`reply_to_user_id` chỉ đủ cho đúng một người, và nó mang nghĩa khác — "đang trả lời ai").

    Vị trí của `@` trong câu nằm ở `tab_comment.body` dưới dạng thẻ `@[<user_id>]`;
    bảng này là danh sách phẳng để bắn chuông và tra tên mà không phải mổ chuỗi.
    """

    __tablename__ = "tab_comment_mention"
    __table_args__ = (UniqueConstraint("comment_id", "user_id", name="uq_comment_mention"),)

    comment_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)


class CommentReaction(Base, AuditMixin):
    """Lượt thích một bình luận — mỗi người tối đa 1 lượt (bấm lại là bỏ).

    Cố ý chỉ có MỘT loại (thích), không có dislike, không có dải biểu tượng cảm xúc:
    trong nội bộ nó mang nghĩa "tôi đã đọc / tôi đồng ý", thay cho hàng loạt bình luận
    "ok anh" làm loãng phiếu. Không sinh thông báo — nếu không chuông sẽ rất ồn.
    """

    __tablename__ = "tab_comment_reaction"
    __table_args__ = (UniqueConstraint("comment_id", "user_id", name="uq_comment_reaction"),)

    comment_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
