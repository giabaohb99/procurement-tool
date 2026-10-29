"""Hằng số của kế hoạch nhân sự theo kỳ. Bộ mã SỐ khai ở `app/core/headcount_plan_codes.py` (thuần stdlib để
`gen_status_ts.py` nạp được); tệp này re-export + thêm trần kích thước của module."""
from app.core.headcount_plan_codes import (  # noqa: F401
    ActualSource, CostAppliesTo, CostCalcMethod, PlanPeriodType)

MAX_COST_ITEMS = 50        # khoản / kế hoạch (hoặc / mẫu)
MAX_LINES = 200            # dòng vị trí / kế hoạch
MAX_DOCUMENTS = 20         # văn bản liên kết / kế hoạch
MAX_MONEY = 10**13         # đồng NGUYÊN; đủ cho cả tập đoàn và không tràn BigInteger khi cộng
MAX_HEADCOUNT = 1_000_000
