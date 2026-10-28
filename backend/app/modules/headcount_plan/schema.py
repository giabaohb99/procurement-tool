"""Schema kế hoạch nhân sự. `max_length` khớp `String(n)` ở `model.py`; số không âm, năm 2000–2100."""
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

#  `title` = nhãn trong câu lỗi tiếng Việt (`core/text_limits.describe_validation_errors`) — API lẫn nhập CSV.
Str500 = Annotated[str, StringConstraints(strip_whitespace=True, max_length=500), Field(title="Ghi chú")]
Year = Annotated[int, Field(ge=2000, le=2100, title="Năm")]
Headcount = Annotated[int, Field(ge=0, le=1_000_000, title="Định biên kế hoạch")]
#  Đồng NGUYÊN; trần 10^13 / tháng đủ cho quỹ lương cả tập đoàn và không tràn BigInteger khi cộng.
PAYROLL_TITLE = "Quỹ lương kế hoạch / tháng"
#  `Money | None` mất `title` của Annotated khi tra nhãn → khai lại `title` ngay trên trường.
Money = Annotated[int, Field(ge=0, le=10**13, title=PAYROLL_TITLE)]


class HeadcountPlanCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    year: Year
    company_id: Annotated[int, Field(ge=1)]
    department_id: Annotated[int, Field(ge=0)] = 0
    planned_headcount: Headcount = 0
    planned_payroll_monthly: Money | None = Field(None, title=PAYROLL_TITLE)   # None / vắng = chưa khai (lưu 0)
    note: Str500 = ""


class HeadcountPlanUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    year: Year | None = None
    company_id: Annotated[int, Field(ge=1)] | None = None
    department_id: Annotated[int, Field(ge=0)] | None = None
    planned_headcount: Headcount | None = None
    planned_payroll_monthly: Money | None = Field(None, title=PAYROLL_TITLE)
    note: Str500 | None = None
