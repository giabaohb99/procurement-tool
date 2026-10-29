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
from .constants import LEAVE_SESSION_LABELS, label
from .period_spans import PeriodView, header_period, periods_by_request
from .request_model import LeaveRequest, LeaveRequestLine
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


def lines_by_request(db: Session,
                     request_ids: set[int]) -> dict[int, list[LeaveRequestLine]]:
    """Dòng loại nghỉ của cả trang — MỘT lượt truy vấn, gom theo id đơn.

    Không dùng quan hệ `LeaveRequest.lines` ở tầng danh sách: quan hệ đó nạp lười
    nên hai mươi dòng thành hai mươi lượt vào cơ sở dữ liệu, đúng thứ N+1 mà cả
    tệp này sinh ra để tránh.
    """
    ids = {i for i in request_ids if i}
    if not ids:
        return {}
    rows = (db.query(LeaveRequestLine)
            .filter(LeaveRequestLine.request_id.in_(ids))
            .order_by(LeaveRequestLine.sort_order)
            .all())
    grouped: dict[int, list[LeaveRequestLine]] = {}
    for row in rows:
        grouped.setdefault(row.request_id, []).append(row)
    return grouped


def periods_for(db: Session, request_ids) -> dict[int, list[PeriodView]]:
    """Khoảng ngày của cả trang — MỘT lượt truy vấn (xem `period_spans.periods_by_request`)."""
    return periods_by_request(db, request_ids)


def dump_periods(obj: LeaveRequest, periods: list[PeriodView] | None) -> list[dict]:
    """Khoảng ngày để trả ra, luôn ≥1 phần tử. Thiếu bản gom thì dựng từ đầu đơn
    (không tự tra — cùng lý lẽ với `lines`)."""
    return [
        {"id": p.id, "from_date": p.from_date, "from_session": p.from_session,
         "from_session_label": label(LEAVE_SESSION_LABELS, p.from_session),
         "to_date": p.to_date, "to_session": p.to_session,
         "to_session_label": label(LEAVE_SESSION_LABELS, p.to_session),
         "days": p.days, "sort_order": p.sort_order}
        for p in (periods or [header_period(obj)])
    ]


def dump_request(obj: LeaveRequest, names: dict[int, str], types: dict[int, str],
                 lines: dict[int, list[LeaveRequestLine]] | None = None,
                 periods: dict[int, list[PeriodView]] | None = None) -> dict:
    """Một dòng đơn để trả ra giao diện.

    `lines` là bản gom sẵn của `lines_by_request`. Không truyền thì khóa `lines`
    trả về **rỗng** chứ không tự đi tra — nơi gọi nào cần bản kê loại nghỉ thì
    phải chủ động gom, để không có đường nào lỡ tay đẻ ra N+1.
    """
    data = LeaveRequestResponse.model_validate(obj).model_dump()
    data.update(request_labels(obj))
    data["employee_name"] = names.get(obj.employee_id, "")
    data["leave_type_name"] = types.get(obj.leave_type_id, "")
    data["lines"] = [
        {"id": line.id, "leave_type_id": line.leave_type_id,
         "leave_type_name": types.get(line.leave_type_id, ""),
         "days": line.days, "sort_order": line.sort_order}
        for line in (lines or {}).get(obj.id, [])
    ]
    data["periods"] = dump_periods(obj, (periods or {}).get(obj.id))
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
