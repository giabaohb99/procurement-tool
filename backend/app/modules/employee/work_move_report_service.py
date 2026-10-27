"""Báo cáo D1 «Điều chuyển & bổ nhiệm» (khóa 24, duoc-CR-688) — `GET /api/work-moves/summary`.

Hàng = dòng quá trình công tác có `from_date` trong kỳ (đã áp lẫn chưa áp vào hồ sơ). Hai chỉ số
THỜI ĐIỂM «kiêm nhiệm đang hiệu lực / hết trong 30 ngày» tính tại `min(cuối kỳ, hôm nay)` và chỉ có ở
Tổng. Dữ liệu ở `work_move_report_data.py`; `/summary/rows` dùng đúng `MoveRow` + `key_of`.
"""
from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.hr_work_history_codes import WORK_EVENT_TYPE_LABELS, WorkEventType
from app.core.report_aggregate import DerivedSpec, DimensionSpec, MetricSpec, ReportSpec, build_report
from app.core.report_drilldown import Col, filter_group, rows_response
from app.core.report_period import Period
from app.core.vn_time import vn_today
from app.modules.employee import work_move_report_data as data_mod
from app.modules.employee.profile_gaps_report_data import load_group_names
from app.modules.employee.work_move_report_data import MoveRow

UNKNOWN = "(Chưa rõ)"
EXPIRING_DAYS = 30
_MONTH_DAYS = 30.4375
#  khóa chỉ số -> loại sự kiện
EVENT_METRICS = {"hires": WorkEventType.HIRE, "transfers": WorkEventType.TRANSFER,
                 "appoints": WorkEventType.APPOINT, "concurrents": WorkEventType.CONCURRENT,
                 "dismisses": WorkEventType.DISMISS, "resigns": WorkEventType.RESIGN}
_EVENT_LABELS = {"hires": "Tuyển dụng", "transfers": "Điều chuyển", "appoints": "Bổ nhiệm",
                 "concurrents": "Kiêm nhiệm", "dismisses": "Miễn nhiệm", "resigns": "Thôi việc",
                 "others": "Sự kiện khác"}
DRILLDOWN_METRICS = {**_EVENT_LABELS, "people_moved": "Số người có biến động",
                     "avg_months_to_appoint": "Số tháng từ lúc vào làm tới lần bổ nhiệm",
                     "concurrent_active": "Kiêm nhiệm đang hiệu lực",
                     "concurrent_expiring_30": "Kiêm nhiệm hết trong 30 ngày"}
_KNOWN = {int(t) for t in EVENT_METRICS.values()}


def _months_to_appoint(r: MoveRow) -> float | None:
    """Tháng từ ngày vào làm tới ngày bổ nhiệm; None khi không phải bổ nhiệm / thiếu hoặc sai ngày vào."""
    if r.event_type != int(WorkEventType.APPOINT) or r.hire_date is None or r.from_date < r.hire_date:
        return None
    return (r.from_date - r.hire_date).days / _MONTH_DAYS


def _dept_label(names: dict, dept_id: int) -> str:
    return names.get(dept_id, "") or UNKNOWN if dept_id else UNKNOWN


def _spec(company_name: dict, department_name: dict) -> tuple[ReportSpec, dict]:
    metrics = [MetricSpec(k, _EVENT_LABELS[k], value_of=lambda r, t=int(t): int(r.event_type == t))
               for k, t in EVENT_METRICS.items()]
    metrics.append(MetricSpec("others", _EVENT_LABELS["others"],
                              value_of=lambda r: int(r.event_type not in _KNOWN)))
    metrics += [
        MetricSpec("people_moved", DRILLDOWN_METRICS["people_moved"], distinct_of=lambda r: r.employee_id),
        MetricSpec("appoint_months_sum", "Tổng tháng tới lúc bổ nhiệm", helper=True,
                   value_of=lambda r: _months_to_appoint(r) or 0),
        MetricSpec("appoint_months_n", "Số lần bổ nhiệm có ngày vào làm", helper=True,
                   value_of=lambda r: int(_months_to_appoint(r) is not None)),
        MetricSpec("concurrent_active", DRILLDOWN_METRICS["concurrent_active"], snapshot=True,
                   value_of=lambda r: 0),
        MetricSpec("concurrent_expiring_30", DRILLDOWN_METRICS["concurrent_expiring_30"], snapshot=True,
                   good="down", value_of=lambda r: 0),
    ]
    derived = [DerivedSpec("avg_months_to_appoint", DRILLDOWN_METRICS["avg_months_to_appoint"],
                           num="appoint_months_sum", den="appoint_months_n", kind="number", scale=1.0)]
    dims = {
        "event_type": DimensionSpec("event_type", "Loại sự kiện", key_of=lambda r: [
            (r.event_type, WORK_EVENT_TYPE_LABELS.get(r.event_type, "Khác"))]),
        "department": DimensionSpec("department", "Phòng đến", key_of=lambda r: (
            [(r.department_id, department_name.get(r.department_id, ""))] if r.department_id else [])),
        "company": DimensionSpec("company", "Công ty", key_of=lambda r: (
            [(r.company_id, company_name.get(r.company_id, ""))] if r.company_id else [])),
        "flow": DimensionSpec("flow", "Phòng đi → Phòng đến", key_of=lambda r: [
            (f"{r.from_department_id}>{r.department_id}",
             f"{_dept_label(department_name, r.from_department_id)} → "
             f"{_dept_label(department_name, r.department_id)}")]),
    }
    return ReportSpec(date_of=lambda r: r.from_date, metrics=metrics, derived=derived, dimensions=dims,
                      rank_by="people_moved"), dims


def _names(db: Session, group_by: str | None, always: bool = False) -> tuple[dict, dict]:
    #  `flow` cần tên phòng ban dù không phải chiều "department".
    return load_group_names(db, "department" if group_by == "flow" else group_by, always)


def _snapshot(db: Session, user, prof: dict, kw: dict):
    def snap(day) -> dict:
        as_of = min(day, vn_today())
        active = data_mod.concurrent_lines(db, user, prof, as_of, with_origin=False, **kw)
        limit = as_of.toordinal() + EXPIRING_DAYS
        return {"concurrent_active": len(active),
                "concurrent_expiring_30": sum(1 for r in active
                                              if r.to_date and r.to_date.toordinal() <= limit)}
    return snap


def build_summary(db: Session, user, prof: dict, period: Period, group_by: str | None,
                  company_id: int | None = None, department_id: int | None = None,
                  action: str = "read") -> dict:
    spec, _ = _spec(*_names(db, group_by))
    kw = dict(company_id=company_id, department_id=department_id, action=action)
    data = build_report(lambda f, t: data_mod.period_lines(db, user, prof, f, t, **kw), spec, period,
                        group_by=group_by, snapshot=_snapshot(db, user, prof, kw))
    data["meta"]["drilldown_metrics"] = list(DRILLDOWN_METRICS)
    data["notes"] = [
        "Tính cả dòng đã áp lẫn CHƯA áp vào hồ sơ; kỳ lọc theo «Từ ngày» (ngày hiệu lực) của dòng.",
        "Bộ lọc phòng ban/công ty theo hồ sơ HIỆN TẠI của người có dòng đó, không theo phòng đến/đi.",
        "«Phòng đi» lấy từ dòng nhóm chính liền trước của cùng người; dòng đầu tiên mà chưa rõ phòng "
        f"đi hiện là «{UNKNOWN}».",
        f"«Kiêm nhiệm đang hiệu lực / hết trong {EXPIRING_DAYS} ngày» là số tại cuối kỳ (hoặc hôm nay "
        "nếu kỳ chưa kết thúc), chỉ hiện ở Tổng.",
        "Số tháng tới lần bổ nhiệm bỏ qua dòng bổ nhiệm của người thiếu ngày vào làm.",
    ]
    return data


_COLUMNS = [Col("employee_code", "Mã NV"), Col("employee_name", "Họ tên"), Col("event", "Loại"),
            Col("from_date", "Từ ngày", "date"), Col("to_date", "Đến ngày", "date"),
            Col("from_department", "Phòng đi"), Col("department", "Phòng đến"),
            Col("position", "Chức vụ"), Col("decision_no", "Số quyết định")]


def build_rows(db: Session, user, prof: dict, period: Period, metric: str, group_by: str | None,
               group_key: str | None, company_id: int | None, department_id: int | None) -> dict:
    company_name, department_name = _names(db, group_by, always=True)
    _, dims = _spec(company_name, department_name)
    if group_by and group_by != "none" and group_by not in dims:
        raise HTTPException(422, f"Xem theo không hợp lệ: {group_by}")
    kw = dict(company_id=company_id, department_id=department_id)
    columns = _COLUMNS
    if metric in ("concurrent_active", "concurrent_expiring_30"):
        as_of = min(period.date_to, vn_today())
        lines = data_mod.concurrent_lines(db, user, prof, as_of, EXPIRING_DAYS if metric.endswith("30") else None,
                                          **kw)
    else:
        lines = data_mod.period_lines(db, user, prof, period.date_from, period.date_to, **kw)
        if metric in EVENT_METRICS:
            lines = [r for r in lines if r.event_type == int(EVENT_METRICS[metric])]
        elif metric == "others":
            lines = [r for r in lines if r.event_type not in _KNOWN]
        elif metric == "avg_months_to_appoint":
            lines = [r for r in lines if _months_to_appoint(r) is not None]
            columns = [*_COLUMNS, Col("months", "Số tháng từ lúc vào làm")]
    lines = filter_group(lines, dims.get(group_by) if group_by else None, group_key)
    lines.sort(key=lambda r: (r.from_date, r.line_id), reverse=True)
    move_counts: dict[int, int] = {}
    if metric == "people_moved":
        #  Thẻ đếm NGƯỜI nên danh sách mỗi người một dòng: lấy sự kiện mới nhất trong kỳ + «Số lượt».
        for r in lines:
            move_counts[r.employee_id] = move_counts.get(r.employee_id, 0) + 1
        seen: set[int] = set()
        latest = []
        for r in lines:       # đã xếp mới nhất trước
            if r.employee_id not in seen:
                seen.add(r.employee_id)
                latest.append(r)
        lines = latest
        columns = [*_COLUMNS, Col("move_count", "Số lượt")]
    out = [{"employee_code": r.code, "employee_name": r.name,
            "event": WORK_EVENT_TYPE_LABELS.get(r.event_type, "Khác"), "from_date": r.from_date,
            "to_date": r.to_date, "from_department": _dept_label(department_name, r.from_department_id),
            "department": _dept_label(department_name, r.department_id), "position": r.position,
            "decision_no": r.decision_no, "link": f"/hr/employees/{r.employee_id}"} for r in lines]
    if metric == "people_moved":
        for row, r in zip(out, lines):
            row["move_count"] = move_counts[r.employee_id]
    if metric == "avg_months_to_appoint":     # cột số tháng chỉ có ở danh sách này; giá trị là SỐ
        for row, r in zip(out, lines):
            row["months"] = round(_months_to_appoint(r) or 0, 1)
    return rows_response(metric, DRILLDOWN_METRICS[metric], columns, out)
