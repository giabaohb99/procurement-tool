"""Quy tắc đánh số văn bản theo chiều, loại văn bản và sổ áp dụng."""

from sqlalchemy import (BigInteger, Boolean, ForeignKey, Index, Integer,
                        SmallInteger, String, UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base


class DocumentNumberingRule(Base, AuditMixin):
    """Một quy tắc có một bộ đếm riêng cho từng pháp nhân.

    `pattern` dùng các token có tên cố định như `{STT}`, `{Nam}`, `{LoaiVB}`.
    Bộ đếm thật vẫn nằm ở `tab_number_sequence` và được khóa dòng lúc cấp số.
    """

    __tablename__ = "tab_document_numbering_rule"
    __table_args__ = (
        Index("ix_numbering_rule_direction", "direction", "is_active", "priority"),
    )

    # 1 văn bản đến, 2 văn bản đi, 3 văn bản nội bộ.
    direction: Mapped[int] = mapped_column(SmallInteger)
    pattern: Mapped[str] = mapped_column(String(200))
    start_no: Mapped[int] = mapped_column(Integer, default=1)
    reset_yearly: Mapped[bool] = mapped_column(Boolean, default=True)
    allow_manual: Mapped[bool] = mapped_column(Boolean, default=False)

    # 1 tất cả, 2 các loại được chọn ở bảng con.
    doc_type_mode: Mapped[int] = mapped_column(SmallInteger, default=1)
    # 1 tất cả sổ, 2 các sổ được chọn, 3 văn bản không vào sổ.
    book_mode: Mapped[int] = mapped_column(SmallInteger, default=1)
    # Số nhỏ được xét trước. Hai quy tắc cùng ưu tiên thì quy tắc cụ thể hơn thắng.
    priority: Mapped[int] = mapped_column(Integer, default=100)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class DocumentNumberingRuleDocType(Base, AuditMixin):
    __tablename__ = "tab_document_numbering_rule_doc_type"
    __table_args__ = (
        UniqueConstraint("rule_id", "doc_type_id", name="uq_numbering_rule_doc_type"),
    )

    rule_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tab_document_numbering_rule.id", ondelete="CASCADE"),
        index=True,
    )
    doc_type_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tab_doc_type.id", ondelete="CASCADE"),
        index=True,
    )


class DocumentNumberingRuleBook(Base, AuditMixin):
    __tablename__ = "tab_document_numbering_rule_book"
    __table_args__ = (
        UniqueConstraint("rule_id", "book_id", name="uq_numbering_rule_book"),
    )

    rule_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tab_document_numbering_rule.id", ondelete="CASCADE"),
        index=True,
    )
    book_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tab_document_book.id", ondelete="CASCADE"),
        index=True,
    )
