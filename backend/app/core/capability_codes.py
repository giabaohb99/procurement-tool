"""Bộ mã NĂNG LỰC THEO LOẠI VIỆC (duoc-CR-656) — task Dự án có kết quả; vòng đời phiếu đã tính sẵn.

R2/QĐ-11: cột phân loại là `SMALLINT` + `IntEnum`, tiếng Việt chỉ ở tầng hiển thị.
Dùng ở: `tab_work_task.outcome` (`WorkTaskOutcome`) và `tab_work_cycle.kind/role/outcome`.

Thuần stdlib (cùng lý do `work_schedule_codes.py`): `code_sets.py` phải nạp được ở máy
không cài SQLAlchemy để chạy `scripts/gen_status_ts.py`.

Luật bất biến: số đã cấp GIỮ NGUYÊN mãi mãi, không tái dùng; `0` không hợp lệ ở bộ nào
(riêng `outcome` của task: `0` = «chưa đánh giá», KHÔNG nằm trong bộ mã); loại mới cấp số TIẾP THEO.
"""
from enum import IntEnum

from app.core.status_catalog import Code, CodeSet, register


class WorkTaskOutcome(IntEnum):
    """Đánh giá của NGƯỜI GIAO sau khi task xong. Cột `outcome = 0` là chưa đánh giá."""

    PASSED = 1    # Đạt
    REWORK = 2    # Phải làm lại (tự mở lại task)


class CycleKind(IntEnum):
    """Loại phiếu có vòng đời được tính vào `tab_work_cycle`.

    Nhận hàng KHÔNG có ở đây: nó là một bước của ĐMH, không có vòng đời riêng (Q4).
    """

    PURCHASE_REQUEST = 1   # Yêu cầu mua hàng
    SURVEY_REQUEST = 2     # Yêu cầu báo giá
    PURCHASE_ORDER = 3     # Đơn mua hàng
    PAYMENT_REQUEST = 4    # Yêu cầu thanh toán
    DOCUMENT = 5           # Văn bản
    VEHICLE_BOOKING = 6    # Đặt xe
    SEAL_REQUEST = 7       # Duyệt dấu
    ROOM_BOOKING = 8       # Phòng họp
    LEAVE_REQUEST = 9      # Nghỉ phép
    WORK_TASK = 10         # Task Dự án


class CycleRole(IntEnum):
    CREATOR = 1    # Người lập / đề nghị
    HANDLER = 2    # Người xử lý


class CycleOutcome(IntEnum):
    OPEN = 1        # Còn đang chạy
    DONE = 2        # Xong
    CANCELLED = 3   # Hủy
    REJECTED = 4    # Bị từ chối (khóa)


WORK_TASK_OUTCOME_LABELS: dict[WorkTaskOutcome, str] = {
    WorkTaskOutcome.PASSED: "Đạt",
    WorkTaskOutcome.REWORK: "Phải làm lại",
}

CYCLE_KIND_LABELS: dict[CycleKind, str] = {
    CycleKind.PURCHASE_REQUEST: "Yêu cầu mua hàng",
    CycleKind.SURVEY_REQUEST: "Yêu cầu báo giá",
    CycleKind.PURCHASE_ORDER: "Đơn mua hàng",
    CycleKind.PAYMENT_REQUEST: "Yêu cầu thanh toán",
    CycleKind.DOCUMENT: "Văn bản",
    CycleKind.VEHICLE_BOOKING: "Đặt xe",
    CycleKind.SEAL_REQUEST: "Duyệt dấu",
    CycleKind.ROOM_BOOKING: "Đặt phòng họp",
    CycleKind.LEAVE_REQUEST: "Nghỉ phép",
    CycleKind.WORK_TASK: "Công việc dự án",
}

CYCLE_ROLE_LABELS: dict[CycleRole, str] = {
    CycleRole.CREATOR: "Người lập/đề nghị",
    CycleRole.HANDLER: "Người xử lý",
}

CYCLE_OUTCOME_LABELS: dict[CycleOutcome, str] = {
    CycleOutcome.OPEN: "Đang chạy",
    CycleOutcome.DONE: "Đã xong",
    CycleOutcome.CANCELLED: "Đã hủy",
    CycleOutcome.REJECTED: "Bị từ chối",
}


def _codes(labels: dict) -> list[Code]:
    #  `value` là SỐ VIẾT DƯỚI DẠNG CHUỖI — khung `status_catalog` dùng mã chuỗi.
    return [Code(str(int(k)), label, sort_order=int(k)) for k, label in labels.items()]


WORK_TASK_OUTCOME_SET = register(CodeSet("work_task_outcome", "Kết quả công việc", _codes(WORK_TASK_OUTCOME_LABELS)))
CYCLE_KIND_SET = register(CodeSet("cycle_kind", "Loại phiếu có vòng đời", _codes(CYCLE_KIND_LABELS)))
CYCLE_ROLE_SET = register(CodeSet("cycle_role", "Vai trong vòng đời phiếu", _codes(CYCLE_ROLE_LABELS)))
CYCLE_OUTCOME_SET = register(CodeSet("cycle_outcome", "Kết cục vòng đời phiếu", _codes(CYCLE_OUTCOME_LABELS)))
