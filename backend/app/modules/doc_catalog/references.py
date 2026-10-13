"""ai-CR-191 — sổ tham chiếu của các danh mục / cấu hình Văn thư (`doc_catalog`).

`doc_catalog/controller.py` import tệp này lúc khởi động. Hai danh mục đi qua `make_crud_router`
(`doc_type`, `external_party`) được chốt tự động; bốn cấu hình có đường xóa riêng (thư mục, sổ, quy tắc
đánh số, quy tắc quan hệ) gọi `reference_guard.ensure_deletable` ngay trong hàm xóa của service — các
service đó cũng import tệp này để sổ được nạp kể cả khi gọi thẳng từ bài kiểm.

Mức mật (`security_level`) KHÔNG đăng ký ở đây: nó tham chiếu bằng CẶP (thang, bậc) và còn phải dò
JSON điều kiện luồng duyệt — chốt riêng `security_level_guard.before_delete` đã làm đủ, giữ nguyên.

Tên entity phải khớp đúng chuỗi ở `make_crud_router(... entity=...)` / `require(entity, "delete")`:
`doc_type`, `external_party`, `doc_folder`, `document_book`, `doc_numbering_rule`, `doc_link_rule`.
"""
from app.core.reference_guard import Reference, register
from app.modules.document.incoming_register_model import IncomingRegister
from app.modules.document.link_model import DocumentLink
from app.modules.document.model import Document
from app.modules.document.recipient_model import DocumentRecipient
from app.modules.document.request_model import DocumentRequest
from app.modules.document.template_model import DocumentTemplate

from .link_rule_model import DocTypeLinkRule
from .model import DocType
from .numbering_rule_model import (DocumentNumberingRuleBook,
                                   DocumentNumberingRuleDocType)

register("doc_type", "Loại văn bản", [
    Reference(Document, "doc_type_id", "văn bản"),
    Reference(DocumentRequest, "doc_type_id", "yêu cầu soạn văn bản"),
    Reference(DocumentTemplate, "doc_type_id", "mẫu văn bản"),
    Reference(DocumentNumberingRuleDocType, "doc_type_id", "quy tắc đánh số"),
    Reference(DocTypeLinkRule, "source_type_id", "quy tắc quan hệ (loại nguồn)"),
    Reference(DocTypeLinkRule, "target_type_id", "quy tắc quan hệ (loại đích)"),
])

register("external_party", "Đối tác ngoài", [
    Reference(DocumentRecipient, "external_party_id", "nơi nhận văn bản"),
    Reference(IncomingRegister, "sender_party_id", "văn bản đến"),
])

#  Thư mục: văn bản trong thư mục KHÔNG chặn (đại ca chốt 25/09/2026 — xóa thì gỡ/chuyển văn bản,
#  xem `folder_service.delete_folder`); chỉ chặn khi một loại văn bản còn lấy nó làm thư mục mặc định,
#  vì `DocType.default_folder_id` sẽ trỏ vào khoảng không và văn bản mới của loại đó mất chỗ rơi.
register("doc_folder", "Thư mục văn bản", [
    Reference(DocType, "default_folder_id", "loại văn bản lấy làm thư mục mặc định"),
])

register("document_book", "Sổ văn bản", [
    Reference(Document, "book_id", "văn bản"),
    Reference(DocumentNumberingRuleBook, "book_id", "quy tắc đánh số"),
])

register("doc_numbering_rule", "Quy tắc đánh số", [
    Reference(Document, "numbering_rule_id", "văn bản"),
])

register("doc_link_rule", "Quy tắc quan hệ loại văn bản", [
    Reference(DocumentLink, "rule_id", "liên kết văn bản"),
])
