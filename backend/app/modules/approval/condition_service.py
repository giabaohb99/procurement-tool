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


def describe(raw: str) -> str:
    """Câu tiếng Việt của điều kiện, cho bảng theo dõi và bản in dấu vết."""
    condition = parse(raw)
    if not condition:
        return "Mọi phiếu"
    return " và ".join(
        f"{row.get('field', '?')} {OP_LABELS.get(row.get('op', 'eq'), '?')} "
        f"{row.get('value', '')}".strip()
        for row in condition
    )
