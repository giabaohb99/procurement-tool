"""Tên phòng ban HIỆN HÀNH cho báo cáo — gom theo ID, không theo bản chụp tên (duoc-CR-663 / N-008).

Chứng từ (ĐMH, YCMH, YCBG) lưu cả `department_id` lẫn cột chữ `department` là BẢN CHỤP tên phòng
lúc lập phiếu. Báo cáo từng gom theo cột chữ, nên đổi tên một phòng trong Danh mục là số liệu tách
làm hai dòng ("Phòng A" cũ, "Phòng B" mới) và phạm vi theo tên của người dùng lệch theo.

Quy tắc một chỗ: có `department_id` khớp một phòng thì nhãn = TÊN HIỆN HÀNH của phòng đó (mọi phiếu
cùng id dồn về một dòng); `department_id = 0` hoặc phòng không còn thì lùi về bản chụp tên cũ.
Khóa `key` của dòng báo cáo vẫn là chuỗi nhãn nên hình dạng JSON và bộ lọc phạm vi theo tên giữ nguyên.
"""
from sqlalchemy.orm import Session

from app.modules.department.model import Department


def load_department_names(db: Session) -> dict[int, str]:
    """`{department_id: tên hiện hành}` — một truy vấn, danh mục phòng ban nhỏ nên nạp hết."""
    return {int(i): (n or "").strip() for i, n in db.query(Department.id, Department.name).all()}


def department_label(names: dict[int, str], department_id, snapshot_name) -> str:
    """Nhãn phòng ban của một chứng từ: tên hiện hành theo id, lùi về bản chụp tên."""
    return names.get(int(department_id or 0)) or (snapshot_name or "")
