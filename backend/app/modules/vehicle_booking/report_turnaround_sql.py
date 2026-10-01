"""Giờ duyệt (turnaround) của Đặt xe — GOM Ở SQL, thay `report_turnaround.turnaround_hours()`
chia lô 900 id (review hiệu năng 01/10/2026 — load test đo 105 lượt hỏi ở mốc 3 năm/50k phiếu,
xem `fullstack-developer-261001-1103-load-test-8-bao-cao-moi.md` §2 mục vehicle-bookings).

Cùng SEMANTICS với `report_turnaround.turnaround_hours()` — phiên DUYỆT/TỪ CHỐI đã kết thúc,
MỚI NHẤT (id lớn nhất) trong các phiên có đủ `started_at`/`finished_at`. Khác đúng MỘT chỗ:
bản kia chia `entity_id IN (...)` thành lô 900 id (N lượt hỏi theo N chứng từ); tệp này JOIN
MỘT LƯỢT — không cần danh sách id, DB tự khớp qua cột `entity_id = <bảng chứng từ>.id` ở nơi
gọi (`outerjoin(sub, Model.id == sub.c.booking_id)`).

KHÔNG sửa `approval/report_turnaround.py` (tệp dùng chung, agent khác đang đổi chữ ký của nó
sang nhận thẳng subquery id — tệp này độc lập, không phụ thuộc bản đó).
"""
from __future__ import annotations

from sqlalchemy import Integer, cast, func, literal_column
from sqlalchemy.orm import Session, aliased

from app.modules.approval.instance_model import (INSTANCE_APPROVED, INSTANCE_REJECTED,
                                                 ApprovalInstance)


def _hours_diff_expr(db: Session, start_col, end_col):
    """`end - start` ra GIỜ (float) — cổng được cả SQLite (test) lẫn MySQL (prod), khớp CHÍNH
    XÁC `(finished-started).total_seconds()/3600` của Python khi cột `DATETIME` không mang
    phần dưới giây (mặc định của MySQL `DATETIME`, không khai `fsp`) — đã kiểm tay bằng
    `sqlite3` (01/10/2026), sai số 0 cho mọi cặp mốc nguyên giây.

    `julianday` (cách làm thường thấy cho SQLite) bị bỏ vì có sai số nổi dấu phẩy động cỡ
    1e-7 giờ do trừ hai số LỚN (~2.46 triệu ngày Julius) — vô hại cho hiển thị (làm tròn 1
    chữ số thập phân ở `DerivedSpec`) nhưng làm khóa kiểm "y hệt dict cũ" ở mức bit trật.
    `strftime('%s', …)` cắt thẳng về GIÂY NGUYÊN, không qua phép trừ số lớn, nên không có
    sai số đó.
    """
    dialect = db.bind.dialect.name if db.bind is not None else "sqlite"
    if dialect == "mysql":
        #  TIMESTAMPDIFF(SECOND, start, end) / 3600.0 — đơn vị là TOKEN SQL (literal_column),
        #  không phải chuỗi, nếu không MySQL đọc thành tham số và báo lỗi cú pháp.
        return func.timestampdiff(literal_column("SECOND"), start_col, end_col) / 3600.0
    return (cast(func.strftime("%s", end_col), Integer)
            - cast(func.strftime("%s", start_col), Integer)) / 3600.0


def turnaround_hours_subquery(db: Session, entity: str):
    """Subquery `(booking_id, hours)` — MỘT dòng cho mỗi chứng từ CÓ phiên đã kết thúc.

    Nơi gọi tự `outerjoin(sub, Model.id == sub.c.booking_id)`: chứng từ KHÔNG có phiên nào
    khớp thì vắng mặt khỏi subquery (JOIN TRÁI ra `NULL`) — giữ đúng luật "vắng khác 0" của
    `report_turnaround.turnaround_hours` (chứng từ đó không góp vào `hours_count`).
    """
    latest = (db.query(ApprovalInstance.entity_id.label("entity_id"),
                       func.max(ApprovalInstance.id).label("max_id"))
             .filter(ApprovalInstance.entity == entity,
                     ApprovalInstance.status.in_((INSTANCE_APPROVED, INSTANCE_REJECTED)),
                     ApprovalInstance.started_at.isnot(None),
                     ApprovalInstance.finished_at.isnot(None))
             .group_by(ApprovalInstance.entity_id)
             .subquery())
    ai = aliased(ApprovalInstance)
    hours = _hours_diff_expr(db, ai.started_at, ai.finished_at)
    return (db.query(latest.c.entity_id.label("booking_id"), hours.label("hours"))
            .join(ai, ai.id == latest.c.max_id)
            .subquery())
