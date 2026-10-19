"""Tham số + hằng của API đọc hồ sơ cách làm việc (duoc-CR-641, phase 05)."""
from dataclasses import dataclass
from datetime import date

from fastapi import HTTPException

from app.core.usage_codes import UsageStyle

MAX_PAGE_SIZE = 100
MAX_Q_LEN = 100
MAX_WEEKS = 26
EXPORT_MAX_ROWS = 5000

#  Cột được sắp xếp (khóa → biểu thức trong list_service). `-` đứng trước = giảm dần.
SORT_KEYS = ("full_name", "emp_code", "active_ratio", "active_days", "workdays_net", "api_writes",
             "docs_created", "approvals", "exports", "http_422_per_100_writes", "last_active_day")


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
