"""Chỉ người được chọn ở ô "Trưởng phòng phê duyệt" mới quyết phiếu — bao-CR-753 (chủ hệ thống chốt 12/11/2026).

Áp cho YCBG · YCMH · ĐMH. Cột `approver_employee_id` là ID NHÂN SỰ (bao-CR-499): trước khi duyệt là
người được chọn, bấm Duyệt xong `stamp_approver` ghi đè bằng người thực duyệt.

Luật:
  * Phiếu có `approver_employee_id` > 0 và đang ở bước chờ Trưởng phòng phê duyệt → CHỈ nhân sự đó
    được Duyệt / Trả về / Từ chối (ĐMH: thêm Hủy duyệt sau khi đã duyệt). Kể cả quản trị cũng không
    quyết thay; người được chọn vắng thì người lập đổi ô người duyệt rồi gửi lại.
  * Ô trống (phiếu cũ nạp Excel) → luật cũ: ai có quyền + phạm vi đều được.
  * Các bước KHÁC (điều phối, thu mua trả về sau duyệt, chuyển phòng…) không đi qua đây.

Người gọi tự quyết "đang ở bước nào" rồi mới gọi; hàm này chỉ so người.
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session


def designated_employee_id(doc) -> int:
    return int(getattr(doc, "approver_employee_id", 0) or 0)


def _employee_of(db: Session | None, user) -> int:
    """Nhân sự của tài khoản: đọc thuộc tính `employee_id`, thiếu thì tra bảng tài khoản."""
    emp = getattr(user, "employee_id", None)
    if emp is None and db is not None:
        from app.core.print_signers import employee_id_of_user
        emp = employee_id_of_user(db, int(getattr(user, "id", 0) or 0))
    return int(emp or 0)


def is_designated_approver(doc, user, db: Session | None = None) -> bool:
    """True khi phiếu không chỉ định ai (luật cũ) hoặc `user` chính là nhân sự được chọn."""
    chosen = designated_employee_id(doc)
    if not chosen:
        return True
    return _employee_of(db, user) == chosen


def ensure_designated_approver(db: Session, doc, user) -> None:
    """403 khi phiếu đã chọn người duyệt mà `user` không phải người đó."""
    if is_designated_approver(doc, user, db):
        return
    from app.core.print_signers import person_block
    name = person_block(db, designated_employee_id(doc))["name"] or "người được chọn"
    raise HTTPException(403, f"Chỉ {name} (người được chọn duyệt) mới duyệt được phiếu này")
