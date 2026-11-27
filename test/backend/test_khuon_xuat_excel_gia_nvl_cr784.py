"""Khuôn tệp Excel của cụm Giá nguyên vật liệu sản xuất theo bản mẫu HTML (duoc-CR-784, 23/11/2026).

Soi thẳng `write_report_sheet`: tiêu đề + dòng phụ + vạch xanh, đầu cột navy / xanh lá, định dạng số kiểu bản mẫu, ô
trống không thành 0, màu tăng XANH giảm ĐỎ (ngược bản mẫu, theo luật chung của cụm), khổ in A4 ngang.
"""
from datetime import date
from decimal import Decimal

from openpyxl import Workbook

from app.core.export_xlsx import Col
from app.modules.packaging_cost.report_xlsx_writer import (DOWN_COLOR, FMT_DATE, FMT_DEC, FMT_INT, FMT_PCT, GREEN_DARK,
                                                          LIME, NAVY, UP_COLOR, Group, bold_tone, change_tone, sign_tone,
                                                          write_report_sheet)

COLS = [Col("code", "Mã"), Col("day", "Ngày", "date"), Col("qty", "Số\nlượng", "qty"), Col("price", "Đơn giá", "price"),
        Col("old", "Giá cũ", "price"), Col("diff", "Chênh", "price"), Col("pct", "%", "percent"), Col("n", "Số lần", "int")]
ROWS = [
    {"code": "CPT0075", "day": "2025-10-07", "qty": Decimal("12000"), "price": Decimal("700"), "old": 623, "diff": 77,
     "pct": 0.1236, "n": 3},
    {"code": "NAP0056", "day": None, "qty": None, "price": Decimal("85.5"), "old": 90, "diff": -4.5, "pct": -0.05, "n": 0},
    {"code": "=CMD()", "day": "2026-01-01", "qty": 1, "price": None, "old": None, "diff": 0, "pct": None, "n": None},
]


def _sheet(**kw):
    ws = Workbook().active
    head = write_report_sheet(ws, subject="Lịch sử mua hàng", note="3 mã", columns=COLS, rows=ROWS,
                              tones={"price": change_tone("price", "old", "bold"), "diff": sign_tone("diff"),
                                     "pct": sign_tone("pct"), "n": bold_tone}, freeze_cols=1, **kw)
    return ws, head


def _color(cell) -> str:
    return (cell.font.color.rgb or "")[-6:] if cell.font.color is not None else ""


def test_tieu_de_dong_phu_vach_xanh_va_dau_cot_nhu_ban_mau():
    ws, head = _sheet()
    assert head == 4
    assert ws["A1"].value == "BÁO CÁO GIÁ NGUYÊN VẬT LIỆU SẢN XUẤT — LỊCH SỬ MUA HÀNG"
    assert ws["A1"].font.b and ws["A1"].font.sz == 14 and _color(ws["A1"]) == NAVY
    assert ws["A2"].font.i and "Phòng Thu mua · Xuất ngày" in ws["A2"].value and ws["A2"].value.endswith("· 3 mã")
    assert all(ws.cell(row=3, column=i).fill.fgColor.rgb[-6:] == LIME for i in range(1, len(COLS) + 1))
    assert ws["C4"].value == "Số\nlượng" and ws["C4"].fill.fgColor.rgb[-6:] == NAVY and _color(ws["C4"]) == "FFFFFF"
    assert ws.freeze_panes == "B5" and ws.auto_filter.ref == "A4:H7"


def test_dinh_dang_so_ngay_phan_tram_va_o_trong_khong_thanh_0():
    ws, _ = _sheet()
    qty, price, pct, day, n = ws["C5"], ws["D6"], ws["G5"], ws["B5"], ws["H5"]
    assert qty.value == 12000 and qty.number_format == FMT_INT          # số tròn: không lẻ
    assert price.value == 85.5 and price.number_format == FMT_DEC       # số lẻ: hai chữ số lẻ
    assert pct.value == 0.1236 and pct.number_format == FMT_PCT         # tỷ số, Excel tự hiện 12,4%
    assert day.value == date(2025, 10, 7) and day.number_format == FMT_DATE
    assert n.number_format == FMT_INT
    #  Ô chưa có số để TRỐNG, không phải 0 (0 đồng đọc nhầm thành "giá bằng không").
    assert ws["D7"].value is None and ws["G7"].value is None and ws["H7"].value is None and ws["B6"].value is None
    assert ws["F7"].value == 0                                           # 0 thật vẫn là 0 (định dạng hiện "-")


def test_mau_tang_do_giam_xanh_va_dam_navy():
    ws, _ = _sheet()
    assert (UP_COLOR, DOWN_COLOR) == ("C0392B", "0B6A3A")                  # tăng đỏ, giảm xanh (người chủ chốt 27/11/2026)
    assert _color(ws["D5"]) == UP_COLOR and ws["D5"].font.b             # 700 > 623: tăng = đỏ
    assert _color(ws["D6"]) == DOWN_COLOR                               # 85,5 < 90: giảm = xanh
    assert _color(ws["F5"]) == UP_COLOR and _color(ws["F6"]) == DOWN_COLOR
    assert not ws["F7"].font.b                                          # chênh 0: không tô
    assert _color(ws["H5"]) == NAVY and ws["H5"].font.b
    assert ws["A5"].border.left.style == "thin"


def test_o_chu_mo_dau_bang_dau_bang_van_la_chu_sau_khi_boc_so():
    from app.core.export_xlsx import guard_workbook
    ws, _ = _sheet()
    guard_workbook(ws.parent)
    assert ws["A7"].data_type == "s" and ws["A7"].value == "=CMD()"


def test_hang_nhom_gop_o_va_cot_xen_ke_nen_xanh_la():
    ws = Workbook().active
    head = write_report_sheet(ws, subject="Giá 5 lần", columns=COLS, rows=ROWS[:1],
                              groups=[Group("THÔNG TIN", 2), Group("LẦN 1", 3), Group("LẦN 2", 3, True)],
                              alt_keys={"old", "diff", "pct"}, freeze_cols=2)
    assert head == 5 and ws.freeze_panes == "C6"
    assert {"A4:B4", "C4:E4", "F4:H4"} <= {str(m) for m in ws.merged_cells.ranges}
    assert ws["F4"].value == "LẦN 2" and ws["F4"].fill.fgColor.rgb[-6:] == GREEN_DARK
    assert ws["E5"].fill.fgColor.rgb[-6:] == GREEN_DARK and ws["D5"].fill.fgColor.rgb[-6:] == NAVY


def test_kho_in_a4_ngang_lap_hang_tieu_de_va_chan_trang():
    ws, _ = _sheet()
    assert ws.page_setup.orientation == "landscape" and int(ws.page_setup.paperSize) == 9
    assert ws.sheet_properties.pageSetUpPr.fitToPage and ws.page_setup.fitToWidth == 1 and ws.page_setup.fitToHeight == 0
    assert ws.print_title_rows == "$4:$4" and not ws.sheet_view.showGridLines
    assert "Trang &P / &N" in ws.oddFooter.center.text


def test_khong_co_dong_nao_thi_khong_bat_bo_loc_va_van_co_tieu_de():
    ws = Workbook().active
    write_report_sheet(ws, subject="Bảng giá", columns=COLS, rows=[])
    assert ws["A1"].value.endswith("BẢNG GIÁ") and ws.auto_filter.ref is None and ws["A4"].value == "Mã"
