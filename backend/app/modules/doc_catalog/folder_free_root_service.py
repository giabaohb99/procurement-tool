"""Thư mục TỰ DO ở GỐC cây — `parent_id = 0`, `company_id = 0`, `kind = NORMAL`.

Chốt 24/09/2026 (đại ca): người dùng muốn tạo thư mục ở gốc cây tùy ý,
không bị buộc vào một pháp nhân — các thư mục pháp nhân chỉ là khung sẵn có.
Trước đó `folder_service._get_active_parent_or_400` chặn hẳn `parent_id = 0`.

Ba luật đi kèm để việc mở này KHÔNG làm hỏng phân quyền đang có:

1. **Người tạo tự nhận mức QUẢN LÝ** bằng một dòng ACL đích danh (nhân sự của
   họ). `company_id = 0` không nằm trong "pháp nhân với tới" của ai (trừ người
   có scope `all`), nên thiếu dòng này thì chính người tạo cũng không thấy thư
   mục vừa tạo — xem `folder_access_service.effective_levels`.
2. **`default_access = PRIVATE`** — người có `document.read` scope `all` không
   tự nhiên nhìn thấy thư mục riêng của người khác. Muốn cho ai xem thì bấm
   «Chia sẻ», giống thư mục tự tạo trên Drive.
3. **Nhận văn bản của MỌI pháp nhân** (`folder_link_service.validate_folder_for_company`
   cho qua khi `folder.company_id == 0`). Gắn vào thư mục KHÔNG mở quyền đọc
   văn bản — `document/access_service.visible_condition` vẫn lọc như cũ.

Thư mục con của thư mục tự do đi qua `folder_service.create_folder` bình
thường và thừa hưởng `company_id = 0` + ACL của cha qua `path`.
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.subject_match import EFFECT_ALLOW, SUBJECT_EMPLOYEE

from .folder_access_model import DocFolderAccess
from .folder_constants import FolderAccessLevel, FolderKind, FolderStatus
from .folder_model import DocFolder
from .folder_naming import ensure_name_unique_among_siblings
from .folder_schema import FolderCreate
from .folder_service import AUDIT_ENTITY, next_sort_order

#  Gốc = cấp 1, cùng quy ước với thư mục pháp nhân (`folder_root_service`).
FREE_ROOT_DEPTH = 1


def grant_owner_manage(db: Session, folder: DocFolder, owner_employee_id: int, actor: int) -> None:
    """Thêm dòng chia sẻ «Quản lý» đích danh cho người tạo/người chuyển —
    bỏ qua nếu họ đã có sẵn một dòng CHO PHÉP còn hiệu lực trên thư mục này.
    Không `commit` — nơi gọi gộp vào giao dịch của mình."""
    exists = (db.query(DocFolderAccess.id)
              .filter(DocFolderAccess.folder_id == folder.id,
                      DocFolderAccess.subject_kind == SUBJECT_EMPLOYEE,
                      DocFolderAccess.subject_id == owner_employee_id,
                      DocFolderAccess.effect == EFFECT_ALLOW,
                      DocFolderAccess.revoked_at.is_(None))
              .first())
    if exists:
        return
    db.add(DocFolderAccess(
        folder_id=folder.id, subject_kind=SUBJECT_EMPLOYEE, subject_id=owner_employee_id,
        effect=EFFECT_ALLOW, level=int(FolderAccessLevel.MANAGE),
        reason="Người tạo thư mục", created_by=actor, updated_by=actor,
    ))


def create_free_root_folder(db: Session, data: FolderCreate, actor: int, owner_employee_id: int) -> DocFolder:
    name = data.name.strip()
    if not name:
        raise HTTPException(400, "Tên thư mục không được để trống")
    #  Không có nhân sự thì không có chủ thể nào để cấp quyền Quản lý — thư mục
    #  sinh ra sẽ mồ côi, không ai (trừ quản trị toàn hệ) thấy được nó.
    if not owner_employee_id:
        raise HTTPException(400, "Tài khoản chưa gắn hồ sơ nhân sự nên không tạo được thư mục ở gốc")
    ensure_name_unique_among_siblings(db, 0, name)

    folder = DocFolder(
        company_id=0, parent_id=0, kind=int(FolderKind.NORMAL),
        name=name, code=(data.code or "").strip(), description=data.description or "",
        path="", depth=FREE_ROOT_DEPTH,
        sort_order=data.sort_order if data.sort_order is not None else next_sort_order(db, 0),
        status=int(FolderStatus.ACTIVE), default_access=int(FolderAccessLevel.PRIVATE),
        created_by=actor, updated_by=actor,
    )
    db.add(folder)
    db.flush()
    folder.path = f"/{folder.id}/"
    grant_owner_manage(db, folder, owner_employee_id, actor)
    db.commit()
    db.refresh(folder)
    record(db, actor, AUDIT_ENTITY, folder.id, "create", f"Tạo thư mục {folder.name} ở gốc cây")
    return folder
