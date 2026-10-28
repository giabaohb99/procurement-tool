"""Bộ mã SỐ của kế hoạch nhân sự theo kỳ (duoc-CR-690) — luật R2/QĐ-11: cột phân loại là SMALLINT + IntEnum.

Thuần stdlib (không import SQLAlchemy) để `code_sets.py` nạp được ở máy không có DB khi chạy
`scripts/gen_status_ts.py`. Số đã cấp GIỮ NGUYÊN mãi mãi, không tái dùng; loại bỏ thì để trống số đó.
"""
from enum import IntEnum

from app.core.status_catalog import Code, CodeSet, register


class PlanPeriodType(IntEnum):
    YEAR = 1      # Năm
    HALF = 2      # Bán niên
    QUARTER = 3   # Quý
    MONTH = 4     # Tháng


class CostCalcMethod(IntEnum):
    PER_HEAD_MONTH = 1   # Số tiền / người / tháng, nhập theo vị trí
    PERCENT_OF = 2       # % trên các khoản khác (có trần / người)
    MONTHS_OF = 3        # Số tháng của một khoản
    PER_HEAD_ONCE = 4    # Số tiền / người / lần
    LUMP_SUM = 5         # Số tiền cả phòng


class CostAppliesTo(IntEnum):
    ALL_POSITIONS = 1        # Mọi vị trí
    SELECTED_POSITIONS = 2   # Chỉ các vị trí đã chọn
    WHOLE_DEPARTMENT = 3     # Cả phòng, không theo người (chỉ hợp lệ với LUMP_SUM)


class ActualSource(IntEnum):
    NONE = 0                          # Không có nguồn thực tế
    BASE_SALARY = 1                   # Lương cơ bản trên HĐLĐ
    ALLOWANCE = 2                     # Phụ cấp trên HĐLĐ
    PERCENT_OF_INSURANCE_SALARY = 3   # % × lương đóng BHXH trên HĐLĐ


def _set(name: str, title: str, labels: dict) -> CodeSet:
    return register(CodeSet(name, title, [
        Code(str(int(k)), label, sort_order=int(k), key=k.name) for k, label in labels.items()]))


PLAN_PERIOD_TYPE_SET = _set("plan_period_type", "Loại kỳ kế hoạch nhân sự", {
    PlanPeriodType.YEAR: "Năm", PlanPeriodType.HALF: "Bán niên",
    PlanPeriodType.QUARTER: "Quý", PlanPeriodType.MONTH: "Tháng"})

COST_CALC_METHOD_SET = _set("cost_calc_method", "Cách tính khoản chi phí nhân sự", {
    CostCalcMethod.PER_HEAD_MONTH: "Số tiền / người / tháng (nhập theo vị trí)",
    CostCalcMethod.PERCENT_OF: "% trên các khoản khác",
    CostCalcMethod.MONTHS_OF: "Số tháng của một khoản",
    CostCalcMethod.PER_HEAD_ONCE: "Số tiền / người / lần",
    CostCalcMethod.LUMP_SUM: "Số tiền cả phòng"})

COST_APPLIES_TO_SET = _set("cost_applies_to", "Khoản chi phí áp cho", {
    CostAppliesTo.ALL_POSITIONS: "Mọi vị trí",
    CostAppliesTo.SELECTED_POSITIONS: "Chỉ các vị trí đã chọn",
    CostAppliesTo.WHOLE_DEPARTMENT: "Cả phòng (không theo người)"})

COST_ACTUAL_SOURCE_SET = _set("cost_actual_source", "Nguồn số thực tế của khoản chi phí", {
    ActualSource.NONE: "Không có",
    ActualSource.BASE_SALARY: "Lương cơ bản trên HĐLĐ",
    ActualSource.ALLOWANCE: "Phụ cấp trên HĐLĐ",
    ActualSource.PERCENT_OF_INSURANCE_SALARY: "% × lương đóng BHXH trên HĐLĐ"})
