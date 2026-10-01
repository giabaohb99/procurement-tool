"""Gom nhóm báo cáo kiểu Haravan — CỘNG bằng Python (khuôn `compute_pr_lines_summary`), chạy
y hệt SQLite (test)/MySQL (prod). Lọc kỳ ở SQL trong `fetch` (`report_period.range_filter`);
tệp này chỉ CỘNG các hàng đã lọc sẵn. Phần TÍNH thuần (không cần biết `ReportSpec` là gì) nằm
ở `report_compute.py` — tách ra để giữ tệp này dưới 200 dòng.

Luật cốt lõi: `totals` cộng TRỰC TIẾP trên toàn bộ hàng, KHÔNG cộng lại từ `groups` (một
chiều nhiều giá trị — vd một PYC có 2 PIC — làm `groups` cộng dôi so với `totals`, đúng ý,
không phải lỗi). `derived` tính LẠI ở mọi cấp (tổng/nhóm/mốc), mẫu số 0 → `None` (H2, "chưa có
dữ liệu" chứ không phải 0%). Khóa chiều rỗng/0 → nhãn `(Chưa gắn)`.

Kỳ SO SÁNH (review 28/09/2026): `trend` của kỳ so sánh được DỜI lên đúng trục/độ hạt của kỳ
NÀY (H1 — trước đây mỗi kỳ tự tính độ hạt riêng rồi ghép theo chỉ số mốc, tuần đấu ngày là sai
âm thầm). `groups` là HỢP khóa của cả hai kỳ (L1 — một nhóm hết việc ở kỳ này vẫn phải hiện,
không biến mất khỏi bảng). Chỉ số THỜI ĐIỂM (`snapshot=True`, vd công nợ còn lại) chỉ có ở
Tổng — vắng mặt (không phải 0) ở `trend`/`groups` (M1).

Dùng tối thiểu (phase sau tự viết `fetch` đã qua `apply_scope`):

    def fetch(d_from, d_to):
        q = apply_scope(db.query(PurchaseRequest), PurchaseRequest,
                         "purchase_request", user, profile)
        q = q.filter(range_filter(PurchaseRequest.request_date, "str", d_from, d_to))
        return q.with_entities(PurchaseRequest.request_date, PurchaseRequest.department,
                                PurchaseRequest.amount).all()

    spec = ReportSpec(date_of=lambda r: to_local_date(r.request_date),
        metrics=[MetricSpec("count", "Số phiếu", kind="int", value_of=lambda r: 1)],
        dimensions={"department": DimensionSpec("department", "Phòng ban",
                    key_of=lambda r: [(r.department or "", r.department or "")])})
    data = build_report(fetch, spec, parse_period(request.query_params), group_by="department")
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Callable

from fastapi import HTTPException
from app.core.report_period import Period, bucket_axis, resolve_granularity
from app.core.report_compute import (bucket_rows, compare_shift, compute_derived, compute_metrics,
                                      drop_snapshot, merge_groups_by_key, merge_trend_by_index,
                                      meta_of, trend_on_axis)

EMPTY_LABEL = "(Chưa gắn)"


@dataclass(frozen=True)
class MetricSpec:
    """Một chỉ số CỘNG ĐƯỢC. Đúng 1 trong `value_of`/`distinct_of`."""
    key: str
    label: str
    kind: str = "int"          # int|money|days|hours|percent
    good: str | None = None    # "up"|"down"|None — chiều tốt cho mũi tên ±%
    value_of: Callable[[Any], float] | None = None    # cộng dồn
    distinct_of: Callable[[Any], Any] | None = None    # đếm SỐ GIÁ TRỊ KHÁC NHAU (bỏ falsy)
    #  Review P03 (28/09/2026): chỉ số PHỤ — chỉ để làm mẫu số/tử số của một `DerivedSpec`,
    #  KHÔNG đứng riêng — FE/Excel bỏ khỏi bảng/cột (vd `deliveries_done`, M1/L4).
    helper: bool = False
    #  Chỉ số THỜI ĐIỂM (đang mở, quá hạn…) — chỉ đúng ở TỔNG (ghi bằng callback `snapshot()`
    #  của `build_report`); nhóm/mốc thời gian KHÔNG cộng dồn được nên phải vắng mặt (M1).
    snapshot: bool = False

    def __post_init__(self):
        if (self.value_of is None) == (self.distinct_of is None):
            raise ValueError(f"MetricSpec {self.key}: cần đúng 1 trong value_of/distinct_of")

@dataclass(frozen=True)
class DerivedSpec:
    """Tỷ lệ/trung bình tính SAU khi cộng: `num/den*scale`, làm tròn `ndigits`. Mẫu số 0 → `None`."""
    key: str
    label: str
    num: str
    den: str
    kind: str = "percent"
    good: str | None = None
    scale: float = 100.0
    ndigits: int = 1
    helper: bool = False
    snapshot: bool = False

@dataclass(frozen=True)
class DimensionSpec:
    """Một chiều gom nhóm. `key_of(row)` trả `[(key,label),...]` — CHO PHÉP nhiều giá trị."""
    key: str
    label: str
    key_of: Callable[[Any], list[tuple[Any, str]]]
    empty_label: str = EMPTY_LABEL

@dataclass(frozen=True)
class ReportSpec:
    date_of: Callable[[Any], date | None]
    metrics: list[MetricSpec]
    derived: list[DerivedSpec] = field(default_factory=list)
    dimensions: dict[str, DimensionSpec] = field(default_factory=dict)
    breakdowns: dict[str, DimensionSpec] = field(default_factory=dict)
    #  Chỉ số XẾP HẠNG nhóm + giá trị của breakdown "Top" (vd `order_value` cho Top NCC).
    #  Bỏ trống = chỉ số đầu. KHÔNG đếm số hàng: một hàng có thể là một LẦN GIAO, không phải một dòng.
    rank_by: str | None = None

    def rank_key(self) -> str | None:
        return self.rank_by or (self.metrics[0].key if self.metrics else None)

#  Breakdown là danh sách "Top" — cắt ngọn cho biểu đồ cột ngang khỏi dài vô tận.
BREAKDOWN_LIMIT = 10

#  Gói A3 (hiệu năng báo cáo, 01/10/2026): `groups` KHÔNG có trần trước đây — `group_by=employee`
#  ở ~5.000 nhân sự ra ~5.000 nhóm/~1MB JSON (load-test, công nợ phép năm). Giữ TOP
#  `GROUP_LIMIT - 1` theo xếp hạng, gộp phần còn lại thành MỘT hàng `"__other__"`.
GROUP_LIMIT = 300
OTHER_GROUP_KEY = "__other__"


def _cap_groups(groups: list[dict], buckets: dict[str, dict], spec: ReportSpec) -> list[dict]:
    """Trần `GROUP_LIMIT` nhóm (gói A3) — giữ TOP đã xếp hạng ở trên, gộp phần dư thành MỘT
    hàng `OTHER_GROUP_KEY` tính LẠI từ CHÍNH CÁC HÀNG bị gộp (không cộng `values` đã tính — tỷ lệ
    dẫn xuất kiểu trung bình-của-trung-bình sẽ sai), để tỷ lệ ở hàng gộp vẫn đúng. Không `rank`
    (hiếm — spec không có chỉ số nào) thì giữ nguyên thứ tự bucket gốc, không có "top" để xếp.
    `merge_groups_by_key` ghép khóa này XUYÊN KỲ bình thường vì cả hai kỳ đều dùng chung một
    chuỗi khóa cố định `"__other__"`."""
    if len(groups) <= GROUP_LIMIT:
        return groups
    kept, overflow = groups[:GROUP_LIMIT - 1], groups[GROUP_LIMIT - 1:]
    overflow_rows = [r for g in overflow for r in buckets[g["key"]]["rows"]]
    other_values = drop_snapshot(
        compute_derived(compute_metrics(overflow_rows, spec.metrics), spec.derived), spec)
    kept.append({"key": OTHER_GROUP_KEY, "label": f"(Các nhóm khác — {len(overflow)} nhóm)",
                "values": other_values})
    return kept


def aggregate(rows: list, spec: ReportSpec, d_from: date, d_to: date,
              granularity: str, group_by: str | None) -> dict:
    """Gom MỘT kỳ (hàng đã lọc sẵn trong [d_from, d_to]) — không biết gì về kỳ so sánh."""
    totals = drop_snapshot(compute_derived(compute_metrics(rows, spec.metrics), spec.derived), spec)
    rank = spec.rank_key()
    dateless = [r for r in rows if spec.date_of(r) is None]
    axis = bucket_axis(d_from, d_to, granularity)
    trend = trend_on_axis(rows, spec, axis, granularity)
    groups = None
    if group_by and group_by != "none":
        dim = spec.dimensions.get(group_by)
        if dim is None:
            raise HTTPException(422, f"Xem theo không hợp lệ: {group_by}")
        buckets = bucket_rows(rows, dim.key_of, dim.empty_label)
        groups = [{"key": k, "label": b["label"],
                   "values": drop_snapshot(compute_derived(compute_metrics(b["rows"], spec.metrics),
                                                            spec.derived), spec)}
                  for k, b in buckets.items()]
        if groups and rank:
            groups.sort(key=lambda g: g["values"].get(rank, 0) or 0, reverse=True)
        groups = _cap_groups(groups, buckets, spec)
    breakdowns = {}
    for name, dim in spec.breakdowns.items():
        buckets = bucket_rows(rows, dim.key_of, dim.empty_label)
        items = [{"key": k, "label": b["label"],
                  "value": compute_derived(compute_metrics(b["rows"], spec.metrics), spec.derived).get(rank, 0) or 0}
                 for k, b in buckets.items()]
        items = sorted((i for i in items if i["value"]), key=lambda x: x["value"], reverse=True)
        breakdowns[name] = items[:BREAKDOWN_LIMIT]
    notes = [f"Có {len(dateless)} dòng không xác định được ngày — không tính vào xu hướng"] \
        if dateless else []
    return {"totals": totals, "trend": trend, "groups": groups, "breakdowns": breakdowns, "notes": notes}


def build_report(fetch: Callable[[date, date], list], spec: ReportSpec, period: Period,
                  group_by: str | None = None, snapshot: Callable[[date], dict] | None = None) -> dict:
    """Gọi `fetch(from,to)` TỐI ĐA 2 lần (kỳ này + kỳ so sánh) rồi trả hợp đồng JSON chuẩn
    (`period·meta·totals·trend·groups?·breakdowns·notes`). `fetch` PHẢI tự scope
    (`require`+`apply_scope`) — khung này không biết gì về quyền. `snapshot(to)` tùy chọn:
    chỉ số "tại thời điểm" (đang mở, quá hạn…), gộp thẳng vào `totals` (SAU khi `drop_snapshot`
    đã dọn giá trị 0 giả của các `MetricSpec(snapshot=True)`, xem M1).
    """
    axis = bucket_axis(period.date_from, period.date_to, period.granularity)
    cur = aggregate(fetch(period.date_from, period.date_to), spec,
                     period.date_from, period.date_to, period.granularity, group_by)
    cmp = None
    cmp_trend = None
    if period.compare != "none" and period.compare_from and period.compare_to:
        cmp_rows = fetch(period.compare_from, period.compare_to)
        cmp_gran = resolve_granularity(period.compare_from, period.compare_to)
        cmp = aggregate(cmp_rows, spec, period.compare_from, period.compare_to, cmp_gran, group_by)
        #  H1: KHÔNG dùng `cmp["trend"]` (độ hạt RIÊNG của kỳ so sánh) — dời hàng lên trục
        #  của kỳ NÀY rồi gộp lại theo cùng độ hạt/mốc.
        cmp_trend = trend_on_axis(cmp_rows, spec, axis, period.granularity, compare_shift(period))
    if snapshot is not None:
        cur["totals"].update(snapshot(period.date_to))
        if cmp is not None:
            cmp["totals"].update(snapshot(period.compare_to))

    result = {"period": period.as_dict(), "meta": meta_of(spec, group_by),
              "totals": {"current": cur["totals"], "compare": cmp["totals"] if cmp else None},
              "trend": merge_trend_by_index(cur["trend"], cmp_trend),
              "breakdowns": cur["breakdowns"], "notes": cur["notes"]}
    if cur["groups"] is not None:
        result["groups"] = merge_groups_by_key(cur["groups"], cmp["groups"] if cmp else None,
                                               spec, spec.rank_key())
    return result
