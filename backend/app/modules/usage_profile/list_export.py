"""Xuất Excel danh sách hồ sơ (duoc-CR-641, phase 05). Dữ liệu cá nhân rời hệ thống nên MỖI lần xuất ghi `tab_export_log`
(entity `usage_profile`); lượt GET này cũng nằm trong `tab_request_log` — đủ trả lời «ai đã xem/xuất hồ sơ ai»."""
from sqlalchemy.orm import Session

from app.core.export_xlsx import Col, check_row_limit, xlsx_response
from app.modules.export_log.model import ExportLog

from . import list_service
from .schema import ListFilters

ENTITY = "usage_profile"

COLUMNS = [
    Col("emp_code", "Mã NV", width=14), Col("full_name", "Họ tên", width=26),
    Col("department_name", "Phòng ban", width=24), Col("cohort_name", "Nhóm so sánh", width=22),
    Col("active_days", "Ngày có vào", kind="int", width=12), Col("workdays_net", "Ngày làm việc ròng", kind="qty", width=16),
    Col("active_ratio", "Tỷ lệ ngày có vào", kind="percent", width=16),
    Col("api_writes", "Lượt ghi", kind="int", width=12), Col("docs_created", "Phiếu lập", kind="int", width=12),
    Col("approvals", "Lượt duyệt", kind="int", width=12), Col("exports", "Lượt xuất", kind="int", width=12),
    Col("http_422_per_100_writes", "Lỗi 422/100 lượt lưu", kind="qty", width=18),
    Col("labels", "Kiểu làm việc (mã)", width=22), Col("last_active_day", "Hoạt động gần nhất", kind="date", width=18),
]


def export_summary(db: Session, user, f: ListFilters):
    label_week, _since = list_service.latest_label_week_and_since(db, f.date_to)
    total = list_service.count_users(db, f, label_week)
    check_row_limit(total)
    items = list_service.decorate(db, list_service.fetch_rows(db, f, label_week), label_week) if total else []
    rows = [{**it, "cohort_name": (it["cohort"] or {}).get("name", ""),
             "labels": ", ".join(str(l["code"]) for l in it["labels"])} for it in items]
    name = f"ho-so-cach-lam-viec-{f.date_from}-{f.date_to}"
    response = xlsx_response(name, COLUMNS, rows, "Ho so")
    db.add(ExportLog(entity=ENTITY, fmt="xlsx", row_count=len(rows), filename=f"{name}.xlsx",
                     file_size=len(response.body), file_id=0, filter_summary="", created_by=user.id,
                     updated_by=user.id))
    db.commit()
    return response
