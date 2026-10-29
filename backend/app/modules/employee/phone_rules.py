"""SỐ ĐIỆN THOẠI KHÁC của hồ sơ nhân sự (duoc-CR-694).

Cột `phone` giữ nguyên là SỐ CHÍNH — khoảng 15 chỗ đọc thẳng nó (tìm kiếm, phiếu in, trợ lý AI, đặt xe,
đăng nhập…), đổi nghĩa cột là vỡ cả loạt. Các số còn lại nằm ở `extra_phones` (JSON): danh sách
`{"number": str ≤ 20, "label": str ≤ 50}`, tối đa `MAX_EXTRA_PHONES` (4) phần tử → tổng 5 số kể cả số chính.

Một nơi duy nhất giữ luật: định dạng số, trùng nhau, trùng số chính, và hai chiều chuyển
danh sách ⇄ chữ (dùng cho cột «Số điện thoại khác» của tệp xuất/nhập Excel).
"""
import re
from typing import Annotated

from fastapi import HTTPException
from pydantic import AfterValidator, BaseModel, field_validator

from .field_limits import Str20, Str50

MAX_EXTRA_PHONES = 4
MIN_DIGITS, MAX_DIGITS = 8, 15

#  Chỉ chữ số, khoảng trắng và + . - ( ) — dán từ Zalo/Excel hay kèm các ký tự này.
_ALLOWED = re.compile(r"^[0-9\s+.\-()]+$")
#  «số (nhãn)»: nhãn là cụm ngoặc CUỐI CÙNG, đứng sau một khoảng trắng — nhờ vậy số kiểu «(028) 3822 1234»
#  (ngoặc ở đầu) không bị đọc nhầm thành nhãn.
_TEXT_ITEM = re.compile(r"^(.*\S)\s+\(([^()]*)\)$")


def digits_of(number: str) -> str:
    """Chỉ giữ chữ số — dùng để so trùng («0901 234 567» = «0901.234.567»)."""
    return re.sub(r"\D", "", number or "")


class PhoneEntry(BaseModel):
    """Một số phụ. Độ dài khớp mô tả cột (20 / 50)."""

    number: Str20
    label: Str50 = ""

    @field_validator("number")
    @classmethod
    def _check_number(cls, v: str) -> str:
        v = v.strip()
        if not v or not _ALLOWED.match(v):
            raise ValueError("Số điện thoại chỉ gồm chữ số, khoảng trắng và các ký tự + . - ( )")
        n = len(digits_of(v))
        if n < MIN_DIGITS or n > MAX_DIGITS:
            raise ValueError(f"Số điện thoại phải có từ {MIN_DIGITS} đến {MAX_DIGITS} chữ số")
        return v

    @field_validator("label")
    @classmethod
    def _strip_label(cls, v: str) -> str:
        return v.strip()


def _check_list(items: list[PhoneEntry]) -> list[PhoneEntry]:
    if len(items) > MAX_EXTRA_PHONES:
        raise ValueError(f"Chỉ nhập tối đa {MAX_EXTRA_PHONES} số điện thoại khác "
                         f"(cùng số chính là {MAX_EXTRA_PHONES + 1} số)")
    seen: set[str] = set()
    for it in items:
        d = digits_of(it.number)
        if d in seen:
            raise ValueError(f"Số điện thoại {it.number} bị nhập trùng")
        seen.add(d)
    return items


#  Kiểu dùng ở schema: kiểm từng số + số lượng + trùng nhau.
ExtraPhones = Annotated[list[PhoneEntry], AfterValidator(_check_list)]


def ensure_distinct_from_main(main_phone: str | None, extras: list | None) -> None:
    """Số phụ không được trùng số chính. Cần cả hai nên không đặt được ở validator từng trường
    (PATCH có thể chỉ gửi một ô) — gọi ở service SAU khi đã biết giá trị cuối cùng."""
    main = digits_of(main_phone or "")
    if not main:
        return
    for e in extras or []:
        if digits_of(e.get("number", "") if isinstance(e, dict) else e.number) == main:
            raise HTTPException(422, "Số điện thoại khác trùng với số chính")


def format_phones_text(extras: list | None) -> str:
    """Danh sách → «số (nhãn); số (nhãn)». Nhãn rỗng thì chỉ có số."""
    parts = []
    for e in extras or []:
        label = (e.get("label") or "").replace(";", ",").replace("(", "[").replace(")", "]").strip()
        parts.append(f"{e.get('number', '')} ({label})" if label else str(e.get("number", "")))
    return "; ".join(parts)


def parse_phones_text(text: str) -> list[dict]:
    """«số (nhãn); số» → danh sách dict. Ném `ValueError` (câu tiếng Việt) khi sai — nơi gọi bọc lại.

    Chỉ tách; định dạng/trùng/số lượng do `ExtraPhones` kiểm khi dựng schema."""
    out: list[dict] = []
    for raw in text.split(";"):
        raw = raw.strip()
        if not raw:
            continue
        m = _TEXT_ITEM.match(raw)
        number, label = (m.group(1), m.group(2)) if m else (raw, "")
        out.append({"number": number.strip(), "label": label.strip()})
    return out
