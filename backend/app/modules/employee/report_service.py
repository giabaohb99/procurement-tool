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

from app.core.report_aggregate import build_report
from app.core.report_compute import zero_values
from app.core.report_period import Period
from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.employee.report_headcount_events import (employees_as_of, hire_events,
                                                           resign_events, vn_today)
from app.modules.employee.report_headcount_gaps import missing_hire_count, missing_resign_count
from app.modules.employee.report_headcount_spec import DRILLDOWN_METRICS, build_spec
from app.modules.employee.report_headcount_groups import (apply_headcount, merge_group_headcount,
                                                           merge_status_breakdown)


def build_summary(db: Session, user, prof: dict, period: Period, group_by: str | None,
                  company_id: int | None = None, department_id: int | None = None) -> dict:
    """Hợp đồng chuẩn `build_report` cho `/api/employees/summary` (+ `/export`)."""
    today = vn_today()
    #  Tên công ty/phòng ban chỉ tra khi CHÍNH chiều đó được chọn "Xem theo" — nhánh
    #  `group_by=none` của trang Tổng quan (gọi SONG SONG cho ~10 báo cáo) bỏ qua cả hai.
    company_name = ({c.id: c.name for c in db.query(Company.id, Company.name).all()}
                    if group_by == "company" else {})
    department_name = ({d.id: d.name for d in db.query(Department.id, Department.name).all()}
                       if group_by == "department" else {})
    spec, status_dim = build_spec(company_name, department_name)

    def fetch(d_from, d_to):
        return hire_events(db, user, prof, d_from, d_to, today, company_id, department_id) + \
            resign_events(db, user, prof, d_from, d_to, company_id, department_id)

    has_compare = period.compare != "none" and period.compare_from and period.compare_to
    #  Bốn mốc TÍNH ĐÚNG MỘT LẦN, dùng lại cho Tổng LẪN từng nhóm (`merge_group_headcount`) —
    #  tránh tính lại `employees_as_of` (2 câu SQL/lần) nhiều nơi.
    snap_end_cur = employees_as_of(db, user, prof, period.date_to, company_id, department_id)
    snap_start_cur = employees_as_of(db, user, prof, period.date_from - timedelta(days=1),
                                     company_id, department_id)
    snap_end_cmp = (employees_as_of(db, user, prof, period.compare_to, company_id, department_id)
                    if has_compare else None)
    snap_start_cmp = (employees_as_of(db, user, prof, period.compare_from - timedelta(days=1),
                                      company_id, department_id)
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
        "Phòng ban/cấp bậc/chức vụ/loại hình lấy theo hồ sơ HIỆN TẠI của nhân sự. Lịch sử điều "
        "chuyển đã có ở Quá trình công tác nhưng báo cáo này CHƯA đọc, nên 'Vào mới'/'Nghỉ việc' "
        "của các kỳ quá khứ hiện theo cơ cấu BÂY GIỜ, không phải cơ cấu tại thời điểm đó.",
        "Biểu đồ xu hướng chỉ vẽ được 'Vào mới'/'Nghỉ việc' (cộng dồn theo mốc); 'Định biên cuối "
        "kỳ' là số TẠI MỘT THỜI ĐIỂM nên chỉ hiện ở thẻ KPI Tổng/bảng Xem theo, không có đường "
        "xu hướng riêng.",
    ]
    missing_hire = missing_hire_count(db, user, prof, company_id, department_id)
    if missing_hire:
        notes.append(f"Có {missing_hire} hồ sơ đang làm thiếu ngày vào làm — báo cáo tạm lấy "
                     "ngày TẠO hồ sơ làm ngày vào (Vào mới, Định biên, Thâm niên có thể lệch), cần "
                     "Nhân sự bổ sung ngày vào làm.")
    missing_resign = missing_resign_count(db, user, prof, company_id, department_id)
    if missing_resign:
        notes.append(f"Có {missing_resign} hồ sơ đánh dấu Nghỉ việc nhưng thiếu ngày nghỉ việc — "
                     "không tính vào chỉ số Nghỉ việc VÀ không được coi là đang làm trong Định "
                     "biên (Q4.3), cần Nhân sự bổ sung ngày.")
    data["notes"] = notes
    data["meta"]["drilldown_metrics"] = list(DRILLDOWN_METRICS)
    return data
