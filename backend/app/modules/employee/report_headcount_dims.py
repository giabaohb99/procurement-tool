"""Các chiều «cơ cấu» tính từ cột hồ sơ cho báo cáo Biến động nhân sự (duoc-CR-687, A2):
nhóm tuổi · trình độ · địa điểm làm việc · nhóm vị trí việc làm.

⚠️ `date_of_birth` là trường NHẠY CẢM (`sensitive.py`): hàm ở đây chỉ dùng nó để chọn NHÓM TUỔI
rồi bỏ — `HeadcountEvent` chỉ giữ khóa/nhãn nhóm, không giữ ngày sinh, nên không thể rò ra
ngoài qua danh sách «bấm số» hay xuất tệp.
"""
from __future__ import annotations

from datetime import date

from app.modules.employee.constants import JOB_CATEGORY_LABELS, job_category_of

#  (trần tuổi — nửa mở, khóa, nhãn). Khóa cuối `None` = «trở lên».
_AGE_BANDS = ((25, "lt25", "Dưới 25"), (35, "25-34", "25–34"), (45, "35-44", "35–44"),
              (55, "45-54", "45–54"), (None, "55+", "55 trở lên"))
NO_AGE = ("", "(Chưa gắn)")


def age_on(dob: date | None, on: date) -> int | None:
    """Tuổi tròn TẠI ngày `on`; None khi thiếu ngày sinh hoặc ngày sinh sau `on`."""
    if dob is None or dob > on:
        return None
    return on.year - dob.year - ((on.month, on.day) < (dob.month, dob.day))


def age_band(dob: date | None, on: date) -> tuple[str, str]:
    """(khóa, nhãn) nhóm tuổi tại `on`; thiếu ngày sinh → khóa rỗng («(Chưa gắn)»)."""
    age = age_on(dob, on)
    if age is None:
        return NO_AGE
    for cap, key, label in _AGE_BANDS:
        if cap is None or age < cap:
            return key, label
    return NO_AGE  # không tới đây — vòng trên luôn khớp nhóm cuối


def normalise_location(raw: str | None) -> tuple[str, str]:
    """(khóa gom, nhãn): khóa = bỏ khoảng trắng thừa + không phân biệt hoa/thường; nhãn = bản
    đã trim của giá trị gốc (nhóm lấy nhãn của hàng gặp ĐẦU TIÊN)."""
    label = " ".join((raw or "").split())
    return label.casefold(), label


def row_dims(row, on: date) -> dict:
    """Các trường chiều cơ cấu của một hàng `with_entities` (cần `date_of_birth`,
    `education_level`, `work_location`, `job_level`), tuổi tính tại `on`."""
    age_key, age_label = age_band(row.date_of_birth, on)
    loc_key, loc_label = normalise_location(row.work_location)
    cat = job_category_of(row.job_level, row.education_level)
    return dict(age_key=age_key, age_label=age_label, education_level=row.education_level or 0,
                location_key=loc_key, location_label=loc_label, job_category=cat,
                job_category_label=JOB_CATEGORY_LABELS.get(cat, ""))
