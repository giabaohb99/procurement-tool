"""Báo cáo A3 "Cơ cấu quản lý" (khóa 23, duoc-CR-688) — `GET /api/management-span/summary`.

Ảnh chụp TẠI MỘT MỐC: `as_of = min(cuối kỳ, hôm nay)`. Kỳ chỉ quyết định mốc và khoảng đếm người
nghỉ việc; không có xu hướng (`trend = []`) và không có kỳ so sánh (`totals.compare = null`).
Dữ liệu + định nghĩa ba loại hàng ở `management_report_data.py`; `/summary/rows` dùng đúng
`SpanRow` + đúng `key_of` của chiều gom nên danh sách khớp con số trên bảng.
"""
from __future__ import annotations

from dataclasses import replace
from datetime import date

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.report_aggregate import DerivedSpec, DimensionSpec, MetricSpec, ReportSpec, build_report
from app.core.report_drilldown import Col, filter_group, rows_response
from app.core.report_period import Period
from app.core.vn_time import vn_today
from app.modules.employee.constants import JOB_LEVEL_LABELS
from app.modules.employee.management_report_data import SPAN_WIDE_OVER, SpanRow, load_rows
from app.modules.employee.profile_gaps_report_data import load_group_names

DRILLDOWN_METRICS = {"managers": "Người có cấp dưới", "unassigned_manager": "Chưa gán quản lý trực tiếp",
                     "manager_resigned": "Quản lý trực tiếp đã nghỉ", "span_one": "Quản lý chỉ 1 cấp dưới",
                     "span_wide": f"Quản lý trên {SPAN_WIDE_OVER} cấp dưới",
                     "departures_under": "Nghỉ việc trong kỳ (theo quản lý hiện tại)"}


def as_of_of(period: Period) -> date:
    return min(period.date_to, vn_today())


def _spec(company_name: dict, department_name: dict, manager_label: dict) -> tuple[ReportSpec, dict]:
    metrics = [
        MetricSpec("staff", "Nhân sự đang làm", value_of=lambda r: int(r.kind == "p")),
        MetricSpec("managers", "Người có cấp dưới", value_of=lambda r: int(r.kind == "m")),
        MetricSpec("direct_reports", "Tổng cấp dưới trực tiếp",
                   value_of=lambda r: r.reports if r.kind == "m" else 0),
        MetricSpec("unassigned_manager", "Chưa gán quản lý trực tiếp", good="down",
                   value_of=lambda r: int(r.kind == "p" and not r.manager_id)),
        MetricSpec("manager_resigned", "Quản lý trực tiếp đã nghỉ", good="down",
                   value_of=lambda r: int(r.kind == "p" and r.manager_gone)),
        MetricSpec("span_one", "Quản lý chỉ 1 cấp dưới", good="down",
                   value_of=lambda r: int(r.kind == "m" and r.reports == 1)),
        MetricSpec("span_wide", f"Quản lý trên {SPAN_WIDE_OVER} cấp dưới", good="down",
                   value_of=lambda r: int(r.kind == "m" and r.reports > SPAN_WIDE_OVER)),
        MetricSpec("departures_under", "Nghỉ việc trong kỳ (theo quản lý hiện tại)", good="down",
                   value_of=lambda r: int(r.kind == "d")),
    ]
    derived = [DerivedSpec("avg_span", "Số cấp dưới bình quân", num="direct_reports", den="managers",
                           kind="number", scale=1.0, ndigits=1)]

    def manager_key(r: SpanRow):
        #  Hàng "m" nằm ở dòng CỦA CHÍNH quản lý đó; người thường/người nghỉ nằm ở dòng quản lý của họ.
        if r.kind == "p" and r.manager_gone:    # quản lý đã nghỉ = không còn người quản lý -> "(Chưa gắn)"
            return []
        mid = r.employee_id if r.kind == "m" else r.manager_id
        return [(mid, manager_label.get(mid, ""))] if mid else []

    dims = {
        "department": DimensionSpec("department", "Phòng ban", key_of=lambda r: (
            [(r.department_id, department_name.get(r.department_id, ""))] if r.department_id else [])),
        "company": DimensionSpec("company", "Công ty", key_of=lambda r: (
            [(r.company_id, company_name.get(r.company_id, ""))] if r.company_id else [])),
        "job_level": DimensionSpec("job_level", "Cấp bậc", key_of=lambda r: (
            [(r.job_level, JOB_LEVEL_LABELS.get(r.job_level, ""))] if r.job_level else [])),
        "manager": DimensionSpec("manager", "Quản lý", key_of=manager_key),
    }
    return ReportSpec(date_of=lambda r: None, metrics=metrics, derived=derived, dimensions=dims,
                      rank_by="staff"), dims


def build_summary(db: Session, user, prof: dict, period: Period, group_by: str | None,
                  company_id: int | None = None, department_id: int | None = None,
                  action: str = "read") -> dict:
    company_name, department_name = load_group_names(db, group_by)
    rows, labels = load_rows(db, user, prof, as_of_of(period), period.date_from, period.date_to,
                             company_id, department_id, action)
    spec, _ = _spec(company_name, department_name, labels)
    flat = replace(period, compare="none", compare_from=None, compare_to=None)
    data = build_report(lambda _f, _t: rows, spec, flat, group_by=group_by)
    data["period"] = period.as_dict()
    data["trend"] = []
    data["meta"]["drilldown_metrics"] = list(DRILLDOWN_METRICS)
    data["notes"] = [
        f"Ảnh chụp tại {as_of_of(period):%d/%m/%Y} (cuối kỳ hoặc hôm nay nếu kỳ chưa kết thúc); "
        "kỳ chỉ dùng để đếm người nghỉ việc. Không có xu hướng và không so sánh kỳ trước.",
        "Quản lý lấy theo hồ sơ HIỆN TẠI. Số cấp dưới chỉ tính người nằm trong phạm vi bạn xem; "
        "quản lý ngoài phạm vi/bộ lọc không được tính vào \"Người có cấp dưới\".",
        "Xem theo \"Quản lý\": mỗi quản lý một dòng — \"Nhân sự đang làm\" của dòng đó chính là số cấp dưới "
        "trực tiếp; dòng \"(Chưa gắn)\" là người chưa gán quản lý.",
        "\"Quản lý trực tiếp đã nghỉ\": người có quản lý ghi trên hồ sơ đã nghỉ việc / ngừng hoạt động — "
        "không tính là đã gán quản lý (không nằm trong số cấp dưới của ai).",
        "\"Nghỉ việc trong kỳ\" được tính theo quản lý hiện tại ghi trên hồ sơ người đã nghỉ.",
    ]
    return data


def _columns(metric: str) -> list[Col]:
    cols = [Col("code", "Mã NV"), Col("name", "Họ tên"), Col("department", "Phòng ban"),
            Col("position", "Chức vụ")]
    if metric == "manager_resigned":
        return cols + [Col("manager", "Quản lý trực tiếp (đã nghỉ)")]
    if metric == "departures_under":
        return cols + [Col("resign_date", "Ngày nghỉ việc", "date"), Col("manager", "Quản lý hiện tại")]
    return cols if metric == "unassigned_manager" else cols + [Col("reports", "Số cấp dưới", "int")]


def build_rows(db: Session, user, prof: dict, period: Period, metric: str, group_by: str | None,
               group_key: str | None, company_id: int | None, department_id: int | None) -> dict:
    company_name, department_name = load_group_names(db, group_by, always=True)
    rows, labels = load_rows(db, user, prof, as_of_of(period), period.date_from, period.date_to,
                             company_id, department_id)
    _, dims = _spec(company_name, department_name, labels)
    if group_by and group_by != "none" and group_by not in dims:
        raise HTTPException(422, f"Xem theo không hợp lệ: {group_by}")
    pick = {"managers": lambda r: r.kind == "m", "unassigned_manager": lambda r: r.kind == "p" and not r.manager_id,
            "manager_resigned": lambda r: r.kind == "p" and r.manager_gone,
            "span_one": lambda r: r.kind == "m" and r.reports == 1,
            "span_wide": lambda r: r.kind == "m" and r.reports > SPAN_WIDE_OVER,
            "departures_under": lambda r: r.kind == "d"}[metric]
    picked = filter_group([r for r in rows if pick(r)], dims.get(group_by) if group_by else None, group_key)
    picked.sort(key=lambda r: (-r.reports, r.code))
    out = [{"code": r.code, "name": r.name, "department": department_name.get(r.department_id, ""),
            "position": r.position, "reports": r.reports, "resign_date": r.resign_date,
            "manager": labels.get(r.manager_id, ""), "link": f"/hr/employees/{r.employee_id}"}
           for r in picked]
    return rows_response(metric, DRILLDOWN_METRICS[metric], _columns(metric), out)
