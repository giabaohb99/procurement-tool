"""Bản THEO KỲ của Báo cáo khảo sát (P03, `GET /api/survey-report/summary` khi có `preset`)
— hợp đồng chuẩn `report_aggregate.build_report`. Tách khỏi `controller.py` để giữ tệp đó
gọn; dùng lại `service.report_rows` + `controller._filter_report_rows` (lọc phi-thời-gian)
nên số liệu luôn khớp bảng `/lines` và bản `date_from/date_to` cũ.

"NSPT" ở đây là NHÂN SỰ phụ trách khảo sát (khác "NCC" nhà cung cấp) — không cần gác thêm
quyền `supplier.read`, ai có `survey.read` cũng thấy chiều này.

P06 (review hiệu năng 28/09/2026): `value_of` đọc `r.get("cnt", 1)` thay vì hằng số `1` — để
CÙNG một `ReportSpec` chạy được với CẢ hai nguồn `fetch`: hàng CŨ (1 hàng = 1 dòng khảo sát,
không có khóa "cnt" -> `.get("cnt", 1)` = 1, y hệt trước) LẪN hàng GOM SẴN của
`report_grouped_fetch.grouped_report_rows_in_range` (1 hàng = N dòng cùng tổ hợp
nspt/nhóm hàng/kết quả duyệt/ngày, mang sẵn "cnt" = N).
"""
from __future__ import annotations

from app.core.report_aggregate import DerivedSpec, DimensionSpec, MetricSpec, ReportSpec
from app.core.report_period import to_local_date

_KIND_LABEL = {"supplier": "Khảo sát NCC", "product": "Khảo sát SP"}


def build_spec() -> ReportSpec:
    metrics = [
        MetricSpec("lines_supplier", "Dòng KS NCC", kind="int",
                  value_of=lambda r: r.get("cnt", 1) if r.get("kind") == "supplier" else 0),
        MetricSpec("lines_product", "Dòng KS SP", kind="int",
                  value_of=lambda r: r.get("cnt", 1) if r.get("kind") == "product" else 0),
        MetricSpec("lines", "Tổng dòng", kind="int", value_of=lambda r: r.get("cnt", 1)),
        MetricSpec("approved", "Đã duyệt", kind="int",
                  value_of=lambda r: r.get("cnt", 1) if r.get("line_approve") == "Đã duyệt" else 0),
    ]
    derived = [DerivedSpec("approved_rate", "Tỷ lệ duyệt", num="approved", den="lines", good="up")]
    dimensions = {
        "nspt": DimensionSpec("nspt", "NSPT",
                              key_of=lambda r: [(r.get("nspt"), r.get("nspt"))] if r.get("nspt") else []),
        "item_group": DimensionSpec("item_group", "Nhóm hàng",
                                    key_of=lambda r: [(r.get("item_group"), r.get("item_group"))]
                                    if r.get("item_group") else []),
        "line_approve": DimensionSpec(
            "line_approve", "Kết quả duyệt",
            key_of=lambda r: [(r.get("line_approve") or "Chờ duyệt", r.get("line_approve") or "Chờ duyệt")]),
        "kind": DimensionSpec("kind", "Loại",
                              key_of=lambda r: [(r.get("kind"), _KIND_LABEL.get(r.get("kind"), r.get("kind")))]
                              if r.get("kind") else []),
    }
    return ReportSpec(date_of=lambda r: to_local_date(r.get("date")), metrics=metrics, derived=derived,
                      dimensions=dimensions, breakdowns=dimensions, rank_by="lines")
