"""Sinh tệp Excel RÀ SOÁT BỘ HỒ SƠ NHẬP KHẨU để gửi Phòng Thu mua nhập khẩu — MỘT sheet.

Nguồn: `app/modules/survey_request/report_constants.py` (mẫu đang chạy thật) +
`report_model.py` (trường của một hồ sơ). Mỗi hồ sơ một khối: dòng hồ sơ rồi
danh mục trường của nó, cuối khối chừa dòng trống để ghi trường còn thiếu.
Chạy: python -X utf8 backend/scripts/gen_khao_sat_ho_so_nhap_khau.py
"""
from __future__ import annotations

import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.modules.survey_request.report_constants import (  # noqa: E402
    DEFAULT_PHASES,
    DEFAULT_TEMPLATE_DOCS,
)

OUT = ROOT / "doc" / "erp" / "nhap-khau" / "ra-soat-ho-so-nhap-khau-v2.xlsx"

FONT = "Arial"
HEAD_FILL = PatternFill("solid", fgColor="1F3864")
DOC_FILL = PatternFill("solid", fgColor="D9E2F3")     # dòng hồ sơ
CUR_FILL = PatternFill("solid", fgColor="F2F2F2")     # hiện trạng, không sửa
ASK_FILL = PatternFill("solid", fgColor="FFF2CC")     # mời điền
NEW_FILL = PatternFill("solid", fgColor="E2EFDA")     # dòng trống để thêm
EX_FILL = PatternFill("solid", fgColor="FCE4D6")      # khối ví dụ
HEAD_FONT = Font(name=FONT, size=10, bold=True, color="FFFFFF")
BASE_FONT = Font(name=FONT, size=10)
BOLD_FONT = Font(name=FONT, size=10, bold=True)
NOTE_FONT = Font(name=FONT, size=10, italic=True, color="C00000")
THIN = Side(style="thin", color="BFBFBF")
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
WRAP = Alignment(vertical="top", wrap_text=True)
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)

DOC_OPTS = '"Giữ,Sửa,Bỏ,Thêm mới"'
FIELD_OPTS = '"Bắt buộc điền,Để rỗng được,Không cần"'

#  Trường của MỘT hồ sơ mà người dùng khai được (theo report_model.SurveyReportDoc).
#  Tên + Giai đoạn nằm ngay dòng hồ sơ; Trạng thái là thao tác tick nên không hỏi.
FIELDS = [
    ("Mô tả / hướng dẫn", "Để rỗng được"),
    ("Mặt hàng áp dụng (Chung / riêng mặt hàng)", "Để rỗng được — mặc định Chung"),
    ("Tệp / link tài liệu", "Để rỗng được"),
    ("Hồ sơ phải xong trước", "Để rỗng được"),
    ("Ngày bắt đầu", "Để rỗng được"),
    ("Ngày hết hiệu lực", "Để rỗng được"),
    ("Ngày dự định hoàn tất", "Để rỗng được"),
    ("Người thực hiện", "Để rỗng được"),
]
EXTRA_ROWS = 2   # dòng trống cuối mỗi khối để ghi trường còn thiếu

HEADS = ["STT", "Giai đoạn", "Hồ sơ", "Trường / thông tin cần khai",
         "Hiện tại trên phần mềm", "Ý kiến Thu mua", "Ghi chú / đề xuất"]
WIDTHS = [6, 24, 40, 40, 40, 18, 44]


def put(ws, row, col, value, *, font=BASE_FONT, fill=None, align=WRAP):
    c = ws.cell(row=row, column=col, value=value)
    c.font = font
    c.alignment = align
    c.border = BOX
    if fill:
        c.fill = fill
    return c


def write_block(ws, r, stt, phase, title, desc, required, dep_text, dv_doc, dv_field,
                *, example=False, blank=False):
    """Một khối = dòng hồ sơ + các dòng trường + EXTRA_ROWS dòng trống. Trả về dòng kế."""
    fill_cur = EX_FILL if example else (NEW_FILL if blank else CUR_FILL)
    fill_doc = EX_FILL if example else (NEW_FILL if blank else DOC_FILL)
    bold = BOLD_FONT

    put(ws, r, 1, stt, font=bold, fill=fill_doc, align=CENTER)
    put(ws, r, 2, phase, font=bold, fill=fill_doc)
    put(ws, r, 3, title, font=bold, fill=fill_doc)
    put(ws, r, 4, desc, fill=fill_doc)
    put(ws, r, 5, "" if blank else ("Hồ sơ bắt buộc" if required else "Hồ sơ không bắt buộc"),
        fill=fill_doc)
    put(ws, r, 6, "Sửa" if example else ("Thêm mới" if blank else ""), fill=ASK_FILL, align=CENTER)
    put(ws, r, 7, "Đổi tên thành «Giấy phép tiền chất — Bộ Công An», chỉ áp cho KNO₃"
        if example else "", fill=ASK_FILL)
    dv_doc.add(ws.cell(r, 6).coordinate)
    ws.row_dimensions[r].height = 44 if desc else 22
    r += 1

    for i, (name, default) in enumerate(FIELDS):
        cur = default
        if name == "Hồ sơ phải xong trước" and dep_text:
            cur = f"Để rỗng được — mẫu đang đặt: {dep_text}"
        put(ws, r, 1, "", fill=fill_cur)
        put(ws, r, 2, "", fill=fill_cur)
        put(ws, r, 3, "", fill=fill_cur)
        put(ws, r, 4, "" if blank else name, fill=fill_cur)
        put(ws, r, 5, "" if blank else cur, fill=fill_cur)
        ex_val = ""
        ex_note = ""
        if example:
            if name.startswith("Tệp"):
                ex_val, ex_note = "Bắt buộc điền", "Phải có bản scan giấy phép mới ký được HĐ"
            elif name.startswith("Ngày hết hiệu lực"):
                ex_val, ex_note = "Bắt buộc điền", "Giấy phép có hạn, cần nhắc trước 30 ngày"
            elif name.startswith("Người thực hiện"):
                ex_val = "Để rỗng được"
        put(ws, r, 6, ex_val, fill=ASK_FILL, align=CENTER)
        put(ws, r, 7, ex_note, fill=ASK_FILL)
        dv_field.add(ws.cell(r, 6).coordinate)
        ws.row_dimensions[r].height = 30 if len(cur) > 45 else 18
        r += 1

    for _ in range(EXTRA_ROWS):
        put(ws, r, 1, "", fill=fill_cur)
        put(ws, r, 2, "", fill=fill_cur)
        put(ws, r, 3, "", fill=fill_cur)
        put(ws, r, 4, "Số giấy phép + cơ quan cấp" if example else "", fill=NEW_FILL)
        put(ws, r, 5, "Chưa có trên phần mềm", fill=NEW_FILL, font=Font(name=FONT, size=9, italic=True, color="7F7F7F"))
        put(ws, r, 6, "Bắt buộc điền" if example else "", fill=ASK_FILL, align=CENTER)
        put(ws, r, 7, "Cần tra cứu khi hải quan hỏi" if example else "", fill=ASK_FILL)
        dv_field.add(ws.cell(r, 6).coordinate)
        example = False   # chỉ dòng trống đầu của khối ví dụ có nội dung mẫu
        r += 1
    return r


def main():
    wb = Workbook()
    ws = wb.active
    ws.title = "Rà soát hồ sơ"
    ws.sheet_view.showGridLines = False
    for i, w in enumerate(WIDTHS, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w

    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=7)
    c = ws.cell(1, 1, "RÀ SOÁT BỘ HỒ SƠ NHẬP KHẨU (khối Báo cáo thực hiện trên Yêu cầu báo giá) "
                      "— 5 giai đoạn · 19 hồ sơ mẫu đang chạy trên phần mềm, xuất ngày 16/09/2026")
    c.font = Font(name=FONT, size=12, bold=True, color="1F3864")
    ws.row_dimensions[1].height = 22

    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=7)
    c = ws.cell(2, 1, "CÁCH ĐIỀN: cột xám là hiện trạng phần mềm, không sửa. Chỉ điền hai cột vàng — "
                      "dòng hồ sơ (xanh đậm) chọn Giữ / Sửa / Bỏ; dòng trường bên dưới chọn Bắt buộc điền / "
                      "Để rỗng được / Không cần; thiếu trường thì ghi vào dòng trống xanh lá cuối khối; "
                      "thiếu hồ sơ thì dùng các khối «Hồ sơ mới» ở cuối. Để trống = đồng ý giữ nguyên. "
                      "Khối VÍ DỤ màu cam ở ngay dưới là mẫu điền, bỏ qua khi tổng hợp.")
    c.font = NOTE_FONT
    c.alignment = WRAP
    ws.row_dimensions[2].height = 48

    for i, (text, _) in enumerate(zip(HEADS, WIDTHS), start=1):
        put(ws, 3, i, text, font=HEAD_FONT, fill=HEAD_FILL, align=CENTER)
    ws.row_dimensions[3].height = 30
    ws.freeze_panes = "A4"

    dv_doc = DataValidation(type="list", formula1=DOC_OPTS, allow_blank=True)
    dv_field = DataValidation(type="list", formula1=FIELD_OPTS, allow_blank=True)
    ws.add_data_validation(dv_doc)
    ws.add_data_validation(dv_field)

    titles = [d[1] for d in DEFAULT_TEMPLATE_DOCS]
    r = 4

    # Khối ví dụ: lấy hồ sơ #1 làm mẫu điền.
    p, t, d, req, deps = DEFAULT_TEMPLATE_DOCS[0]
    r = write_block(ws, r, "VD", f"{p}. {DEFAULT_PHASES[p - 1][0]}", t, d, req, "",
                    dv_doc, dv_field, example=True)

    for idx, (p, t, d, req, deps) in enumerate(DEFAULT_TEMPLATE_DOCS, start=1):
        dep_text = "; ".join(f"#{n} {titles[n - 1]}" for n in deps)
        r = write_block(ws, r, idx, f"{p}. {DEFAULT_PHASES[p - 1][0]}", t, d, req, dep_text,
                        dv_doc, dv_field)

    for i in range(5):
        r = write_block(ws, r, len(DEFAULT_TEMPLATE_DOCS) + i + 1, "", "Hồ sơ mới (ghi tên)", "",
                        True, "", dv_doc, dv_field, blank=True)

    ws.auto_filter.ref = f"A3:G{r - 1}"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUT)
    print(f"OK -> {OUT}  ({len(DEFAULT_TEMPLATE_DOCS)} ho so, {r - 1} dong)")


if __name__ == "__main__":
    main()
