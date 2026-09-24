"""BẢNG NỐI NHIỀU-NHIỀU văn bản ↔ thư mục — `tab_document_folder_link`.

Một văn bản nằm ở NHIỀU thư mục (chốt 1, `plan.md`); đúng MỘT dòng mang
`is_primary=1` cho mỗi văn bản — thư mục đó hiện ở cột/breadcrumb. Ràng buộc
"đúng một chính" không diễn đạt được bằng UNIQUE (MySQL không có UNIQUE có điều
kiện), nên kiểm ở tầng service (`folder_link_service.set_folders`) + bài kiểm.

Cố ý KHÔNG có `updated_at`/`updated_by`: một dòng nối chỉ SINH hoặc MẤT, không
có khái niệm "sửa" — đổi thư mục chính là xóa dòng cũ, thêm dòng mới (hoặc đổi
cờ `is_primary` tại chỗ, vẫn không phải "sửa nội dung" dòng nối).

Không FK cho `document_id`/`folder_id` — cùng quy ước với các bảng `doc_catalog`
khác (xem `folder_model.py`).
"""
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Index, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base


class DocumentFolderLink(Base):
    __tablename__ = "tab_document_folder_link"
    __table_args__ = (
        UniqueConstraint("document_id", "folder_id", name="uq_document_folder_link"),
        Index("ix_document_folder_link_document", "document_id"),
        Index("ix_document_folder_link_folder", "folder_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(BigInteger)
    folder_id: Mapped[int] = mapped_column(BigInteger)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[int] = mapped_column(BigInteger, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
