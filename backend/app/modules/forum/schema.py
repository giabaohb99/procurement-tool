"""Schema chiều VÀO của Diễn đàn (F1).

Chiều RA trả dict dựng ở controller — đúng khuôn module comment: phong bì
`{success, message, data}` với các map gom theo trang, không ép qua Pydantic
để khỏi khai trùng hai lần một cấu trúc chỉ một chỗ dùng.
"""
from pydantic import BaseModel, Field

from .model import ForumAudience, ForumPostKind


class PostIn(BaseModel):
    """Đăng bài: chữ + ảnh/video tải-trước-gắn-sau + đối tượng xem (QĐ-D3).

    `kind` (F10): bài sự kiện — hiện chỉ AVATAR_UPDATE, do chính chủ bấm đăng
    từ hộp thoại sau khi đổi avatar; luật ràng buộc nằm ở service.
    """

    body: str = ""
    audience: int = int(ForumAudience.PUBLIC)
    file_ids: list[int] = Field(default_factory=list)
    kind: int = int(ForumPostKind.NORMAL)


class ModerationIn(BaseModel):
    """Ẩn/xóa bài (F5) — `reason` bắt buộc ở service (QĐ-D1: không ẩn lặng lẽ);
    khôi phục dùng chung schema với reason để trống."""

    reason: str = ""
