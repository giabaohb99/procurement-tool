"""YCBG — biểu thức SQL xếp cột danh sách KHÔNG xếp thẳng theo cột lưu (duoc-CR-744).

`apply_sort_from_request(..., allow=...)` nhận map {khóa cột ở giao diện: biểu thức SQLAlchemy}.
"""
from app.core.code_rank_sql import build_value_rank_expression

from .model import SurveyRequest

#  Dòng đời của phiếu (cột `status`) theo đúng thứ tự `SR_STATUS_LABELS` ở giao diện: nhãn đang hiện
#  là tiếng Việt nên xếp theo TIẾN TRÌNH, không theo chữ cái của mã tiếng Anh. Nhánh rẽ (bị trả lại,
#  từ chối) đứng sau chuỗi.
SR_STATUS_ORDER = ("draft", "submitted", "approved", "processing", "survey_done", "pr_created",
                   "done", "rejected", "cancelled", "")


def list_sort_allow() -> dict:
    """Map cho cột danh sách YCBG: `status` xếp theo hạng dòng đời."""
    return {"status": build_value_rank_expression(SurveyRequest.status, SR_STATUS_ORDER)}
