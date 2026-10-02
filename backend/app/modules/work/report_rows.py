"""Báo cáo Công việc / Dự án (phase 06) — nền SCOPE + tra TÊN dùng chung cho
`report_service.py`/`report_grouped_fetch.py`/`report_pic_groups.py`.

Chỉ tính TASK CHA còn sống, bỏ CỘT MỐC (Q6.1, chốt 01/10/2026) — khác
`overview_service.overview` (không lọc `kind`), nên "Quá hạn" ở đây có thể NHỎ
HƠN con số Tổng quan nếu đang có cột mốc quá hạn.

Review hiệu năng "gói B" (01/10/2026): hàng SỰ KIỆN (tạo mới/hoàn thành) nay GOM
Ở SQL (`report_grouped_fetch.py`) thay vì nạp từng task vào Python — tệp này chỉ
còn giữ phần NỀN dùng chung (`base_query`/`open_at_query`, phạm vi `visible_ids`)
+ tra TÊN theo lô nhỏ (list/company/employee), không còn `fetch_rows` cũ.
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta

from fastapi import HTTPException
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.modules.company.model import Company
from app.modules.employee.model import Employee

from .model import WorkGroup, WorkList, WorkTaskKind, WorkTaskStatus
from .task_model import WorkTask

VN_OFFSET = timedelta(hours=7)   # container chạy UTC — "hôm nay" phải là hôm nay ở VN
EMPTY_LIST_META = {"name": "", "group_id": 0, "group_name": ""}


def today_vn() -> date:
    return (datetime.utcnow() + VN_OFFSET).date()


def cutoff_utc(as_of: date) -> datetime:
    """Mốc UTC = HẾT ngày `as_of` giờ VN — cùng công thức cận trên của
    `report_period.range_filter(..., 'datetime_utc', ...)`, dùng cho snapshot
    "tại mốc" (M1, review 01/10/2026)."""
    return datetime.combine(as_of + timedelta(days=1), time.min) - VN_OFFSET


def open_at_query(db: Session, list_ids, as_of: date):
    """Việc ĐANG MỞ TẠI MỐC `as_of` (M1) — nền DÙNG CHUNG cho "Đang mở"/"Quá
    hạn" (`report_service._snapshot_fn`) lẫn hai breakdown "Top"
    (`report_service._breakdowns`), để hai nơi không lệch luật nhau: đã TẠO
    trước mốc, và TẠI MỐC đó chưa xong — còn `OPEN` bây giờ, hoặc đã `DONE`
    nhưng xong SAU mốc. Việc đã HỦY không có dấu "lúc hủy" nên KHÔNG tính được
    ở mốc quá khứ — bị loại khỏi kết quả (ghi ở `report_service.NOTES`), khác
    bản cũ chỉ đọc `status == OPEN` HIỆN TẠI (sai với mọi mốc không phải hôm nay)."""
    cutoff = cutoff_utc(as_of)
    return (base_query(db, list_ids)
            .filter(WorkTask.created_at < cutoff)
            .filter(or_(WorkTask.status == int(WorkTaskStatus.OPEN),
                        and_(WorkTask.status == int(WorkTaskStatus.DONE),
                             WorkTask.completed_at >= cutoff))))


def base_query(db: Session, list_ids):
    """Nền chung TASK CHA còn sống, không phải cột mốc — mọi query đếm/báo cáo đi qua đây.

    Chỉ chọn `id` mặc định (điểm 1, review hiệu năng 01/10/2026): `.count()` ở
    `_snapshot_fn` không cần cột nào khác, và `with_entities(...)` ở nơi gọi khác
    (`report_grouped_fetch.py`) THAY HẲN danh sách cột này, không cộng dồn.
    """
    return (db.query(WorkTask.id)
            .filter(WorkTask.list_id.in_(list_ids), WorkTask.parent_id.is_(None),
                    WorkTask.kind == int(WorkTaskKind.TASK), WorkTask.deleted_at.is_(None)))


def valid_scope_ids(visible_ids: set[int], raw_list_id: str | None) -> set[int]:
    """Lọc riêng "dự án" của FE (`extraFilters`) — PHẢI khớp phạm vi, không nhận id trần."""
    if not raw_list_id:
        return visible_ids
    if not raw_list_id.isdigit():
        raise HTTPException(422, "Dự án không hợp lệ")
    lid = int(raw_list_id)
    if lid not in visible_ids:
        raise HTTPException(403, "Không có quyền xem dự án này")
    return {lid}


def list_meta(db: Session, list_ids, need_group_names: bool = True) -> dict[int, dict]:
    """Tên dự án (LUÔN cần — breakdown "Top dự án theo quá hạn" dùng tới) + tên NHÓM dự
    án (chỉ hỏi thêm khi `group_by="group"`, điểm 4 — một JOIN không rẻ cho dải KPI)."""
    if not list_ids:
        return {}
    lists = (db.query(WorkList.id, WorkList.name, WorkList.group_id)
            .filter(WorkList.id.in_(list_ids)).all())
    group_names: dict[int, str] = {}
    if need_group_names:
        group_ids = {gid for _, _, gid in lists if gid}
        if group_ids:
            group_names = {g.id: g.name for g in db.query(WorkGroup).filter(WorkGroup.id.in_(group_ids)).all()}
    return {lid: {"name": name, "group_id": gid or 0, "group_name": group_names.get(gid, "") if gid else ""}
            for lid, name, gid in lists}


def company_names(db: Session) -> dict[int, str]:
    return dict(db.query(Company.id, Company.name).all())


def employee_names(db: Session, emp_ids) -> dict[int, str]:
    """Tên hiển thị PIC — chỉ HỌ TÊN (chốt review 01/10/2026, điểm 5); mã nhân sự
    chỉ dự phòng khi hồ sơ chưa nhập tên."""
    if not emp_ids:
        return {}
    people = (db.query(Employee.id, Employee.code, Employee.full_name)
             .filter(Employee.id.in_(emp_ids)).all())
    return {eid: (name or code) for eid, code, name in people}
