"""Điều kiện SQL lọc `Document` theo THƯ MỤC — dùng cho `document/controller.py`.

⚠️ Luôn `EXISTS`, không `JOIN`: một văn bản có thể nằm ở NHIỀU thư mục con của
cùng một nhánh đang lọc, `JOIN` sẽ nhân dòng (rủi ro đã ghi ở `plan.md`
§"Rủi ro" — "Bảng nối làm danh sách nhân dòng → luôn dùng EXISTS, có test").
"""
from sqlalchemy import and_, exists
from sqlalchemy.orm import Session

from app.modules.document.model import Document

from .folder_link_model import DocumentFolderLink
from .folder_model import DocFolder


def folder_documents_condition(db: Session, folder_id: int, include_subfolders: bool,
                               user, profile: dict):
    """Điều kiện `Document.id` nằm trong thư mục `folder_id` (kèm cả nhánh nếu
    `include_subfolders`). Trả một biểu thức SQL để `.filter(...)` — không tự
    chạy truy vấn, nơi gọi ghép vào query đang có để giữ nguyên phạm vi/tìm
    kiếm/phân trang đang áp.

    Phase 04 (duoc-CR-475): thư mục KHÔNG THẤY → coi như RỖNG, không phải lỗi
    và không rơi về "bỏ qua bộ lọc". Với `include_subfolders`, mọi thư mục con
    KHÔNG THẤY cũng bị loại khỏi tập — văn bản chỉ nằm trong một nhánh con
    riêng tư không được lộ ra qua lượt duyệt thư mục cha.
    """
    from .folder_access_service import effective_levels

    visible_ids = set(effective_levels(db, user, profile).keys())
    if folder_id not in visible_ids:
        #  `Document.id == -1` (không đụng `DocumentFolderLink`) — tránh cartesian
        #  product giữa hai bảng khi điều kiện này đứng một mình trong `.filter()`.
        return Document.id == -1

    if include_subfolders:
        folder = db.get(DocFolder, folder_id)
        if not folder or not folder.path:
            folder_ids = db.query(DocFolder.id).filter(DocFolder.id == -1)
        else:
            #  Giao với `visible_ids` NGAY TRONG SQL: thư mục con KHÔNG THẤY
            #  không được góp văn bản vào lượt duyệt thư mục cha.
            folder_ids = (db.query(DocFolder.id)
                         .filter(DocFolder.path.like(f"{folder.path}%"),
                                DocFolder.id.in_(visible_ids)))
    else:
        folder_ids = db.query(DocFolder.id).filter(DocFolder.id == folder_id)

    return exists().where(and_(
        DocumentFolderLink.document_id == Document.id,
        DocumentFolderLink.folder_id.in_(folder_ids),
    ))
