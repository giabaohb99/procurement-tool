"""Bộ mã LOẠI MẪU trong bảng `tab_document_template` — cột `template_kind` (duoc-CR-629b bước B).

Một bảng chứa hai loại mẫu (single-table inheritance của SQLAlchemy):
  - HTML: văn bản mẫu theo loại văn bản (thư viện "Văn bản mẫu", mọi vai trò `doc_template.read` đều đọc);
  - LABOR_CONTRACT_DOCX: mẫu .docx hợp đồng lao động theo pháp nhân (chỉ qua quyền `labor_contract_template`).

Thuần stdlib (như `labor_contract_codes.py`). Số đã cấp GIỮ NGUYÊN, KHÔNG tái dùng.
Thêm loại mẫu mới = cấp số kế tiếp ở đây + thêm lớp con STI ở model + chạy `gen_status_ts.py`.
"""
from enum import IntEnum

from app.core.status_catalog import Code, CodeSet, register


class DocumentTemplateKind(IntEnum):
    HTML = 1                  # Văn bản mẫu (HTML theo loại văn bản)
    LABOR_CONTRACT_DOCX = 2   # Mẫu hợp đồng lao động (.docx theo pháp nhân)


DOCUMENT_TEMPLATE_KIND_LABELS: dict[DocumentTemplateKind, str] = {
    DocumentTemplateKind.HTML: "Văn bản mẫu",
    DocumentTemplateKind.LABOR_CONTRACT_DOCX: "Mẫu hợp đồng lao động",
}

DOCUMENT_TEMPLATE_KIND_SET = register(CodeSet("document_template_kind", "Loại mẫu văn bản", [
    Code(str(int(k)), label, sort_order=int(k))
    for k, label in DOCUMENT_TEMPLATE_KIND_LABELS.items()
]))
