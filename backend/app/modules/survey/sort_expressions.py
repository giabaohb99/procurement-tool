"""Phiếu khảo sát — biểu thức SQL xếp cột danh sách KHÔNG xếp thẳng theo cột lưu (duoc-CR-744).

`apply_sort_from_request(..., allow=...)` nhận map {khóa cột ở giao diện: biểu thức SQLAlchemy}.
"""
from app.core.code_rank_sql import build_value_rank_expression

from .model import Survey

#  Dòng đời của phiếu (cột `status`) theo đúng thứ tự `SURVEY_STATUS_LABELS` ở giao diện: nhãn đang
#  hiện là tiếng Việt nên xếp theo TIẾN TRÌNH, không theo chữ cái của mã tiếng Anh.
SURVEY_STATUS_ORDER = ("draft", "submitted", "approved", "rejected", "cancelled", "")

#  Loại phiếu (cột `survey_type`) theo thứ tự chữ cái của NHÃN đang hiện: "Khảo sát NCC" <
#  "Khảo sát NCC & SP" < "Khảo sát SP" (`SURVEY_TYPE_LABELS`).
SURVEY_TYPE_ORDER = ("supplier", "combined", "product", "")


def list_sort_allow() -> dict:
    """Map cho cột danh sách phiếu khảo sát: Trạng thái và Loại xếp theo nhãn / dòng đời."""
    return {
        "status": build_value_rank_expression(Survey.status, SURVEY_STATUS_ORDER),
        "survey_type": build_value_rank_expression(Survey.survey_type, SURVEY_TYPE_ORDER),
    }
