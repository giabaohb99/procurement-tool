"""An toàn Ô Excel khi xuất Thuốc BVTV — review 02/10/2026:

  · H1 — bỏ ký tự điều khiển CẤM của XML (`\\x00`-`\\x08`, `\\x0b`, `\\x0c`, `\\x0e`-`\\x1f`…)
    trước khi ghi: openpyxl không tự lọc, ghi thẳng ra là tệp `.xlsx` HỎNG (Excel/LibreOffice
    báo lỗi, phải "sửa" thủ công mới mở được) — nguồn (ô chữ tự do, câu tóm tắt) có thể dính
    ký tự này.
  · C3 — chuỗi bắt đầu bằng `=`/`+`/`-`/`@` hay tab/CR: `Workbook(write_only=True).append(...)`
    cho chuỗi thường thì openpyxl TỰ suy ra đó là CÔNG THỨC (`data_type='f'`); Excel/
    LibreOffice mở ra sẽ CHẠY nó — tên thuốc/cách dùng/tóm tắt là chữ người dùng gõ tự do
    (CSV/Excel injection kinh điển). Ép `data_type='s'` qua `WriteOnlyCell` để hiện NGUYÊN
    VĂN; cùng ngưỡng ký tự với `app.core.export_xlsx._FORMULA_TRIGGER_CHARS` (không import vì
    tên đó là private của tệp kia, chép lại 6 ký tự ngắn rẻ hơn phá tính riêng tư của module).
"""
from openpyxl.cell import WriteOnlyCell
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE

_FORMULA_TRIGGER_CHARS = ("=", "+", "-", "@", "\t", "\r")


def safe_cell(ws, value):
    """Một GIÁ TRỊ của `list_row`/`use_rows` → giá trị AN TOÀN để `ws.append([...])`.

    Không phải chuỗi (số, ngày, `None`) thì trả nguyên — hai rủi ro trên chỉ có ở chuỗi.
    """
    if not isinstance(value, str):
        return value
    cleaned = ILLEGAL_CHARACTERS_RE.sub("", value)
    if cleaned[:1] in _FORMULA_TRIGGER_CHARS:
        cell = WriteOnlyCell(ws, value=cleaned)
        cell.data_type = "s"
        return cell
    return cleaned


def safe_row(ws, row: list) -> list:
    return [safe_cell(ws, v) for v in row]
