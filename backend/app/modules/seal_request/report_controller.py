"""Báo cáo Duyệt đóng dấu (phase 05, 5.2).

Router RIÊNG chỉ chứa `/summary` + `/summary/export` (khung báo cáo kiểu Haravan,
`core/report_aggregate.py`). Đăng ký trong `main.py` TRƯỚC router chính của phân hệ để
`/summary` không bị `/{id}` nuốt (422).

Cùng `require` + `apply_scope` với danh sách Duyệt dấu (`controller.list_seal_requests`) —
GIỮ NGUYÊN luật company/văn thư (bậc `company` chỉ thấy phiếu ĐÃ DUYỆT/HOÀN THÀNH, lọc
qua bảng nối nhiều công ty). Bỏ `SEAL_DRAFT` THÊM ở đây (áp cho MỌI bậc phạm vi, kể cả
`own`/`dept` vẫn thấy nháp qua danh sách thường); kỳ tính theo `created_at` (Q5.2).

Ô lọc "Công ty" (review 01/10/2026, [H1]): `company_id` đọc bằng
`procurement_summary_rows.valid_company_id` (rỗng -> không lọc; rác -> 422, không 500) rồi
lọc SAU `apply_scope` — chỉ THU HẸP thêm. Một phiếu gắn NHIỀU công ty qua bảng nối
`tab_seal_request_company`, nên lọc bằng `IN (subquery)` trên bảng nối — KHÔNG so cột
`SealRequest.company_id` đơn (chỉ là "công ty chính", phiếu 2 công ty A+B lọc theo B vẫn
phải hiện, cột đơn chỉ giữ A thì B sẽ bị bỏ sót).
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
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
from .model import SEAL_DRAFT, SealRequest, SealRequestCompany

router = APIRouter(prefix="/api/seal-requests", tags=["seal-request"])


def _fetch_builder(db: Session, user, prof: dict, group_by: str | None, company_id: int | None):
    """`fetch(d_from, d_to)` đã scope — dùng chung cho `/summary` và `/summary/export`.

    `with_entities(*FETCH_COLUMNS)` (review hiệu năng 01/10/2026): chỉ kéo đúng cột cần,
    không nạp object ORM đầy đủ. `group_by` truyền xuống `decorate()` để nó chỉ tra nhãn
    của ĐÚNG chiều đang dùng (xem docstring `report_service.py`)."""

    def fetch(d_from, d_to):
        q = (db.query(SealRequest)
             .filter(SealRequest.is_deleted == False, SealRequest.status != SEAL_DRAFT))  # noqa: E712
        q = apply_scope(q, SealRequest, "seal_request", user, prof)
        if company_id is not None:   # [H1] lọc SAU scope, qua BẢNG NỐI — chỉ thu hẹp
            sub = select(SealRequestCompany.seal_request_id).where(
                SealRequestCompany.company_id == company_id)
            q = q.filter(SealRequest.id.in_(sub))
        q = q.filter(range_filter(SealRequest.created_at, "datetime_utc", d_from, d_to))
        rows = q.with_entities(*report_service.FETCH_COLUMNS).all()
        return report_service.decorate(db, rows, group_by)

    return fetch


@router.get("/summary", dependencies=[Depends(require_report(ReportKey.SEAL_REQUEST))])
def seal_summary(request: Request, db: Session = Depends(get_db),
                 user=Depends(require("seal_request", "read"))):
    prof = get_perm_profile(db, user)
    period = parse_period(request.query_params)
    group_by = request.query_params.get("group_by") or None
    cid = valid_company_id(request.query_params.get("company_id"))
    data = build_report(_fetch_builder(db, user, prof, group_by, cid),
                        report_service.build_spec(), period, group_by=group_by)
    return success(data)


@router.get("/summary/export", dependencies=[Depends(require_report(ReportKey.SEAL_REQUEST))])
def seal_summary_export(request: Request, db: Session = Depends(get_db),
                        user=Depends(require("seal_request", "export"))):
    prof = get_perm_profile(db, user)
    period = parse_period(request.query_params)
    group_by = request.query_params.get("group_by") or None
    cid = valid_company_id(request.query_params.get("company_id"))
    data = build_report(_fetch_builder(db, user, prof, group_by, cid),
                        report_service.build_spec(), period, group_by=group_by)
    return report_xlsx("duyet-dong-dau", data)
