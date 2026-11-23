"""Cột + dựng tệp Excel cho cụm Giá nguyên vật liệu sản xuất (duoc-CR-784): Tác động giá (hai sheet), Tổng hợp theo sản
phẩm, Bảng giá VTBB, Giá mua gần nhất, Lịch sử mua hàng.

Mọi sheet vẽ theo khuôn của bản mẫu HTML (tiêu đề, dòng phụ, vạch xanh, đầu cột navy, số có định dạng, ô tăng / giảm tô
màu, in A4 ngang) — xem `report_xlsx_writer.py`. Nhãn tiếng Việt chỉ ở tầng hiển thị này (API trả mã số). Phần trăm ghi
TỶ SỐ, Excel tự hiện dạng 12,5%. Ô chữ mở đầu bằng = + - @ bị ép về chuỗi (chống công thức Excel).
"""
from datetime import datetime
from io import BytesIO

from fastapi.responses import Response
from openpyxl import Workbook

from app.core.export_xlsx import VN_OFFSET, Col, check_row_limit, guard_workbook
from app.core.packaging_price_codes import (COST_TREND_LABELS, COST_WARNING_LABELS, PACKAGING_ROLE_LABELS,
                                            PRICE_SOURCE_TYPE_LABELS, CostTrend, CostWarning, PackagingRole, PriceSourceType)

from .last_prices_service import flatten_for_export
from .report_xlsx_writer import Group, bold_tone, change_tone, sign_tone, write_report_sheet

XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

PRICE_LIST_COLUMNS = [
    Col("code", "Mã VTBB", width=11), Col("name", "Tên vật tư", width=44), Col("group", "Nhóm", width=12),
    Col("unit", "ĐVT", width=7), Col("old", "Giá cũ", "price", 11), Col("new", "Giá mới", "price", 11),
    Col("diff", "Chênh lệch", "price", 11), Col("pct", "%", "percent", 9),
    Col("last_purchase_price", "Giá mua\ngần nhất", "price", 11), Col("last_purchase_date", "Mua gần nhất", "date", 12),
    Col("prev_purchase_price", "Giá mua\nlần trước", "price", 11), Col("usage", "Số SP\nđang dùng", "int", 9),
    Col("purchase_count", "Số lần\nmua", "int", 8), Col("last_date", "Ngày mua cuối", "date", 12),
    Col("min", "Giá thấp nhất", "price", 11), Col("max", "Giá cao nhất", "price", 11), Col("floor", "Ngưỡng sàn", "price", 11),
    Col("ceiling", "Ngưỡng trần", "price", 11), Col("quote_price", "Báo giá mới", "price", 11),
    Col("quote_from", "Ngày hiệu lực\nbáo giá", "date", 12), Col("warn_text", "Cảnh báo", width=34),
]
#  Màu chữ: giá mới đậm navy, chênh lệch / phần trăm tăng xanh giảm đỏ (cùng luật với màn hình).
_DIFF_TONES = {"diff": sign_tone("diff"), "pct": sign_tone("pct")}


def warning_text(kinds) -> str:
    return "; ".join(COST_WARNING_LABELS[CostWarning(int(k))] for k in kinds)


def price_list_rows(rows: list[dict]) -> list[dict]:
    """Bổ sung chữ cảnh báo cho dòng bảng giá."""
    return [{**r, "warn_text": warning_text(r["warnings"])} for r in rows]


def _save(wb: Workbook) -> bytes:
    buf = BytesIO()
    guard_workbook(wb).save(buf)
    return buf.getvalue()


def _selected_columns() -> list[Col]:
    return [Col("code", "Mã", width=11), Col("name", "Tên vật tư", width=40), Col("group", "Nhóm", width=12),
            Col("unit", "ĐVT", width=7), Col("old", "Giá cũ", "price", 11), Col("new", "Giá mới\n(bảng giá)", "price", 11),
            Col("assumed", "Giá giả định", "price", 11), Col("applied", "Giá áp dụng", "price", 11),
            Col("diff", "Chênh lệch", "price", 11), Col("pct", "%", "percent", 9),
            Col("usage", "Số SP\nđang dùng", "int", 9), Col("warn_text", "Cảnh báo", width=34)]


def _product_columns(new_word: str = "áp dụng") -> tuple[list[Col], set[str], dict]:
    """Cột + khóa cột thành phần (đầu cột xanh lá như bản mẫu) + luật màu của bảng sản phẩm.

    `new_word` = chữ gọi giá sau: "áp dụng" ở Tác động giá (có giá giả định), "mới" ở Tổng hợp theo sản phẩm.
    """
    cols = [Col("hh_code", "Mã HH", width=11), Col("hh_name", "Tên hàng hoá", width=48),
            Col("legal_name", "Tên pháp lý", width=22), Col("carton_qty", "Quy cách\nthùng", "int", 9)]
    alt, tones = set(), {}
    for role in PackagingRole:
        label, r = PACKAGING_ROLE_LABELS[role].lower(), int(role)
        per_carton = "\n(/thùng)" if role in (PackagingRole.CARTON_LABEL, PackagingRole.CARTON) else ""
        cols += [Col(f"code_{r}", f"Mã {label}", width=11), Col(f"old_{r}", f"Giá {label} cũ{per_carton}", "price", 11),
                 Col(f"applied_{r}", f"Giá {label} {new_word}{per_carton}", "price", 11)]
        alt |= {f"code_{r}", f"old_{r}", f"applied_{r}"}
        tones[f"applied_{r}"] = change_tone(f"applied_{r}", f"old_{r}")
    cols += [Col("cost_old_bottle", "CP bao bì/chai\ncũ", "price", 13), Col("cost_applied_bottle", "CP bao bì/chai\nmới", "price", 13),
             Col("diff_bottle", "Tăng/giảm\n/chai", "price", 11), Col("pct", "%", "percent", 9),
             Col("diff_carton", "Tăng/giảm\n/thùng", "price", 12), Col("trend_text", "Trạng thái", width=13),
             Col("warn_text", "Ghi chú", width=34)]
    tones |= {"cost_applied_bottle": bold_tone, "diff_bottle": sign_tone("diff_bottle"), "pct": sign_tone("pct"),
              "diff_carton": sign_tone("diff_carton"), "trend_text": sign_tone("diff_bottle")}
    return cols, alt, tones


def _flat_product(p: dict) -> dict:
    row = {**p, "trend_text": COST_TREND_LABELS[CostTrend(p["trend"])]}
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


def _count(n: float) -> str:
    """Số kiểu Việt cho dòng phụ: 1234 -> "1.234", 85.5 -> "85,5" (giá giả định lẻ tới phần đồng)."""
    text = f"{n:,.0f}" if float(n).is_integer() else f"{n:,.2f}".rstrip("0")
    return text.replace(",", "_").replace(".", ",").replace("_", ".")


def _describe_selected(selected: list[dict]) -> str:
    parts = [f"{s['code']} (giả định {_count(s['assumed'])})" if s.get("assumed") is not None else s["code"]
             for s in selected]
    return "Mã đã chọn: " + ", ".join(parts) if parts else "Chưa chọn mã"


def build_impact_workbook(result: dict) -> bytes:
    """Hai sheet: "Sản phẩm bị ảnh hưởng" (đầu, như bản mẫu) và "Mã đã chọn". Trần số dòng như mọi lần xuất khác."""
    check_row_limit(max(len(result["selected"]), len(result["products"])))
    note = _describe_selected(result["selected"])
    wb = Workbook()
    ws = wb.active
    ws.title = "Sản phẩm bị ảnh hưởng"
    cols, alt, tones = _product_columns()
    write_report_sheet(ws, subject="Tác động tăng giá bao bì", note=f"{note} · {_count(len(result['products']))} sản phẩm",
                       columns=cols, rows=[_flat_product(p) for p in result["products"]], alt_keys=alt, tones=tones,
                       freeze_cols=2)
    sel = [{**s, "warn_text": warning_text(s["warnings"])} for s in result["selected"]]
    write_report_sheet(wb.create_sheet("Mã đã chọn"), subject="Tác động tăng giá bao bì — mã đã chọn", note=note,
                       columns=_selected_columns(), rows=sel, tones={"applied": bold_tone, **_DIFF_TONES}, freeze_cols=1)
    return _save(wb)


def build_product_overview_workbook(rows: list[dict]) -> bytes:
    """Một sheet "Tổng hợp theo sản phẩm": cùng cột với bảng sản phẩm của Tác động giá (giá sau gọi là "mới")."""
    check_row_limit(len(rows))
    wb = Workbook()
    ws = wb.active
    ws.title = "Tổng hợp theo sản phẩm"
    cols, alt, tones = _product_columns("mới")
    write_report_sheet(ws, subject="Tổng hợp giá bao bì theo sản phẩm",
                       note=f"{_count(len(rows))} sản phẩm · CP/chai = chai + nắp + nhãn + (nhãn thùng + thùng) ÷ quy cách thùng",
                       columns=cols, rows=[_flat_product(p) for p in rows], alt_keys=alt,
                       tones=tones, freeze_cols=2)
    return _save(wb)


def build_price_list_workbook(rows: list[dict]) -> bytes:
    check_row_limit(len(rows))
    wb = Workbook()
    ws = wb.active
    ws.title = "Bảng giá VTBB"
    write_report_sheet(ws, subject="Bảng giá vật tư bao bì & nguyên liệu",
                       note=f"{_count(len(rows))} mã · Có báo giá mới: mới = báo giá, cũ = giá mua gần nhất · Không có: so 2 lần mua "
                            "có giá gần nhất", columns=PRICE_LIST_COLUMNS, rows=price_list_rows(rows),
                       tones={"new": bold_tone, **_DIFF_TONES}, freeze_cols=2)
    return _save(wb)


def _last_price_layout(n: int, show_qty: bool) -> tuple[list[Col], list[Group], set[str], dict]:
    """Cột + hàng nhóm (THÔNG TIN VTBB · LẦN k · BIẾN ĐỘNG · GIÁ TB, lần chẵn nền xanh lá) + luật màu, như bản mẫu."""
    cols = [Col("code", "Mã VTBB", width=11), Col("name", "Tên vật tư", width=42), Col("group", "Nhóm", width=11),
            Col("unit", "ĐVT", width=6), Col("purchase_count", "Số lần\ncó giá", "int", 8)]
    groups, alt, tones = [Group("THÔNG TIN VTBB", 5)], set(), {}
    for k in range(1, n + 1):
        part = [Col(f"p{k}_date", "Ngày mua", "date", 11), Col(f"p{k}_supplier", "Nhà cung cấp", width=26)]
        if show_qty:
            part.append(Col(f"p{k}_qty", "Số lượng", "qty", 10))
        part.append(Col(f"p{k}_price", "Đơn giá", "price", 11))
        even = k % 2 == 0
        groups.append(Group(f"LẦN {k}" + (" (gần nhất)" if k == 1 else ""), len(part), even))
        if even:
            alt |= {c.key for c in part}
        #  Đơn giá: xanh = cao hơn lần trước nó, đỏ = thấp hơn, không đổi / lần cuối thì đậm navy.
        tones[f"p{k}_price"] = change_tone(f"p{k}_price", f"p{k + 1}_price", "bold") if k < n else bold_tone
        cols += part
    cols += [Col("v12", "Lần 1 so\nlần 2", "percent", 10), Col("v1n", f"Lần 1 so\nlần {n}", "percent", 10),
             Col("avg", f"Giá TB\n{n} lần", "price", 12)]
    groups += [Group("BIẾN ĐỘNG", 2), Group("GIÁ TB", 1)]
    tones |= {"v12": sign_tone("v12"), "v1n": sign_tone("v1n"), "avg": bold_tone}
    return cols, groups, alt, tones


def build_last_prices_workbook(rows: list[dict], n: int = 5, show_qty: bool = False) -> bytes:
    """Một sheet "Giá mua gần nhất": n lần (tùy chọn kèm số lượng), theo đúng bộ lọc + thứ tự đang xem."""
    check_row_limit(len(rows))
    wb = Workbook()
    ws = wb.active
    ws.title = f"Giá {n} lần gần nhất"
    cols, groups, alt, tones = _last_price_layout(n, show_qty)
    write_report_sheet(ws, subject=f"Lịch sử giá {n} lần mua gần nhất",
                       note=f"{_count(len(rows))} mã · Lần 1 = lần mua có đơn giá gần nhất · Đơn giá xanh = cao hơn lần trước, đỏ = "
                            "thấp hơn · Giá TB = trung bình cộng các lần đang hiện",
                       columns=cols, rows=[flatten_for_export(r, n) for r in rows], groups=groups, alt_keys=alt,
                       tones=tones, freeze_cols=2)
    return _save(wb)


def _history_columns(product_mode: bool) -> list[Col]:
    cols = [Col("date", "Ngày mua", "date", 12), Col("code", "Mã VTBB", width=11), Col("name", "Tên vật tư", width=40)]
    if product_mode:
        cols.append(Col("role_text", "Thành phần", width=12))
    return cols + [Col("supplier_code", "Mã NCC", width=12), Col("supplier", "Nhà cung cấp", width=36),
                   Col("warehouse", "Kho", width=20), Col("unit", "ĐVT", width=7),
                   Col("qty", "Số lượng", "qty", 11), Col("price", "Đơn giá", "price", 11), Col("vat", "VAT (%)", "decimal", 8),
                   Col("amount", "Giá trị mua", "money", 15), Col("diff", "Chênh lệch so\nlần có giá trước", "price", 14),
                   Col("pct", "%", "percent", 9), Col("source_text", "Nguồn", width=16), Col("po_code", "Số ĐMH", width=14)]


def build_history_workbook(rows: list[dict], product_mode: bool = False) -> bytes:
    """Một sheet "Lịch sử mua hàng": cùng bộ lọc + thứ tự đang xem; chế độ sản phẩm thêm cột Thành phần của mã."""
    check_row_limit(len(rows))
    flat = [{**r, "role_text": ", ".join(PACKAGING_ROLE_LABELS[PackagingRole(x)] for x in r["roles"]),
             "source_text": PRICE_SOURCE_TYPE_LABELS[PriceSourceType(r["source_type"])]} for r in rows]
    codes = len({r["code"] for r in rows})
    wb = Workbook()
    ws = wb.active
    ws.title = "Lịch sử mua hàng"
    write_report_sheet(ws, subject="Lịch sử mua hàng theo sản phẩm" if product_mode else "Lịch sử mua hàng",
                       note=f"{_count(codes)} mã · {_count(len(rows))} lần mua", columns=_history_columns(product_mode),
                       rows=flat, tones={"price": bold_tone, **_DIFF_TONES}, freeze_cols=3)
    return _save(wb)
