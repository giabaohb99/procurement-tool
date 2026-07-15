from sqlalchemy import BigInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, AuditMixin


class PushSubscription(Base, AuditMixin):
    """Đăng ký nhận Web Push của 1 thiết bị/trình duyệt (mỗi endpoint = 1 thiết bị)."""

    __tablename__ = "tab_push_subscription"

    user_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    endpoint: Mapped[str] = mapped_column(Text)          # URL push service (dài, không unique DB — dedup ở code)
    p256dh: Mapped[str] = mapped_column(String(255), default="")
    auth: Mapped[str] = mapped_column(String(255), default="")
