"""Bộ mã TRẠNG THÁI yêu cầu sửa hồ sơ — `tab_employee_change_request.status` (duoc-CR-676).

R2/QĐ-11: cột trạng thái mới là `SMALLINT` + `IntEnum`, tiếng Việt chỉ ở tầng hiển thị.
Thuần stdlib — cùng lý do với `hr_work_history_codes.py`.

Luật bất biến: số đã cấp giữ nguyên mãi mãi, không tái dùng.
"""
from enum import IntEnum

from app.core.status_catalog import Code, CodeSet, register


class EmployeeChangeRequestStatus(IntEnum):
    PENDING = 1     # Chờ duyệt
    APPROVED = 2    # Đã duyệt (đã áp vào hồ sơ)
    REJECTED = 3    # Từ chối
    WITHDRAWN = 4   # Đã rút lại


EMPLOYEE_CHANGE_REQUEST_STATUS_LABELS: dict[EmployeeChangeRequestStatus, str] = {
    EmployeeChangeRequestStatus.PENDING: "Chờ duyệt",
    EmployeeChangeRequestStatus.APPROVED: "Đã duyệt",
    EmployeeChangeRequestStatus.REJECTED: "Từ chối",
    EmployeeChangeRequestStatus.WITHDRAWN: "Đã rút lại",
}

#  `value` là số viết dưới dạng chuỗi — khung `status_catalog` dùng mã chuỗi (cùng lối `report_keys.py`).
EMPLOYEE_CHANGE_REQUEST_STATUS_SET = register(CodeSet(
    "employee_change_request_status", "Trạng thái yêu cầu sửa hồ sơ", [
        Code(str(int(key)), label, sort_order=int(key),
             is_terminal=key != EmployeeChangeRequestStatus.PENDING)
        for key, label in EMPLOYEE_CHANGE_REQUEST_STATUS_LABELS.items()
    ]))
