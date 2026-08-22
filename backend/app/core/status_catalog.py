"""Khung khai báo bộ mã cố định dùng chung — nền của QĐ-9.

QĐ-9 (22/08/2026): mọi cột trạng thái của Thu mua lưu **mã chuỗi tiếng Anh**, tiếng Việt chỉ
còn ở tầng hiển thị. Đúng khuôn CR-118 đã làm cho `tab_contract.contract_type`, KHÔNG phải
khuôn `SMALLINT` + `IntEnum` mà R2 ở `doc/erp/06` §1 từng viết.

Trước đây mỗi bộ mã tự khai một tệp riêng (`contract_types.py`, `document_types.py`) và mỗi
giao diện lại chép lại một bản `Record<string, string>` bằng tay. Ba bản chép đó lệch nhau là
chuyện đã xảy ra thật — xem đầu tệp `contract_types.py`. Tệp này là chỗ duy nhất khai, còn
`scripts/gen_status_ts.py` sinh bản TypeScript ra từ đây nên không thể lệch.

So với `contract_types.py`, khung này mang thêm ba thứ mà bộ mã trạng thái cần:

- `sort_order` — thứ tự trong chuỗi tiến trình. Đây là thứ bù cho cái mất của khuôn mã chuỗi:
  `SMALLINT` thì so sánh lớn/bé được luôn, mã chuỗi thì không. `progress_status` của Đơn mua
  hàng hiện đang dựa vào **vị trí trong list** `PROGRESS_ORDER` để đi tới bước kế — dùng
  `ordered_values` / `next_value` ở đây thay cho `PROGRESS_ORDER.index(...)`.
- `is_terminal` — trạng thái kết, không đi tiếp được (Hoàn thành).
- `is_exception` — nhánh rẽ ra khỏi chuỗi, không có chỗ trong thứ tự (Tạm ngưng, Hủy đơn).

Hai cờ sau thay cho việc rải `in ("completed", "cancelled")` khắp các service.

Cách dùng: khai `CodeSet` rồi `register(...)` ngay tại tệp của phân hệ; nạp tệp đó ở
`app/core/code_sets.py` để `/meta/statuses` và kịch bản sinh TypeScript nhìn thấy.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Code:
    """Một mã trong bộ. `value` lưu DB và KHÔNG bao giờ đổi; `label` đổi thoải mái."""

    value: str
    label: str
    # Vị trí trong chuỗi tiến trình. Bộ mã không có thứ tự (loại hợp đồng, loại chứng từ)
    # thì để mặc định 0 cho tất cả — lúc đó `ordered_values` giữ nguyên thứ tự khai.
    sort_order: int = 0
    is_terminal: bool = False
    is_exception: bool = False


class CodeSet:
    """Một bộ mã cố định. Bất biến sau khi dựng — đừng sửa thuộc tính từ bên ngoài."""

    def __init__(self, name: str, title: str, codes: list[Code]):
        values = [c.value for c in codes]
        dups = {v for v in values if values.count(v) > 1}
        if dups:
            raise ValueError(f"Bộ mã '{name}' khai trùng value: {sorted(dups)}")

        # Bộ KHÔNG có chuỗi tiến trình (loại hợp đồng, loại chứng từ) để `sort_order` mặc
        # định 0 hết — lúc đó giữ nguyên thứ tự khai. Còn bộ ĐÃ khai thứ tự thì phải là thứ
        # tự toàn phần, nếu không `next_value` trả về tùy hên xui. Ngoại lệ đứng ngoài chuỗi.
        orders = [c.sort_order for c in codes if not c.is_exception]
        if any(orders) and len(set(orders)) != len(orders):
            raise ValueError(f"Bộ mã '{name}' có sort_order trùng nhau: {orders}")

        self.name = name
        self.title = title
        self.codes: tuple[Code, ...] = tuple(codes)
        self.values: frozenset[str] = frozenset(values)
        self.labels: dict[str, str] = {c.value: c.label for c in codes}
        self._by_value: dict[str, Code] = {c.value: c for c in codes}

    # --- đọc ---------------------------------------------------------------

    @property
    def options(self) -> list[dict]:
        """Dạng `[{value, label}]` — ĐÚNG hình dạng các endpoint `/meta/...` cũ đang trả.

        Giữ nguyên hai khóa này để đổi sang khung mới không làm đổi thân phản hồi API.
        Phần thông tin thêm nằm ở `full_options`.
        """
        return [{"value": c.value, "label": c.label} for c in self.codes]

    @property
    def full_options(self) -> list[dict]:
        """Bản đầy đủ cho `/meta/statuses` và kịch bản sinh TypeScript."""
        return [
            {
                "value": c.value,
                "label": c.label,
                "sort_order": c.sort_order,
                "is_terminal": c.is_terminal,
                "is_exception": c.is_exception,
            }
            for c in self.codes
        ]

    @property
    def ordered_values(self) -> tuple[str, ...]:
        """Chuỗi tiến trình theo `sort_order`, ĐÃ bỏ các mã ngoại lệ."""
        chain = [c for c in self.codes if not c.is_exception]
        return tuple(c.value for c in sorted(chain, key=lambda c: c.sort_order))

    def label_of(self, value: str | None, default: str = "") -> str:
        return self.labels.get(value or "", default)

    def is_terminal(self, value: str | None) -> bool:
        c = self._by_value.get(value or "")
        return bool(c and c.is_terminal)

    def is_exception(self, value: str | None) -> bool:
        c = self._by_value.get(value or "")
        return bool(c and c.is_exception)

    def next_value(self, value: str | None) -> str | None:
        """Mã kế tiếp trong chuỗi. Trả None khi đã ở bước cuối, mã ngoại lệ hoặc mã lạ.

        Thay cho `ORDER[ORDER.index(x) + 1]` — kiểu cũ ném `ValueError` với mã lạ và
        `IndexError` ở bước cuối, hai lỗi mà nơi gọi hầu như không ai bắt.
        """
        chain = self.ordered_values
        if value not in chain:
            return None
        i = chain.index(value)
        return chain[i + 1] if i + 1 < len(chain) else None

    # --- kiểm tra đầu vào --------------------------------------------------

    def validate(self, value: str | None, *, allow_blank: bool = True) -> str | None:
        """Chỉ nhận mã trong bộ. Rỗng/None = chưa phân loại, mặc định cho qua.

        Dùng thẳng trong `field_validator` của `schema.py`. Chặn ở đây để cột không đẻ
        thêm giá trị lạ — đúng bài học của CR-118.
        """
        if value is None or value == "":
            if allow_blank:
                return value
            raise ValueError(f"{self.title} không được để trống")
        if value not in self.values:
            raise ValueError(f"{self.title} không hợp lệ: {value}")
        return value


# --- sổ đăng ký ------------------------------------------------------------

_REGISTRY: dict[str, CodeSet] = {}


def register(code_set: CodeSet) -> CodeSet:
    """Ghi bộ mã vào sổ. Trả lại chính nó để khai và đăng ký trong một câu lệnh."""
    old = _REGISTRY.get(code_set.name)
    if old is not None and old is not code_set:
        raise ValueError(f"Bộ mã '{code_set.name}' đã được đăng ký bởi nơi khác")
    _REGISTRY[code_set.name] = code_set
    return code_set


def get(name: str) -> CodeSet:
    if name not in _REGISTRY:
        raise KeyError(f"Chưa đăng ký bộ mã '{name}'")
    return _REGISTRY[name]


def all_sets() -> dict[str, CodeSet]:
    """Bản sao sổ đăng ký, sắp theo tên cho `/meta/statuses` và bản TypeScript ổn định."""
    return {name: _REGISTRY[name] for name in sorted(_REGISTRY)}
