"""Tab «Tệp» của văn bản (phase 09, duoc-CR-478) — tệp của MỌI phiên bản trong
MỘT lần gọi.

Khác `GET /api/attachments?entity=document_version&entity_id=<phiên bản>`:
đường đó chỉ trả tệp của MỘT phiên bản. Tab Tệp cần dựng CÂY THEO PHIÊN BẢN
(bản đang dùng + các bản cũ) ngay trên một màn hình, nên phải gộp hết trong một
truy vấn — mở văn bản có năm phiên bản không thể là năm lượt gọi.

Quyền: đi qua CHÍNH văn bản (`doc_reader` + `_load`, đúng khuôn `get_document`
ở `controller.py`), không lặp lại kiểm quyền theo từng phiên bản riêng — đọc
được văn bản thì đọc được tệp của mọi phiên bản nó có (đính kèm không có ACL
riêng ngoài quyền đọc văn bản cha).
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import success
from app.modules.attachment.controller import _link_out
from app.modules.attachment.model import FileLink, StoredFile
from app.modules.employee.model import Employee
from app.modules.user.model import User

from .controller import _load, doc_reader
from .version_model import DocumentVersion

router = APIRouter(prefix="/api/documents", tags=["document"])

ATTACH_ENTITY = "document_version"


@router.get("/{document_id}/attachments")
def list_all_attachments(
    document_id: int,
    db: Session = Depends(get_db),
    user=Depends(doc_reader),
):
    """Tệp của MỌI phiên bản — dùng cho tab Tệp (rẽ 0/1/nhiều, cây theo phiên bản)."""
    doc = _load(db, document_id, user)

    versions = (db.query(DocumentVersion)
                .filter(DocumentVersion.document_id == document_id)
                .order_by(DocumentVersion.major.desc(), DocumentVersion.minor.desc())
                .all())
    version_ids = [v.id for v in versions]
    if not version_ids:
        return success([])

    rows = (db.query(FileLink, StoredFile)
            .join(StoredFile, StoredFile.id == FileLink.file_id)
            .filter(FileLink.entity == ATTACH_ENTITY, FileLink.entity_id.in_(version_ids))
            .order_by(FileLink.sort_order.asc(), FileLink.id.desc()).all())

    #  «Người tải» — MỘT truy vấn gộp cho cả trang, không tra tên trong vòng lặp
    #  (đúng nguyên tắc của `document/serializer.py`). Số dòng của một văn bản
    #  hiếm khi vượt vài chục nên không cần phân trang cho riêng đường này.
    creator_ids = {link.created_by for link, _ in rows if link.created_by}
    creator_names: dict[int, str] = {}
    if creator_ids:
        for uid, full_name, email in (
            db.query(User.id, Employee.full_name, User.email)
            .outerjoin(Employee, Employee.id == User.employee_id)
            .filter(User.id.in_(creator_ids)).all()
        ):
            creator_names[uid] = full_name or email or ""

    version_by_id = {v.id: v for v in versions}
    out = []
    for link, f in rows:
        version = version_by_id.get(link.entity_id)
        item = _link_out(link, f)
        item["version_id"] = version.id if version else 0
        item["version_no"] = version.version_no if version else ""
        item["is_current_version"] = bool(version and doc.current_version_id == version.id)
        item["created_by_name"] = creator_names.get(link.created_by, "")
        item["created_at"] = link.created_at.isoformat() if link.created_at else ""
        out.append(item)
    return success(out)
