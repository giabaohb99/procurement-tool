"""NSPT (nhân sự phụ trách) của đơn mua hàng: MÃ kèm TÊN tra từ hồ sơ nhân sự (duoc-CR-775).

Cột `tab_purchase_order.nspt` là CHỮ chụp lúc lưu đơn. Giao diện từng gửi mã nhân sự vào ô đó (v2 lấy thẳng
`assignee` của YCMH, v1 tra tên không ra thì trả lại mã), nên màn Tiến độ có đơn hiện `NM_NV` thay cho tên, và
đổi tên nhân sự thì màn vẫn hiện tên cũ. Ở đây tra theo `nspt_id` — liên kết thật tới hồ sơ — để trả mã + tên
hiện hành; đơn chưa có liên kết (dữ liệu cũ kiểu "Mr Tiên") lùi về chữ đã lưu, không đoán.

Gom MỘT truy vấn cho cả trang / cả tệp xuất, không truy vấn theo từng dòng.
"""
from collections.abc import Iterable

from sqlalchemy.orm import Session

from app.modules.employee.model import Employee
from app.modules.purchase_order.model import PurchaseOrder

#  Ngăn mã và tên khi ghép một chuỗi (cột Excel, câu hiển thị gọn).
SEPARATOR = " · "


def load_nspt_people(db: Session, orders: Iterable[PurchaseOrder]) -> dict[int, tuple[str, str]]:
    """`nspt_id` -> (mã, họ tên) cho các đơn đưa vào. Đơn không có liên kết thì không có mặt trong kết quả."""
    ids = {int(po.nspt_id or 0) for po in orders} - {0}
    if not ids:
        return {}
    rows = db.query(Employee.id, Employee.code, Employee.full_name).filter(Employee.id.in_(ids)).all()
    return {int(eid): (code or "", name or "") for eid, code, name in rows}


def nspt_fields(po: PurchaseOrder, people: dict[int, tuple[str, str]]) -> dict:
    """Hai khóa cho API: `nspt_code` (rỗng khi đơn chưa liên kết hồ sơ) và `nspt_name` (tên hiện hành, lùi về chữ đã lưu)."""
    code, name = people.get(int(po.nspt_id or 0), ("", ""))
    return {"nspt_code": code, "nspt_name": name or (po.nspt or "")}


def nspt_label(po: PurchaseOrder, people: dict[int, tuple[str, str]]) -> str:
    """Một chuỗi cho tệp xuất: "NSU209 · Nguyễn Văn A" (mã trước, anh Được chốt 17/11/2026); chưa liên kết thì
    đúng chữ đã lưu. Cột NSPT xếp theo mã cho khớp — xem `sort_expressions.get_computed_sort_expression("nspt")`.
    """
    fields = nspt_fields(po, people)
    if fields["nspt_code"]:
        return f"{fields['nspt_code']}{SEPARATOR}{fields['nspt_name']}"
    return fields["nspt_name"]
