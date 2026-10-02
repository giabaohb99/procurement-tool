"""Phần TÍNH của khung báo cáo Haravan — tách khỏi `report_aggregate.py` để giữ tệp đó dưới
200 dòng (review P01–P03, 28/09/2026). Các hàm ở đây CHỈ đọc `spec.metrics/derived/dimensions`
qua duck-typing (không import `ReportSpec` lúc chạy) để tránh import vòng với
`report_aggregate.py` — gợi ý kiểu cho `ReportSpec`/`Period` chỉ dùng lúc kiểm tra kiểu tĩnh.

Ba nhóm hàm:
  - `compute_metrics`/`compute_derived`/`bucket_rows`: cộng dồn một tập hàng (như cũ, P01).
  - `drop_snapshot`/`zero_values`: luật cho chỉ số THỜI ĐIỂM (snapshot) — chỉ đúng ở TỔNG,
    nhóm/mốc thời gian phải THIẾU HẲN khóa, không phải 0 (M1, review 28/09/2026).
  - `trend_on_axis`/`compare_shift`/`merge_trend_by_index`/`merge_groups_by_key`/`meta_of`:
    gộp kỳ so sánh lên ĐÚNG trục của kỳ này (H1) và hợp khóa `groups` giữa hai kỳ (L1).
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import TYPE_CHECKING, Callable

from app.core.report_period import bucket_of

if TYPE_CHECKING:
    from app.core.report_aggregate import DerivedSpec, MetricSpec, ReportSpec
    from app.core.report_period import Period


def compute_metrics(rows: list, metrics: list["MetricSpec"]) -> dict[str, float]:
    """Cộng từng `MetricSpec` trên một tập hàng — dùng cho tổng / mốc / nhóm."""
    out = {}
    for m in metrics:
        if m.value_of is not None:
            out[m.key] = sum(float(m.value_of(r) or 0) for r in rows)
        else:
            out[m.key] = len({v for r in rows if (v := m.distinct_of(r))})
    return out


def compute_derived(values: dict, derived: list["DerivedSpec"]) -> dict:
    """Tính tỷ lệ/trung bình TỪ metric đã cộng — gọi được ở mọi cấp (tổng/nhóm/mốc).

    H2 (review 28/09/2026): mẫu số 0 nghĩa "chưa có dữ liệu", KHÔNG PHẢI 0% — trả về `None`
    để FE hiện "—" thay vì mũi tên ±100% giả trên một ngày/kỳ trống dữ liệu."""
    out = dict(values)
    for d in derived:
        den = values.get(d.den, 0)
        out[d.key] = round(values.get(d.num, 0) / den * d.scale, d.ndigits) if den else None
    return out


def bucket_rows(rows: list, key_of, empty_label: str) -> dict[str, dict]:
    """Rows -> {key: {"label","rows"}}. Một hàng góp NHIỀU khóa nếu `key_of` trả nhiều cặp,
    nhưng không cộng đôi nếu hàng tự trả trùng khóa. Khóa rỗng/0 gộp về `empty_label`."""
    buckets: dict[str, dict] = {}
    for r in rows:
        pairs = key_of(r) or [("", empty_label)]
        added = set()
        for raw_key, label in pairs:
            k = "" if raw_key in (None, "", 0) else str(raw_key)
            if k in added:
                continue
            added.add(k)
            b = buckets.setdefault(k, {"label": label if k else empty_label, "rows": []})
            b["rows"].append(r)
    return buckets


def drop_snapshot(values: dict, spec: "ReportSpec") -> dict:
    """Bỏ khóa của MetricSpec/DerivedSpec đánh dấu `snapshot=True` khỏi một tập giá trị đã
    cộng (M1). Snapshot (vd công nợ còn lại) là số THỜI ĐIỂM, chỉ có nghĩa ở TỔNG —
    `build_report` ghi đè bằng callback `snapshot()` SAU khi gọi hàm này; nhóm/mốc thời gian
    phải THIẾU HẲN khóa (không phải 0), để FE/Excel biết mà bỏ qua thay vì vẽ toàn số 0."""
    keys = {m.key for m in spec.metrics if m.snapshot} | {d.key for d in spec.derived if d.snapshot}
    return {k: v for k, v in values.items() if k not in keys} if keys else values


def zero_values(spec: "ReportSpec") -> dict:
    """Giá trị "0" cho một NHÓM chỉ xuất hiện ở kỳ SO SÁNH (L1) — số đo THƯỜNG về 0, số đo
    DẪN XUẤT về `None` (chia 0/0 vô nghĩa), số đo THỜI ĐIỂM (snapshot) bỏ hẳn khóa."""
    zeros = {m.key: 0 for m in spec.metrics if not m.snapshot}
    zeros.update({d.key: None for d in spec.derived if not d.snapshot})
    return zeros


def trend_on_axis(rows: list, spec: "ReportSpec", axis: list[dict], granularity: str,
                   shift: Callable[[date], date] | None = None) -> list[dict]:
    """Gom `rows` lên các mốc có sẵn của `axis` (trục của kỳ NÀY). `shift` (H1): dời ngày của
    một hàng trước khi tính khóa mốc — dùng để gộp `trend` của kỳ SO SÁNH lên cùng trục/độ hạt
    với kỳ này, thay vì tự tính độ hạt riêng rồi ghép theo CHỈ SỐ (tuần đấu ngày là sai âm
    thầm). Ngày dời ra ngoài trục (đầu/cuối kỳ) bị BỎ, không dồn vào mốc biên."""
    by_bucket: dict[str, list] = {a["key"]: [] for a in axis}
    for r in rows:
        d = spec.date_of(r)
        if d is None:
            continue
        if shift is not None:
            d = shift(d)
        k = bucket_of(d, granularity)
        if k in by_bucket:
            by_bucket[k].append(r)
    return [{"key": a["key"], "label": a["label"],
             "values": drop_snapshot(compute_derived(compute_metrics(by_bucket[a["key"]], spec.metrics),
                                                       spec.derived), spec)}
            for a in axis]


def compare_shift(period: "Period") -> Callable[[date], date]:
    """H1 — hàm dời một NGÀY của kỳ SO SÁNH sang trục kỳ NÀY, để `trend` gộp cùng mốc/độ hạt
    thay vì tự tính độ hạt riêng rồi ghép theo CHỈ SỐ (kỳ này ra tuần, kỳ trước ra ngày, ghép
    mốc 1↔1 là sai). `compare=year`: dời đúng 1 NĂM LỊCH (29/02 → 28/02 năm không nhuận, cùng
    luật `_shift_years` của `report_period`); còn lại (`previous`): dời đúng số ngày
    `date_from − compare_from` — khớp mọi preset LỊCH (parse_period đã tính sẵn khoảng lùi cố
    định) lẫn preset CUỘN/`custom` (hai kỳ liền kề, số ngày bằng nhau tuyệt đối)."""
    if period.compare == "year":
        def shift(d: date) -> date:
            try:
                return d.replace(year=d.year + 1)
            except ValueError:
                return date(d.year + 1, 2, 28)   # 29/02 -> 28/02 năm sau không nhuận
        return shift
    offset = (period.date_from - period.compare_from).days
    return lambda d: d + timedelta(days=offset)


def merge_trend_by_index(cur: list, cmp: list | None) -> list:
    """Ghép `trend` theo CHỈ SỐ mốc — cả hai vế nay CÙNG trục (`trend_on_axis` gọi từ
    `build_report` với cùng `axis`/độ hạt), nên chỉ số i luôn là cùng một mốc thời gian thật."""
    return [{"key": c["key"], "label": c["label"], "current": c["values"],
              "compare": cmp[i]["values"] if cmp and i < len(cmp) else None}
            for i, c in enumerate(cur)]


def merge_groups_by_key(cur: list, cmp: list | None, spec: "ReportSpec", rank: str | None) -> list:
    """Ghép `groups`/`breakdowns` theo KHÓA chiều — HỢP cả khóa chỉ có ở kỳ so sánh (L1: một
    phòng ban/NCC hết việc ở kỳ này vẫn phải hiện, giá trị kỳ này về 0, để thấy sụt giảm thay
    vì biến mất khỏi bảng). Sắp lại theo chỉ số XẾP HẠNG của kỳ NÀY, giảm dần."""
    cmp_list = cmp or []
    cmp_values = {c["key"]: c["values"] for c in cmp_list}
    cmp_label = {c["key"]: c["label"] for c in cmp_list}
    cur_by_key = {c["key"]: c for c in cur}
    zero = zero_values(spec)
    keys = list(cur_by_key) + [k for k in cmp_values if k not in cur_by_key]
    out = [{"key": k,
            "label": cur_by_key[k]["label"] if k in cur_by_key else cmp_label[k],
            "current": cur_by_key[k]["values"] if k in cur_by_key else dict(zero),
            "compare": cmp_values.get(k)} for k in keys]
    if rank:
        out.sort(key=lambda g: g["current"].get(rank) or 0, reverse=True)
    return out


def meta_of(spec: "ReportSpec", group_by: str | None) -> dict:
    """`meta` trả cho FE: nhãn/loại từng chỉ số + cờ `helper` (chỉ số PHỤ, không đứng riêng)
    và `snapshot` (số THỜI ĐIỂM, chỉ đúng ở Tổng) — FE/Excel dựa vào hai cờ này để ẩn cột."""
    metrics = [{"key": m.key, "label": m.label, "kind": m.kind, "good": m.good,
               "helper": m.helper, "snapshot": m.snapshot} for m in spec.metrics]
    metrics += [{"key": d.key, "label": d.label, "kind": d.kind, "good": d.good,
                "helper": d.helper, "snapshot": d.snapshot} for d in spec.derived]
    dims = [{"key": k, "label": d.label} for k, d in spec.dimensions.items()]
    gb = group_by if group_by and group_by != "none" else None
    return {"metrics": metrics, "dimensions": dims, "group_by": gb, "rank_by": spec.rank_key()}
