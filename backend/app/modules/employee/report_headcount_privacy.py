"""Che số nhóm tuổi nhỏ + chặn danh sách theo nhóm tuổi (duoc-CR-687, A2).

Nhóm tuổi chỉ ~5 nhóm; nhóm dưới `MIN_GROUP` người cho phép đoán tuổi từng người (nhất là khi
lọc thêm theo phòng ban). Người có `employee_sensitive.read` (được xem ngày sinh thật) không bị che.
"""
from __future__ import annotations

from fastapi import HTTPException

from app.core.report_small_group import drop_unsafe_breakdown, suppress_small_groups
from app.modules.employee.sensitive import can_read_sensitive

AGE_NOTE = "Nhóm tuổi dưới 3 người được che số để không đoán ra tuổi từng người"
EXTRA_NOTE = ("Để số bị che không suy ngược được từ Tổng, báo cáo che thêm nhóm tuổi nhỏ kế tiếp; "
              "dòng Tổng vẫn đủ số")
#  Bốn số ĐẾM của một nhóm — chỉ cần MỘT số ở mức 1–2 (kỳ này hoặc kỳ so sánh) là đủ chỉ ra từng người.
_COUNT_KEYS = ("headcount_start", "headcount_end", "new_hires", "departures")


def _counts(values: dict) -> list[int]:
    return [values.get(k) or 0 for k in _COUNT_KEYS]


def suppress_small_age_groups(data: dict, prof: dict) -> None:
    """Che nhóm tuổi nhỏ cho người KHÔNG có `employee_sensitive.read` (`employee_id=0` ở `can_read_sensitive`
    = chỉ xét KHÓA quyền, không xét ngoại lệ «chính mình»). Luật sơ cấp/thứ cấp (xét riêng kỳ này và kỳ so
    sánh) ở `core/report_small_group.py`; quy mô nhóm = định biên cuối kỳ. Không cứu được thì bỏ bảng nhóm tuổi."""
    if can_read_sensitive(prof):
        return
    res = suppress_small_groups(data, _counts, lambda v: v.get("headcount_end") or 0, AGE_NOTE, EXTRA_NOTE)
    if res.unsafe_sides:     # còn một nhóm / hai nhóm 1 người: che xong Tổng vẫn lộ -> bỏ cả bảng nhóm tuổi
        drop_unsafe_breakdown(data, "age_band", "nhóm tuổi")


def require_age_rows_allowed(prof: dict, group_by: str | None, group_key: str | None) -> None:
    """Danh sách người của MỘT nhóm tuổi tiết lộ tuổi từng người → cần `employee_sensitive.read`."""
    if group_by == "age_band" and group_key is not None and not can_read_sensitive(prof):
        raise HTTPException(403, "Danh sách theo nhóm tuổi cần quyền xem thông tin nhạy cảm của nhân sự")
