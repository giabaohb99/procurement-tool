"""Xuất / nạp CSV danh mục (CRUD) — và chặn chèn công thức (bao-CR-726 / BM-033).

CSV không có kiểu ô: Excel mở tệp là tự hiểu ô mở đầu bằng = + - @ (hay tab / CR) là CÔNG THỨC. Nên khi xuất, ô
CHUỖI nguy hiểm được thêm một dấu `'` ở đầu (cách OWASP khuyên — Excel hiện nguyên văn). Để xuất -> sửa -> nạp lại
không đổi dữ liệu, mọi bộ nạp CSV danh mục đi qua `unescape_row`, gỡ đúng dấu đó.

Luật thoát (đảo ngược được với mọi chuỗi):
- xuất: chuỗi mở đầu bằng ký tự công thức HOẶC bằng `'` -> thêm `'` ở đầu;
- nạp: chuỗi mở đầu bằng `'` mà ký tự kế là ký tự công thức hoặc `'` -> bỏ một dấu `'`.
Chuỗi gốc mở đầu bằng `'` cũng được thoát, nên `'abc` xuất ra `''abc` và nạp lại vẫn là `'abc`. Ô số (int, float,
Decimal) KHÔNG thoát — số âm vẫn là số.
"""
import csv
from io import StringIO

from fastapi.responses import Response

from app.core.export_xlsx import _FORMULA_TRIGGER_CHARS

_QUOTE = "'"
_ESCAPED_NEXT = (*_FORMULA_TRIGGER_CHARS, _QUOTE)


def csv_escape(value: str) -> str:
    """Ô chữ xuất ra CSV: thêm `'` trước ô mở đầu bằng ký tự công thức hoặc `'`."""
    return _QUOTE + value if value[:1] in _ESCAPED_NEXT else value


def csv_unescape(value):
    """Ngược của `csv_escape` cho một ô vừa đọc từ tệp (giữ nguyên ô không phải chuỗi, vd None khi dòng thiếu cột)."""
    if isinstance(value, str) and value[:1] == _QUOTE and value[1:2] in _ESCAPED_NEXT:
        return value[1:]
    return value


def unescape_row(row: dict) -> dict:
    """Một dòng của `csv.DictReader` đã gỡ dấu thoát — dùng ở MỌI bộ nạp CSV đọc tệp do `export_csv_response` xuất."""
    return {k: csv_unescape(v) for k, v in row.items()}


def _cell(value) -> str:
    if value is None:
        return ""
    return csv_escape(str(value)) if isinstance(value, str) else str(value)


def export_csv_response(items, headers_map, filename):
    output = StringIO()

    writer = csv.writer(output)
    writer.writerow(list(headers_map.values()) + ["Trạng thái"])

    for item in items:
        row = [_cell(getattr(item, field, "")) for field in headers_map]
        is_active = getattr(item, "is_active", True)
        row.append("Hoạt động" if is_active else "Đã ẩn")
        writer.writerow(row)

    headers = {"Content-Disposition": f"attachment; filename={filename}.csv"}
    return Response(content=output.getvalue().encode("utf-8-sig"), media_type="text/csv; charset=utf-8", headers=headers)
