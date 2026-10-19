"""LUẬT THUẦN của biến mẫu HĐLĐ (duoc-CR-630): kiểm mã, chuẩn hóa giá trị theo kiểu, định dạng khi in.

Không DB, không HTTP — test rẻ. Thông báo lỗi bằng tiếng Việt và KHÔNG chép lại GIÁ TRỊ người dùng
nhập (giá trị có thể nhạy cảm như lương): chỉ nêu quy tắc.

Dạng CHUẨN lưu trong `custom_values` / `default_value` theo kiểu:
    TEXT/MULTILINE  chuỗi đã dọn · NUMBER  «1234.5» (dấu chấm thập phân, không ngăn nghìn)
    DATE  «YYYY-MM-DD» · MONEY  chuỗi chữ số «15000000»
Dạng IN ra tệp (`format_value`): ngày «dd/mm/yyyy», tiền «15.000.000», số «1.234,5».
"""
import keyword
import re
from datetime import date
from decimal import Decimal, InvalidOperation

from app.core.labor_contract_codes import LaborContractVariableType as T
from app.modules.labor_contract.context_builder import fmt_date, fmt_money
from app.modules.labor_contract.placeholder_catalog import KNOWN_KEYS

MAX_CUSTOM_VARIABLES = 100
MAX_CUSTOM_VALUES_CHARS = 20_000
MAX_TEXT, MAX_MULTILINE = 255, 2000
MONEY_MAX = 10**12
YEAR_MIN, YEAR_MAX = 1900, 2100
MONEY_WORD_SUFFIX = "_bang_chu"

CODE_RE = re.compile(r"^[a-z][a-z0-9_]{1,39}$")
_NUMBER_RE = re.compile(r"^\d{1,13}(\.\d{1,2})?$")
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_DIGITS_RE = re.compile(r"^\d{1,13}$")

#  Tên Jinja / Python có nghĩa riêng — đặt làm biến sẽ render sai hoặc bị sandbox chặn.
RESERVED: frozenset[str] = frozenset(w.lower() for w in keyword.kwlist) | frozenset({
    "true", "false", "none", "loop", "self", "super", "caller", "varargs", "kwargs",
    "range", "dict", "lipsum", "cycler", "joiner", "namespace"})

VALID_TYPES = frozenset(int(t) for t in T)


def money_word_key(code: str) -> str:
    """Biến tiền `luong_thuong` tự có bạn đồng hành `luong_thuong_bang_chu` (đọc số thành chữ)."""
    return f"{code}{MONEY_WORD_SUFFIX}"


def check_code(code: str) -> str:
    """Trả `code` nếu hợp lệ; sai → `ValueError` (câu tiếng Việt)."""
    if not isinstance(code, str) or not CODE_RE.match(code):
        raise ValueError("Mã biến gồm 2–40 ký tự: chữ thường không dấu, số và dấu gạch dưới, "
                         "bắt đầu bằng chữ cái (ví dụ so_ngay_phep)")
    if "__" in code or code.endswith("_"):
        raise ValueError("Mã biến không có hai dấu gạch dưới liền nhau và không kết thúc bằng dấu gạch dưới")
    if code.endswith(MONEY_WORD_SUFFIX):
        raise ValueError(f"Mã biến không được kết thúc bằng «{MONEY_WORD_SUFFIX}» — hệ thống tự sinh "
                         "biến đọc bằng chữ cho biến kiểu Tiền")
    if code in RESERVED:
        raise ValueError("Mã biến trùng từ khóa của bộ máy mẫu — hãy chọn mã khác")
    if code in KNOWN_KEYS:
        raise ValueError("Mã biến trùng một biến hệ thống — hãy chọn mã khác")
    return code


#  Ký tự điều khiển ASCII (trừ \n, \t, \r) làm hỏng XML của .docx / dán lẫn từ Excel — bỏ đi.
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def _text(raw: str, multiline: bool) -> str:
    s = _CONTROL_RE.sub("", raw).replace("\r\n", "\n").replace("\r", "\n")
    if multiline:
        s = s.strip()
        if len(s) > MAX_MULTILINE:
            raise ValueError(f"Giá trị tối đa {MAX_MULTILINE} ký tự")
        return s
    s = " ".join(s.split("\n")).strip()
    if len(s) > MAX_TEXT:
        raise ValueError(f"Giá trị tối đa {MAX_TEXT} ký tự")
    return s


def _number(raw: str) -> str:
    s = raw.strip().replace(",", ".")
    if not _NUMBER_RE.match(s):
        raise ValueError("Số phải không âm, tối đa 13 chữ số nguyên và 2 chữ số lẻ (ví dụ 1,5)")
    out = format(Decimal(s), "f")
    return out.rstrip("0").rstrip(".") if "." in out else out


def _date(raw: str) -> str:
    s = raw.strip()
    try:
        if not _ISO_DATE_RE.match(s):
            raise ValueError
        d = date.fromisoformat(s)
    except ValueError:
        raise ValueError("Ngày phải đúng dạng năm-tháng-ngày (YYYY-MM-DD) và có thật") from None
    if not (YEAR_MIN <= d.year <= YEAR_MAX):
        raise ValueError(f"Ngày phải trong khoảng năm {YEAR_MIN}–{YEAR_MAX}")
    return d.isoformat()


def _money(raw) -> str:
    if isinstance(raw, int) and not isinstance(raw, bool):
        n = raw
    else:
        s = str(raw).strip()
        if not _DIGITS_RE.match(s):
            raise ValueError("Tiền là số nguyên đồng không âm, chỉ gồm chữ số (không dấu chấm, phẩy)")
        n = int(s)
    if not (0 <= n <= MONEY_MAX):
        raise ValueError("Tiền từ 0 đến 1.000.000.000.000 đồng")
    return str(n)


def normalize_value(vtype: int, raw) -> str:
    """Giá trị người dùng nhập → dạng CHUẨN của kiểu. Rỗng/None → «» (nghĩa là «không có giá trị»)."""
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return ""
    try:
        kind = T(int(vtype))
    except ValueError:
        raise ValueError("Kiểu giá trị không hợp lệ") from None
    if kind is T.MONEY:
        return _money(raw)
    s = str(raw)
    if kind is T.TEXT:
        return _text(s, multiline=False)
    if kind is T.MULTILINE:
        return _text(s, multiline=True)
    if kind is T.NUMBER:
        return _number(s)
    return _date(s)


def format_value(vtype: int, stored: str) -> str:
    """Dạng CHUẨN → chuỗi in ra tệp. Giá trị lưu hỏng (không nên có) thì in nguyên văn, không nổ."""
    if not stored:
        return ""
    try:
        kind = T(int(vtype))
        if kind is T.DATE:
            return fmt_date(date.fromisoformat(stored))
        if kind is T.MONEY:
            return fmt_money(int(stored))
        if kind is T.NUMBER:
            whole, _, frac = format(Decimal(stored), "f").partition(".")
            grouped = f"{int(whole):,}".replace(",", ".")
            return f"{grouped},{frac}" if frac else grouped
    except (ValueError, InvalidOperation):
        return stored
    return stored
