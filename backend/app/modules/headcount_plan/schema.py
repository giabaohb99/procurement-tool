"""Schema kế hoạch nhân sự theo kỳ. `max_length` khớp `String(n)` ở `model.py` / `cost_model.py`; số không âm;
mọi danh sách có TRẦN số phần tử (cột JSON không được phình vô hạn) — `.claude/rules/backend-input-limits.md`."""
from datetime import date
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

from .constants import (MAX_COST_ITEMS, MAX_DOCUMENTS, MAX_HEADCOUNT, MAX_LINES, MAX_MONEY, CostAppliesTo,
                        CostCalcMethod, ActualSource, PlanPeriodType)

#  `title` = nhãn trong câu lỗi tiếng Việt (`core/text_limits.describe_validation_errors`).
Str500 = Annotated[str, StringConstraints(strip_whitespace=True, max_length=500), Field(title="Ghi chú")]
Str100 = Annotated[str, StringConstraints(strip_whitespace=True, max_length=100)]
Money = Annotated[int, Field(ge=0, le=MAX_MONEY)]
Id = Annotated[int, Field(ge=0)]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CostGroupIn(_Strict):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100),
                    Field(title="Tên nhóm chi phí")]
    sort_order: Annotated[int, Field(ge=0, le=100000)] = 0
    is_active: bool = True


class CostGroupPatch(_Strict):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100),
                    Field(title="Tên nhóm chi phí")] | None = None
    sort_order: Annotated[int, Field(ge=0, le=100000)] | None = None
    is_active: bool | None = None


class CostItemIn(_Strict):
    """Một khoản chi phí (của mẫu hoặc của kế hoạch). Tiền `None` = người xem không thấy tiền, gửi lại để GIỮ NGUYÊN."""

    code: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=30,
                                           pattern=r"^[A-Za-z0-9_]+$"), Field(title="Mã khoản")]
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=150),
                    Field(title="Tên khoản")]
    group_id: Id = 0
    calc_method: Annotated[int, Field(ge=1, le=5)]
    rate: Annotated[float, Field(ge=0, le=999.9999)] = 0
    factor: Annotated[float, Field(ge=0, le=9999.99)] = 0
    cap_amount: Money | None = 0
    amount: Money | None = 0
    base_codes: Annotated[list[Annotated[str, Field(max_length=30)]], Field(max_length=MAX_COST_ITEMS)] = []
    applies_to: Annotated[int, Field(ge=1, le=3)] = int(CostAppliesTo.ALL_POSITIONS)
    position_ids: Annotated[list[Annotated[int, Field(ge=1)]], Field(max_length=MAX_LINES)] = []
    months: Annotated[list[Annotated[int, Field(ge=1, le=12)]], Field(max_length=12)] = []
    actual_source: Annotated[int, Field(ge=0, le=3)] = int(ActualSource.NONE)
    sort_order: Annotated[int, Field(ge=0, le=100000)] = 0

    @field_validator("calc_method")
    @classmethod
    def _known_method(cls, v: int) -> int:
        CostCalcMethod(v)
        return v


class CostTemplateIn(_Strict):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=150),
                    Field(title="Tên mẫu")]
    note: Str500 = ""
    is_active: bool = True
    items: Annotated[list[CostItemIn], Field(max_length=MAX_COST_ITEMS)] = []


class CostTemplatePatch(_Strict):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=150),
                    Field(title="Tên mẫu")] | None = None
    note: Str500 | None = None
    is_active: bool | None = None
    items: Annotated[list[CostItemIn], Field(max_length=MAX_COST_ITEMS)] | None = None   # có → thay NGUYÊN danh sách


class PlanLineIn(_Strict):
    position_id: Id = 0
    headcounts: Annotated[list[Annotated[int, Field(ge=0, le=MAX_HEADCOUNT)]],
                          Field(min_length=1, max_length=4, title="Số người kế hoạch")]
    #  None = người xem không thấy tiền (giữ nguyên số đang lưu).
    amounts: Annotated[dict[Annotated[str, Field(max_length=30)], Money], Field(max_length=MAX_COST_ITEMS)] | None = None
    note: Str500 = ""


class PlanHeader(_Strict):
    year: Annotated[int, Field(ge=2000, le=2100, title="Năm")]
    period_type: Annotated[int, Field(ge=1, le=4, title="Loại kỳ")]
    period_no: Annotated[int, Field(ge=1, le=12, title="Kỳ")] = 1
    company_id: Annotated[int, Field(ge=1)]
    department_id: Id = 0
    basis_no: Str100 = ""
    basis_date: date | None = None
    approver_employee_id: Id = 0
    note: Str500 = ""

    @field_validator("period_type")
    @classmethod
    def _known_period_type(cls, v: int) -> int:
        PlanPeriodType(v)
        return v

    @field_validator("basis_date")
    @classmethod
    def _sane_basis_date(cls, v: date | None) -> date | None:
        if v is not None and not 2000 <= v.year <= 2100:
            raise ValueError("Ngày căn cứ phải trong khoảng năm 2000–2100")
        return v


DocumentIds = Annotated[list[Annotated[int, Field(ge=1)]], Field(max_length=MAX_DOCUMENTS)]


class PlanDraft(PlanHeader):
    """Nội dung một kế hoạch (dùng cho `PUT` và xem trước `POST /compute`)."""

    cost_items: Annotated[list[CostItemIn], Field(max_length=MAX_COST_ITEMS)] = []
    lines: Annotated[list[PlanLineIn], Field(max_length=MAX_LINES)] = []


class HeadcountPlanSave(PlanDraft):
    """`PUT /{id}`: thay nguyên header + khoản + dòng + văn bản liên kết."""

    document_ids: DocumentIds = []


class HeadcountPlanCreate(PlanHeader):
    """`POST`: header + `template_id` (chép khoản từ mẫu). Gửi `cost_items` thì dùng nó thay vì chép mẫu."""

    template_id: Id = 0
    cost_items: Annotated[list[CostItemIn], Field(max_length=MAX_COST_ITEMS)] | None = None
    lines: Annotated[list[PlanLineIn], Field(max_length=MAX_LINES)] = []
    document_ids: DocumentIds = []
