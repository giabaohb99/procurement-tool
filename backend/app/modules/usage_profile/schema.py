"""Tham số + hằng của API đọc hồ sơ cách làm việc (duoc-CR-641, phase 05)."""
from dataclasses import dataclass
from datetime import date

from fastapi import HTTPException

from app.core.usage_codes import UsageStyle

from .metric_catalog import METRIC_CATALOG

MAX_PAGE_SIZE = 100
MAX_Q_LEN = 100
MAX_WEEKS = 26
EXPORT_MAX_ROWS = 5000

#  Cột được sắp xếp (khóa → biểu thức trong list_service). `-` đứng trước = giảm dần.
SORT_KEYS = ("full_name", "emp_code", "active_ratio", "active_days", "workdays_net", "api_writes",
             "docs_created", "approvals", "exports", "http_422_per_100_writes", "last_active_day",
             "metric")   # `metric` (duoc-CR-650): giá trị chỉ số chọn ở tham số `metric`, đọc từ snapshot tuần nhãn


@dataclass(frozen=True)
class ListFilters:
    date_from: date
    date_to: date
    company_id: int | None = None
    department_id: int | None = None
    role_id: int | None = None
    labels: tuple[int, ...] | None = None   # nhiều kiểu = OR (người có BẤT KỲ nhãn nào trong danh sách)
    q: str = ""
    sort: str = "full_name"
    metric: str | None = None   # duoc-CR-650: khóa trong METRIC_CATALOG; có thì dòng trả thêm `metric_value`


MAX_METRIC_LEN = 60
MAX_LABELS = len(UsageStyle)


def validate_labels(labels: list[int] | None) -> tuple[int, ...] | None:
    """Danh sách nhãn lọc: rỗng → không lọc; có giá trị lạ → 422; bỏ trùng, giữ thứ tự."""
    if not labels:
        return None
    known = {int(s) for s in UsageStyle}
    if any(v not in known for v in labels):
        raise HTTPException(422, "Kiểu làm việc không hợp lệ")
    return tuple(dict.fromkeys(labels))


def parse_sort(raw: str | None) -> tuple[str, bool]:
    """`-api_writes` → ("api_writes", True). Khóa lạ → 422 (không cho sắp theo cột tùy ý)."""
    raw = (raw or "full_name").strip()
    desc = raw.startswith("-")
    key = raw.lstrip("-")
    if key not in SORT_KEYS:
        raise HTTPException(422, f"Cột sắp xếp không hợp lệ: {key}")
    return key, desc


def validate_metric(metric: str | None, sort: str | None) -> str | None:
    """duoc-CR-650: khóa chỉ số phải nằm trong danh mục (lạ → 422); `sort=metric` mà thiếu `metric` → 422."""
    metric = (metric or "").strip() or None
    if metric is not None and metric not in METRIC_CATALOG:
        raise HTTPException(422, f"Chỉ số không hợp lệ: {metric}")
    if metric is None and (sort or "").lstrip("-") == "metric":
        raise HTTPException(422, "Sắp theo chỉ số cần kèm tham số metric")
    return metric
