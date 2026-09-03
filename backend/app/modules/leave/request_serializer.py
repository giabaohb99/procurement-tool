"""Dựng một dòng ĐƠN NGHỈ PHÉP để trả ra giao diện.

Tách khỏi `request_controller` vì từ CR-260 có HAI controller cùng trả đơn:
đường danh sách thường, và hộp việc duyệt (`inbox_controller`). Để hàm dump ở
một trong hai chỗ thì chỗ kia phải nhập chéo controller — vòng nhập và khó đọc.

Ba hàm ở đây đều nhận / trả **tra cứu theo lô**. Danh sách hai mươi dòng mà mỗi
dòng tự đi hỏi tên nhân sự và tên loại nghỉ là bốn mươi lượt vào cơ sở dữ liệu
cho một lần mở trang.
"""
from sqlalchemy.orm import Session

from app.modules.employee.model import Employee

from .catalog_model import LeaveType
from .request_model import LeaveRequest
from .schema import LeaveRequestResponse, request_labels


def names_of(db: Session, employee_ids: set[int]) -> dict[int, str]:
    """Tên nhân sự theo id — một lượt truy vấn cho cả trang, không N+1."""
    ids = {i for i in employee_ids if i}
    if not ids:
        return {}
    rows = db.query(Employee.id, Employee.full_name).filter(Employee.id.in_(ids)).all()
    return {r[0]: r[1] for r in rows}


def type_names(db: Session) -> dict[int, str]:
    return {r[0]: r[1] for r in db.query(LeaveType.id, LeaveType.name).all()}


def dump_request(obj: LeaveRequest, names: dict[int, str],
                 types: dict[int, str]) -> dict:
    data = LeaveRequestResponse.model_validate(obj).model_dump()
    data.update(request_labels(obj))
    data["employee_name"] = names.get(obj.employee_id, "")
    data["leave_type_name"] = types.get(obj.leave_type_id, "")
    return data


def dump_handovers(obj: LeaveRequest, names: dict[int, str]) -> list[dict]:
    """Danh sách người nhận bàn giao. `names` phải đã chứa sẵn tên của họ.

    Nhận `names` từ ngoài chứ không tự tra: chỗ gọi đang dựng cả một trang, và
    tra tên trong vòng lặp là đúng thứ N+1 mà cả tầng này sinh ra để tránh.
    """
    return [
        {"id": h.id, "employee_id": h.employee_id,
         "employee_name": names.get(h.employee_id, ""),
         "content": h.content, "sort_order": h.sort_order}
        for h in obj.handovers
    ]
