"""Áp phần CHÊNH LỆCH do chia ngày theo kỳ/mốc (`report_day_split.py`) lên số đo đã gom ở SQL.

Đường SQL cũ gán TOÀN BỘ ngày của đơn vào kỳ/mốc chứa ngày BẮT ĐẦU. Với mỗi đơn vắt biên:
    chênh lệch = phần ngày THẬT rơi vào kỳ/mốc − phần SQL đã gán (1 nếu ngày bắt đầu trong kỳ).
Cộng chênh lệch vào Tổng / nhóm / «Top loại nghỉ» / mốc xu hướng ⇒ đơn bắt đầu trước kỳ được CỘNG
phần trong kỳ, đơn kéo qua cuối kỳ bị TRỪ phần ngoài kỳ. Chỉ chạm ba số đo ngày
(`days_approved`/`days_pending`/`days_unpaid`); số ĐƠN/người/tỷ lệ/thời gian duyệt giữ theo
ngày bắt đầu.
"""
from __future__ import annotations

from datetime import date
from typing import Callable

from app.core.report_aggregate import EMPTY_LABEL, OTHER_GROUP_KEY
from app.core.report_compute import compute_derived
from app.modules.leave.constants import LR_APPROVED, LR_PENDING
from app.modules.leave.report_day_split import SplitRequest
from app.modules.leave.report_sql_merge import ZERO_METRICS

_EPS = 1e-9


def _delta(sr: SplitRequest, share_split: float, share_sql: float, unpaid_types: set[int],
           type_id: int | None = None) -> dict[str, float]:
    """Chênh lệch ngày của MỘT đơn (hoặc riêng dòng loại `type_id`) giữa chia thật và SQL."""
    f = share_split - share_sql
    if abs(f) < _EPS:
        return {}
    if sr.status == LR_APPROVED:
        unpaid = sum(d for t, d in sr.lines
                     if t in unpaid_types and (type_id is None or t == type_id))
        return {"days_approved": sr.line_days(type_id) * f, "days_unpaid": unpaid * f}
    if sr.status == LR_PENDING:
        return {"days_pending": sr.line_days(type_id) * f}
    return {}


def _add(values: dict, delta: dict[str, float]) -> None:
    for k, v in delta.items():
        values[k] = round(max(float(values.get(k) or 0) + v, 0.0), 6)


def _range_shares(sr: SplitRequest, d_from: date, d_to: date) -> tuple[float, float]:
    """(phần ngày thật trong kỳ, phần SQL đã gán vào kỳ)."""
    return (sr.share_where(lambda d: d_from <= d <= d_to),
            1.0 if d_from <= sr.from_date <= d_to else 0.0)


def apply_to_totals(values: dict, srs: list[SplitRequest], d_from: date, d_to: date,
                    unpaid_types: set[int], derived) -> None:
    for sr in srs:
        _add(values, _delta(sr, *_range_shares(sr, d_from, d_to), unpaid_types))
    values.update(compute_derived(values, derived))


def _dim_keys(sr: SplitRequest, dim: str) -> list[tuple[int, int | None]]:
    """[(giá trị thô của chiều, loại nghỉ riêng nếu chiều là loại nghỉ)] — `leave_type` tính theo
    TỪNG DÒNG (như `dim_columns`), các chiều khác theo cột chép trên đơn."""
    if dim == "leave_type":
        return [(t, t) for t, _d in sr.lines]
    raw = {"company": sr.company_id, "department": sr.department_id, "employee": sr.employee_id,
           "status": sr.status}[dim]
    return [(raw, None)]


def apply_to_groups(groups: list[dict], srs: list[SplitRequest], dim: str, d_from: date,
                    d_to: date, unpaid_types: set[int], label_of: Callable[[int], str],
                    derived) -> list[dict]:
    """Cộng chênh lệch vào `groups`. Khóa chưa có nhóm → vào «(Các nhóm khác)» nếu đã bị cắt
    trần, ngược lại tạo nhóm mới (đơn bắt đầu trước kỳ, nhóm chưa có đơn nào trong kỳ)."""
    by_key = {g["key"]: g for g in groups}
    touched = set()
    for sr in srs:
        shares = _range_shares(sr, d_from, d_to)
        for raw, type_id in _dim_keys(sr, dim):
            delta = _delta(sr, *shares, unpaid_types, type_id)
            if not delta:
                continue
            key = "" if raw in (None, "", 0) else str(raw)
            g = by_key.get(key) or by_key.get(OTHER_GROUP_KEY)
            if g is None:
                g = {"key": key, "label": label_of(raw) if key else EMPTY_LABEL,
                     "values": dict(ZERO_METRICS)}
                groups.append(g)
                by_key[key] = g
            _add(g["values"], delta)
            touched.add(g["key"])
    for g in groups:
        if g["key"] in touched:
            g["values"].update(compute_derived(g["values"], derived))
    return groups


def leave_type_approved_deltas(srs: list[SplitRequest], d_from: date, d_to: date
                               ) -> dict[str, float]:
    """`{khóa loại nghỉ: chênh lệch days_approved}` cho «Top loại nghỉ» (xếp theo ngày đã duyệt)."""
    out: dict[str, float] = {}
    for sr in srs:
        if sr.status != LR_APPROVED:
            continue
        split, sql = _range_shares(sr, d_from, d_to)
        for t, days in sr.lines:
            key = "" if not t else str(t)
            out[key] = out.get(key, 0.0) + days * (split - sql)
    return {k: v for k, v in out.items() if abs(v) >= _EPS}


def apply_to_trend(by_bucket: dict[str, dict], srs: list[SplitRequest], d_from: date, d_to: date,
                   bucket_key: Callable[[date], str | None], unpaid_types: set[int]) -> None:
    """Cộng chênh lệch vào từng mốc `by_bucket` (khóa mốc → số đo thô). `bucket_key` trả None cho
    ngày ngoài trục. Ngày ngoài [d_from, d_to] không thuộc mốc nào của kỳ này."""
    for sr in srs:
        split: dict[str, float] = {}
        for day, share in sr.day_share.items():
            if d_from <= day <= d_to and (k := bucket_key(day)) is not None:
                split[k] = split.get(k, 0.0) + share
        sql_key = bucket_key(sr.from_date) if d_from <= sr.from_date <= d_to else None
        for k in set(split) | ({sql_key} - {None}):
            if k in by_bucket:
                _add(by_bucket[k], _delta(sr, split.get(k, 0.0), 1.0 if k == sql_key else 0.0,
                                          unpaid_types))
