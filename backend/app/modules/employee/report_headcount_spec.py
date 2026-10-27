"""Khai báo `ReportSpec` (chỉ số + chiều) của báo cáo Biến động nhân sự — tách khỏi
`report_service.py` để giữ < 200 dòng, và để danh sách «bấm số» (`report_drill_rows.py`) dùng
lại ĐÚNG các `DimensionSpec.key_of` khi lọc nhóm."""
from __future__ import annotations

from app.core.report_aggregate import DimensionSpec, MetricSpec, ReportSpec
from app.core.status_codes import EMPLOYEE_STATUS
from app.modules.employee.constants import EMPLOYMENT_TYPE_LABELS, GENDER_LABELS, JOB_LEVEL_LABELS

#  Chỉ số bấm được ra danh sách nhân sự (`GET /api/employees/summary/rows`).
DRILLDOWN_METRICS = {"new_hires": "Vào mới", "departures": "Nghỉ việc",
                     "headcount_end": "Định biên cuối kỳ"}


def build_spec(company_name: dict, department_name: dict) -> tuple[ReportSpec, DimensionSpec]:
    metrics = [
        MetricSpec("new_hires", "Vào mới", kind="int",
                  value_of=lambda r: 1 if r.kind == "hire" else 0),
        MetricSpec("departures", "Nghỉ việc", kind="int", good="down",
                  value_of=lambda r: 1 if r.kind == "resign" else 0),
        #  Bốn chỉ số THỜI ĐIỂM — `value_of` luôn 0 (bị `drop_snapshot` bỏ khỏi trend/groups,
        #  M1 của khung); giá trị THẬT ghép vào `totals`/`groups` SAU khi `build_report` chạy xong.
        MetricSpec("headcount_start", "Định biên đầu kỳ", kind="int", snapshot=True,
                  value_of=lambda r: 0),
        MetricSpec("headcount_end", "Định biên cuối kỳ", kind="int", snapshot=True,
                  value_of=lambda r: 0),
        MetricSpec("net_change", "Thay đổi ròng", kind="int", snapshot=True, value_of=lambda r: 0),
        MetricSpec("turnover_rate", "Tỷ lệ nghỉ việc", kind="percent", good="down", snapshot=True,
                  value_of=lambda r: 0),
    ]
    dimensions = {
        "company": DimensionSpec("company", "Công ty", key_of=lambda r: (
            [(r.company_id, company_name.get(r.company_id, ""))] if r.company_id else [])),
        "department": DimensionSpec("department", "Phòng ban", key_of=lambda r: (
            [(r.department_id, department_name.get(r.department_id, ""))] if r.department_id else [])),
        "job_level": DimensionSpec("job_level", "Cấp bậc", key_of=lambda r: (
            [(r.job_level, JOB_LEVEL_LABELS.get(r.job_level, ""))] if r.job_level else [])),
        "employment_type": DimensionSpec("employment_type", "Loại hình", key_of=lambda r: (
            [(r.employment_type, EMPLOYMENT_TYPE_LABELS.get(r.employment_type, ""))]
            if r.employment_type else [])),
        "gender": DimensionSpec("gender", "Giới tính", key_of=lambda r: (
            [(r.gender, GENDER_LABELS.get(r.gender, ""))] if r.gender else [])),
        "position": DimensionSpec("position", "Chức vụ", key_of=lambda r: (
            [(r.position_id, r.position_name)] if r.position_id else [])),
        "seniority": DimensionSpec("seniority", "Thâm niên", key_of=lambda r: (
            [(r.seniority_key, r.seniority_label)] if r.seniority_key else [])),
    }
    status_dim = DimensionSpec("status", "Trạng thái", key_of=lambda r: (
        [(r.status, EMPLOYEE_STATUS.label_of(r.status) or r.status)] if r.status else []))
    spec = ReportSpec(date_of=lambda r: r.event_date, metrics=metrics, derived=[],
                      dimensions=dimensions, breakdowns={"status": status_dim}, rank_by="new_hires")
    return spec, status_dim
