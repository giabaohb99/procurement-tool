"""Bộ mã ĐỀ XUẤT KẾ HOẠCH AI (kh-AI1-3, doc/erp/tai-lieu-ai/22 §5.2).

R2/QĐ-11: cột trạng thái là `SMALLINT` + `IntEnum`, tiếng Việt chỉ ở tầng hiển thị. Thuần stdlib (cùng lý do
`capability_codes.py`): `code_sets.py` phải nạp được ở máy không cài SQLAlchemy để chạy `scripts/gen_status_ts.py`.
Số đã cấp giữ nguyên mãi mãi, không tái dùng; `0` không hợp lệ.
"""
from enum import IntEnum

from app.core.status_catalog import Code, CodeSet, register


class AiPlanStatus(IntEnum):
    PENDING = 1     # Chờ duyệt — chưa tạo việc nào
    APPROVED = 2    # Người thật đã duyệt → đã dựng bảng Dự án
    REJECTED = 3    # Người duyệt từ chối
    CANCELLED = 4   # Chủ đề xuất tự hủy
    #  Công tắc duyệt TẮT: "tạo" dựng bảng ngay như bao-CR-616. Ghi riêng để dữ liệu học không lẫn lần tạo thẳng với lần
    #  người thật gật (A1 chốt 22/10).
    DIRECT = 5


AI_PLAN_STATUS_LABELS: dict[AiPlanStatus, str] = {
    AiPlanStatus.PENDING: "Chờ duyệt",
    AiPlanStatus.APPROVED: "Đã duyệt",
    AiPlanStatus.REJECTED: "Từ chối",
    AiPlanStatus.CANCELLED: "Đã hủy",
    AiPlanStatus.DIRECT: "Tạo thẳng (chưa qua duyệt)",
}

AI_PLAN_STATUS_SET = register(CodeSet(
    "ai_plan_status", "Trạng thái đề xuất kế hoạch AI",
    [Code(str(int(k)), label, sort_order=int(k), is_terminal=k != AiPlanStatus.PENDING)
     for k, label in AI_PLAN_STATUS_LABELS.items()]))
