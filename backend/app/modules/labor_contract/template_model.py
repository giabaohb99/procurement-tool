"""MẪU HỢP ĐỒNG LAO ĐỘNG theo pháp nhân — dòng `template_kind = 2` của `tab_document_template`.

Mỗi mẫu = một tệp .docx do HR tải lên, gắn ĐÚNG MỘT pháp nhân + ĐÚNG MỘT loại HĐ.
Tệp lưu ở `tab_file` (riêng tư, không qua `FileLink`); `file_id` là FK MỀM.

duoc-CR-629b (bước B): trước đây là bảng riêng `tab_labor_contract_template` (nay đổi tên
`..._bak629`, không còn model). Lớp con STI của `TemplateRecord` — xem
`app/modules/document/template_model.py`; `id` mẫu GIỮ NGUYÊN nên
`tab_labor_contract.template_id` (FK mềm) không đổi.
"""
from sqlalchemy.orm import synonym

from app.core.document_template_codes import DocumentTemplateKind
from app.modules.document.template_model import TemplateRecord


class LaborContractTemplate(TemplateRecord):
    __mapper_args__ = {"polymorphic_identity": DocumentTemplateKind.LABOR_CONTRACT_DOCX}
    #  Lịch sử thay đổi (`tab_change_log.table_name`) của mẫu HĐLĐ giữ tên bảng CŨ: liền mạch với dữ liệu
    #  trước khi gộp, không lẫn với mẫu văn bản, và `_backfill_audit` ghép đúng entity `labor_contract_template`.
    __change_log_table__ = "tab_labor_contract_template"

    #  Ghi chú dùng cột `description` chung (schema HĐLĐ vẫn chặn 500 ký tự)
    note = synonym("description")
