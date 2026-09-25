"""Tra NGƯỜI cho phân hệ Dự án: tên · mã · ảnh đại diện — một query cho cả bó.

bao-CR-482: trước đây ba chỗ (thành viên nhóm, thành viên dự án, người phụ trách
việc) mỗi chỗ tự tra `Employee` lấy tên + mã, và không chỗ nào kèm ảnh — nên màn
Dự án chỉ vẽ được chữ tắt dù hồ sơ có ảnh. Gom về một hàm để ảnh đi theo người ở
mọi chỗ, và mai thêm gì (chức vụ, phòng) cũng chỉ sửa một nơi.

Ảnh lấy từ TÀI KHOẢN gắn với nhân sự (`tab_user.avatar_file_id`) — cùng chỗ với
ảnh người dùng tự đổi ở Trang cá nhân, xem `User.avatar`. Nhân sự chưa có tài
khoản thì ảnh rỗng, màn hình lùi về chữ tắt.
"""
from sqlalchemy.orm import Session, joinedload


def employee_info(db: Session, ids) -> dict[int, dict]:
    """`{employee_id: {name, code, avatar}}` — HAI query bất kể bao nhiêu người."""
    from app.modules.employee.model import Employee
    from app.modules.user.model import User

    ids = [int(i) for i in set(ids or []) if i]
    if not ids:
        return {}
    out = {e.id: {"name": e.full_name or "", "code": e.code or "", "avatar": ""}
           for e in db.query(Employee).filter(Employee.id.in_(ids)).all()}
    #  `joinedload` để `User.avatar` (đọc `avatar_file`) không thành N query.
    users = (db.query(User).options(joinedload(User.avatar_file))
             .filter(User.employee_id.in_(ids), User.avatar_file_id != 0).all())
    for u in users:
        if u.employee_id in out:
            out[u.employee_id]["avatar"] = u.avatar or ""
    return out
