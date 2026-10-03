"""Bộ mã LOẠI SỰ KIỆN quá trình công tác — `tab_employee_work_history.event_type`.

R2/QĐ-11: cột mới mang nghĩa phân loại phải là `SMALLINT` + `IntEnum`, tiếng Việt
chỉ ở tầng hiển thị. Thiết kế đầy đủ: phase-01 của plan
`frontend-v2/plans/261003-0837-qua-trinh-lam-viec-nhan-su/`.

Thuần stdlib (không import SQLAlchemy) — cùng lý do tách `forum_codes.py` khỏi
`forum/model.py`: `code_sets.py` phải nạp được ở máy không cài SQLAlchemy để
chạy `scripts/gen_status_ts.py`.

Luật bất biến — đọc trước khi sửa:
  - Số đã cấp cho một loại sự kiện GIỮ NGUYÊN mãi mãi, KHÔNG tái dùng (một dòng
    lịch sử cũ sẽ đổi nghĩa nếu số bị gán lại cho loại khác).
  - Loại bị bỏ thì để TRỐNG số đó, không dồn xuống — cùng luật `ReportKey`.
  - Loại mới → cấp số TIẾP THEO sau số lớn nhất đang có. Số 7 đã để dành cho
    "Đi làm lại" (V2-5), đừng cấp nó cho loại khác.
"""
from enum import IntEnum

from app.core.status_catalog import Code, CodeSet, register


class WorkEventType(IntEnum):
    """7 loại sự kiện quá trình công tác. `0` KHÔNG phải giá trị hợp lệ — chặn
    ở tầng schema (phase 02), SMALLINT dưới DB không tự biết enum."""

    HIRE = 1         # Tuyển dụng
    TRANSFER = 2     # Điều chuyển
    APPOINT = 3      # Bổ nhiệm
    CONCURRENT = 4   # Kiêm nhiệm
    DISMISS = 5      # Miễn nhiệm
    RESIGN = 6       # Thôi việc
    # 7 để dành "Đi làm lại" (V2-5) — ĐỪNG cấp cho loại khác.
    OTHER = 9        # Khác


WORK_EVENT_TYPE_LABELS: dict[WorkEventType, str] = {
    WorkEventType.HIRE: "Tuyển dụng",
    WorkEventType.TRANSFER: "Điều chuyển",
    WorkEventType.APPOINT: "Bổ nhiệm",
    WorkEventType.CONCURRENT: "Kiêm nhiệm",
    WorkEventType.DISMISS: "Miễn nhiệm",
    WorkEventType.RESIGN: "Thôi việc",
    WorkEventType.OTHER: "Khác",
}

#  Nhóm "chính" — đổi công ty/phòng/chức vụ CHÍNH của hồ sơ (so với CONCURRENT
#  là kiêm nhiệm THÊM, không đổi chức vụ chính). RESIGN cũng ở nhóm chính vì nó
#  KẾT THÚC chuỗi chính (chuyển tình trạng → nghỉ việc), xem Q2 của plan.
MAIN_TRACK: frozenset[WorkEventType] = frozenset({
    WorkEventType.HIRE,
    WorkEventType.TRANSFER,
    WorkEventType.APPOINT,
    WorkEventType.DISMISS,
    WorkEventType.RESIGN,
})

#  Loại sự kiện CÓ áp được vào hồ sơ (phase 02 dùng để tính cờ `can_apply`
#  trả về cùng danh sách — FE không tự chép luật này, xem A9 của plan).
#  OTHER không áp vào đâu cả: chỉ ghi chú, không có đích áp.
APPLICABLE: frozenset[WorkEventType] = frozenset(MAIN_TRACK | {WorkEventType.CONCURRENT})

#  Loại sự kiện đổi company_id/department_id/position_id CHÍNH của hồ sơ (áp
#  qua `update_employee`). RESIGN áp qua nhánh `has_left_company` của cùng hàm
#  đó nhưng KHÔNG đổi ba cột này, nên không nằm trong nhóm này. CONCURRENT áp
#  qua `set_extra_departments` (khác hàm), cũng không nằm trong nhóm này.
POSITION_TRACK: frozenset[WorkEventType] = frozenset({
    WorkEventType.HIRE,
    WorkEventType.TRANSFER,
    WorkEventType.APPOINT,
    WorkEventType.DISMISS,
})

#  `value` là SỐ VIẾT DƯỚI DẠNG CHUỖI — khung `status_catalog` dùng mã chuỗi,
#  cùng lối `report_keys.py`. `sort_order` = chính con số khóa.
WORK_EVENT_TYPE_SET = register(CodeSet("work_event_type", "Loại quá trình công tác", [
    Code(str(int(key)), label, sort_order=int(key))
    for key, label in WORK_EVENT_TYPE_LABELS.items()
]))
