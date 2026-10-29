"""Dựng dict số đo THÔ từ kết quả GOM ở SQL — tách khỏi `report_sql_metrics.py` (giữ < 200 dòng).

`totals_dict` cho TỔNG (một dòng), `merge_dim_rows` hợp hai tập kết quả GOM theo cùng một chiều.
`ZERO_METRICS` là giá trị mặc định của một NHÓM/MỐC chưa có hàng nào khớp (9 khóa thô; các
khóa DẪN XUẤT tính sau bằng `compute_derived(.., DERIVED)`).
"""
from __future__ import annotations

from typing import Callable

from app.core.report_aggregate import EMPTY_LABEL

ZERO_METRICS = {"requests": 0, "days_approved": 0.0, "days_pending": 0.0, "days_unpaid": 0.0,
                "people_on_leave": 0, "requests_reject_return": 0, "requests_pending_over_3d": 0,
                "turnaround_hours_sum": 0.0, "turnaround_hours_count": 0}


def totals_dict(h_row, l_row) -> dict:
    """Dựng dict khóa THÔ cho TỔNG (không chia nhóm) từ 2 dòng gộp `header_aggregate`/
    `line_aggregate(group_col=None)`."""
    return {"requests": int(h_row.requests or 0),
            "requests_reject_return": int(h_row.requests_reject_return or 0),
            "people_on_leave": int(h_row.people_on_leave or 0),
            "turnaround_hours_sum": float(h_row.turnaround_hours_sum or 0),
            "turnaround_hours_count": int(h_row.turnaround_hours_count or 0),
            "requests_pending_over_3d": int(h_row.requests_pending_over_3d or 0),
            "days_approved": float(l_row.days_approved or 0),
            "days_pending": float(l_row.days_pending or 0),
            "days_unpaid": float(l_row.days_unpaid or 0)}


def merge_dim_rows(header_rows, line_rows, label_of: Callable[[int], str]) -> dict[str, dict]:
    """Hợp (UNION) 2 tập kết quả GOM theo CÙNG một chiều — một khóa có thể chỉ xuất hiện ở
    MỘT bên (vd loại nghỉ chỉ từng là loại PHỤ, chưa bao giờ là loại CHÍNH của đơn nào, xem
    `TestBreakdownLoaiNghiXepTheoNgay`); bên vắng mặt giữ nguyên `ZERO_METRICS`. Khóa rỗng/0
    gộp về `""`/`EMPTY_LABEL` — cùng luật chuẩn hóa của `report_compute.bucket_rows`.

    ⚠️ **Bẫy thứ tự hòa điểm** (cùng bài học `survey/report_grouped_fetch.py`): bản cũ xếp
    nhóm theo `rank_by` rồi dùng THỨ TỰ LẦN ĐẦU GẶP trong hàng thô làm tiêu chí phụ khi HÒA
    ĐIỂM (Python `sort` ổn định) — mà thứ tự đó, đo thực tế, là theo `from_date` TĂNG DẦN (nhờ
    chỉ số `ix_leave_request_range`). `GROUP BY` ở SQL không giữ thứ tự đó, nên hàm này giữ
    thêm `first_date` (yêu cầu gọi `header_aggregate`/`line_aggregate` với
    `with_first_date=True`) để `groups_for_dim`/breakdown SẮP LẠI đúng thứ tự "lần đầu gặp"
    trước khi đưa cho `report_compute.merge_groups_by_key`/`sorted()`."""
    out: dict[str, dict] = {}

    def _bucket(raw) -> dict:
        k = "" if raw in (None, "", 0) else str(raw)
        if k not in out:
            out[k] = {"label": label_of(raw) if k else EMPTY_LABEL, "first_date": None, **ZERO_METRICS}
        return out[k]

    def _track_date(b: dict, first_date) -> None:
        if first_date is not None and (b["first_date"] is None or first_date < b["first_date"]):
            b["first_date"] = first_date

    for r in header_rows:
        b = _bucket(r.key)
        b["requests"] = int(r.requests or 0)
        b["requests_reject_return"] = int(r.requests_reject_return or 0)
        b["people_on_leave"] = int(r.people_on_leave or 0)
        b["turnaround_hours_sum"] = float(r.turnaround_hours_sum or 0)
        b["turnaround_hours_count"] = int(r.turnaround_hours_count or 0)
        b["requests_pending_over_3d"] = int(r.requests_pending_over_3d or 0)
        _track_date(b, getattr(r, "first_date", None))
    for r in line_rows:
        b = _bucket(r.key)
        b["days_approved"] = float(r.days_approved or 0)
        b["days_pending"] = float(r.days_pending or 0)
        b["days_unpaid"] = float(r.days_unpaid or 0)
        _track_date(b, getattr(r, "first_date", None))
    return out
