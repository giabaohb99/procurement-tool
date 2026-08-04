from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base


class Faq(Base, AuditMixin):
    """Câu hỏi thường gặp — hiển thị ở trang người dùng của Trung tâm Hướng dẫn."""

    __tablename__ = "tab_faq"

    question: Mapped[str] = mapped_column(String(500))
    answer: Mapped[str] = mapped_column(Text, default="")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    # Tắt để ẩn khỏi trang người dùng mà không cần xóa
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
