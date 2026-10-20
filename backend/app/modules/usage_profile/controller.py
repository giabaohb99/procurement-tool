"""API đọc hồ sơ cách làm việc (duoc-CR-641, phase 05) — `prefix=/api/usage-profiles`.

Gác KÉP như 13 báo cáo cũ: `require("setting", …)` (cửa quyền phân hệ Quản trị) VÀ `require_report(ReportKey.USAGE_PROFILE)`
(chủ sản phẩm: mặc định chỉ admin; admin gán thêm ở Phân quyền → Báo cáo). Admin xem TẤT CẢ người (không `apply_scope`:
khóa `setting` không có bảng để lọc). KHÔNG có đường «hồ sơ của tôi», không mở cho quản lý. Mỗi lần mở hồ sơ để lại một dòng
`tab_request_log` (GET không bị loại) — đủ trả lời «ai đã xem hồ sơ ai».
`/summary`, `/summary/export`, `/cohorts`, `/metrics`, `/by-app` khai TRƯỚC `/{user_id}` để không bị đường tham số nuốt.
"""
from datetime import date

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.auth import require
from app.core.database import get_db
from app.core.report_keys import ReportKey
from app.core.report_period import parse_period
from app.core.response import success
from app.modules.report_access.guard import require_report

from . import app_split_service, cohort_service, list_export, metric_catalog_service, list_service, profile_service
from .schema import MAX_LABELS, MAX_METRIC_LEN, MAX_PAGE_SIZE, MAX_Q_LEN, MAX_WEEKS, ListFilters, parse_sort, validate_labels, validate_metric

router = APIRouter(prefix="/api/usage-profiles", tags=["usage-profile"])
GUARD = [Depends(require_report(ReportKey.USAGE_PROFILE))]


def _filters(request: Request, company_id, department_id, role_id, label, q, sort, metric) -> ListFilters:
    #  Dùng chung bộ kỳ của các báo cáo (preset / date_from / date_to); compare không dùng ở đây.
    period = parse_period({**request.query_params, "compare": "none"})
    parse_sort(sort)   # 422 sớm nếu cột lạ
    return ListFilters(period.date_from, period.date_to, company_id, department_id, role_id,
                       validate_labels(label), (q or "").strip(), sort, validate_metric(metric, sort))


MAX_METRIC_LABEL_LEN = 80


@router.get("/summary", dependencies=GUARD)
def usage_summary(request: Request, company_id: int | None = Query(None, ge=1),
                  department_id: int | None = Query(None, ge=1), role_id: int | None = Query(None, ge=1),
                  label: list[int] | None = Query(None, max_length=MAX_LABELS), q: str | None = Query(None, max_length=MAX_Q_LEN),
                  page: int = Query(1, ge=1, le=10000), page_size: int = Query(20, ge=1, le=MAX_PAGE_SIZE),
                  sort: str = Query("full_name", max_length=40), metric: str | None = Query(None, max_length=MAX_METRIC_LEN),
                  db: Session = Depends(get_db), user=Depends(require("setting", "read"))):
    f = _filters(request, company_id, department_id, role_id, label, q, sort, metric)
    return success(list_service.summary(db, f, page, page_size))


@router.get("/summary/export", dependencies=GUARD)
def usage_summary_export(request: Request, company_id: int | None = Query(None, ge=1),
                         department_id: int | None = Query(None, ge=1), role_id: int | None = Query(None, ge=1),
                         label: list[int] | None = Query(None, max_length=MAX_LABELS), q: str | None = Query(None, max_length=MAX_Q_LEN),
                         sort: str = Query("full_name", max_length=40),
                         metric: str | None = Query(None, max_length=MAX_METRIC_LEN),
                         metric_label: str | None = Query(None, max_length=MAX_METRIC_LABEL_LEN),
                         db: Session = Depends(get_db), user=Depends(require("setting", "export"))):
    f = _filters(request, company_id, department_id, role_id, label, q, sort, metric)
    #  Chỉ là chữ tiêu đề cột: bỏ ký tự điều khiển (chống chèn công thức / xuống dòng lạ vào ô Excel).
    clean_label = "".join(ch for ch in (metric_label or "") if ch.isprintable()).strip().lstrip("=+-@") or None
    return list_export.export_summary(db, user, f, clean_label)


@router.get("/cohorts", dependencies=GUARD)
def usage_cohorts(week: date | None = Query(None), db: Session = Depends(get_db),
                  user=Depends(require("setting", "read"))):
    return success(cohort_service.list_cohorts(db, week))


@router.get("/metrics", dependencies=GUARD)
def usage_metrics(db: Session = Depends(get_db), user=Depends(require("setting", "read"))):
    #  duoc-CR-649: danh mục chỉ số + số người đo được / trung vị công ty của tuần mới nhất (chỉ khóa và mã).
    return success(metric_catalog_service.list_metrics(db))


@router.get("/by-app", dependencies=GUARD)
def usage_by_app(request: Request, db: Session = Depends(get_db), user=Depends(require("setting", "read"))):
    #  bao-CR-649: sự kiện giao diện tách theo app gửi (ERP v2 / thumua) trong kỳ — đọc thẳng tab_ui_event (90 ngày).
    period = parse_period({**request.query_params, "compare": "none"})
    return success(app_split_service.split_by_app(db, period.date_from, period.date_to))


@router.get("/{user_id}", dependencies=GUARD)
def usage_profile(user_id: int, weeks: int = Query(8, ge=1, le=MAX_WEEKS), db: Session = Depends(get_db),
                  user=Depends(require("setting", "read"))):
    return success(profile_service.get_profile(db, user_id, weeks))
