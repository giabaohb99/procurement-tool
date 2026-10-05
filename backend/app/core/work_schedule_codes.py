"""Bộ mã LỊCH LÀM VIỆC — `tab_work_schedule_day.day_kind` và
`tab_work_schedule_assignment.target_level`.

R2/QĐ-11: cột phân loại là `SMALLINT` + `IntEnum`, tiếng Việt chỉ ở tầng hiển thị.
Thiết kế: `frontend-v2/plans/261005-0925-hr-lich-lam-viec/`.

Thuần stdlib (cùng lý do `hr_work_history_codes.py`): `code_sets.py` phải nạp được
ở máy không cài SQLAlchemy để chạy `scripts/gen_status_ts.py`.

Luật bất biến: số đã cấp GIỮ NGUYÊN mãi mãi, không tái dùng; `0` không hợp lệ
(quy ước «0 = chưa khai»); loại mới cấp số TIẾP THEO.
"""
from enum import IntEnum

from app.core.status_catalog import Code, CodeSet, register


class WorkDayKind(IntEnum):
    """Loại của MỘT ngày trong tuần ở mẫu lịch. Nửa ngày là LOẠI NGÀY, không suy từ giờ."""

    OFF = 1        # Nghỉ
    FULL = 2       # Cả ngày
    MORNING = 3    # Chỉ buổi sáng (vd T7 08:00–12:00 → 0.5 công)
    AFTERNOON = 4  # Chỉ buổi chiều


class WorkScheduleLevel(IntEnum):
    """Cấp đối tượng của một dòng gán lịch."""

    SYSTEM = 1      # Toàn hệ thống (target_id = 0)
    COMPANY = 2     # Pháp nhân
    DEPARTMENT = 3  # Phòng ban
    EMPLOYEE = 4    # Nhân sự


#  Hẹp thắng rộng — KHÔNG suy từ độ lớn của số khóa.
LEVEL_PRECEDENCE: tuple[WorkScheduleLevel, ...] = (
    WorkScheduleLevel.EMPLOYEE,
    WorkScheduleLevel.DEPARTMENT,
    WorkScheduleLevel.COMPANY,
    WorkScheduleLevel.SYSTEM,
)

WORK_DAY_KIND_LABELS: dict[WorkDayKind, str] = {
    WorkDayKind.OFF: "Nghỉ",
    WorkDayKind.FULL: "Cả ngày",
    WorkDayKind.MORNING: "Buổi sáng",
    WorkDayKind.AFTERNOON: "Buổi chiều",
}

WORK_SCHEDULE_LEVEL_LABELS: dict[WorkScheduleLevel, str] = {
    WorkScheduleLevel.SYSTEM: "Toàn hệ thống",
    WorkScheduleLevel.COMPANY: "Pháp nhân",
    WorkScheduleLevel.DEPARTMENT: "Phòng ban",
    WorkScheduleLevel.EMPLOYEE: "Nhân sự",
}

#  `value` là SỐ VIẾT DƯỚI DẠNG CHUỖI — khung `status_catalog` dùng mã chuỗi.
WORK_DAY_KIND_SET = register(CodeSet("work_day_kind", "Loại ngày làm việc", [
    Code(str(int(k)), label, sort_order=int(k)) for k, label in WORK_DAY_KIND_LABELS.items()
]))
WORK_SCHEDULE_LEVEL_SET = register(CodeSet("work_schedule_level", "Cấp gán lịch làm việc", [
    Code(str(int(k)), label, sort_order=int(k)) for k, label in WORK_SCHEDULE_LEVEL_LABELS.items()
]))
