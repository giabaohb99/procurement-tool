"""Xuất Excel cho báo cáo kiểu Haravan — dựng cột từ `meta`, dòng `Tổng` đầu tiên + mỗi nhóm.

Dùng lại `export_xlsx.xlsx_response`/`Col`. Nhận thẳng hợp đồng JSON do `report_aggregate.
build_report` trả (không cần `ReportSpec` riêng — `meta` đã đủ nhãn/loại). Tên tệp:
`bao-cao-<slug>-<từ>-<đến>` (`xlsx_response` tự gắn thêm `-DDMMYYYY` theo ngày XUẤT, khác
với khoảng ngày của KỲ báo cáo nằm sẵn trong tên).
"""
from __future__ import annotations

from fastapi.responses import Response

from app.core.export_xlsx import Col, xlsx_response

#  Loại chỉ số của báo cáo -> loại cột Excel (`export_xlsx.Col.kind`).
_KIND_MAP = {"int": "int", "money": "money", "days": "qty", "hours": "qty", "percent": "percent"}


def _fmt_delta(cur, cmp) -> str:
    """± % so với kỳ trước, làm tròn 1 số lẻ — trống nếu kỳ trước không có/bằng 0 (chia cho 0)
    hoặc kỳ này không có dữ liệu (`cur is None` — H2, mẫu số 0 của một chỉ số dẫn xuất)."""
    if not isinstance(cur, (int, float)) or not isinstance(cmp, (int, float)) or not cmp:
        return ""
    pct = (cur - cmp) / cmp * 100
    return f"{'+' if pct >= 0 else ''}{pct:.1f}%"


def _snap_text(v) -> str:
    """Ô của chỉ số THỜI ĐIỂM (snapshot, vd công nợ còn lại — M1): chỉ có nghĩa ở dòng Tổng,
    nên cột này khai `kind="text"` — RỖNG ở mọi dòng nhóm/mốc (không phải 0), số có dấu phẩy
    nghìn ở dòng Tổng. Không dùng cột số thật vì `export_xlsx.cell_value` quy None/rỗng về 0
    cho các kind số khác (percent là ngoại lệ duy nhất, xem `export_xlsx.cell_value`)."""
    return "" if v is None else f"{v:,.0f}"


def _metric_columns(meta: dict, has_compare: bool) -> list[Col]:
    cols = []
    for m in meta["metrics"]:
        if m.get("helper"):
            continue   # chỉ số PHỤ (mẫu số/tử số của một derived) — không lên cột Excel (L4)
        kind = "text" if m.get("snapshot") else _KIND_MAP.get(m["kind"], "text")
        cols.append(Col(f"{m['key']}__cur", m["label"], kind=kind))
        if has_compare:
            cols.append(Col(f"{m['key']}__cmp", f"{m['label']} (kỳ trước)", kind=kind))
            cols.append(Col(f"{m['key']}__pct", f"{m['label']} (±%)", kind="text"))
    return cols


def _row_of(row_label: str, has_dim_col: bool, has_compare: bool,
            current: dict, compare: dict | None, meta: dict) -> dict:
    row = {"__dim__": row_label} if has_dim_col else {}
    compare = compare or {}
    for m in meta["metrics"]:
        if m.get("helper"):
            continue
        key, is_snap = m["key"], m.get("snapshot", False)
        #  `.get(key)` (KHÔNG mặc định 0): số đo THƯỜNG luôn có khóa (0 nếu rỗng dữ liệu);
        #  chỉ số dẫn xuất chia 0 giữ nguyên `None` (H2); chỉ số snapshot VẮNG khóa ở dòng
        #  nhóm/mốc (M1) — cả hai trường hợp phải phân biệt được với 0 thật.
        cur_v, cmp_v = current.get(key), compare.get(key)
        row[f"{key}__cur"] = _snap_text(cur_v) if is_snap else cur_v
        if has_compare:
            row[f"{key}__cmp"] = _snap_text(cmp_v) if is_snap else cmp_v
            row[f"{key}__pct"] = _fmt_delta(cur_v, cmp_v)
    return row


def report_xlsx(slug: str, data: dict) -> Response:
    """`data` = hợp đồng JSON của `build_report` (có `period/meta/totals/groups?`).

    Route gọi hàm này PHẢI tự gác `require(entity, 'export')` trước — xuất Excel không
    tự kiểm quyền, cùng luật với mọi đường `/export` khác trong repo.
    """
    meta = data["meta"]
    period = data["period"]
    has_compare = data["totals"].get("compare") is not None
    group_by = meta.get("group_by")
    dim_label = next((d["label"] for d in meta["dimensions"] if d["key"] == group_by), group_by) \
        if group_by else None

    columns = ([Col("__dim__", dim_label, kind="text", width=22)] if dim_label else [])
    columns += _metric_columns(meta, has_compare)

    rows = [_row_of("Tổng", bool(dim_label), has_compare,
                     data["totals"]["current"], data["totals"].get("compare"), meta)]
    for g in (data.get("groups") or []):
        rows.append(_row_of(g["label"], bool(dim_label), has_compare, g["current"], g.get("compare"), meta))

    filename = f"bao-cao-{slug}-{period['date_from']}-{period['date_to']}"
    return xlsx_response(filename, columns, rows, sheet_title="Bao cao")
