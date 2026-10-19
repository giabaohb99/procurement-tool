"""VĂN BẢN MẪU - nội dung khởi tạo cho một loại văn bản.

Mẫu chỉ là điểm bắt đầu khi tạo văn bản: nội dung được CHÉP vào phiên bản 1.0,
không giữ liên kết sống với mẫu. Vì vậy sửa mẫu sau này không làm thay đổi các
văn bản đã được tạo từ mẫu đó.

duoc-CR-629b (bước B): bảng `tab_document_template` chứa CẢ mẫu hợp đồng lao động
(single-table inheritance, phân biệt bằng `template_kind`):

    TemplateRecord (lớp gốc, mang mọi cột)
      ├─ DocumentTemplate      (kind=1)  ← module document, quyền `doc_template` (mọi vai trò đọc)
      └─ LaborContractTemplate (kind=2)  ← module labor_contract, quyền `labor_contract_template`

Truy vấn qua lớp con TỰ thêm `WHERE template_kind = …` (kể cả `db.get`, `apply_scope`,
`names_map`, `Reference`) nên văn thư KHÔNG BAO GIỜ thấy mẫu HĐLĐ.
⚠️ CẤM `db.query(TemplateRecord)` / `TemplateRecord.__table__` / bulk `update()` không lọc
loại ở mã ứng dụng — chỉ migration được đụng lớp gốc (test T13 grep chặn).
Thêm loại mẫu mới = thêm lớp con + mã `DocumentTemplateKind`.
"""
from sqlalchemy import (JSON, BigInteger, Boolean, Index, SmallInteger, String,
                        Text, UniqueConstraint)
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base
from app.core.document_template_codes import DocumentTemplateKind


class TemplateRecord(Base, AuditMixin):
    __tablename__ = "tab_document_template"
    __table_args__ = (
        # Loại 1: company_id=0 ⇒ ≡ (doc_type_id, name) cũ — trong cùng một loại văn
        # bản hai mẫu trùng tên khiến ô chọn không còn phân biệt được.
        # Loại 2: doc_type_id=0 ⇒ ≡ (company_id, name) cũ.
        UniqueConstraint("template_kind", "doc_type_id", "company_id", "name",
                         name="uq_document_template_kind_scope_name"),
        Index("ix_document_template_type_active", "doc_type_id", "is_active"),
        Index("ix_document_template_lct_pick",
              "template_kind", "company_id", "contract_type", "is_active"),
    )
    __mapper_args__ = {"polymorphic_on": "template_kind"}

    #  `DocumentTemplateKind` (core/document_template_codes.py)
    template_kind: Mapped[int] = mapped_column(
        SmallInteger, default=DocumentTemplateKind.HTML, server_default="1")
    doc_type_id: Mapped[int] = mapped_column(BigInteger, default=0)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    # Cùng kiểu với `DocumentVersion.content_html`: mẫu có thể chứa văn bản dài,
    # bảng biểu và ảnh base64 nên TEXT 64KB là không đủ.
    content_html: Mapped[str] = mapped_column(
        Text().with_variant(MEDIUMTEXT(), "mysql"), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    # ---- Chỉ dùng cho kind=2 (mẫu HĐLĐ); kind=1 để mặc định 0/''/NULL ----
    company_id: Mapped[int] = mapped_column(BigInteger, default=0, server_default="0")
    #  `LaborContractType` (core/labor_contract_codes.py)
    contract_type: Mapped[int] = mapped_column(SmallInteger, default=0, server_default="0")
    #  FK MỀM → tab_file.id (riêng tư, không qua FileLink)
    file_id: Mapped[int] = mapped_column(BigInteger, default=0, server_default="0")
    original_filename: Mapped[str] = mapped_column(String(255), default="", server_default="")
    #  Danh sách biến phát hiện lúc tải lên (list[str])
    placeholders: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)


class DocumentTemplate(TemplateRecord):
    __mapper_args__ = {"polymorphic_identity": DocumentTemplateKind.HTML}
