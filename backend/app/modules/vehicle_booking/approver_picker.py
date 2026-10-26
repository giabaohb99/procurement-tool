"""Phiếu đặt xe tự CHỌN Công ty và Người duyệt (duoc-CR-681).

Hai ô ĐỘC LẬP (anh Được chốt 23/10/2026): chọn công ty không lọc danh sách người duyệt và ngược lại.

**Danh sách người duyệt** = MỌI người có ô Duyệt phiếu đặt xe ở màn Phân quyền — mọi phạm vi, kể cả
Quản trị (anh Được 24/10/2026: bản đầu lọc như lúc bộ máy tự giao nên ô chọn trống trên hệ chỉ có «Quản lý
thu mua · Của mình» + Quản trị). Tài khoản mở + hồ sơ còn làm. Phạm vi không quan trọng vì người được chọn
được mở quyền xem + duyệt riêng phiếu đó (`approval_bridge.is_picked_legacy_approver`, cách 9 bỏ soi phạm vi). `first_approver_id` lưu id TÀI KHOẢN (cột có từ bản cũ).

Người được chọn đi đâu: bộ máy duyệt TẮT → thư «Gửi duyệt» chỉ tới người đó (`notify._approvers`);
bộ máy BẬT → bước cách 9 chỉ giao cho người đó (`permission_approvers.resolve` đọc
`picked_approver_employee_id` của bối cảnh), rồi `_after_submit` gửi thư cho người nhận việc.
"""
from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.approval import permission_approvers

ENTITY = "vehicle_booking"


def approver_options(db: Session) -> list[dict]:
    """Người chọn được làm người duyệt — kèm `user_id` (giá trị lưu vào `first_approver_id`)."""
    users = _pickable_users(db)   # holder_profiles gọi lại lần nữa — số truy vấn vẫn cố định
    user_of: dict[int, object] = {}
    for user in users:   # một hồ sơ nhiều tài khoản → lấy tài khoản mở có id nhỏ nhất (đã sắp)
        user_of.setdefault(user.employee_id, user)
    #  Ảnh đại diện (bản thu nhỏ) cho ô chọn có avatar — nạp sẵn một truy vấn, không N+1.
    return [{**row, "user_id": user_of[row["employee_id"]].id, "avatar": user_of[row["employee_id"]].avatar}
            for row in permission_approvers.holder_profiles(db, ENTITY, pickable=True)
            if row["employee_id"] in user_of]


def _pickable_users(db: Session) -> list:
    """Ai chọn được: MỌI người có ô Duyệt đặt xe (mọi phạm vi, kể cả Quản trị) — anh Được 24/10/2026."""
    return permission_approvers.holders(db, ENTITY, permission_approvers.pickable_role_ids(db, ENTITY))


def company_options(db: Session) -> list[dict]:
    """Công ty chọn được trên phiếu — mọi pháp nhân đang dùng (hai ô độc lập, không lọc theo người).

    Trả ngay ở đường API của đặt xe chứ không bắt giao diện gọi `/api/companies`: nhân viên đặt xe
    thường không có quyền `company.read`, ô chọn sẽ rỗng.
    """
    from app.modules.company.model import Company

    from app.modules.company.service import get_company_logo_map

    rows = (db.query(Company.id, Company.name, Company.short_name, Company.tax_code)
            .filter(Company.is_active.is_(True)).order_by(Company.name.asc()).all())
    logos = get_company_logo_map(db, [r.id for r in rows])
    return [{"id": r.id, "name": r.name, "short_name": r.short_name or "", "tax_code": r.tax_code or "",
             "logo": logos.get(r.id, "")} for r in rows]


def pick_options(db: Session, default_company_id: int) -> dict:
    """Dữ liệu cho hai ô «Công ty» + «Người duyệt» của form đặt xe — một lượt gọi."""
    return {"companies": company_options(db), "approvers": approver_options(db),
            "default_company_id": int(default_company_id or 0)}


def _allowed_user_ids(db: Session) -> set[int]:
    return {user.id for user in _pickable_users(db)}


def check_company(db: Session, company_id: int | None) -> None:
    """Công ty chọn trên phiếu phải tồn tại — nó quyết định luồng duyệt và ai thấy phiếu."""
    from app.modules.company.model import Company

    if not company_id:
        return
    company = db.get(Company, int(company_id))
    if company is None or not company.is_active:
        raise HTTPException(422, "Công ty đã chọn không tồn tại hoặc đã ngừng dùng")


def check_approver(db: Session, approver_user_id: int | None, *self_user_ids: int) -> None:
    """Người duyệt chọn trên phiếu phải còn quyền Duyệt đặt xe, và không phải người tạo / người bấm gửi.

    So theo HỒ SƠ NHÂN SỰ chứ không theo tài khoản (review M2): một người hai tài khoản, hoặc người sửa
    phiếu hộ tự chọn mình rồi bấm gửi, thì bộ máy loại người nộp → bước rỗng, phiếu kẹt.
    """
    if not approver_user_id:
        return
    picked_employee = picked_employee_id(db, approver_user_id)
    for self_id in self_user_ids:
        if not self_id:
            continue
        if int(approver_user_id) == int(self_id) or (
                picked_employee and picked_employee == picked_employee_id(db, self_id)):
            raise HTTPException(422, "Không tự chọn mình làm người duyệt phiếu của mình")
    if int(approver_user_id) not in _allowed_user_ids(db):
        raise HTTPException(422, "Người duyệt đã chọn không có quyền duyệt phiếu đặt xe — chọn lại")


def picked_employee_id(db: Session, approver_user_id: int | None) -> int:
    """Hồ sơ nhân sự của người duyệt đã chọn (0 nếu chưa chọn / tài khoản không gắn hồ sơ)."""
    from app.modules.user.model import User

    if not approver_user_id:
        return 0
    user = db.get(User, int(approver_user_id))
    return int(user.employee_id or 0) if user else 0
