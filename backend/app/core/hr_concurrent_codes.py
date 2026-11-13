"""Bộ mã TRẠNG THÁI KIÊM NHIỆM — dẫn xuất từ ngày, KHÔNG lưu cột (duoc-CR-755).

`tab_employee_concurrent` chỉ lưu `from_date` / `to_date`; trạng thái hiện trên giao diện
(Sắp tới / Đang hiệu lực / Đã hết) tính từ hai ngày đó và `vn_today()` mỗi lần đọc. Không có
tác vụ nền chuyển trạng thái nên không thể quên chạy và không lệch với phạm vi quyền (hồ sơ
quyền cũng lọc theo cùng điều kiện ngày — xem `employee/concurrent_service.effective_filter`).

R2/QĐ-11: API trả SỐ kèm nhãn; tiếng Việt chỉ ở tầng hiển thị. Thuần stdlib (không import
SQLAlchemy) để `scripts/gen_status_ts.py` nạp được ở máy không cài SQLAlchemy.

Luật bất biến: số đã cấp giữ nguyên mãi mãi, không tái dùng; loại mới cấp số tiếp theo.
"""
from datetime import date
from enum import IntEnum

from app.core.status_catalog import Code, CodeSet, register


class ConcurrentStatus(IntEnum):
    """3 trạng thái dẫn xuất. `0` KHÔNG hợp lệ."""

    UPCOMING = 1   # Sắp tới (từ ngày > hôm nay)
    ACTIVE = 2     # Đang hiệu lực
    ENDED = 3      # Đã hết (đến ngày < hôm nay)


CONCURRENT_STATUS_LABELS: dict[ConcurrentStatus, str] = {
    ConcurrentStatus.UPCOMING: "Sắp tới",
    ConcurrentStatus.ACTIVE: "Đang hiệu lực",
    ConcurrentStatus.ENDED: "Đã hết",
}


class ConcurrentKind(IntEnum):
    """Loại dòng kiêm nhiệm (duoc-CR-756) — LƯU cột `kind`, khác `ConcurrentStatus` (dẫn xuất). `0` KHÔNG hợp lệ.

    - DEPARTMENT: kiêm nhiệm một PHÒNG BAN của chính công ty chính (`company_id` = công ty chính lúc ghi).
    - COMPANY: kiêm nhiệm cả một CÔNG TY khác (`department_id = 0`, không phòng).
    """

    DEPARTMENT = 1   # Phòng ban
    COMPANY = 2      # Công ty


CONCURRENT_KIND_LABELS: dict[ConcurrentKind, str] = {
    ConcurrentKind.DEPARTMENT: "Phòng ban",
    ConcurrentKind.COMPANY: "Công ty",
}


def get_concurrent_status(from_date: date | None, to_date: date | None, today: date) -> ConcurrentStatus:
    """Trạng thái của một dòng tại ngày `today` (giờ VN — nơi gọi truyền `vn_today()`).

    `from_date` trống (chỉ có ở dòng chép từ dữ liệu cũ) = đã có hiệu lực từ trước; `to_date`
    trống = chưa kết thúc. Biên là BAO GỒM hai đầu: đúng ngày `to_date` vẫn còn hiệu lực.
    """
    if from_date is not None and from_date > today:
        return ConcurrentStatus.UPCOMING
    if to_date is not None and to_date < today:
        return ConcurrentStatus.ENDED
    return ConcurrentStatus.ACTIVE


#  `value` là số viết dạng chuỗi — khung `status_catalog` dùng mã chuỗi (cùng lối `hr_work_history_codes`).
CONCURRENT_STATUS_SET = register(CodeSet("concurrent_status", "Trạng thái kiêm nhiệm", [
    Code(str(int(key)), label, sort_order=int(key))
    for key, label in CONCURRENT_STATUS_LABELS.items()
]))

CONCURRENT_KIND_SET = register(CodeSet("concurrent_kind", "Loại kiêm nhiệm", [
    Code(str(int(key)), label, sort_order=int(key))
    for key, label in CONCURRENT_KIND_LABELS.items()
]))
