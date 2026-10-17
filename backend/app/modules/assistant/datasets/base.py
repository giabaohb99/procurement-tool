"""Khuôn SỔ BỘ DỮ LIỆU cho AI (ai-CR-210, K12 — tầng T2 của doc/erp/21 §5.5).

Mỗi bộ dữ liệu khai MỘT lần: đo được gì (`Measure`) × chia theo gì (`Dimension`) × lọc được gì (`Filter`), cùng model,
entity gác quyền, entity phạm vi (`apply_scope`) và khóa báo cáo nếu có. Máy chủ tự tính trong phạm vi quyền người hỏi rồi
trả bảng nhỏ. KHÔNG có đường sinh SQL: model chỉ chọn TÊN chỉ số / chiều / bộ lọc trong danh sách đã khai — biểu thức SQL
nằm sẵn ở đây.

Trần: tối đa `MAX_MEASURES` chỉ số, `MAX_DIMENSIONS` chiều, `MAX_GROUPS` (500) nhóm một lượt — vượt trần trả `truncated`
kèm gợi ý lọc hẹp.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Callable

from sqlalchemy import func, select

from app.core.scoping import apply_scope

MAX_GROUPS = 500
DEFAULT_LIMIT = 50
MAX_MEASURES = 4
MAX_DIMENSIONS = 2
TEXT_MAX_LEN = 100
_DATE_RX = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SORTS = ("value_desc", "value_asc", "dimension")


@dataclass(frozen=True)
class Measure:
    key: str
    label: str
    expr: Callable[[], Any]           # biểu thức SQL gộp (sum / count / avg…) — dựng mỗi lượt
    kind: str = "money"               # money | int | qty | price
    vat: str = ""                     # "sau VAT" / "trước VAT" — chỉ ghi khi đã soi công thức
    unit: str = ""


@dataclass(frozen=True)
class Dimension:
    key: str
    label: str
    code: Callable[[], Any]                               # cột nhóm (mã)
    name: Callable[[], Any] | None = None                 # cột tên đi kèm (lấy max theo nhóm)
    labels: dict | None = None                            # mã → nhãn cố định (trạng thái…)
    lookup: Callable[[Any, set], dict] | None = None      # (db, các mã) → {mã: nhãn} sau truy vấn (pháp nhân, phòng ban)
    needs: tuple[str, ...] = ()                           # entity phải có quyền read mới được chia theo chiều này


@dataclass(frozen=True)
class Filter:
    key: str
    label: str
    apply: Callable[[Any, Any], Any]      # (query, giá trị đã kiểm) → query
    kind: str = "text"                    # text | date | int | enum | bool
    enum: tuple = ()


@dataclass(frozen=True)
class Dataset:
    key: str
    label: str
    description: str
    model: Any
    entity: str                            # quyền read phải có
    scope_entity: str | None               # entity `apply_scope` (None = bảng không có khóa phạm vi, xem ghi chú bộ)
    measures: tuple[Measure, ...]
    dimensions: tuple[Dimension, ...]
    filters: tuple[Filter, ...]
    report_key: Any = None                 # ReportKey nếu bộ này trùng số liệu của một báo cáo (duoc-CR-562)
    base: Callable[[Any], Any] | None = None
    link: str = ""
    currency: str = "VND"
    notes: tuple[str, ...] = field(default_factory=tuple)

    def measure(self, key: str) -> Measure | None:
        return next((m for m in self.measures if m.key == key), None)

    def dimension(self, key: str) -> Dimension | None:
        return next((d for d in self.dimensions if d.key == key), None)

    def filter(self, key: str) -> Filter | None:
        return next((f for f in self.filters if f.key == key), None)

    def describe(self) -> dict:
        return {"dataset": self.key, "label": self.label, "description": self.description, "currency": self.currency,
                "measures": [_measure_meta(m) for m in self.measures],
                "dimensions": [{"key": d.key, "label": d.label} for d in self.dimensions],
                "filters": [{"key": f.key, "label": f.label, "kind": f.kind, **({"enum": list(f.enum)} if f.enum else {})}
                            for f in self.filters],
                "notes": list(self.notes)}


def _measure_meta(m: Measure) -> dict:
    out = {"key": m.key, "label": m.label, "kind": m.kind}
    if m.vat:
        out["vat"] = m.vat
    if m.unit:
        out["unit"] = m.unit
    return out


def _value(m: Measure, raw):
    if m.kind == "int":
        return int(raw or 0)
    if raw is None:
        return 0 if m.kind != "price" else None
    return round(float(raw), 3 if m.kind == "qty" else 2)


def _as_list(raw) -> list[str]:
    if raw is None or raw == "":
        return []
    items = raw if isinstance(raw, (list, tuple)) else str(raw).split(",")
    return [str(x).strip().lower() for x in items if str(x).strip()]


def _check_value(f: Filter, raw) -> tuple[Any, str | None]:
    if f.kind == "date":
        text = str(raw).strip()
        if not _DATE_RX.match(text):
            return None, f"{f.key} phải dạng YYYY-MM-DD"
        try:
            date.fromisoformat(text)
        except ValueError:
            return None, f"{f.key} không phải ngày có thật"
        return text, None
    if f.kind == "int":
        try:
            return int(raw), None
        except (TypeError, ValueError):
            return None, f"{f.key} phải là số nguyên"
    if f.kind == "enum":
        text = str(raw).strip()
        if text not in f.enum:
            return None, f"{f.key} chỉ nhận: {', '.join(f.enum)}"
        return text, None
    if f.kind == "bool":
        return str(raw).strip().lower() in ("1", "true", "yes", "co", "có"), None
    return str(raw).strip()[:TEXT_MAX_LEN], None


def _denied(what: str) -> dict:
    return {"denied": True, "error": what}


def run(ctx, ds: Dataset, args: dict) -> dict:
    """Chạy một truy vấn tổng hợp trên bộ `ds` dưới quyền người hỏi (`ctx`). Trả dict theo chuẩn §5.6."""
    if not ctx.can(ds.entity):
        return _denied(f"Không có quyền xem «{ds.label}» (cần quyền đọc {ds.entity}) — nhờ quản trị gán vai trò.")
    if ds.report_key is not None:
        from app.core.report_keys import REPORT_META
        from app.modules.report_access.service import can_view_report

        if not can_view_report(ctx.db, ctx.user, ds.report_key):
            return _denied(f"Chưa được giao xem báo cáo «{REPORT_META[ds.report_key][0]}» — nhờ quản trị gán ở Phân quyền "
                           "tài khoản → tab Báo cáo.")

    m_keys = _as_list(args.get("measures")) or [ds.measures[0].key]
    d_keys = [k for k in _as_list(args.get("dimensions")) if k != "none"]
    if len(m_keys) > MAX_MEASURES or len(d_keys) > MAX_DIMENSIONS:
        return {"error": f"Tối đa {MAX_MEASURES} chỉ số và {MAX_DIMENSIONS} chiều mỗi lượt."}
    bad_m = [k for k in m_keys if ds.measure(k) is None]
    bad_d = [k for k in d_keys if ds.dimension(k) is None]
    if bad_m or bad_d:
        return {"error": "Không có " + "; ".join(
            ([f"chỉ số {', '.join(bad_m)} (chọn: {', '.join(m.key for m in ds.measures)})"] if bad_m else [])
            + ([f"chiều {', '.join(bad_d)} (chọn: {', '.join(d.key for d in ds.dimensions)})"] if bad_d else []))}
    measures = [ds.measure(k) for k in dict.fromkeys(m_keys)]
    dims = [ds.dimension(k) for k in dict.fromkeys(d_keys)]
    for d in dims:
        missing = [e for e in d.needs if not ctx.can(e)]
        if missing:
            return _denied(f"Chia «{ds.label}» theo {d.label} cần thêm quyền đọc {', '.join(missing)}.")

    raw_filters = args.get("filters") if isinstance(args.get("filters"), dict) else {}
    applied, ignored = {}, []
    for k, v in raw_filters.items():
        f = ds.filter(str(k))
        if f is None:
            ignored.append(str(k))
            continue
        if v is None or v == "":
            continue
        value, err = _check_value(f, v)
        if err:
            return {"error": f"Bộ lọc sai: {err}."}
        applied[f.key] = value

    sort = str(args.get("sort") or "value_desc").strip().lower()
    if sort not in SORTS:
        sort = "value_desc"
    try:
        limit = max(1, min(int(args.get("limit") or DEFAULT_LIMIT), MAX_GROUPS))
    except (TypeError, ValueError):
        limit = DEFAULT_LIMIT

    def scoped(q):
        q = q.select_from(ds.model)
        if ds.scope_entity:
            q = apply_scope(q, ds.model, ds.scope_entity, ctx.user, ctx.profile)
        if ds.base is not None:
            q = ds.base(q)
        for key, value in applied.items():
            q = ds.filter(key).apply(q, value)
        return q

    m_exprs = [m.expr() for m in measures]
    totals_row = scoped(ctx.db.query(*m_exprs)).one()
    out = {"dataset": ds.key, "label": ds.label, "currency": ds.currency,
           "measures": [_measure_meta(m) for m in measures],
           "dimensions": [{"key": d.key, "label": d.label} for d in dims],
           "filters": applied, "totals": {m.key: _value(m, v) for m, v in zip(measures, totals_row)}}
    if ds.link:
        out["link"] = ds.link
    if ignored:
        out["ignored_filters"] = ignored
        out["allowed_filters"] = [f.key for f in ds.filters]
    if not dims:
        return out

    codes = [d.code() for d in dims]
    names = [func.max(d.name()) for d in dims if d.name is not None]
    grouped = scoped(ctx.db.query(*codes, *names, *m_exprs)).group_by(*codes)
    total = ctx.db.scalar(select(func.count()).select_from(grouped.subquery())) or 0
    first = m_exprs[0]
    order = {"value_asc": [first.asc()], "dimension": [c.asc() for c in codes]}.get(sort, [first.desc()])
    rows = grouped.order_by(*order).limit(limit).all()

    resolved: list[dict] = []
    for d_i, d in enumerate(dims):
        if d.lookup is not None:
            resolved.append(d.lookup(ctx.db, {r[d_i] for r in rows}))
        else:
            resolved.append(d.labels or {})
    items = []
    for r in rows:
        item, name_i = {}, len(dims)
        for d_i, d in enumerate(dims):
            code = r[d_i]
            label = resolved[d_i].get(code)
            if d.name is not None:
                label = label or r[name_i]
                name_i += 1
            item[d.key] = code
            item[f"{d.key}_label"] = label if label not in (None, "") else (code if code not in (None, "") else "(Chưa gắn)")
        for m_i, m in enumerate(measures):
            item[m.key] = _value(m, r[len(dims) + len(names) + m_i])
        items.append(item)
    out.update(rows=items, total=int(total), returned=len(items), has_more=total > len(items), sort=sort)
    if total > len(items):
        out["truncated"] = True
        out["note"] = (f"Có {total} nhóm, mới trả {len(items)}. Thêm bộ lọc (kỳ ngắn hơn, một NCC / pháp nhân) hoặc tăng "
                       f"limit (tối đa {MAX_GROUPS}).")
    return out
