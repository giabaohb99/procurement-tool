"""GIÁ TRỊ của bộ trường tùy biến — kiểm `tab_dossier.extra_fields` theo loại.

Bộ trường khai ở loại hồ sơ (`field_schema.py`); tệp này là chốt lúc GHI một hồ
sơ: ô bắt buộc đã điền chưa, số có phải số không, mục chọn có nằm trong danh
sách khai không.

Ba luật, mỗi luật đổi lấy một thứ — đọc kỹ trước khi nới:

1. **Khóa KHÔNG còn khai vẫn được giữ.** Người quản trị bỏ một ô khỏi loại hồ sơ
   thì hàng trăm hồ sơ cũ vẫn đang mang giá trị của ô đó. Ném 422 là khóa chết
   luôn việc sửa chúng (đụng ô nào cũng không lưu nổi); xóa lặng là **mất dữ
   liệu thật** mà không ai kịp thấy. Nên giữ, và vẫn bắt chúng qua chốt kích
   thước — giữ lại không có nghĩa là để chúng phình ra vô hạn.
2. **Ô bắt buộc kiểm ở NGAY LÚC GHI, theo bộ trường HIỆN TẠI.** Hệ quả phải biết
   trước: thêm một ô bắt buộc vào loại đã có hồ sơ thì lần sửa kế tiếp của từng
   hồ sơ cũ bị đòi điền ô đó. Đấy đúng là ý nghĩa của «bắt buộc», và giao diện
   vẽ dấu sao đỏ nên người dùng thấy ngay mình đang bị đòi gì — khác hẳn một câu
   422 không chỉ được ô nào.
3. **Rỗng không phải là sai, trừ khi ô đó bắt buộc.** Ô chưa nhập lưu chuỗi rỗng
   chứ không lưu `null`: hai thứ đó phân biệt được trên JSON nhưng không phân
   biệt được trên biểu mẫu, và giữ hai dạng cho cùng một nghĩa là mời gọi đúng
   loại lỗi «chỗ này kiểm `is None`, chỗ kia kiểm `== ''»`.
"""
import json
from datetime import date

from .field_schema import DossierFieldDef

#  Trần cho MỘT giá trị. Ô nhiều dòng rộng hơn vì nó sinh ra để chứa đoạn văn
#  (điều khoản, ghi chú thẩm định); ô một dòng thì 500 đã quá rộng cho một số
#  giấy phép hay một tên cơ quan.
MAX_VALUE_LEN = 500
MAX_TEXTAREA_LEN = 2_000
#  Tổng cả ô JSON. Chốt cuối — ba chốt trên vẫn để lọt 20 khóa × 2000 ký tự.
MAX_TOTAL_BYTES = 16_000

#  Chỉ nhận giá trị VÔ HƯỚNG. Nhận cả cây lồng nhau là biến ô này thành một cơ
#  sở dữ liệu thứ hai mà không ai rà, không ai di trú được, và không màn hình
#  nào hiện nổi (cùng lý lẽ đã ghi ở `employee/field_limits.py`).
_SCALAR_TYPES = (str, int, float, bool, type(None))


def _coerce(d: DossierFieldDef, raw):
    """Ép một giá trị về đúng kiểu ô đã khai. Ném `ValueError` kèm tên ô."""
    if d.type == "switch":
        #  Chuỗi `"false"` là bẫy kinh điển của đường JSON: `bool("false")` ra
        #  `True`. Ô công tắc gửi từ biểu mẫu thì luôn là bool thật, nhưng đường
        #  nhập CSV và người gọi thẳng API thì không.
        if isinstance(raw, str):
            return raw.strip().lower() in ("1", "true", "yes", "co", "có")
        return bool(raw)

    if d.type == "number":
        if raw in (None, ""):
            return ""
        try:
            num = float(raw)
        except (TypeError, ValueError):
            raise ValueError(f"«{d.label}» phải là một con số")
        if num != num or num in (float("inf"), float("-inf")):
            raise ValueError(f"«{d.label}» phải là một con số")
        #  Trả về `int` khi tròn, để hồ sơ không bày ra «2026.0» ở chỗ đáng lẽ
        #  là một năm.
        return int(num) if num == int(num) else num

    if d.type == "date":
        if raw in (None, ""):
            return ""
        text = str(raw).strip()[:10]
        try:
            date.fromisoformat(text)
        except ValueError:
            raise ValueError(f"«{d.label}» phải là ngày dạng nam-thang-ngay (2026-09-16)")
        return text

    text = "" if raw is None else str(raw)
    if d.type == "select":
        if text and text not in d.options:
            raise ValueError(
                f"«{d.label}» nhận một trong các mục: {', '.join(d.options)}"
            )
        return text

    limit = MAX_TEXTAREA_LEN if d.type == "textarea" else MAX_VALUE_LEN
    if len(text) > limit:
        raise ValueError(f"«{d.label}» tối đa {limit} ký tự")
    return text


def validate_extra_values(defs: list[DossierFieldDef], value: dict | None) -> dict:
    """Kiểm + chuẩn hoá `extra_fields` của một hồ sơ theo bộ trường của loại."""
    raw = value or {}
    if not isinstance(raw, dict):
        raise ValueError("Trường tùy biến phải là một đối tượng {khóa: giá trị}")

    out: dict = {}
    declared = {d.key for d in defs}

    for d in defs:
        coerced = _coerce(d, raw.get(d.key))
        #  `False` của ô công tắc là một câu trả lời, không phải ô bỏ trống —
        #  nên so với chuỗi rỗng chứ đừng dùng `if not coerced`.
        if d.required and coerced in ("", None):
            #  ⚠️ KHÔNG nói «của loại hồ sơ này»: hàm này nhận CHUNG hai nguồn
            #  khai — ô của loại và trường riêng người lập tự thêm. Câu cũ nói
            #  sai nguồn với nhóm thứ hai, và người dùng sẽ đi mở màn Loại hồ sơ
            #  tìm một ô không có ở đó.
            raise ValueError(f"«{d.label}» là ô bắt buộc, chưa có giá trị")
        out[d.key] = coerced

    #  Khóa không còn khai: giữ nguyên (luật 1 ở đầu tệp), nhưng vẫn phải qua
    #  chốt vô hướng — không thì đường duy nhất nhét được một cây JSON khổng lồ
    #  vào cột này là khai một ô, gửi giá trị, rồi xóa ô đó đi.
    for key, item in raw.items():
        if key in declared:
            continue
        if not isinstance(item, _SCALAR_TYPES):
            raise ValueError(
                f"Trường «{key}» không còn được loại hồ sơ này khai báo và phải là "
                "một giá trị đơn (chữ, số, đúng/sai)."
            )
        if isinstance(item, str) and len(item) > MAX_TEXTAREA_LEN:
            raise ValueError(f"Trường «{key}» tối đa {MAX_TEXTAREA_LEN} ký tự")
        out[key] = item

    size = len(json.dumps(out, ensure_ascii=False).encode())
    if size > MAX_TOTAL_BYTES:
        raise ValueError(
            f"Trường tùy biến tối đa {MAX_TOTAL_BYTES} byte (đang gửi {size})."
        )
    return out
