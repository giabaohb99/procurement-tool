"""ĐIỀU KIỆN RẼ NHÁNH (I04).

Điều kiện khai bằng JSON, đọc trên **bối cảnh phiếu** — một dict phẳng do chính
module chứng từ cung cấp (`{"total": 50000000, "doc_type_id": 3, …}`). Bộ máy
duyệt không biết gì về cấu trúc bảng của chứng từ, và cố ý như vậy: biết rồi thì
mỗi lần thêm một loại chứng từ lại phải sửa bộ máy.

    [{"field": "total", "op": "gte", "value": 50000000},
     {"field": "company_id", "op": "in", "value": [1, 4]}]

Các dòng nối nhau bằng VÀ. Cần HOẶC thì khai thành hai nhánh — dễ đọc hơn hẳn
một cây điều kiện lồng nhau, mà đây là thứ người không viết mã phải khai được.
"""
import json

OPS = ("eq", "ne", "gt", "gte", "lt", "lte", "in", "not_in", "contains", "empty", "not_empty")

OP_LABELS = {
    "eq": "bằng",
    "ne": "khác",
    "gt": "lớn hơn",
    "gte": "từ",
    "lt": "nhỏ hơn",
    "lte": "đến",
    "in": "thuộc danh sách",
    "not_in": "không thuộc danh sách",
    "contains": "chứa",
    "empty": "để trống",
    "not_empty": "có giá trị",
}


def parse(raw: str) -> list[dict]:
    """Đọc chuỗi điều kiện. Hỏng thì coi như KHÔNG có điều kiện, không nổ.

    Nổ ở đây là chặn cả phiếu vì một ô cấu hình gõ sai. Nhánh không đọc được
    thì `matches()` trả `False`, phiếu rơi vào nhánh mặc định — có nhánh mặc
    định chính là để đỡ những ca thế này.
    """
    if not (raw or "").strip():
        return []
    try:
        data = json.loads(raw)
    except (ValueError, TypeError):
        return []
    return data if isinstance(data, list) else []


#  Hai phép không cần giá trị để so, và hai phép nhận DANH SÁCH giá trị.
VALUE_FREE_OPS = ("empty", "not_empty")
LIST_OPS = ("in", "not_in")


def find_error(raw: str, fields: dict) -> str:
    """Lỗi ĐẦU TIÊN của chuỗi điều kiện, nói bằng câu tiếng Việt; rỗng = hợp lệ — bao-CR-528.

    `fields` = {khóa trong bối cảnh phiếu: nhãn tiếng Việt}. Dùng ở CỬA LƯU (màn Cấu hình hệ
    thống), KHÔNG dùng lúc chạy: lúc chạy `parse()` vẫn khoan dung như cũ để một ô cấu hình hỏng
    không chặn được phiếu nào. Chặn ở cửa lưu là để lỗi gõ sai lộ ra ngay lúc bấm Lưu, thay vì
    lặng lẽ thành «không bỏ qua phiếu nào» như trước.
    """
    if not (raw or "").strip():
        return ""
    try:
        data = json.loads(raw)
    except (ValueError, TypeError):
        return "không đọc được (sai cú pháp). Hãy khai lại bằng bộ chọn điều kiện"
    if not isinstance(data, list):
        return "phải là một danh sách các dòng điều kiện"
    known = ", ".join(f"{label} ({key})" for key, label in fields.items())
    for index, row in enumerate(data, start=1):
        if not isinstance(row, dict):
            return f"dòng {index} không phải một điều kiện"
        field = row.get("field")
        if not isinstance(field, str) or field not in fields:
            return f"dòng {index} dùng trường «{field}» không có. Trường dùng được: {known}"
        op = row.get("op", "eq")
        if not isinstance(op, str) or op not in OPS:
            return f"dòng {index} dùng phép so «{op}» không có"
        value = row.get("value")
        if op in LIST_OPS and not _as_list(value):
            return f"dòng {index} ({fields[field]}) chưa chọn giá trị nào"
        if op not in VALUE_FREE_OPS and op not in LIST_OPS and value in (None, ""):
            return f"dòng {index} ({fields[field]}) chưa có giá trị để so"
    return ""


def matches(raw: str, subject: dict) -> bool:
    """Bối cảnh phiếu có thỏa điều kiện không. Không khai điều kiện = luôn thỏa."""
    condition = parse(raw)
    if not condition:
        return True
    return all(_one(row, subject) for row in condition)


def _one(row: dict, subject: dict) -> bool:
    if not isinstance(row, dict):
        return False

    op = row.get("op", "eq")
    raw_value = subject.get(row.get("field", ""))
    threshold = row.get("value")

    if op == "empty":
        return raw_value in (None, "", 0)
    if op == "not_empty":
        return raw_value not in (None, "", 0)

    if op == "in":
        return _as_list(threshold) and str(raw_value) in [str(item) for item in _as_list(threshold)]
    if op == "not_in":
        return str(raw_value) not in [str(item) for item in _as_list(threshold)]
    if op == "contains":
        return str(threshold or "").lower() in str(raw_value or "").lower()

    if op in ("eq", "ne"):
        #  So bằng chuỗi: `doc_type_id` từ ô chọn về là "3", từ phiếu là 3 —
        #  so thô thì không bao giờ khớp và nhánh im lặng không chạy.
        equal = str(raw_value) == str(threshold)
        return equal if op == "eq" else not equal

    #  Bốn phép còn lại là so lớn nhỏ, chỉ có nghĩa trên số.
    try:
        left, right = float(raw_value), float(threshold)
    except (TypeError, ValueError):
        return False
    return {
        "gt": left > right,
        "gte": left >= right,
        "lt": left < right,
        "lte": left <= right,
    }[op]


def _as_list(value) -> list:
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return [value] if value is not None else []


def describe(raw: str, labels: dict | None = None) -> str:
    """Câu tiếng Việt của điều kiện, cho bảng theo dõi và bản in dấu vết.

    `labels` (tùy chọn, bao-CR-528) đổi khóa trường ra nhãn tiếng Việt — nhật ký màn Cấu hình
    đọc «Phòng xử lý có giá trị» thay vì «handler_dept_id có giá trị».
    """
    condition = parse(raw)
    if not condition:
        return "Mọi phiếu"
    names = labels or {}

    def _one_text(row) -> str:
        if not isinstance(row, dict):
            return "?"
        field = row.get("field", "?")
        op = row.get("op", "eq")
        value = "" if op in VALUE_FREE_OPS else row.get("value", "")
        name = names.get(field, field) if isinstance(field, str) else field
        return f"{name} {OP_LABELS.get(op, '?') if isinstance(op, str) else '?'} {value}".strip()

    return " và ".join(_one_text(row) for row in condition)
