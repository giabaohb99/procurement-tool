"""Thư mục PHÁP NHÂN (gốc của mỗi nhánh) — tự sinh, không tạo tay.

Rà soát 24/09/2026 (duoc-CR-475): chủ dự án chốt gốc chỉ là CHỖ CHỨA MẶC ĐỊNH
cho văn bản chưa gắn thư mục — nó phải XÓA ĐƯỢC y hệt thư mục thường
(`folder_service.delete_folder`), và một khi đã xóa thì KHÔNG được tự mọc lại.
Vì vậy việc sinh gốc không còn chạy TỰ ĐỘNG ở đâu trong ứng dụng nữa:

  * `ensure_company_roots` (hàng loạt, MỌI công ty) — không còn ai gọi lúc
    khởi động (`app/seed.py`, `app/seed_prod.py`) hay lúc tạo pháp nhân
    (`company/service.create_company`). Giữ lại CHỈ để một script vận hành
    gọi tay khi cần dựng lại toàn bộ (vd sau khi phục hồi dữ liệu từ bản sao
    cũ hơn migration `e4a1c9d572b6`).
  * `get_or_create_company_root` (MỘT công ty) — đường LAZY duy nhất còn lại,
    gọi từ `folder_link_service._company_root_id` đúng lúc một văn bản cần
    thư mục mặc định mà công ty đó chưa có gốc. Không đụng tới gốc của công ty
    khác — khác hẳn gọi cả `ensure_company_roots` (sẽ hồi sinh MỌI gốc đã bị
    xóa, không chỉ đúng công ty đang cần).

Cả hai dùng chung `_insert_root` — IntegrityError-safe dưới tải đồng thời (M8,
rà soát 23/09/2026): chỉ mục UNIQUE `ux_doc_folder_root_company` (model) chặn
hai gốc trùng company_id ở tầng DB, ở đây chỉ cần bắt lỗi rồi đọc lại.
"""
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.audit import record

from .folder_constants import (COMPANY_GROUP_NAME, COMPANY_ROOT_DEFAULT_ACCESS, FolderAccessLevel,
                               FolderKind, FolderStatus)
from .folder_model import DocFolder

AUDIT_ENTITY = "doc_folder"


def _find_root(db: Session, company_id: int) -> DocFolder | None:
    return (
        db.query(DocFolder)
        .filter(DocFolder.company_id == company_id, DocFolder.kind == int(FolderKind.COMPANY))
        .first()
    )


def get_or_create_company_group(db: Session, actor: int = 0) -> DocFolder:
    """Thư mục NHÓM «Công ty» ở gốc cây — chứa mọi thư mục pháp nhân (24/09/2026).
    Đúng MỘT dòng (`kind = COMPANY_GROUP`); migration `c0mpgr0up01` đã tạo sẵn
    trên hệ đang chạy, ở đây chỉ còn là lưới đỡ cho DB mới (bài kiểm, seed)."""
    group = db.query(DocFolder).filter(DocFolder.kind == int(FolderKind.COMPANY_GROUP)).first()
    if group:
        return group
    group = DocFolder(
        company_id=0, parent_id=0, kind=int(FolderKind.COMPANY_GROUP),
        name=COMPANY_GROUP_NAME, path="", depth=1, sort_order=0,
        status=int(FolderStatus.ACTIVE), default_access=int(FolderAccessLevel.VIEW),
        created_by=actor, updated_by=actor,
    )
    db.add(group)
    db.flush()
    group.path = f"/{group.id}/"
    db.commit()
    db.refresh(group)
    return group


def _insert_root(db: Session, company_id: int, actor: int) -> DocFolder | None:
    """Chèn MỘT gốc cho `company_id` — NẰM TRONG thư mục nhóm «Công ty»
    (24/09/2026), không phải ở gốc cây. Trả `None` nếu thua cuộc đua (một giao
    dịch khác vừa chèn xong) — người gọi tự đọc lại nếu cần lấy đúng dòng đó."""
    group = get_or_create_company_group(db, actor)
    root = DocFolder(
        company_id=company_id, root_company_id=company_id, parent_id=group.id,
        kind=int(FolderKind.COMPANY),
        name="", path="", depth=group.depth + 1, sort_order=0,
        status=int(FolderStatus.ACTIVE),
        default_access=int(COMPANY_ROOT_DEFAULT_ACCESS),
        created_by=actor, updated_by=actor,
    )
    db.add(root)
    try:
        db.flush()
    except IntegrityError:
        #  Thua cuộc đua — `rollback()` hủy CẢ giao dịch hiện tại nên phải
        #  `commit()` từng gốc NGAY khi vừa tạo (bên dưới), không gộp cuối vòng.
        db.rollback()
        return None
    root.path = f"{group.path}{root.id}/"
    db.commit()
    db.refresh(root)
    record(db, actor, AUDIT_ENTITY, root.id, "create",
          f"Tự sinh thư mục pháp nhân cho công ty #{company_id}")
    return root


def get_or_create_company_root(db: Session, company_id: int, actor: int = 0) -> DocFolder | None:
    """LẤY gốc của một công ty, TẠO ngay nếu chưa có — đường LAZY duy nhất còn
    lại sau khi bỏ tự sinh ở seed/tạo pháp nhân. `None` nếu `company_id` không
    ứng với một `Company` nào (không có pháp nhân thì không có gốc nào đúng để
    tạo — người gọi tự quyết định coi đó là lỗi hay bỏ qua)."""
    root = _find_root(db, company_id)
    if root:
        return root
    from app.modules.company.model import Company

    if not db.get(Company, company_id):
        return None
    return _insert_root(db, company_id, actor) or _find_root(db, company_id)


def ensure_company_roots(db: Session, actor: int = 0) -> list[DocFolder]:
    """Tạo thư mục pháp nhân cho MỌI `Company` còn thiếu — idempotent, AN TOÀN
    dưới tải đồng thời (M8). KHÔNG còn tự chạy ở seed hay lúc tạo pháp nhân
    (rà soát 24/09/2026) — chỉ còn dùng cho script vận hành gọi tay.
    """
    from app.modules.company.model import Company

    existing = {row[0] for row in db.query(DocFolder.company_id)
                .filter(DocFolder.kind == int(FolderKind.COMPANY)).all()}
    created: list[DocFolder] = []
    for company in db.query(Company).all():
        if company.id in existing:
            continue
        root = _insert_root(db, company.id, actor)
        if root:
            created.append(root)
    return created
