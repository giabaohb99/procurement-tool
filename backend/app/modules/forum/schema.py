"""Schema chiều VÀO của Diễn đàn (F1).

Chiều RA trả dict dựng ở controller — đúng khuôn module comment: phong bì
`{success, message, data}` với các map gom theo trang, không ép qua Pydantic
để khỏi khai trùng hai lần một cấu trúc chỉ một chỗ dùng.
"""
from pydantic import BaseModel, Field

from .model import (ForumAudience, ForumBoardStatus, ForumBodyFormat,
                    ForumPostKind, ForumPrefix, ForumReactionKind)


class PostIn(BaseModel):
    """Đăng bài: chữ + ảnh/video tải-trước-gắn-sau + đối tượng xem (QĐ-D3).

    `kind` (F10): bài sự kiện — hiện chỉ AVATAR_UPDATE, do chính chủ bấm đăng
    từ hộp thoại sau khi đổi avatar; luật ràng buộc nằm ở service.

    F13a: `board_id` > 0 = đăng thành THREAD trong box — `title` bắt buộc,
    `audience` bị ÉP theo box (giá trị client gửi bị bỏ qua); luật ở service.
    """

    body: str = ""
    # CR-261: RICH_HTML = body là HTML từ RichTextField — service sanitize +
    # đo trần riêng; mặc định PLAIN để client cũ không phải đổi gì.
    body_format: int = int(ForumBodyFormat.PLAIN)
    audience: int = int(ForumAudience.PUBLIC)
    file_ids: list[int] = Field(default_factory=list)
    kind: int = int(ForumPostKind.NORMAL)
    board_id: int = 0
    title: str = ""
    prefix: int = int(ForumPrefix.NONE)


class BoardIn(BaseModel):
    """Tạo/sửa nhóm hoặc box chuyên mục (F13a) — chỉ `forum_admin` đi được.

    `parent_id` = 0: NHÓM tiêu đề; > 0: BOX thuộc nhóm đó (đúng hai tầng,
    service chặn lồng sâu hơn). `audience` KHÔNG nhận từ client — đợt đầu ép
    PUBLIC (QĐ-D7a).
    """

    name: str = ""
    description: str = ""
    icon: str = ""
    parent_id: int = 0
    sort_order: int = 0
    status: int = int(ForumBoardStatus.ACTIVE)


class ReactionIn(BaseModel):
    """Bấm cảm xúc (CR-206) — `kind` theo `ForumReactionKind`; client cũ gửi
    `{}` thì rơi về LIKE nên không gãy."""

    kind: int = int(ForumReactionKind.LIKE)


class ModerationIn(BaseModel):
    """Ẩn/xóa bài (F5) — `reason` bắt buộc ở service (QĐ-D1: không ẩn lặng lẽ);
    khôi phục dùng chung schema với reason để trống."""

    reason: str = ""
