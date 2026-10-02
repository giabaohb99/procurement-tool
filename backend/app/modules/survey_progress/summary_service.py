"""Bản THEO KỲ của màn Tiến độ báo giá (P03, `GET /api/survey-progress/summary` khi có
`preset`) — hợp đồng chuẩn `report_aggregate.build_report`. Tách khỏi `controller.py` để giữ
tệp đó dưới 200 dòng; dùng lại `_build_query`/`_decorate` của `controller.py` nên số liệu
luôn khớp bảng gốc.

Không có chiều NCC/NSPT nhạy cảm ở đây — "NSPT" của báo cáo khảo sát là NHÂN SỰ phụ trách
(khác "NCC" nhà cung cấp), không cần gác thêm quyền `supplier.read`.
"""
from __future__ import annotations

from app.core.report_aggregate import DerivedSpec, DimensionSpec, MetricSpec, ReportSpec
from app.core.report_period import to_local_date
from app.modules.survey_request.line_state import STATE_DONE, STATE_PR_CREATED

#  Hai mốc cuối của chuỗi tiến độ — dòng đã rời tay NSTM, không còn là việc đang mở.
#  Cùng nguồn với `_CLOSED_STATES` của `controller.py` (cả hai đọc thẳng `line_state`,
#  không tự chép chuỗi ra đây — tránh trôi khi đổi bộ trạng thái).
CLOSED_STATES = (STATE_PR_CREATED, STATE_DONE)

#  L11 (review 28/09/2026) — `open_lines`/`late` đọc trạng thái HIỆN TẠI của dòng khảo sát tại
#  thời điểm chạy báo cáo, không phải trạng thái CỦA KỲ đó. Ở kỳ so sánh, một dòng "đang mở/
#  trễ hạn" nghĩa là "dòng nhận trong kỳ đó, tính tới HÔM NAY vẫn còn mở/đã trễ" — không phải
#  ảnh chụp tại cuối kỳ (hệ thống không lưu lịch sử trạng thái).
NOTE = ("'Đang mở'/'Trễ hạn' tính theo trạng thái HIỆN TẠI của dòng, không phải trạng thái tại "
       "cuối kỳ — ở kỳ so sánh, đây là số dòng nhận trong kỳ đó mà tới HÔM NAY vẫn còn mở/đã trễ.")


def build_spec() -> ReportSpec:
    metrics = [
        MetricSpec("lines", "Số dòng", kind="int", value_of=lambda r: 1),
        MetricSpec("open_lines", "Đang mở", kind="int",
                  value_of=lambda r: 1 if (r.get("progress_state") or "") not in CLOSED_STATES else 0),
        MetricSpec("late", "Trễ hạn", kind="int", good="down",
                  value_of=lambda r: 1 if r.get("days_late") is not None else 0),
        MetricSpec("answered", "Đã trả kết quả", kind="int",
                  value_of=lambda r: 1 if r.get("result_date") else 0),
        #  Hai chỉ số PHỤ — chỉ để làm mẫu số/tử số của `avg_handling_days`, không đứng riêng.
        MetricSpec("handling_days_sum", "Tổng ngày xử lý", kind="days", helper=True,
                  value_of=lambda r: r["handling_days"] if r.get("handling_days") is not None else 0),
        MetricSpec("handling_days_count", "Số dòng có ngày xử lý", kind="int", helper=True,
                  value_of=lambda r: 1 if r.get("handling_days") is not None else 0),
    ]
    derived = [DerivedSpec("avg_handling_days", "Ngày xử lý TB", num="handling_days_sum",
                          den="handling_days_count", kind="days", good="down", scale=1)]
    #  `scale=1`: DerivedSpec mặc định ×100 cho TỶ LỆ %; đây là TRUNG BÌNH ngày — quên là ra 168,4 thay vì 1,7.
    dimensions = {
        "assignee": DimensionSpec("assignee", "NSTM",
                                  key_of=lambda r: [(r.get("assignee_name"), r.get("assignee_name"))]
                                  if r.get("assignee_name") else []),
        "item_group": DimensionSpec("item_group", "Nhóm hàng",
                                    key_of=lambda r: [(r.get("item_group"), r.get("item_group"))]
                                    if r.get("item_group") else []),
        "progress": DimensionSpec("progress", "Tiến độ",
                                  key_of=lambda r: [(r.get("progress_state"), r.get("progress_state"))]
                                  if r.get("progress_state") else []),
    }
    return ReportSpec(date_of=lambda r: to_local_date(r.get("request_date")), metrics=metrics,
                      derived=derived, dimensions=dimensions, breakdowns=dimensions)
