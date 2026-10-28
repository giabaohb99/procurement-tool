"""Tải tệp căn cứ của kế hoạch nhân sự -> TỰ TẠO văn bản ở phân hệ Văn bản (duoc-CR-690).

Người lập chọn tệp (quyết định, tờ trình…) ngay ở mục «Văn bản liên kết»; hệ thống tạo một văn bản loại
`CCKHNS` («Căn cứ kế hoạch nhân sự») có đúng tệp đó ở phiên bản hiện hành, rồi trả thông tin để giao diện
thêm vào danh sách văn bản của bản nháp. KHÔNG cần id kế hoạch (dùng được cả lúc tạo mới); gắn vào kế hoạch
vẫn đi qua `document_ids` của lệnh lưu (`service.link_documents`).

KÍN: loại `CCKHNS` bật `is_personal` — phạm vi vai trò (kể cả «công ty») KHÔNG mở được; chỉ người tạo, người
được chia đích danh, người duyệt và vai trò phạm vi «tất cả» đọc. Tệp có thể chứa bảng lương.
Khuôn tạo văn bản + gắn tệp: `labor_contract/document_archive_sync.py` + `document_archive_files.py`.
"""
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.auth import user_has_permission
from app.core.file_registry import policy
from app.core.scoping import get_perm_profile
from app.modules.attachment.model import FileLink
from app.modules.attachment.service import delete_stored_file
from app.modules.doc_catalog.model import DocType
from app.modules.document import service as doc_service
from app.modules.document.access_service import can as can_read_document
from app.modules.document.model import CONTENT_MODE_FILES, Document
from app.modules.document.schema import DocumentCreate
from app.modules.employee.model import Employee

DOC_TYPE_CODE = "CCKHNS"
TITLE_MAX = 500
NO_DOC_READ = "Bạn chưa có quyền xem phân hệ Văn bản nên chưa tải tệp căn cứ lên được"
NO_DOC_TYPE = "Chưa có loại văn bản «Căn cứ kế hoạch nhân sự» — liên hệ quản trị để chạy cập nhật dữ liệu"


def document_item(doc: Document) -> dict:
    """Một dòng văn bản liên kết ở dạng đọc được — dùng chung cho chi tiết kế hoạch và kết quả tải lên."""
    return {"document_id": doc.id, "can_read": True, "code": doc.doc_code or doc.issue_number or "",
            "title": doc.title or "", "status": int(doc.status or 0)}


def _title_of(title: str, filename: str) -> str:
    title = (title or "").strip()
    if len(title) > TITLE_MAX:
        raise HTTPException(422, f"Trích yếu tối đa {TITLE_MAX} ký tự")
    return title or f"Căn cứ kế hoạch nhân sự – {filename}"[:TITLE_MAX]


def create_from_upload(db: Session, user, file: UploadFile, title: str) -> dict:
    """Lưu tệp (cùng luật đuôi / dung lượng / byte đầu như đính kèm Văn bản) rồi tạo văn bản có tệp đó."""
    #  Tạo xong mà chính người tạo không đọc được thì lúc lưu kế hoạch `link_documents` sẽ 403 — chặn sớm, đỡ sinh văn bản vô ích.
    if not user_has_permission(db, user, "document", "read"):
        raise HTTPException(403, NO_DOC_READ)
    doc_type = db.query(DocType).filter(DocType.code == DOC_TYPE_CODE, DocType.is_active.is_(True)).first()
    if doc_type is None:
        raise HTTPException(409, NO_DOC_TYPE)
    final_title = _title_of(title, file.filename or "tệp")

    #  Import cục bộ: attachment.controller kéo theo nhiều module (tránh vòng import lúc nạp router).
    from app.modules.attachment.controller import _store_one
    from app.modules.document.search_index_service import queue_reindex

    _, exts, max_mb = policy("document_version")
    stored = _store_one(db, file, exts, max_mb, user.id)   # 400/413/415 tiếng Việt từ guard_upload; commit dòng tab_file
    try:
        emp = db.get(Employee, user.employee_id) if getattr(user, "employee_id", 0) else None
        payload = DocumentCreate(
            doc_type_id=doc_type.id, company_id=(emp.company_id if emp else 0) or 0,
            department_id=(emp.department_id if emp else 0) or 0,
            owner_employee_id=(emp.id if emp else 0), title=final_title,
            summary="Tệp căn cứ tải lên từ kế hoạch nhân sự", content_mode=CONTENT_MODE_FILES)
        doc = doc_service.create_document(db, payload, user.id, user=user, commit=False)
        db.add(FileLink(file_id=stored.id, entity=doc_service.ATTACH_ENTITY, entity_id=doc.current_version_id,
                        created_by=user.id, updated_by=user.id))
        db.commit()
        db.refresh(doc)
    except Exception:
        db.rollback()
        delete_stored_file(db, stored.id)   # tệp vừa đẩy lên không còn ai dùng
        db.commit()
        raise
    queue_reindex(db, doc.id)
    if not can_read_document(db, doc, user, get_perm_profile(db, user), "read"):
        #  Không xảy ra với vai trò có document.read phạm vi bất kỳ; giữ làm lưới an toàn trước khi trả về giao diện.
        raise HTTPException(403, NO_DOC_READ)
    return document_item(doc)
