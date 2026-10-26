"""bao-CR-662 — tệp GTT02 hải quan xuất dạng HTML hoặc XML (SpreadsheetML) nhưng đặt đuôi .xls.

Sự cố 26/10/2026 trên prod: nạp 7 tệp .xls, bị từ chối «không phải Excel» vì chữ ký đầu tệp không
phải OLE2 hay ZIP. Excel vẫn mở được các tệp đó. Bộ đọc nay nhận thêm hai dạng này, mọi ô đọc thành
chữ; luật từng ô đã biết đọc ngày và số từ chữ nên kết quả phải trùng với tệp .xlsx thật.
"""
from datetime import date
from html import escape

import pytest

from app.modules.customs import reader
from app.modules.customs.constants import COLUMNS

from test_hai_quan_cot_tuy_chon_tep_nap_cr603 import ROW, _xlsx

HEADERS = list(COLUMNS)


def _cell_text(v) -> str:
    return "" if v is None else str(v)


def _html(rows: list[dict], headers=HEADERS) -> bytes:
    head = "".join(f"<td>{escape(label)}</td>" for _, label in headers)
    body = "".join("<tr>" + "".join(f"<td>{escape(_cell_text(r.get(k)))}</td>" for k, _ in headers) + "</tr>"
                   for r in rows)
    page = (f"<html><head><meta charset='utf-8'></head><body><table border=1>"
            f"<tr>{head}</tr>{body}</table></body></html>")
    return page.encode("utf-8")


def _spreadsheetml(rows: list[dict], headers=HEADERS) -> bytes:
    ns = 'xmlns="urn:schemas-microsoft-com:office:spreadsheet" xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet"'

    def row_xml(values):
        return "<Row>" + "".join(f'<Cell><Data ss:Type="String">{escape(_cell_text(v))}</Data></Cell>' for v in values) + "</Row>"

    xml = (f'<?xml version="1.0"?><Workbook {ns}><Worksheet ss:Name="GTT02"><Table>'
           + row_xml([label for _, label in headers])
           + "".join(row_xml([r.get(k) for k, _ in headers]) for r in rows)
           + "</Table></Worksheet></Workbook>")
    return xml.encode("utf-8")


def _first_row(raw: bytes) -> dict:
    res = reader.parse(raw, today=date(2026, 10, 26))
    assert len(res.rows) == 1, res.errors
    return res.rows[0]


def test_html_gia_xls_doc_duoc_va_trung_voi_xlsx_that():
    reader.check_headers(_html([ROW]), "1.xls")
    got = _first_row(_html([ROW]))
    expected = _first_row(_xlsx([ROW], HEADERS))
    for key in ("reg_date", "hs_code", "importer_tax_code", "product_name", "quantity", "price_usd", "transport_mode"):
        assert got[key] == expected[key], key


def test_spreadsheetml_gia_xls_doc_duoc():
    raw = _spreadsheetml([ROW])
    reader.check_headers(raw, "2.xls")
    got = _first_row(raw)
    assert got["product_name"] == ROW["product_name"]
    assert got["reg_date"] == date(2026, 1, 13)


def test_html_co_bom_va_khoang_trang_dau_van_nhan():
    raw = b"\xef\xbb\xbf\r\n  " + _html([ROW])
    reader.check_headers(raw, "3.xls")


def test_html_khong_co_bang_thi_bao_ro():
    with pytest.raises(reader.CustomsFileError, match="không có bảng"):
        reader.load_cells(b"<html><body>khong co gi</body></html>", "4.xls")


def test_tep_la_van_bi_tu_choi_kem_huong_dan():
    with pytest.raises(reader.CustomsFileError, match="lưu lại dạng .xlsx"):
        reader.load_cells(b"hoat chat,ham luong\n1,2\n", "5.xls")
