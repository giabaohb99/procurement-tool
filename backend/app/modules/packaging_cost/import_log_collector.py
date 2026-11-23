"""Gom nhật ký + số đếm của một lô nhập Excel cụm Giá NVL sản xuất (duoc-CR-784) theo đúng hình dạng `_persist` của Quản lý
Import cần (`sheet, row_no, level, category, message, ref_key, target_code`). Dùng chung cho nhập báo giá VTBB và Sổ Misa.
"""
from app.modules.import_tool.model import LogLevel

#  Trần số dòng nhật ký INFO một lô — Sổ Misa có hàng nghìn dòng; lỗi / cảnh báo thì luôn ghi đủ.
MAX_INFO_LOGS = 300


class ImportLogCollector:
    def __init__(self, sheet: str):
        self.sheet = (sheet or "")[:40]
        self.logs: list[dict] = []
        self.counts = {"created": 0, "updated": 0, "skipped": 0, "deleted": 0, "warning": 0, "review": 0, "error": 0}
        self._info = 0
        self.info_dropped = 0

    def log(self, row_no: int, level: LogLevel, category: str, message: str, ref: str = "") -> None:
        key = {LogLevel.WARNING: "warning", LogLevel.REVIEW: "review", LogLevel.ERROR: "error"}.get(level)
        if key:
            self.counts[key] += 1
        elif self._info >= MAX_INFO_LOGS:
            self.info_dropped += 1
            return
        else:
            self._info += 1
        self.logs.append({"sheet": self.sheet, "row_no": row_no, "level": int(level), "category": category,
                          "message": message, "ref_key": ref, "target_code": ref[:50]})

    def note_dropped(self) -> None:
        """Ghi một dòng cuối cho biết đã bớt bao nhiêu dòng nhật ký thông tin (số đếm vẫn đủ)."""
        if self.info_dropped:
            self.logs.append({"sheet": self.sheet, "row_no": 0, "level": int(LogLevel.INFO), "category": "log_trimmed",
                              "message": f"Còn {self.info_dropped:,} dòng thông tin không ghi vào nhật ký (số đếm ở trên đã "
                                         "tính đủ).".replace(",", "."), "ref_key": "", "target_code": ""})
