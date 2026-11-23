"""Vẽ một sheet Excel theo ĐÚNG khuôn của bản mẫu HTML "Báo cáo giá NVL sản xuất" (người chủ chốt 23/11/2026).

Khuôn (chép từ hàm `XL.save` của bản mẫu):
  dòng 1  tiêu đề "BÁO CÁO GIÁ NGUYÊN VẬT LIỆU SẢN XUẤT — <TÊN BÁO CÁO>", đậm 14, màu navy;
  dòng 2  dòng phụ nghiêng xám: "Dego Holding – Phòng Thu mua · Xuất ngày dd/mm/yyyy · Đơn vị: VNĐ, giá chưa VAT · ...";
  dòng 3  vạch xanh lá mảnh;
  (tùy chọn) hàng nhóm cột gộp ô; rồi hàng tiêu đề cột nền navy chữ trắng (cột "alt" nền xanh lá đậm);
  dữ liệu: viền mảnh xám xanh, số có dấu nghìn, âm màu đỏ, bằng 0 hiện "-", phần trăm 0.0%, ngày dd/mm/yyyy;
  ô "tăng" / "giảm" tô màu chữ đậm, ô "bold" đậm navy. Cố định hàng tiêu đề + vài cột đầu, bật bộ lọc,
  khổ A4 ngang vừa một trang chiều ngang, lặp hàng tiêu đề khi in, chân trang "Trang x / y", không kẻ lưới.

Khác bản mẫu ở MỘT chỗ có chủ đích: màu tăng / giảm theo luật chung của cụm (tăng = XANH, giảm = ĐỎ — người chủ chốt
20/11/2026); bản mẫu tô tăng đỏ.

Phần trăm (`kind="percent"`) nhận TỶ SỐ (0.125 = 12,5%) — đúng như API trả, Excel tự nhân 100 khi hiện.
Ô chữ mở đầu bằng = + - @ không bị chạy như công thức: người gọi bọc sổ bằng `guard_workbook` trước khi lưu.
"""
from collections.abc import Callable
from datetime import date, datetime
from decimal import Decimal
from typing import Any, NamedTuple

from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from app.core.export_xlsx import VN_OFFSET, Col

TITLE_PREFIX = "BÁO CÁO GIÁ NGUYÊN VẬT LIỆU SẢN XUẤT — "
FONT_NAME = "Montserrat"
NAVY, GREEN_DARK, LIME, GRID = "0F3B6E", "0B6A3A", "7FD148", "D0D7E2"
UP_COLOR, DOWN_COLOR = "0B6A3A", "C0392B"           # tăng xanh, giảm đỏ (luật màu chung của cụm)

FMT_INT = '#,##0;[Red]-#,##0;"-"'
FMT_DEC = '#,##0.00;[Red]-#,##0.00;"-"'
FMT_PCT = '0.0%;[Red]-0.0%;"-"'
FMT_DATE = "dd/mm/yyyy"
NUMBER_KINDS = ("int", "qty", "price", "money", "decimal", "percent")

#  Một hàm nhận DÒNG, trả "up" | "down" | "bold" | None — quyết định màu chữ của ô.
ToneRule = Callable[[dict], str | None]


class Group(NamedTuple):
    """Một ô nhóm trên hàng tiêu đề, gộp `span` cột; `alt` = nền xanh lá đậm thay vì navy."""

    label: str
    span: int
    alt: bool = False


def tone_of(value: Any) -> str | None:
    """Chiều của một con số: dương "up", âm "down", 0 / trống không tô."""
    if value is None or value == "":
        return None
    v = float(value)
    if abs(v) < 1e-9:
        return None
    return "up" if v > 0 else "down"


def sign_tone(key: str) -> ToneRule:
    """Tô theo dấu của chính ô `key` (cột chênh lệch, phần trăm)."""
    return lambda row: tone_of(row.get(key))


def change_tone(new_key: str, old_key: str, fallback: str | None = None) -> ToneRule:
    """Tô theo chiều `new - old` (giá mới so giá cũ); thiếu một đầu thì dùng `fallback`."""
    def rule(row: dict) -> str | None:
        new, old = row.get(new_key), row.get(old_key)
        if new is None or old is None:
            return fallback
        return tone_of(float(new) - float(old)) or fallback
    return rule


def bold_tone(_row: dict) -> str:
    return "bold"


def build_subtitle(extra: str = "") -> str:
    today = (datetime.utcnow() + VN_OFFSET).strftime("%d/%m/%Y")
    base = f"Dego Holding – Phòng Thu mua · Xuất ngày {today} · Đơn vị: VNĐ, giá chưa VAT"
    return f"{base} · {extra}" if extra else base


def _font(bold: bool = False, italic: bool = False, size: float = 10, color: str | None = None) -> Font:
    return Font(name=FONT_NAME, bold=bold, italic=italic, size=size, color=color)


_SIDE = Side(style="thin", color=GRID)
_BORDER = Border(left=_SIDE, right=_SIDE, top=_SIDE, bottom=_SIDE)
_HEAD_ALIGN = Alignment(horizontal="center", vertical="center", wrap_text=True)
_TONE_FONT = {None: _font(), "up": _font(bold=True, color=UP_COLOR), "down": _font(bold=True, color=DOWN_COLOR),
              "bold": _font(bold=True, color=NAVY)}


def _fill(color: str) -> PatternFill:
    return PatternFill("solid", fgColor=color)


def _head_cell(ws, row: int, col: int, label: str | None, alt: bool) -> None:
    c = ws.cell(row=row, column=col, value=label)
    c.font, c.fill, c.border, c.alignment = _font(bold=True, color="FFFFFF"), _fill(GREEN_DARK if alt else NAVY), _BORDER, _HEAD_ALIGN


def _number(value: Any) -> float | int | None:
    if value is None or value == "":
        return None
    v = float(value) if isinstance(value, Decimal) else value
    return v if isinstance(v, (int, float)) else None


def _to_date(value: Any):
    if isinstance(value, (datetime, date)) or not value:
        return value or None
    try:
        return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
    except ValueError:
        return str(value)


def _write_cell(ws, r: int, i: int, col: Col, row: dict, tone: str | None) -> None:
    raw = row.get(col.key)
    c = ws.cell(row=r, column=i)
    c.border, c.font = _BORDER, _TONE_FONT.get(tone, _TONE_FONT[None])
    if col.kind == "date":
        c.value = _to_date(raw)
        c.number_format, c.alignment = FMT_DATE, Alignment(horizontal="center", vertical="center")
        return
    number = _number(raw) if col.kind in NUMBER_KINDS else None
    if number is None:
        #  Ô số chưa có giá để TRỐNG (không phải 0) — 0 đồng đọc nhầm thành "giá bằng không".
        c.value = None if col.kind in NUMBER_KINDS else ("" if raw is None else str(raw)) or None
        c.alignment = Alignment(vertical="center")
        return
    c.value = number
    if col.kind == "percent":
        c.number_format = FMT_PCT
    elif col.kind == "int":
        c.number_format = FMT_INT
    else:   # giá, số lượng, tiền: có số lẻ thì hai chữ số lẻ, số tròn thì không lẻ (như bản mẫu)
        c.number_format = FMT_DEC if abs(number - round(number)) > 1e-9 else FMT_INT
    c.alignment = Alignment(vertical="center")


def write_report_sheet(ws, *, subject: str, columns: list[Col], rows: list[dict], note: str = "",
                       alt_keys: frozenset[str] | set[str] = frozenset(), groups: list[Group] | None = None,
                       tones: dict[str, ToneRule] | None = None, freeze_cols: int = 0) -> int:
    """Vẽ trọn sheet theo khuôn bản mẫu; trả về SỐ HÀNG của hàng tiêu đề cột (dữ liệu bắt đầu ngay dưới)."""
    n = max(len(columns), 1)
    tones = tones or {}
    ws.cell(row=1, column=1, value=TITLE_PREFIX + subject.upper()).font = _font(bold=True, size=14, color=NAVY)
    ws.row_dimensions[1].height = 24
    ws.cell(row=2, column=1, value=build_subtitle(note)).font = _font(italic=True, size=9, color="5A5A5A")
    ws.row_dimensions[3].height = 4
    for i in range(1, n + 1):
        ws.cell(row=3, column=i).fill = _fill(LIME)
    head = 4
    if groups:
        start = 1
        for g in groups:
            for k in range(g.span):
                _head_cell(ws, head, start + k, g.label if k == 0 else None, g.alt)
            if g.span > 1:
                ws.merge_cells(start_row=head, start_column=start, end_row=head, end_column=start + g.span - 1)
            start += g.span
        ws.row_dimensions[head].height = 20
        head += 1
    for i, col in enumerate(columns, start=1):
        _head_cell(ws, head, i, col.label, col.key in alt_keys)
        ws.column_dimensions[get_column_letter(i)].width = col.width
    ws.row_dimensions[head].height = 32
    for r, row in enumerate(rows, start=head + 1):
        for i, col in enumerate(columns, start=1):
            rule = tones.get(col.key)
            _write_cell(ws, r, i, col, row, rule(row) if rule else None)
    last = head + len(rows)
    ws.freeze_panes = f"{get_column_letter(freeze_cols + 1)}{head + 1}"
    if rows:
        ws.auto_filter.ref = f"A{head}:{get_column_letter(n)}{last}"
    _setup_page(ws, head)
    return head


def _setup_page(ws, head_row: int) -> None:
    ws.sheet_view.showGridLines = False
    ws.sheet_properties.tabColor = NAVY
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth, ws.page_setup.fitToHeight = 1, 0
    ws.page_margins.left = ws.page_margins.right = 0.4
    ws.page_margins.top = ws.page_margins.bottom = 0.6
    ws.print_title_rows = f"{head_row}:{head_row}"
    ws.oddHeader.right.text, ws.oddHeader.right.size = "DEGO HOLDING – Phòng Thu mua", 8
    ws.oddFooter.center.text, ws.oddFooter.center.size = "Trang &P / &N", 8
