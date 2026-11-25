"""Tệp mẫu (.xlsx) cho ba loại nhập Excel của cụm Giá NVL sản xuất (duoc-CR-784): định mức bao bì, báo giá VTBB, Sổ Misa.

Tải qua `GET /api/imports/template?module=4|5|6`. Mỗi tệp: sheet DỮ LIỆU (chỉ có dòng tiêu đề, đúng chữ bộ đọc nhận) + sheet
"Hướng dẫn" (giải thích từng cột + bảng ví dụ). Bảng ví dụ đặt từ dòng 10 trở xuống vì bộ đọc Sổ Misa quét mọi sheet nhưng chỉ
tìm dòng tiêu đề trong 6 dòng đầu — để nguyên tệp mẫu mà bấm nhập thì không nạp nhầm dòng ví dụ.
"""
from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from app.modules.import_tool.model import ImportModule

NAVY, LIME = "0F3B6E", "7FD148"
_HEAD_FONT = Font(name="Montserrat", bold=True, color="FFFFFF")
_HEAD_FILL = PatternFill("solid", fgColor=NAVY)
_EXAMPLE_ROW = 10

#  (tiêu đề cột, bề rộng, giải thích) — tiêu đề phải khớp chữ bộ đọc nhận (`quote_import.COLUMNS`, `misa_xlsx_import.COLUMNS`).
QUOTE_COLUMNS = [
    ("Mã VTBB", 14, "Bắt buộc. Mã vật tư bao bì, phải có trong danh mục sản phẩm (vd CPT0075)."),
    ("Đơn giá", 14, "Bắt buộc, lớn hơn 0. VNĐ CHƯA VAT, theo đơn vị tính của danh mục."),
    ("Ngày hiệu lực", 16, "Bắt buộc. Ngày báo giá bắt đầu áp dụng (dd/mm/yyyy). Ngày ở tương lai vẫn tính ngay là giá mới."),
    ("Mã NCC", 14, "Không bắt buộc. Mã nhà cung cấp trong danh mục; bỏ trống nếu chưa rõ."),
    ("VAT (%)", 10, "Không bắt buộc. Ghi 8 nghĩa là 8% (ghi 0,08 cũng hiểu là 8%)."),
    ("Ghi chú", 40, "Không bắt buộc, tối đa 500 ký tự."),
]
QUOTE_EXAMPLE = [["CPT0075", 2650, "01/12/2026", "NCC0185", 8, "Báo giá qua Zalo ngày 20/11"],
                 ["NAP0056", 700, "01/12/2026", "", 8, ""]]

MISA_COLUMNS = [
    ("Ngày hạch toán", 14, "Bắt buộc. Ngày của lần mua (dd/mm/yyyy hoặc ô ngày của Excel)."),
    ("Mã nhà cung cấp", 16, "Mã NCC trong Misa."),
    ("Tên nhà cung cấp", 36, "Tên NCC; đuôi ' - VTBB' tự bỏ."),
    ("Tên kho", 22, "Kho nhập hàng, hiện ở cột Kho của Lịch sử mua hàng."),
    ("Mã hàng", 12, "Bắt buộc. Mã vật tư; mã đầu PPA / CKC / CPM / CPN bị bỏ qua."),
    ("Tên hàng", 40, "Tên vật tư (chỉ để đối chiếu)."),
    ("ĐVT", 8, "Đơn vị tính."),
    ("Số lượng", 12, "Bắt buộc, khác 0; dòng số lượng 0 bị bỏ qua."),
    ("Đơn giá", 12, "Bắt buộc có cột. VNĐ chưa VAT; trống hoặc 0 vẫn nhận (đếm lần mua, không làm giá)."),
    ("Giá trị", 14, "Thành tiền của lần mua, hiện ở cột Giá trị mua của Lịch sử mua hàng; trống / 0 thì dùng đơn giá x số lượng. Nạp lại cùng tệp sẽ bổ sung thành tiền cho dòng đã nạp."),
]
MISA_EXAMPLE = [["17/01/2025", "NCC38", "CÔNG TY CỔ PHẦN PHL - VTBB", "KHO NCC_HÀ LONG", "CET0028",
                 "Chai PAPE tròn cổ 43 240,250ml (40gr) logo IDA màu trắng", "Cái", 12000, 4724, 56688000]]

BOM_COLUMNS = [            # đúng vị trí A..K của sheet MAP_SP (`bom_import.run`); G, H để trống
    ("Mã chai", 12, "Bắt buộc. Mã chai trong danh mục sản phẩm."),
    ("Mã nắp", 12, "Mã nắp; bỏ trống nếu sản phẩm không dùng nắp."),
    ("Mã HH", 12, "Bắt buộc. Mã hàng hóa; đã có thì cập nhật, chưa có thì tạo. HH0417.1 và HH417.1 coi là một."),
    ("Tên hàng hóa", 44, "Tên sản phẩm."),
    ("Tên pháp lý", 24, "Tên pháp lý (không bắt buộc)."),
    ("Quy cách thùng", 12, "Số chai một thùng (số nguyên); 0 = chưa có."),
    ("(để trống)", 6, "Cột G — không dùng."),
    ("(để trống)", 6, "Cột H — không dùng."),
    ("Mã nhãn", 12, "Mã nhãn (tính theo chai)."),
    ("Mã nhãn thùng", 14, "Mã nhãn thùng (giá tính cho cả thùng)."),
    ("Mã thùng", 12, "Mã thùng (giá tính cho cả thùng)."),
]
BOM_EXAMPLE = [["CPT0075", "NAP0057", "HH0313.1", "LOT IDA Global - I - 313.1 - Chlorpyrifos", "Pro-tin 480EC", 40, None, None,
                "NHG0313", "NDT0010", "THU0021"]]


def _head(ws, row: int, columns) -> None:
    for i, (label, width, _) in enumerate(columns, start=1):
        c = ws.cell(row=row, column=i, value=label)
        c.font, c.fill = _HEAD_FONT, _HEAD_FILL
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws.column_dimensions[get_column_letter(i)].width = width
    ws.row_dimensions[row].height = 24
    ws.freeze_panes = f"A{row + 1}"


def _guide(wb, title: str, steps: list[str], columns, example) -> None:
    ws = wb.create_sheet("Hướng dẫn")
    ws.cell(row=1, column=1, value=title).font = Font(name="Montserrat", bold=True, size=14, color=NAVY)
    for i, text in enumerate(steps, start=2):
        ws.cell(row=i, column=1, value=text).font = Font(name="Montserrat", size=10)
    ws.column_dimensions["A"].width = 24
    ws.column_dimensions["B"].width = 100
    start = _EXAMPLE_ROW
    ws.cell(row=start - 1, column=1, value="Giải thích từng cột").font = Font(name="Montserrat", bold=True, color=NAVY)
    for i, (label, _, note) in enumerate(columns):
        ws.cell(row=start + i, column=1, value=label).font = Font(name="Montserrat", bold=True)
        ws.cell(row=start + i, column=2, value=note)
    ex = start + len(columns) + 2
    ws.cell(row=ex - 1, column=1, value="Ví dụ (KHÔNG nhập sheet này — chép sang sheet dữ liệu)").font = Font(
        name="Montserrat", bold=True, color=NAVY)
    for j, (label, _, _) in enumerate(columns, start=1):
        c = ws.cell(row=ex, column=j, value=label)
        c.font, c.fill = Font(name="Montserrat", bold=True), PatternFill("solid", fgColor=LIME)
    for r, values in enumerate(example, start=ex + 1):
        for j, v in enumerate(values, start=1):
            ws.cell(row=r, column=j, value=v)


def _save(wb) -> bytes:
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


def build_quote_template() -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Báo giá VTBB"
    _head(ws, 1, QUOTE_COLUMNS)
    _guide(wb, "NHẬP BÁO GIÁ VTBB TỪ EXCEL", [
        "1. Điền mỗi báo giá một dòng ở sheet Báo giá VTBB (giữ nguyên dòng tiêu đề).",
        "2. Ở màn Bảng giá VTBB bấm Nhập báo giá, chọn tệp, bấm Chạy thử: hệ thống chưa ghi gì, chỉ liệt kê sẽ thêm / sửa gì.",
        "3. Xem nhật ký ở trang lô Quản lý Import; đúng thì bấm Ghi thật.",
        "Trùng mã VTBB + mã NCC + ngày hiệu lực với báo giá đã có thì cập nhật đơn giá, VAT, ghi chú; chưa có thì thêm mới.",
    ], QUOTE_COLUMNS, QUOTE_EXAMPLE)
    return _save(wb)


def build_misa_template() -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Sổ chi tiết mua hàng"
    _head(ws, 1, MISA_COLUMNS)
    _guide(wb, "NẠP SỔ CHI TIẾT MUA HÀNG MISA", [
        "1. Xuất Sổ chi tiết mua hàng từ Misa ra Excel (giữ nguyên tiêu đề cột của Misa) hoặc dán vào sheet Sổ chi tiết mua hàng.",
        "2. Ở màn Lịch sử mua hàng bấm Nạp sổ Misa, chọn tệp, bấm Chạy thử; xem nhật ký rồi bấm Ghi thật.",
        "Chỉ thay dữ liệu Misa TRONG khoảng ngày của tệp (dòng trùng giữ nguyên, dòng mới thêm, dòng không còn thì bỏ); ngoài khoảng giữ nguyên.",
        "Mốc sổ Misa = ngày lớn nhất đã nạp: tới mốc giá lấy từ Misa, sau mốc lấy từ đơn mua hàng trên ERP.",
    ], MISA_COLUMNS, MISA_EXAMPLE)
    return _save(wb)


def build_bom_template() -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "MAP_SP"
    ws.cell(row=1, column=1, value="ĐỊNH MỨC BAO BÌ THEO MÃ HÀNG HÓA (MAP_SP)").font = Font(name="Montserrat", bold=True, size=13,
                                                                                         color=NAVY)
    ws.cell(row=2, column=1, value="Điền từ dòng 5. Giữ nguyên 4 dòng đầu và thứ tự cột A–K.").font = Font(
        name="Montserrat", italic=True, size=9)
    _head(ws, 4, BOM_COLUMNS)
    _guide(wb, "NHẬP ĐỊNH MỨC BAO BÌ", [
        "1. Điền mỗi mã hàng hóa (mã HH) một dòng ở sheet MAP_SP, từ dòng 5.",
        "2. Ở màn Định mức bao bì bấm Nhập từ Excel, chọn tệp, bấm Chạy thử; xem nhật ký rồi bấm Ghi thật.",
        "Mã HH đã có thì cập nhật, chưa có thì tạo; định mức đang có mà không nằm trong tệp được giữ nguyên.",
        "Cũng nhận tệp DATA_CHAI.xlsx dạng hai sheet data + DATA CHUNG như trước.",
    ], BOM_COLUMNS, BOM_EXAMPLE)
    return _save(wb)


TEMPLATES = {
    ImportModule.PACKAGING_BOM: ("mau-nhap-dinh-muc-bao-bi", build_bom_template),
    ImportModule.PACKAGING_QUOTE: ("mau-nhap-bao-gia-vtbb", build_quote_template),
    ImportModule.PACKAGING_MISA: ("mau-nap-so-misa", build_misa_template),
}
