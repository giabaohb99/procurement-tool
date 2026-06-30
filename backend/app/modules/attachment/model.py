from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, AuditMixin


class Attachment(Base, AuditMixin):
    """File đính kèm (đa hình) — lưu trên R2, DB chỉ giữ key/url."""

    __tablename__ = "tab_attachment"

    entity: Mapped[str] = mapped_column(String(50), index=True)
    entity_id: Mapped[int] = mapped_column(BigInteger, index=True)
    purchase_order_id: Mapped[int] = mapped_column(BigInteger, default=0)  # gom bộ chứng từ theo đơn
    filename: Mapped[str] = mapped_column(String(255))
    file_key: Mapped[str] = mapped_column(String(500))
    url: Mapped[str] = mapped_column(String(1000), default="")
    content_type: Mapped[str] = mapped_column(String(100), default="")
    size: Mapped[int] = mapped_column(BigInteger, default=0)
