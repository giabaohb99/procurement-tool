"""Báo cáo Đặt xe (phase 05, 5.1).

Router RIÊNG chỉ chứa `/summary` + `/summary/export` (khung báo cáo kiểu Haravan,
`core/report_aggregate.py`). Đăng ký trong `main.py` TRƯỚC router chính của phân hệ để
`/summary` không bị `/{id}` nuốt (422).

Cùng `require` + `apply_scope` với danh sách Đặt xe (`controller.list_bookings`) — kể cả
nhánh tài xế (chỉ thấy chuyến được phân) và `dept_proc` — khung báo cáo không biết gì về
quyền, mọi việc gác nằm ở `fetch()` dưới đây. Bỏ `BK_DRAFT` (chưa gửi duyệt thì không
tính vào số liệu); kỳ tính theo NGÀY ĐI (`start_time`, Q5.1).

Ô lọc "Công ty" (review 01/10/2026, [H1]): `company_id` đọc bằng
`procurement_summary_rows.valid_company_id` (rỗng -> không lọc; rác -> 422, không 500) rồi
lọc SAU `apply_scope` — chỉ THU HẸP thêm phạm vi đã có, không bao giờ mở rộng.

Review hiệu năng 01/10/2026: `fetch()` không còn nạp MỖI PHIẾU một hàng rồi tra
`turnaround_hours()` chia lô 900 id — `report_grouped_fetch.fetch_grouped_rows()` GOM Ở SQL
(GROUP BY ngày/trạng thái/loại[, chiều group_by] + JOIN giờ duyệt một lượt), xem docstring
`report_service.py`.
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.auth import get_perm_profile, require
from app.core.database import get_db
from app.core.report_aggregate import build_report
from app.core.report_export import report_xlsx
from app.core.report_keys import ReportKey
from app.core.report_period import parse_period, range_filter
from app.core.response import success
from app.core.scoping import apply_scope
from app.modules.report.procurement_summary_rows import valid_company_id
from app.modules.report_access.guard import require_report

from . import report_service
from .model import BK_DRAFT, VehicleBooking
from .report_grouped_fetch import fetch_grouped_rows

router = APIRouter(prefix="/api/vehicle-bookings", tags=["vehicle-booking"])


def _fetch_builder(db: Session, user, prof: dict, group_by: str | None, company_id: int | None):
    """`fetch(d_from, d_to)` đã scope — dùng chung cho `/summary` và `/summary/export`.

    `fetch_grouped_rows` (review hiệu năng 01/10/2026): GOM Ở SQL ngay trong câu truy vấn đã
    scope, không nạp object ORM đầy đủ của từng phiếu. `group_by` truyền xuống cả hai bước
    (GROUP BY ở SQL + tra nhãn ở `decorate()`) để chỉ dùng đúng chiều đang cần (xem docstring
    `report_service.py`)."""

    def fetch(d_from, d_to):
        q = (db.query(VehicleBooking)
             .filter(VehicleBooking.is_deleted == False, VehicleBooking.status != BK_DRAFT))  # noqa: E712
        q = apply_scope(q, VehicleBooking, "vehicle_booking", user, prof)
        if company_id is not None:   # [H1] lọc SAU scope — chỉ thu hẹp
            q = q.filter(VehicleBooking.company_id == company_id)
        q = q.filter(range_filter(VehicleBooking.start_time, "str", d_from, d_to))
        rows = fetch_grouped_rows(db, q, group_by)
        return report_service.decorate(db, rows, group_by)

    return fetch


@router.get("/summary", dependencies=[Depends(require_report(ReportKey.VEHICLE_BOOKING))])
def booking_summary(request: Request, db: Session = Depends(get_db),
                    user=Depends(require("vehicle_booking", "read"))):
    prof = get_perm_profile(db, user)
    period = parse_period(request.query_params)
    group_by = request.query_params.get("group_by") or None
    cid = valid_company_id(request.query_params.get("company_id"))
    data = build_report(_fetch_builder(db, user, prof, group_by, cid),
                        report_service.build_spec(), period, group_by=group_by)
    return success(data)


@router.get("/summary/export", dependencies=[Depends(require_report(ReportKey.VEHICLE_BOOKING))])
def booking_summary_export(request: Request, db: Session = Depends(get_db),
                           user=Depends(require("vehicle_booking", "export"))):
    prof = get_perm_profile(db, user)
    period = parse_period(request.query_params)
    group_by = request.query_params.get("group_by") or None
    cid = valid_company_id(request.query_params.get("company_id"))
    data = build_report(_fetch_builder(db, user, prof, group_by, cid),
                        report_service.build_spec(), period, group_by=group_by)
    return report_xlsx("dat-xe", data)
