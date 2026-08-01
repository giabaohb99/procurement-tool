from sqlalchemy import BigInteger, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import AuditMixin, Base


class HelpArticleSlide(Base, AuditMixin):
    """Ảnh hướng dẫn từng bước gắn vào 1 bài viết."""

    __tablename__ = "tab_help_article_slide"

    article_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tab_help_article.id", ondelete="CASCADE")
    )
    image_url: Mapped[str] = mapped_column(String(500))
    caption: Mapped[str | None] = mapped_column(Text, nullable=True)
    step_order: Mapped[int] = mapped_column(Integer, default=0)


class HelpArticle(Base, AuditMixin):
    """Bài viết hướng dẫn sử dụng. Tự tham chiếu parent_id để tạo cây thư mục."""

    __tablename__ = "tab_help_article"

    parent_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("tab_help_article.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text, default="")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    slides = relationship(
        "HelpArticleSlide",
        backref="article",
        cascade="all, delete-orphan",
        order_by="HelpArticleSlide.step_order",
    )
