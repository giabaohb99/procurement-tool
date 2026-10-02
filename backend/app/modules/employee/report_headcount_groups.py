"""Ghép định biên ĐẦU/CUỐI kỳ vào `groups`/`breakdowns` của báo cáo Nhân sự — tách
khỏi `report_service.py` để giữ tệp đó dưới 200 dòng (review 01/10/2026, mục 4).

Vấn đề: `aggregate()` của khung chỉ dựng `groups` từ SỰ KIỆN vào/nghỉ rơi vào kỳ
— một phòng ổn định (không ai vào/nghỉ trong kỳ) không có sự kiện nào nên
KHÔNG có mặt trong `groups`, dù phòng đó vẫn có người. Báo cáo "cơ cấu" (xem
theo phòng ban/cấp bậc/...) mà thiếu hẳn phòng ổn định là sai lệch nghiêm
trọng — người xem tưởng phòng đó không tồn tại.

Giải: tính ĐỊNH BIÊN (snapshot) cho TỪNG NHÓM bằng cách gom lại danh sách
`employees_as_of(...)` (đã có sẵn ở `report_headcount_events.py`) qua ĐÚNG
`DimensionSpec.key_of` của chiều đang `group_by` — tái dùng luật gom nhóm có
sẵn, không viết lại. Nhóm nào CÓ NGƯỜI nhưng chưa có trong `groups` (không sự
kiện) được THÊM với số liệu sự kiện bằng 0; nhóm nào ĐÃ CÓ (có sự kiện) được
ghép thêm 4 khóa thời điểm. Sắp lại theo `headcount_end` — khác `rank_by`
mặc định "new_hires" của khung, vì báo cáo cơ cấu quan tâm QUY MÔ nhóm trước.
"""
from __future__ import annotations

from app.core.report_aggregate import BREAKDOWN_LIMIT, DimensionSpec
from app.core.report_compute import bucket_rows

from .report_headcount_events import HeadcountEvent


def apply_headcount(values: dict, start: int, end: int) -> None:
    """Ghi 4 khóa THỜI ĐIỂM vào một tập giá trị đã có sẵn (Tổng hoặc MỘT nhóm)."""
    values["headcount_start"] = start
    values["headcount_end"] = end
    values["net_change"] = end - start
    avg = (start + end) / 2
    values["turnover_rate"] = round((values.get("departures") or 0) / avg * 100, 1) if avg else None


def merge_group_headcount(data: dict, dim: DimensionSpec, zero: dict,
                          end_cur: list[HeadcountEvent], start_cur: list[HeadcountEvent],
                          end_cmp: list[HeadcountEvent] | None,
                          start_cmp: list[HeadcountEvent] | None) -> None:
    """`data["groups"]` (đã dựng từ sự kiện) → ghép thêm định biên theo TỪNG khóa của `dim`,
    thêm khóa còn thiếu (có người, không sự kiện), sắp lại theo `headcount_end`."""
    if data.get("groups") is None:
        return
    end_cur_b = bucket_rows(end_cur, dim.key_of, dim.empty_label)
    start_cur_b = bucket_rows(start_cur, dim.key_of, dim.empty_label)
    end_cmp_b = bucket_rows(end_cmp, dim.key_of, dim.empty_label) if end_cmp is not None else {}
    start_cmp_b = bucket_rows(start_cmp, dim.key_of, dim.empty_label) if start_cmp is not None else {}
    has_compare = data["totals"]["compare"] is not None

    by_key = {g["key"]: g for g in data["groups"]}
    for key in set(end_cur_b) | set(end_cmp_b) | set(by_key):
        g = by_key.get(key)
        if g is None:
            label = (end_cur_b.get(key) or end_cmp_b[key])["label"]
            g = {"key": key, "label": label, "current": dict(zero),
                "compare": dict(zero) if has_compare else None}
            data["groups"].append(g)
            by_key[key] = g
        apply_headcount(g["current"], len(start_cur_b.get(key, {}).get("rows", [])),
                        len(end_cur_b.get(key, {}).get("rows", [])))
        if g["compare"] is not None:
            apply_headcount(g["compare"], len(start_cmp_b.get(key, {}).get("rows", [])),
                            len(end_cmp_b.get(key, {}).get("rows", [])))
    data["groups"].sort(key=lambda g: g["current"].get("headcount_end") or 0, reverse=True)


def merge_status_breakdown(data: dict, status_dim: DimensionSpec, end_cur: list[HeadcountEvent]) -> None:
    """Low #1 (review) — "Theo trạng thái" là ĐỊNH BIÊN theo trạng thái tại cuối kỳ, không phải
    đếm sự kiện vào/nghỉ theo trạng thái (vốn gần như luôn ra "Chính thức", không nói lên cơ cấu)."""
    if "status" not in (data.get("breakdowns") or {}):
        return
    buckets = bucket_rows(end_cur, status_dim.key_of, status_dim.empty_label)
    items = [{"key": k, "label": b["label"], "value": len(b["rows"])} for k, b in buckets.items()]
    items = sorted((i for i in items if i["value"]), key=lambda x: x["value"], reverse=True)
    data["breakdowns"]["status"] = items[:BREAKDOWN_LIMIT]
