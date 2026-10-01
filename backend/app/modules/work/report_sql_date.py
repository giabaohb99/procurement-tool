"""Hai biểu thức SQL ngày giờ VN dùng chung cho `report_grouped_fetch.py` +
`report_pic_groups.py` (review hiệu năng "gói B", 01/10/2026).

NHÁNH THEO DIALECT (`db.bind.dialect.name`, cùng khuôn `core/utils.py`/
`approval/flow_sync_service.py`) vì SQLite (bộ test) và MySQL (prod) không có
MỘT biểu thức CHUNG để cộng giờ vào timestamp rồi lấy hiệu hai ngày — khác các
phép lọc `>=`/`<` thuần túy của `report_period.range_filter`, vốn portable nhờ
đã tính xong biên ở Python trước khi đưa vào SQL. Luôn ép kết quả về CHUỖI
'YYYY-MM-DD' (`type_=String()`) để tránh driver MySQL trả `datetime.date` còn
SQLite trả `str` cho cùng một lời gọi `date()` — nơi gọi chỉ cần biết "chuỗi".
"""
from __future__ import annotations

from sqlalchemy import String, func, text
from sqlalchemy.orm import Session


def vn_date_str(db: Session, col):
    """Ngày LỊCH giờ VN (chuỗi 'YYYY-MM-DD') của một cột DATETIME UTC."""
    if db.bind is not None and db.bind.dialect.name == "mysql":
        return func.date_format(func.date_add(col, text("INTERVAL 7 HOUR")), "%Y-%m-%d",
                                type_=String())
    return func.date(col, "+7 hours", type_=String())


def date_diff_days(db: Session, later, earlier):
    """`later - earlier` tính theo NGÀY (cả hai đã qua `vn_date_str`)."""
    if db.bind is not None and db.bind.dialect.name == "mysql":
        return func.datediff(later, earlier)
    return func.julianday(later) - func.julianday(earlier)
