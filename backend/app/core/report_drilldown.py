"""«Bấm vào con số ra danh sách người» của báo cáo kiểu Haravan (duoc-CR-686).

Hợp đồng chung cho mọi `GET <gốc>/summary/rows` (chi tiết ở phase-01 của plan
`261027-1045-kho-mau-bao-cao-nhan-su`):

- Tham số = mọi tham số của `/summary` + `metric` (bắt buộc) + `group_by`/`group_key` (tùy chọn,
  `group_key=""` là nhóm «(Chưa gắn)»). Nhóm gộp `__other__` không có danh sách → 422.
- Trả `{metric: {key, label}, columns: [{key, label, kind}], rows: [...], total, truncated}`.
  `kind` ∈ `text | date | int | days | money`; mỗi dòng có thể kèm `link` (đường giao diện v2).
- Trần `ROWS_LIMIT` dòng — `total` luôn là số THẬT trước khi cắt.

Đường `/rows` PHẢI gác y hệt `/summary` của nó: `require(entity, 'read')` + `apply_scope` +
`require_report(key)`. Tệp này không biết gì về quyền.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Iterable, Mapping

from fastapi import HTTPException

from app.core.report_aggregate import OTHER_GROUP_KEY, DimensionSpec

ROWS_LIMIT = 500
COLUMN_KINDS = ("text", "date", "int", "days", "money")


@dataclass(frozen=True)
class Col:
    """Một cột của bảng danh sách. `kind` quyết định giao diện định dạng ô thế nào."""
    key: str
    label: str
    kind: str = "text"

    def __post_init__(self):
        if self.kind not in COLUMN_KINDS:
            raise ValueError(f"Col {self.key}: kind lạ {self.kind!r}")

    def as_dict(self) -> dict:
        return {"key": self.key, "label": self.label, "kind": self.kind}


def parse_rows_params(params: Mapping[str, Any], allowed: Mapping[str, str]
                      ) -> tuple[str, str | None, str | None]:
    """(metric, group_by, group_key) từ query string. `allowed` = `{khóa chỉ số: nhãn}` mà báo
    cáo đó có danh sách. Thiếu / lạ `metric` → 422; `group_key` của nhóm gộp → 422.
    `group_by` rỗng hoặc `none` → không lọc nhóm (`group_key` bị bỏ qua)."""
    metric = (params.get("metric") or "").strip()
    if metric not in allowed:
        raise HTTPException(422, f"Chỉ số không có danh sách: {metric or '(trống)'}")
    group_by = (params.get("group_by") or "").strip() or None
    if group_by == "none":
        group_by = None
    group_key = params.get("group_key") if group_by else None
    if group_key is not None:
        group_key = str(group_key)
        if group_key == OTHER_GROUP_KEY:
            raise HTTPException(422, "Nhóm gộp «Các nhóm khác» không có danh sách riêng")
    return metric, group_by, group_key


def _norm_key(raw) -> str:
    """Cùng luật chuẩn hóa khóa của `report_compute.bucket_rows`: rỗng/0/None → `""`."""
    return "" if raw in (None, "", 0) else str(raw)


def filter_group(rows: Iterable, dim: DimensionSpec | None, group_key: str | None) -> list:
    """Giữ hàng thuộc nhóm `group_key` theo ĐÚNG `dim.key_of` mà `/summary` dùng để gom — nhờ
    vậy danh sách luôn khớp con số trên bảng. `dim` None hoặc `group_key` None → giữ hết.
    Hàng có `key_of` rỗng thuộc nhóm `""` («(Chưa gắn)»)."""
    rows = list(rows)
    if dim is None or group_key is None:
        return rows
    out = []
    for r in rows:
        keys = [_norm_key(k) for k, _label in dim.key_of(r)] or [""]
        if group_key in keys:
            out.append(r)
    return out


def _cell(v):
    """Ngày/giờ → chuỗi ISO cho JSON; còn lại giữ nguyên."""
    if isinstance(v, datetime):
        return v.isoformat()
    if isinstance(v, date):
        return v.isoformat()
    return v


def rows_response(metric_key: str, label: str, columns: list[Col], rows: list[dict]) -> dict:
    """Dựng `data` của `/summary/rows` — cắt về `ROWS_LIMIT`, `total` là số trước khi cắt."""
    total = len(rows)
    kept = rows[:ROWS_LIMIT]
    return {
        "metric": {"key": metric_key, "label": label},
        "columns": [c.as_dict() for c in columns],
        "rows": [{k: _cell(v) for k, v in r.items()} for r in kept],
        "total": total,
        "truncated": total > ROWS_LIMIT,
    }
