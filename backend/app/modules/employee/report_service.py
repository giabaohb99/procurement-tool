"""Báo cáo Nhân sự — biến động & cơ cấu (phase 04, `GET /api/employees/summary`).

Sự kiện VÀO/NGHỈ + "định biên tại một thời điểm" ở `report_headcount_events.py`;
ghép định biên vào `groups`/breakdown "Theo trạng thái" ở `report_headcount_groups.py`
(tách để giữ tệp này dưới 200 dòng). Khung báo cáo (`aggregate()`) cộng các sự
kiện rơi vào kỳ để ra "Vào mới"/"Nghỉ việc"; bốn chỉ số ĐỊNH BIÊN (đầu/cuối kỳ,
thay đổi ròng, tỷ lệ nghỉ việc) là số TẠI MỘT THỜI ĐIỂM nên không cộng được
theo hàng — tính riêng (`employees_as_of`, ĐÚNG 1 lần cho mỗi mốc, dùng lại
cho cả Tổng LẪN từng nhóm) rồi ghép vào `totals`/`groups` sau khi `build_report`
trả về.

Review 01/10/2026 (mục 4): "Xem theo" phòng ban/công ty/cấp bậc/... PHẢI hiện
định biên cho TỪNG NHÓM, kể cả nhóm không có sự kiện vào/nghỉ trong kỳ (phòng
ổn định) — xem `report_headcount_groups.merge_group_headcount`.

Hiệu năng: Số truy vấn CỐ ĐỊNH, không tăng theo số nhân sự (xem test đếm truy
vấn). `company_id` (H1) lọc SAU `apply_scope` ở MỌI truy vấn (chỉ thu hẹp).
Tên công ty/phòng ban chỉ tra khi `group_by` thật sự cần.

Không đọc cột nào trong `employee.sensitive.SENSITIVE_FIELDS`, không có chiều
độ tuổi — các chiều ở đây chỉ dùng cột phân loại công khai.
"""
from __future__ import annotations

from datetime import timedelta

from sqlalchemy.orm import Session

from app.core.report_aggregate import DimensionSpec, MetricSpec, ReportSpec, build_report
from app.core.report_compute import zero_values
from app.core.report_period import Period
from app.core.status_codes import EMPLOYEE_STATUS
from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.employee.constants import EMPLOYMENT_TYPE_LABELS, GENDER_LABELS, JOB_LEVEL_LABELS
from app.modules.employee.report_headcount_events import (employees_as_of, hire_events,
                                                           missing_resign_count, resign_events,
                                                           vn_today)
from app.modules.employee.report_headcount_groups import (apply_headcount, merge_group_headcount,
                                                           merge_status_breakdown)


def _build_spec(company_name: dict, department_name: dict) -> tuple[ReportSpec, DimensionSpec]:
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


def build_summary(db: Session, user, prof: dict, period: Period, group_by: str | None,
                  company_id: int | None = None) -> dict:
    """Hợp đồng chuẩn `build_report` cho `/api/employees/summary` (+ `/export`)."""
    today = vn_today()
    #  Tên công ty/phòng ban chỉ tra khi CHÍNH chiều đó được chọn "Xem theo" — nhánh
    #  `group_by=none` của trang Tổng quan (gọi SONG SONG cho ~10 báo cáo) bỏ qua cả hai.
    company_name = ({c.id: c.name for c in db.query(Company.id, Company.name).all()}
                    if group_by == "company" else {})
    department_name = ({d.id: d.name for d in db.query(Department.id, Department.name).all()}
                       if group_by == "department" else {})
    spec, status_dim = _build_spec(company_name, department_name)

    def fetch(d_from, d_to):
        return hire_events(db, user, prof, d_from, d_to, today, company_id) + \
            resign_events(db, user, prof, d_from, d_to, company_id)

    has_compare = period.compare != "none" and period.compare_from and period.compare_to
    #  Bốn mốc TÍNH ĐÚNG MỘT LẦN, dùng lại cho Tổng LẪN từng nhóm (`merge_group_headcount`) —
    #  tránh tính lại `employees_as_of` (2 câu SQL/lần) nhiều nơi.
    snap_end_cur = employees_as_of(db, user, prof, period.date_to, company_id)
    snap_start_cur = employees_as_of(db, user, prof, period.date_from - timedelta(days=1), company_id)
    snap_end_cmp = employees_as_of(db, user, prof, period.compare_to, company_id) if has_compare else None
    snap_start_cmp = (employees_as_of(db, user, prof, period.compare_from - timedelta(days=1), company_id)
                      if has_compare else None)

    def snap(as_of) -> dict:
        return {"headcount_end": len(snap_end_cur if as_of == period.date_to else (snap_end_cmp or []))}

    data = build_report(fetch, spec, period, group_by=group_by, snapshot=snap)
    apply_headcount(data["totals"]["current"], len(snap_start_cur), len(snap_end_cur))
    if data["totals"]["compare"] is not None:
        apply_headcount(data["totals"]["compare"], len(snap_start_cmp or []), len(snap_end_cmp or []))

    if group_by in spec.dimensions:
        merge_group_headcount(data, spec.dimensions[group_by], zero_values(spec),
                              snap_end_cur, snap_start_cur, snap_end_cmp, snap_start_cmp)
    merge_status_breakdown(data, status_dim, snap_end_cur)

    notes = [
        "Phòng ban/cấp bậc/chức vụ/loại hình lấy theo hồ sơ HIỆN TẠI của nhân sự — hệ thống "
        "chưa lưu lịch sử điều chuyển, nên 'Vào mới'/'Nghỉ việc' của các kỳ quá khứ cũng hiện "
        "theo cơ cấu BÂY GIỜ, không phải cơ cấu tại thời điểm đó.",
        "Biểu đồ xu hướng chỉ vẽ được 'Vào mới'/'Nghỉ việc' (cộng dồn theo mốc); 'Định biên cuối "
        "kỳ' là số TẠI MỘT THỜI ĐIỂM nên chỉ hiện ở thẻ KPI Tổng/bảng Xem theo, không có đường "
        "xu hướng riêng.",
    ]
    missing_resign = missing_resign_count(db, user, prof, company_id)
    if missing_resign:
        notes.append(f"Có {missing_resign} hồ sơ đánh dấu Nghỉ việc nhưng thiếu ngày nghỉ việc — "
                     "không tính vào chỉ số Nghỉ việc VÀ không được coi là đang làm trong Định "
                     "biên (Q4.3), cần Nhân sự bổ sung ngày.")
    data["notes"] = notes
    return data
