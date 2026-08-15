"""VĂN BẢN MẪU - nội dung khởi tạo cho một loại văn bản.

Mẫu chỉ là điểm bắt đầu khi tạo văn bản: nội dung được CHÉP vào phiên bản 1.0,
không giữ liên kết sống với mẫu. Vì vậy sửa mẫu sau này không làm thay đổi các
văn bản đã được tạo từ mẫu đó.
"""
from sqlalchemy import (BigInteger, Boolean, Index, String, Text,
                        UniqueConstraint)
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base


class DocumentTemplate(Base, AuditMixin):
    __tablename__ = "tab_document_template"
    __table_args__ = (
        # Trong cùng một loại, hai mẫu trùng tên khiến ô chọn ở trang tạo văn
        # bản không còn phân biệt được. Khác loại vẫn được phép trùng tên.
        UniqueConstraint("doc_type_id", "name", name="uq_document_template_type_name"),
        Index("ix_document_template_type_active", "doc_type_id", "is_active"),
    )

    doc_type_id: Mapped[int] = mapped_column(BigInteger)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    # Cùng kiểu với `DocumentVersion.content_html`: mẫu có thể chứa văn bản dài,
    # bảng biểu và ảnh base64 nên TEXT 64KB là không đủ.
    content_html: Mapped[str] = mapped_column(
        Text().with_variant(MEDIUMTEXT(), "mysql"), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
