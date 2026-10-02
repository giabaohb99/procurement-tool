"""Thời gian duyệt (giờ) của chứng từ — dùng chung cho báo cáo Đặt xe · Đóng dấu · Văn bản.

Một chứng từ có thể được gửi duyệt nhiều lần (trả về rồi gửi lại) → lấy phiên duyệt ĐÃ KẾT
THÚC (duyệt / từ chối) MỚI NHẤT, giờ = `finished_at - started_at`. Phiên đang chạy, bị rút,
trả về hoặc thiếu mốc thời gian thì chứng từ đó KHÔNG có giá trị (vắng khỏi dict) — người
gọi đếm nó vào mẫu số hay không là việc của chỉ số, đừng coi vắng là 0 giờ.

Tham số `entity_ids_or_select` PHẢI đến từ truy vấn ĐÃ SCOPE của chính phân hệ chứng từ — hàm
này không biết gì về quyền.

Gói A4 (hiệu năng báo cáo, 01/10/2026): nhận THÊM một SELECTABLE id (`Select`/`.subquery()`/
`.scalar_subquery()` — bất kỳ `ClauseElement` nào), ngoài iterable id CŨ. Selectable chạy ĐÚNG
MỘT truy vấn `entity_id.in_(select)`, không chia lô — `vehicle-bookings` ở khoảng 3 năm từng tốn
105 lượt round-trip SQL vì chunk 900 id phía Python (load-test §2/§5.4); subquery để MySQL tự lo,
không còn chunk. Vẫn giữ nguyên hành vi iterable (chunk 900/lượt) cho các caller CHƯA đổi."""
from __future__ import annotations

from sqlalchemy import ClauseElement
from sqlalchemy.orm import Session

from app.modules.approval.instance_model import (INSTANCE_APPROVED, INSTANCE_REJECTED,
                                                 ApprovalInstance)

#  IN (...) quá dài làm MySQL chậm và SQLite vượt trần biến — cắt lô. CHỈ áp cho nhánh iterable;
#  nhánh selectable (gói A4) không cần vì điều kiện nằm TRONG câu SQL, không phải tham số.
_CHUNK = 900


def turnaround_hours(db: Session, entity: str, entity_ids_or_select) -> dict[int, float]:
    """`{entity_id: giờ duyệt}` của phiên kết thúc mới nhất.

    `entity_ids_or_select`: iterable id (hành vi CŨ, chia lô 900) HOẶC một `ClauseElement`
    (select/subquery/scalar_subquery id ĐÃ SCOPE) — đúng MỘT truy vấn, không chunk."""
    if isinstance(entity_ids_or_select, ClauseElement):
        return _latest_per_entity(_fetch(db, entity, entity_ids_or_select))

    ids = sorted({int(i) for i in entity_ids_or_select if i})
    out: dict[int, float] = {}
    for start in range(0, len(ids), _CHUNK):
        out.update(_latest_per_entity(_fetch(db, entity, ids[start:start + _CHUNK])))
    return out


def _fetch(db: Session, entity: str, ids_or_select):
    """Một lượt `SELECT` — `ids_or_select` là list (lô CŨ) hoặc `ClauseElement` (gói A4), cả
    hai đều hợp lệ cho `Column.in_(...)`."""
    return (db.query(ApprovalInstance.entity_id, ApprovalInstance.started_at,
                     ApprovalInstance.finished_at)
            .filter(ApprovalInstance.entity == entity,
                    ApprovalInstance.entity_id.in_(ids_or_select),
                    ApprovalInstance.status.in_((INSTANCE_APPROVED, INSTANCE_REJECTED)),
                    ApprovalInstance.started_at.isnot(None),
                    ApprovalInstance.finished_at.isnot(None))
            .order_by(ApprovalInstance.id)
            .all())


def _latest_per_entity(rows) -> dict[int, float]:
    """Sắp theo id tăng dần → phiên sau ghi đè phiên trước = giữ phiên MỚI NHẤT."""
    out: dict[int, float] = {}
    for entity_id, started, finished in rows:
        out[int(entity_id)] = max((finished - started).total_seconds(), 0) / 3600
    return out
