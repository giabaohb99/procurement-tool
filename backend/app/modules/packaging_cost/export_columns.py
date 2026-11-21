"""Cột + dựng tệp Excel cho màn Giá bao bì (duoc-CR-784, phase 04): Bảng giá VTBB và Tác động giá (hai sheet).

Nhãn tiếng Việt chỉ ở tầng hiển thị này (API trả mã số). Ô chữ mở đầu bằng = + - @ bị ép về chuỗi (chống công thức Excel).
"""
from datetime import datetime
from io import BytesIO

from fastapi.responses import Response
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from app.core.export_xlsx import HEAD_BG, HEAD_TEXT, VN_OFFSET, Col, cell_value, check_row_limit, guard_workbook
from app.core.packaging_price_codes import (COST_TREND_LABELS, COST_WARNING_LABELS, PACKAGING_ROLE_LABELS,
                                            PRICE_SOURCE_TYPE_LABELS, CostTrend, CostWarning, PackagingRole, PriceSourceType)

from .last_prices_service import flatten_for_export

XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

PRICE_LIST_COLUMNS = [
    Col("code", "Mã VTBB", width=14), Col("name", "Tên vật tư", width=40), Col("group", "Nhóm", width=14),
    Col("unit", "ĐVT", width=8), Col("old", "Giá cũ", "price"), Col("new", "Giá mới", "price"),
    Col("diff", "Chênh lệch", "price"), Col("pct_view", "% chênh", "percent", 10),
    Col("last_purchase_price", "Giá mua gần nhất", "price"), Col("last_purchase_date", "Mua gần nhất", "date"),
    Col("prev_purchase_price", "Giá mua lần trước", "price"), Col("usage", "Số SP dùng", "int", 10),
    Col("purchase_count", "Số lần mua", "int", 10), Col("last_date", "Ngày mua cuối", "date"),
    Col("min", "Giá thấp nhất", "price"), Col("max", "Giá cao nhất", "price"), Col("floor", "Ngưỡng sàn", "price"),
    Col("ceiling", "Ngưỡng trần", "price"), Col("quote_price", "Giá báo giá", "price"),
    Col("quote_from", "Báo giá từ ngày", "date"), Col("warn_text", "Cảnh báo", width=36),
]


def warning_text(kinds) -> str:
    return "; ".join(COST_WARNING_LABELS[CostWarning(int(k))] for k in kinds)


def price_list_rows(rows: list[dict]) -> list[dict]:
    """Bổ sung hai cột hiển thị (% theo thang 0–100, chữ cảnh báo) cho dòng bảng giá."""
    return [{**r, "pct_view": None if r["pct"] is None else r["pct"] * 100, "warn_text": warning_text(r["warnings"])}
            for r in rows]


def _write(ws, columns: list[Col], rows: list[dict]) -> None:
    head_font, head_fill = Font(bold=True, color=HEAD_TEXT), PatternFill("solid", fgColor=HEAD_BG)
    for i, col in enumerate(columns, start=1):
        c = ws.cell(row=1, column=i, value=col.label)
        c.font, c.fill = head_font, head_fill
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws.column_dimensions[get_column_letter(i)].width = col.width
    for r, row in enumerate(rows, start=2):
        for i, col in enumerate(columns, start=1):
            #  Ô số chưa có giá để TRỐNG (không phải 0) — 0 đồng đọc nhầm thành "giá bằng không".
            blank = row.get(col.key) is None and col.kind not in ("text", "bool")
            ws.cell(row=r, column=i, value=None if blank else cell_value(col, row))
    ws.freeze_panes = "A2"


def _selected_columns() -> list[Col]:
    return [Col("code", "Mã", width=14), Col("name", "Tên vật tư", width=40), Col("group", "Nhóm", width=14),
            Col("unit", "ĐVT", width=8), Col("old", "Giá cũ", "price"), Col("new", "Giá mới (bảng giá)", "price"),
            Col("assumed", "Giá giả định", "price"), Col("applied", "Giá áp dụng", "price"),
            Col("diff", "Chênh lệch", "price"), Col("pct_view", "% chênh", "percent", 10),
            Col("usage", "Số SP dùng", "int", 10), Col("warn_text", "Cảnh báo", width=36)]


def _product_columns(new_word: str = "áp dụng") -> list[Col]:
    """`new_word` = chữ gọi giá sau: "áp dụng" ở Tác động giá (có giá giả định), "mới" ở Tổng hợp theo sản phẩm."""
    cols = [Col("hh_code", "Mã HH", width=14), Col("hh_name", "Tên hàng hóa", width=44),
            Col("legal_name", "Tên pháp lý", width=30), Col("carton_qty", "Quy cách thùng", "int", 12)]
    for role in PackagingRole:
        label = PACKAGING_ROLE_LABELS[role].lower()
        cols += [Col(f"code_{int(role)}", f"Mã {label}", width=12), Col(f"old_{int(role)}", f"Giá {label} cũ", "price"),
                 Col(f"applied_{int(role)}", f"Giá {label} {new_word}", "price")]
    return cols + [Col("cost_old_bottle", "CP bao bì/chai cũ", "price"), Col("cost_applied_bottle", "CP bao bì/chai mới", "price"),
                   Col("diff_bottle", "Tăng/giảm /chai", "price"), Col("diff_carton", "Tăng/giảm /thùng", "price"),
                   Col("pct_view", "% chênh", "percent", 10), Col("trend_text", "Xu hướng", width=14),
                   Col("warn_text", "Ghi chú", width=40)]


def _flat_product(p: dict) -> dict:
    row = {**p, "pct_view": None if p["pct"] is None else p["pct"] * 100,
           "trend_text": COST_TREND_LABELS[CostTrend(p["trend"])]}
    for part in p["parts"]:
        r = part["role"]
        row[f"code_{r}"], row[f"old_{r}"], row[f"applied_{r}"] = part["code"], part["old"], part["applied"]
    texts = []
    for w in p["warnings"]:
        label = COST_WARNING_LABELS[CostWarning(w["kind"])]
        texts.append(f"{label} ({PACKAGING_ROLE_LABELS[PackagingRole(w['role'])].lower()})" if "role" in w else label)
    row["warn_text"] = "; ".join(texts)
    return row


def _stamped(name: str) -> str:
    return f"{name}-{(datetime.utcnow() + VN_OFFSET).strftime('%d%m%Y')}.xlsx"


def xlsx_download(data: bytes, name: str) -> Response:
    return Response(content=data, media_type=XLSX, headers={"Content-Disposition": f'attachment; filename="{_stamped(name)}"'})


def build_impact_workbook(result: dict) -> bytes:
    """Hai sheet: "Mã đã chọn" và "Sản phẩm bị ảnh hưởng". Trần số dòng như mọi lần xuất khác."""
    check_row_limit(max(len(result["selected"]), len(result["products"])))
    wb = Workbook()
    ws = wb.active
    ws.title = "Mã đã chọn"
    sel = [{**s, "pct_view": None if s["pct"] is None else s["pct"] * 100, "warn_text": warning_text(s["warnings"])}
           for s in result["selected"]]
    _write(ws, _selected_columns(), sel)
    _write(wb.create_sheet("Sản phẩm bị ảnh hưởng"), _product_columns(), [_flat_product(p) for p in result["products"]])
    buf = BytesIO()
    guard_workbook(wb).save(buf)
    return buf.getvalue()


def build_product_overview_workbook(rows: list[dict]) -> bytes:
    """Một sheet "Tổng hợp theo sản phẩm": cùng cột với bảng sản phẩm của Tác động giá (giá sau gọi là "mới")."""
    check_row_limit(len(rows))
    wb = Workbook()
    ws = wb.active
    ws.title = "Tổng hợp theo sản phẩm"
    _write(ws, _product_columns("mới"), [_flat_product(p) for p in rows])
    buf = BytesIO()
    guard_workbook(wb).save(buf)
    return buf.getvalue()


def build_price_list_workbook(rows: list[dict]) -> bytes:
    check_row_limit(len(rows))
    wb = Workbook()
    ws = wb.active
    ws.title = "Bảng giá VTBB"
    _write(ws, PRICE_LIST_COLUMNS, price_list_rows(rows))
    buf = BytesIO()
    guard_workbook(wb).save(buf)
    return buf.getvalue()


def _last_price_columns(n: int, show_qty: bool) -> list[Col]:
    cols = [Col("code", "Mã VTBB", width=14), Col("name", "Tên vật tư", width=40), Col("group", "Nhóm", width=14),
            Col("unit", "ĐVT", width=8), Col("purchase_count", "Số lần có giá", "int", 10)]
    for k in range(1, n + 1):
        tag = f"Lần {k}" + (" (gần nhất)" if k == 1 else "")
        cols += [Col(f"p{k}_date", f"{tag} - Ngày mua", "date"), Col(f"p{k}_supplier", f"{tag} - Nhà cung cấp", width=26)]
        if show_qty:
            cols.append(Col(f"p{k}_qty", f"{tag} - Số lượng", "qty"))
        cols.append(Col(f"p{k}_price", f"{tag} - Đơn giá", "price"))
    return cols + [Col("v12_view", "Lần 1 so lần 2 (%)", "percent", 12), Col("v1n_view", f"Lần 1 so lần {n} (%)", "percent", 12),
                   Col("avg", f"Giá TB {n} lần", "price")]


def build_last_prices_workbook(rows: list[dict], n: int = 5, show_qty: bool = False) -> bytes:
    """Một sheet "Giá mua gần nhất": cùng thứ tự cột như màn hình (n lần, tùy chọn kèm số lượng), theo đúng bộ lọc + thứ tự đang xem."""
    check_row_limit(len(rows))
    wb = Workbook()
    ws = wb.active
    ws.title = "Giá mua gần nhất"
    _write(ws, _last_price_columns(n, show_qty), [flatten_for_export(r, n) for r in rows])
    buf = BytesIO()
    guard_workbook(wb).save(buf)
    return buf.getvalue()


def _history_columns(product_mode: bool) -> list[Col]:
    cols = [Col("date", "Ngày mua", "date"), Col("code", "Mã VTBB", width=14), Col("name", "Tên vật tư", width=40)]
    if product_mode:
        cols.append(Col("role_text", "Vai trò", width=14))
    return cols + [Col("supplier_code", "Mã NCC", width=12), Col("supplier", "Nhà cung cấp", width=28), Col("unit", "ĐVT", width=8),
                   Col("qty", "Số lượng", "qty"), Col("price", "Đơn giá", "price"), Col("vat", "VAT (%)", "decimal", 9),
                   Col("amount", "Thành tiền", "money"), Col("diff", "Chênh so lần trước", "price"),
                   Col("pct_view", "% chênh", "percent", 10), Col("source_text", "Nguồn", width=20),
                   Col("po_code", "Số ĐMH", width=14)]


def build_history_workbook(rows: list[dict], product_mode: bool = False) -> bytes:
    """Một sheet "Lịch sử mua hàng": cùng bộ lọc + thứ tự đang xem; chế độ sản phẩm thêm cột Vai trò của mã thành phần."""
    check_row_limit(len(rows))
    flat = [{**r, "pct_view": None if r["pct"] is None else r["pct"] * 100,
             "role_text": ", ".join(PACKAGING_ROLE_LABELS[PackagingRole(x)] for x in r["roles"]),
             "source_text": PRICE_SOURCE_TYPE_LABELS[PriceSourceType(r["source_type"])]} for r in rows]
    wb = Workbook()
    ws = wb.active
    ws.title = "Lịch sử mua hàng"
    _write(ws, _history_columns(product_mode), flat)
    buf = BytesIO()
    guard_workbook(wb).save(buf)
    return buf.getvalue()
