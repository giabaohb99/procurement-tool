"""TỰ SỬA LIÊN HỆ ở Trang cá nhân (bao-CR-508, khách chốt 28/09/2026).

Người đã gắn hồ sơ nhân sự tự sửa được nhóm LIÊN HỆ của chính mình — số điện
thoại, địa chỉ thường trú, địa chỉ hiện nay, người báo tin — mà không cần khóa
`employee.write`. Lưu là áp ngay, không báo phòng Nhân sự, nhưng vẫn để lại dấu
trong nhật ký như mọi lần sửa hồ sơ khác (`core/audit.record` ở controller +
lớp ORM `core/change_tracker` tự ghi giá trị trước/sau).

⚠️ **Hồ sơ lấy từ PHIÊN ĐĂNG NHẬP, không bao giờ từ tham số.** Không có id nào
trong URL hay thân yêu cầu để người dùng đổi thành id người khác — đó là lý do
cửa này được phép bỏ qua `require(...)` và `get_scoped(...)`, y như `GET /me`.

⚠️ Hàm ở đây KHÔNG commit hộ bảng người báo tin — cái đó đi thẳng
`contact_service.set_contacts` để trần dòng / luật bỏ dòng rỗng họ tên chỉ có
MỘT bản.
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from .model import Employee
from .schema import SelfContactUpdate

#  Ô được tự sửa → nhãn dùng trong câu nhật ký. Thêm một ô vào đây mà không
#  thêm vào `SelfContactUpdate` thì không có tác dụng gì, và ngược lại — hai chỗ
#  cùng khai là cố ý: schema là cửa, danh sách này là chốt thứ hai.
SELF_CONTACT_FIELDS: dict[str, str] = {
    "phone": "số điện thoại",
    "permanent_address": "địa chỉ thường trú",
    "current_address": "địa chỉ hiện nay (tạm trú)",
}


def get_own_employee(db: Session, user) -> Employee:
    """Hồ sơ nhân sự gắn với tài khoản đang đăng nhập, không có thì báo rõ.

    Khác `GET /me` (trả `None` vì chỉ ĐỌC): ở đây là cửa GHI, không có hồ sơ thì
    không có gì để ghi — phải nói thành lời chứ đừng trả thành công rỗng.
    """
    employee_id = int(getattr(user, "employee_id", 0) or 0)
    if not employee_id:
        raise HTTPException(
            400, "Tài khoản này chưa gắn hồ sơ nhân sự nên chưa có thông tin liên hệ để sửa. "
                 "Hãy liên hệ bộ phận Nhân sự.")
    obj = db.get(Employee, employee_id)
    if not obj:
        raise HTTPException(404, "Không tìm thấy hồ sơ nhân sự gắn với tài khoản này")
    return obj


def update_own_contact(db: Session, emp: Employee, data: SelfContactUpdate,
                       user_id: int) -> list[str]:
    """Ghi các ô liên hệ ĐÃ GỬI và ĐỔI THẬT, trả nhãn của những ô đã đổi.

    Cắt khoảng trắng hai đầu: dán số điện thoại từ Zalo hay kèm dấu cách, lưu
    nguyên thì lần sau so khớp số trùng trượt mà không ai hiểu vì sao. `null`
    tường minh đọc thành chuỗi rỗng (xóa ô) — cột là `String NOT NULL` về nghĩa.
    """
    changed: list[str] = []
    for key, value in data.model_dump(exclude_unset=True).items():
        if key not in SELF_CONTACT_FIELDS:
            continue
        new_value = (value or "").strip()
        if new_value != (getattr(emp, key) or ""):
            setattr(emp, key, new_value)
            changed.append(SELF_CONTACT_FIELDS[key])
    if changed:
        emp.updated_by = user_id
        db.commit()
        db.refresh(emp)
    return changed
