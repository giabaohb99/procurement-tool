"""Chuyển thư mục sang cha khác — `folder_service.move_folder` tách riêng.

Rebalance `path`/`depth` của CẢ NHÁNH là nghiệp vụ tự đứng một mình (khác hẳn
create/update/reorder/delete thuần CRUD), nên tách khỏi `folder_service.py` để
giữ cả hai tệp dưới 200 dòng.
"""
from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.audit import record

from .folder_constants import MAX_DEPTH, PATH_MAX_LENGTH, FolderKind, FolderStatus
from .folder_free_root_service import grant_owner_manage
from .folder_model import DocFolder
from .folder_naming import ensure_name_unique_among_siblings
from .folder_service import AUDIT_ENTITY


def move_folder(db: Session, folder: DocFolder, new_parent_id: int, actor: int,
                owner_employee_id: int = 0) -> DocFolder:
    """Chuyển thư mục sang cha khác — BẤT KỲ đâu, kể cả sang nhánh pháp nhân
    khác, ra GỐC cây (`new_parent_id = 0`), hay chuyển chính thư mục pháp nhân
    (đại ca chốt 24/09/2026: thư mục là chỗ người dùng tự sắp xếp, không buộc
    theo công ty). Cập nhật `path`/`depth` của CẢ NHÁNH bằng MỘT câu `UPDATE`
    (không đệ quy Python) trong cùng giao dịch.

    `company_id` của thư mục KHÔNG đổi theo chỗ mới — nó quyết định ai "với
    tới" thư mục qua quyền theo pháp nhân (`folder_access_service`), còn quyền
    chia sẻ đích danh thì kế thừa theo `path` mới.
    """
    if folder.kind == int(FolderKind.COMPANY_GROUP):
        raise HTTPException(400, "Thư mục nhóm «Công ty» luôn nằm ở gốc cây, không chuyển được")
    if new_parent_id == folder.parent_id:
        return folder

    #  Khóa CẢ HAI dòng TRƯỚC khi đọc `path` để kiểm vòng (M7, rà soát
    #  23/09/2026) — không khóa thì hai lệnh dời CHÉO cùng lúc (A→con của B,
    #  B→con của A) đều đọc `path` CŨ song song, đều qua được kiểm tiền tố,
    #  ghi xong `path` thành một vòng lặp không lối ra. Khóa theo THỨ TỰ id
    #  TĂNG DẦN để hai giao dịch dời chéo không tự gây deadlock lẫn nhau.
    #  `with_for_update()` là `SELECT ... FOR UPDATE` thật trên MySQL (prod);
    #  SQLite (bài kiểm) không hỗ trợ khóa dòng nên SQLAlchemy tự bỏ qua mệnh
    #  đề này — vô hại, không lỗi.
    lock_ids = sorted({folder.id, new_parent_id} - {0})
    locked_rows = {
        row.id: row
        for row in db.query(DocFolder).filter(DocFolder.id.in_(lock_ids)).with_for_update().all()
    }
    folder = locked_rows.get(folder.id, folder)
    if new_parent_id:
        new_parent = locked_rows.get(new_parent_id)
        if new_parent is None:
            raise HTTPException(404, "Không tìm thấy thư mục")
        if new_parent.status != int(FolderStatus.ACTIVE):
            raise HTTPException(400, "Thư mục đích đang ngừng dùng")
        #  Chặn vòng: cha mới không được là chính nó hay một hậu duệ của nó — nhờ
        #  `path`, chỉ cần so tiền tố chuỗi, không phải đệ quy dò cha từng cấp.
        if new_parent.id == folder.id or (folder.path and new_parent.path.startswith(folder.path)):
            raise HTTPException(400, "Không chuyển thư mục vào chính nó hoặc vào thư mục con của nó")
        parent_id, parent_path, parent_depth, parent_name = (
            new_parent.id, new_parent.path, new_parent.depth, new_parent.name or "(thư mục pháp nhân)")
    else:
        parent_id, parent_path, parent_depth, parent_name = 0, "/", 0, "gốc cây"

    #  Thư mục pháp nhân chưa đặt tên tay có `name = ""` — bỏ qua kiểm trùng,
    #  không thì hai gốc pháp nhân gặp nhau là "«» đã tồn tại".
    if folder.name:
        ensure_name_unique_among_siblings(db, parent_id, folder.name, exclude_id=folder.id)

    old_prefix = folder.path
    max_depth_in_branch = db.query(func.max(DocFolder.depth)).filter(
        DocFolder.path.like(f"{old_prefix}%")).scalar() or folder.depth
    depth_delta = (parent_depth + 1) - folder.depth
    if max_depth_in_branch + depth_delta > MAX_DEPTH:
        raise HTTPException(400, f"Chuyển vào đây vượt quá độ sâu tối đa {MAX_DEPTH} cấp")

    new_prefix = f"{parent_path}{folder.id}/"
    #  `path` dài nhất trong nhánh sau khi thay tiền tố — vượt cột thì câu
    #  `UPDATE` bên dưới nổ 500 ở MySQL (SQLite của bộ test thì im lặng nhận).
    longest_path = db.query(func.max(func.length(DocFolder.path))).filter(
        DocFolder.path.like(f"{old_prefix}%")).scalar() or len(old_prefix)
    if longest_path - len(old_prefix) + len(new_prefix) > PATH_MAX_LENGTH:
        raise HTTPException(400, "Chuyển vào đây thì nhánh thư mục quá sâu, hệ thống không lưu được đường dẫn")
    #  Vị trí (1-based) NGAY SAU tiền tố cũ — `SUBSTR` chạy được cả MySQL lẫn
    #  SQLite (bộ test), khác `UPDATE ... CONCAT` viết tay dễ lệch phương ngữ.
    cut_at = len(old_prefix) + 1
    db.query(DocFolder).filter(
        DocFolder.path.like(f"{old_prefix}%"), DocFolder.id != folder.id,
    ).update(
        {
            DocFolder.path: func.concat(new_prefix, func.substr(DocFolder.path, cut_at)),
            DocFolder.depth: DocFolder.depth + depth_delta,
        },
        synchronize_session=False,
    )

    folder.parent_id = parent_id
    folder.path = new_prefix
    folder.depth = parent_depth + 1
    folder.updated_by = actor
    #  Thư mục TỰ DO (`company_id = 0`) ra gốc thì mất quyền kế thừa từ cha cũ —
    #  người chuyển (đã có mức Quản lý, route gác) giữ lại quyền bằng một dòng
    #  chia sẻ đích danh, không thì thư mục biến mất khỏi mắt chính họ.
    if not parent_id and not folder.company_id and owner_employee_id:
        grant_owner_manage(db, folder, owner_employee_id, actor)
    db.commit()
    db.refresh(folder)
    record(db, actor, AUDIT_ENTITY, folder.id, "update",
          f"Chuyển thư mục {folder.name} sang {parent_name}")
    return folder
