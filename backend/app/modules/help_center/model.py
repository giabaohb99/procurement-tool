from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, String, Text
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
    # Mô tả ngắn hiển thị dưới tiêu đề ở thẻ danh mục ngoài trang chủ portal
    summary: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Icon: lưu slug icon (vd 'rocket', 'shopping-cart') HOẶC URL ảnh do người dùng
    # tự upload (vd '/uploads/help/xxx.png' trả về từ endpoint upload-image)
    icon: Mapped[str | None] = mapped_column(String(500), nullable=True)

    slides = relationship(
        "HelpArticleSlide",
        backref="article",
        cascade="all, delete-orphan",
        order_by="HelpArticleSlide.step_order",
    )


class HelpHomeSection(Base, AuditMixin):
    """1 trong 4 khung cố định trên trang chủ khu người dùng (quick_start/categories/faq/tips).

    4 dòng được seed sẵn, KHÔNG cho thêm/xóa qua API — chỉ đổi tiêu đề/ẩn-hiện/thứ tự.
    """

    __tablename__ = "tab_help_home_section"

    key: Mapped[str] = mapped_column(String(30), unique=True)
    title: Mapped[str] = mapped_column(String(150))
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    items = relationship(
        "HelpHomeItem",
        backref="section",
        cascade="all, delete-orphan",
        order_by="HelpHomeItem.sort_order",
    )


class HelpHomeItem(Base, AuditMixin):
    """Bài viết được chọn gắn vào 1 khung trang chủ — chỉ dùng cho khung quick_start/categories."""

    __tablename__ = "tab_help_home_item"

    section_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tab_help_home_section.id", ondelete="CASCADE")
    )
    article_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tab_help_article.id", ondelete="CASCADE")
    )
    # Ảnh minh họa góc phải của tile — chỉ khung quick_start dùng
    background_image: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # Slug nền gradient dựng sẵn (frontend tự ánh xạ sang CSS, backend chỉ lưu chuỗi)
    gradient: Mapped[str | None] = mapped_column(String(30), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
