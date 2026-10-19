"""Kết quả từng phần của chỉ số một người (duoc-CR-641, phase 04): giá trị / chưa đo được / danh sách / số đếm thô."""
from dataclasses import dataclass, field

from app.core.usage_codes import UnmeasuredReason

from .metric_stats import rnd


@dataclass
class Partial:
    values: dict = field(default_factory=dict)       # khóa → số
    unmeasured: dict = field(default_factory=dict)   # khóa → UnmeasuredReason
    lists: dict = field(default_factory=dict)        # danh sách / bản đồ chỉ gồm số + định danh (route mẫu, entity)
    counts: dict = field(default_factory=dict)       # số đếm thô để luật nhận kiểu kiểm «dữ liệu tối thiểu»

    def put(self, key: str, value, reason: UnmeasuredReason = UnmeasuredReason.NOT_APPLICABLE) -> None:
        """Không có giá trị → ghi mã lý do, KHÔNG BAO GIỜ ghi 0 thay cho «không đo được»."""
        if value is None:
            self.unmeasured[key] = int(reason)
        else:
            self.values[key] = rnd(value)

    def merge(self, other: "Partial") -> "Partial":
        self.values.update(other.values)
        self.unmeasured.update(other.unmeasured)
        self.lists.update(other.lists)
        self.counts.update(other.counts)
        return self
