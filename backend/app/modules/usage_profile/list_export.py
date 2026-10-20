"""Xuất Excel danh sách hồ sơ (duoc-CR-641, phase 05). Dữ liệu cá nhân rời hệ thống nên MỖI lần xuất ghi `tab_export_log`
(entity `usage_profile`); lượt GET này cũng nằm trong `tab_request_log` — đủ trả lời «ai đã xem/xuất hồ sơ ai»."""
from sqlalchemy.orm import Session

from app.core.export_xlsx import Col, check_row_limit, xlsx_response
from app.modules.export_log.model import ExportLog

from . import list_service
from .metric_catalog import METRIC_CATALOG
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


def format_metric_cell(v: float | None, unit: str):
    """Giá trị chỉ số cho ô Excel theo ĐƠN VỊ (duoc-CR-650): giờ trong ngày ra HH:MM, thời lượng kèm đơn vị, cờ ra Có/Không.

    Tỷ lệ trả số thang 0-100 cho cột `percent`; còn lại trả chữ để ô CHƯA ĐO được để trống (không thành 0).
    """
    if v is None:
        return None
    if unit == "ratio":
        return round(v * 100, 2)
    if unit == "minute_of_day":
        m = int(round(v)) % 1440
        return f"{m // 60:02d}:{m % 60:02d}"
    if unit == "min":
        return f"{v:g} phút"
    if unit == "h":
        return f"{round(v, 1):g} giờ"
    if unit == "ms":
        return f"{round(v / 1000, 1):g} giây"
    if unit == "flag":
        return "Có" if v else "Không"
    return f"{v:g}"


def export_summary(db: Session, user, f: ListFilters, metric_label: str | None = None):
    label_week, _since = list_service.latest_label_week_and_since(db, f.date_to)
    total = list_service.count_users(db, f, label_week)
    check_row_limit(total)
    items = list_service.decorate(db, list_service.fetch_rows(db, f, label_week), label_week, bool(f.metric)) if total else []
    columns = COLUMNS
    if f.metric:
        #  duoc-CR-650: thêm cột chỉ số đang xem. Chưa đo được PHẢI để ô trống, không phải 0: chỉ kind="percent" của
        #  khung xuất giữ None thành ô trống (thang 0-100) nên tỷ lệ nhân 100; đơn vị khác ghi chữ để ô trống được.
        unit = METRIC_CATALOG[f.metric].unit
        #  Tên tiếng Việt của chỉ số nằm ở giao diện (R2) — giao diện gửi kèm `metric_label`; thiếu thì dùng mã.
        header = metric_label or f"Chỉ số {f.metric}"
        columns = [*COLUMNS, Col("metric_value", header, kind="percent" if unit == "ratio" else "text", width=24)]
        for it in items:
            it["metric_value"] = format_metric_cell(it["metric_value"], unit)
    rows = [{**it, "cohort_name": (it["cohort"] or {}).get("name", ""),
             "labels": ", ".join(str(l["code"]) for l in it["labels"])} for it in items]
    name = f"ho-so-cach-lam-viec-{f.date_from}-{f.date_to}"
    response = xlsx_response(name, columns, rows, "Ho so")
    db.add(ExportLog(entity=ENTITY, fmt="xlsx", row_count=len(rows), filename=f"{name}.xlsx",
                     file_size=len(response.body), file_id=0, filter_summary="", created_by=user.id,
                     updated_by=user.id))
    db.commit()
    return response
