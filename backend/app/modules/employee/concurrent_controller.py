"""API KIÊM NHIỆM — `prefix=/api/employees` (duoc-CR-755; hai loại dòng độc lập ở duoc-CR-756).

Bốn đường REST trên `tab_employee_concurrent`. Mọi đường ghi qua `concurrent_service` (L1/L2/L3);
đọc xét phạm vi HỒ SƠ CHA (`employee_in_scope` → 404 ngoài phạm vi). Hai loại dòng: 1 Phòng ban (phòng của công ty
chính), 2 Công ty (công ty khác, không phòng).
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.audit import record as audit_record
from app.core.auth import get_perm_profile, require
from app.core.database import get_db
from app.core.response import success

from . import concurrent_access, concurrent_service
from .concurrent_schema import ConcurrentIn, ConcurrentPatch
from .concurrent_serializer import serialize_list, serialize_one
from .service import clear_perm_cache_of
from .work_history_access import employee_in_scope

router = APIRouter(prefix="/api/employees", tags=["employee"])


def _describe(row) -> str:
    """Câu cho nhật ký thao tác — mã phòng / công ty theo id (tên nằm ở danh sách)."""
    msg = f"công ty #{row.company_id}" if row.kind == 2 else f"phòng #{row.department_id}"
    if row.from_date:
        msg += f", từ {row.from_date.isoformat()}"
    if row.to_date:
        msg += f" đến {row.to_date.isoformat()}"
    if row.decision_no:
        msg += f", QĐ {row.decision_no}"
    msg += "" if row.counts_scope else " (không tính vào phạm vi quyền)"
    return msg


@router.get("/{eid}/concurrents")
def list_concurrents(eid: int, db: Session = Depends(get_db), user=Depends(require("employee", "read"))):
    """Danh sách kiêm nhiệm của một nhân sự (mới nhất trước).

    Quyền `employee.read` + hồ sơ nằm trong phạm vi (ngoài phạm vi: 404). Trả `items` (mỗi dòng có
    `kind` số 1 Phòng ban / 2 Công ty kèm `kind_label`, `status` số 1 Sắp tới / 2 Đang hiệu lực / 3 Đã hết kèm
    `status_label`, tên công ty / phòng ban (loại Công ty: `department_id` 0, tên phòng trống), `file_count`), `can_edit` (được ghi, không phải hồ sơ của chính mình) và `can_open_files`.
    """
    profile = get_perm_profile(db, user)
    employee_in_scope(db, eid, user, profile, "read")
    rows = concurrent_service.list_concurrents(db, eid)
    return success({
        "items": serialize_list(db, rows),
        "can_edit": concurrent_access.can_edit(db, user, profile, eid),
        "can_open_files": concurrent_access.can_open_files(profile, eid),
    })


@router.post("/{eid}/concurrents")
def create_concurrent(eid: int, data: ConcurrentIn, db: Session = Depends(get_db),
                      user=Depends(require("employee", "write"))):
    """Thêm một dòng kiêm nhiệm: `kind` bắt buộc (1 Phòng ban, 2 Công ty) kèm chức vụ, ngày, quyết định, công tắc phạm vi.

    Loại 1 chỉ gửi `department_id` (công ty điền ở máy chủ = công ty chính của hồ sơ); loại 2 chỉ gửi `company_id`
    (khác công ty chính, không phòng) — gửi sai hình là 422. Quyền `employee.write` đúng phạm vi hồ sơ. Chặn: tự sửa
    của mình (403); loại 1 ngoài phạm vi ghi theo phòng (403); loại 2 mà người thao tác không có phạm vi ghi toàn công
    ty đó (403); hồ sơ chưa gắn pháp nhân chính, phòng không phục vụ công ty hiện tại, trùng phòng / công ty chính
    (400); chồng giai đoạn cùng phòng (loại 1) hoặc cùng công ty (loại 2) (409); quá 30 dòng (400).
    """
    profile = get_perm_profile(db, user)
    emp = employee_in_scope(db, eid, user, profile, "write")
    row = concurrent_service.create_concurrent(db, emp, data, user, profile)
    db.commit()
    db.refresh(row)
    clear_perm_cache_of(db, eid)
    audit_record(db, user.id, "employee", emp.id, "update",
                 f"Thêm kiêm nhiệm: {_describe(row)}", doc_code=emp.code or "")
    return success({"item": serialize_one(db, row)}, "Đã thêm kiêm nhiệm", 201)


@router.patch("/{eid}/concurrents/{cid}")
def update_concurrent(eid: int, cid: int, data: ConcurrentPatch, db: Session = Depends(get_db),
                      user=Depends(require("employee", "write"))):
    """Sửa một dòng kiêm nhiệm tại chỗ (id dòng và tệp quyết định giữ nguyên).

    Cùng luật chặn với thêm mới; KHÔNG đổi `kind` (đổi loại = xóa + thêm). Loại 1 chỉ nhận `department_id`, loại 2
    chỉ nhận `company_id` (gửi ô của loại kia: 400). Đổi phòng / công ty thì dòng cũ lẫn dòng mới phải trong phạm vi
    ghi. `cid` không thuộc `eid` → 404. Chỉ `to_date` / `decision_date` được gửi null.
    """
    profile = get_perm_profile(db, user)
    emp = employee_in_scope(db, eid, user, profile, "write")
    row = concurrent_service.update_concurrent(db, emp, cid, data, user, profile)
    db.commit()
    db.refresh(row)
    clear_perm_cache_of(db, eid)
    audit_record(db, user.id, "employee", emp.id, "update",
                 f"Sửa kiêm nhiệm: {_describe(row)}", doc_code=emp.code or "")
    return success({"item": serialize_one(db, row)}, "Đã cập nhật kiêm nhiệm")


@router.delete("/{eid}/concurrents/{cid}")
def delete_concurrent(eid: int, cid: int, db: Session = Depends(get_db),
                      user=Depends(require("employee", "write"))):
    """Xóa một dòng kiêm nhiệm cùng tệp quyết định đính kèm.

    Cùng luật L1/L2 với sửa; dòng có tệp quyết định của người khác cần thêm `employee_sensitive.read`
    (xóa dòng kéo theo xóa tệp). `cid` không thuộc `eid` → 404.
    """
    profile = get_perm_profile(db, user)
    emp = employee_in_scope(db, eid, user, profile, "write")
    row = concurrent_service.get_row_in_employee(db, eid, cid)
    concurrent_access.block_delete_without_sensitive(db, user, row)
    removed = concurrent_service.delete_concurrent(db, emp, cid, user, profile)
    message = _describe(removed)
    db.commit()
    clear_perm_cache_of(db, eid)
    audit_record(db, user.id, "employee", emp.id, "update",
                 f"Xóa kiêm nhiệm: {message}", doc_code=emp.code or "")
    return success(None, "Đã xóa")
