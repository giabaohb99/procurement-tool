"""Đọc số tiền thành chữ tiếng Việt cho bản in HĐ / chứng từ.

⚠️ BẢN PYTHON của `frontend-v2/src/shared/utils/number-to-vietnamese-words.ts` — phải
cho CÙNG kết quả. Bộ ca test dùng chung số liệu: `test/backend/test_hdld_doc_so_thanh_chu.py`
↔ `number-to-vietnamese-words.test.ts`. Sửa luật ở một bên thì sửa cả bên kia.
"""
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

_DIGITS = ("không", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín")
_SCALES = ("", " nghìn", " triệu", " tỷ", " nghìn tỷ")
#  Trần: 10^15 - 1 (999 nghìn tỷ) — quá bậc `_SCALES` thì đọc sai bậc, nên chặn thay vì đọc bậy.
MAX_AMOUNT = 10**15 - 1


def read_amount_vi(amount) -> str:
    """Số tiền → chữ, vd 15_000_000 → «Mười lăm triệu đồng chẵn».

    Làm tròn về ĐỒNG (half-up như `Math.round`); ≤ 0 / rỗng / không phải số → «Không đồng».
    Quá `MAX_AMOUNT` → ValueError (không đọc bậy).
    """
    try:
        value = Decimal(str(amount))
    except (InvalidOperation, ValueError, TypeError):
        return "Không đồng"
    if not value.is_finite() or value <= 0:
        return "Không đồng"
    #  Chặn TRƯỚC khi `quantize`: số quá lớn làm quantize ném InvalidOperation (độ chính xác 28
    #  chữ số) — nuốt lỗi đó thành «Không đồng» là im lặng sai trên một bản in tiền.
    if value > MAX_AMOUNT:
        raise ValueError("Số tiền vượt giới hạn đọc thành chữ")
    remaining = int(value.quantize(Decimal(1), rounding=ROUND_HALF_UP))
    if remaining <= 0:
        return "Không đồng"

    groups: list[int] = []
    while remaining > 0:
        groups.append(remaining % 1000)
        remaining //= 1000

    parts: list[str] = []
    for index in range(len(groups) - 1, -1, -1):
        if groups[index] == 0:
            continue
        #  Nhóm không phải nhóm cao nhất thì luôn đọc đủ hàng trăm («một triệu KHÔNG TRĂM năm mươi nghìn»).
        parts.append(_read_triple(groups[index], index < len(groups) - 1) + _SCALES[index])

    text = " ".join(" ".join(parts).split())
    return text[:1].upper() + text[1:] + " đồng chẵn"


def _read_triple(value: int, force_hundred: bool) -> str:
    hundred, ten, unit = value // 100, (value % 100) // 10, value % 10
    parts: list[str] = []
    if force_hundred or hundred > 0:
        parts.append(f"{_DIGITS[hundred]} trăm")
    if ten == 0:
        if unit > 0:
            parts.append(("lẻ " if (force_hundred or hundred > 0) else "") + _DIGITS[unit])
    elif ten == 1:
        parts.append("mười")
        if unit == 5:
            parts.append("lăm")
        elif unit > 0:
            parts.append(_DIGITS[unit])
    else:
        parts.append(f"{_DIGITS[ten]} mươi")
        if unit == 1:
            parts.append("mốt")
        elif unit == 5:
            parts.append("lăm")
        elif unit > 0:
            parts.append(_DIGITS[unit])
    return " ".join(parts)
