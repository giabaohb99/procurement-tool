"""QUAN HỆ GIỮA CÁC VĂN BẢN (`04` mục 5.5).

Một dòng = một câu "văn bản A <quan hệ> văn bản B". Mười giá trị `relation` khai
ở `doc_catalog/link_rule_model.py`, dùng chung với bảng quy tắc.

Hai dòng KHÔNG xóa được (`is_system = True`):

1. **Căn cứ theo** của bản clone về bản gốc — xóa được thì vài tháng sau có bản
   clone mồ côi, không truy về gốc được.
2. **Trích từ** — và dòng này bắt buộc có `source_version_id`. Không ghi phiên
   bản gốc thì sáu tháng sau không ai biết bản trích đang nói theo bản nào; đó
   chính là cách nội dung cũ rò rỉ ra ngoài dưới danh nghĩa văn bản còn hiệu lực.
"""
from sqlalchemy import BigInteger, Boolean, Index, SmallInteger, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base


class DocumentLink(Base, AuditMixin):
    __tablename__ = "tab_document_link"
    __table_args__ = (
        UniqueConstraint("source_document_id", "target_document_id", "relation",
                         name="uq_document_link"),
        #  Cây tài liệu tra cả hai chiều: "con của tôi là ai" và "tôi là con của ai".
        Index("ix_document_link_source", "source_document_id", "relation"),
        Index("ix_document_link_target", "target_document_id", "relation"),
    )

    source_document_id: Mapped[int] = mapped_column(BigInteger)
    target_document_id: Mapped[int] = mapped_column(BigInteger)
    relation: Mapped[int] = mapped_column(SmallInteger)

    #  Quy tắc nào sinh ra quan hệ này. Rỗng với quan hệ khai tay ngoài quy tắc.
    rule_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    #  CHỈ dùng cho quan hệ "trích từ": bản trích tách ra từ phiên bản nào của
    #  gốc. So với `current_version_id` của gốc để biết bản trích đã lạc hậu chưa.
    source_version_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    note: Mapped[str] = mapped_column(String(500), default="")
    #  Hệ thống tự tạo — không màn hình nào, không nút nào, không hàm nào xóa được.
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
