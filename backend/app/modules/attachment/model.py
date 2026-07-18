from sqlalchemy import BigInteger, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, AuditMixin


class StoredFile(Base, AuditMixin):
    """FILE THẬT — 1 dòng = 1 file trên storage (R2/local). Tách khỏi liên kết để 1 file
    có thể gắn vào nhiều record, và quản lý file rác (không có link) dễ dàng."""

    __tablename__ = "tab_file"

    filename: Mapped[str] = mapped_column(String(255))
    file_key: Mapped[str] = mapped_column(String(500))
    url: Mapped[str] = mapped_column(String(1000), default="")
    content_type: Mapped[str] = mapped_column(String(100), default="")
    size: Mapped[int] = mapped_column(BigInteger, default=0)


class FileLink(Base, AuditMixin):
    """LIÊN KẾT file ↔ record. Xóa link không nhất thiết xóa file (file có thể dùng chỗ khác)."""

    __tablename__ = "tab_file_link"

    file_id: Mapped[int] = mapped_column(BigInteger, index=True)
    entity: Mapped[str] = mapped_column(String(50), index=True)
    entity_id: Mapped[int] = mapped_column(BigInteger, index=True)
    purchase_order_id: Mapped[int] = mapped_column(BigInteger, default=0)   # gom bộ chứng từ theo đơn
    doc_type: Mapped[str] = mapped_column(String(50), default="", index=True)  # loại chứng từ (cố định trong code)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")  # thứ tự hiển thị (ảnh SP); nhỏ = trước
