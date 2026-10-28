"""Báo cáo A5 «Quỹ lương theo pháp nhân» (duoc-CR-688, khóa 21) — `GET /api/payroll-fund/summary`.

Chỉ số là số TẠI MỘT MỐC (`as_of = min(cuối kỳ, hôm nay)`, kỳ so sánh tại mốc của chính nó) trên HĐ đã ký
còn hiệu lực của người còn làm — xem `payroll_report_data.py`. Cả kỳ này, kỳ so sánh lẫn xu hướng tháng
dùng CHUNG một lần nạp HĐ.

⚠️ Đây là số LƯƠNG: nhóm dưới 3 người bị che với MỌI người xem (kể cả admin) bằng luật chung
`core/report_small_group.py`; lương từng người chỉ xem qua `/summary/rows` (danh sách).
"""
from __future__ import annotations

from datetime import date

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.report_aggregate import DerivedSpec, DimensionSpec, MetricSpec, ReportSpec, build_report
from app.core.report_drilldown import Col, filter_group, rows_response
from app.core.report_period import Period
from app.core.report_small_group import drop_unsafe_breakdown, suppress_small_groups
from app.core.vn_time import vn_today
from app.modules.employee.constants import JOB_CATEGORY_LABELS, JOB_CATEGORY_OTHER
from app.modules.employee.profile_gaps_report_data import load_group_names

from .payroll_report_data import PayRecord, load_records, rows_at
from .payroll_report_extras import add_minmax, build_trend
from .payroll_report_plan import add_plan_columns
from .report_data import type_label

METRICS = {"people_paid": "Số người hưởng lương"}   # chỉ số có danh sách `/rows`
NOTE_SMALL = ("Nhóm dưới 3 người bị che số trên màn hình. Báo cáo dành cho người được phép xem lương; "
              "tệp xuất và danh sách từng người vẫn theo quyền xem hợp đồng của bạn")
NOTE_EXTRA = ("Để số bị che không suy ngược được từ Tổng, báo cáo che thêm nhóm nhỏ kế tiếp; "
              "dòng Tổng vẫn đủ số")
COLUMNS = [Col("employee_code", "Mã NV"), Col("employee_name", "Họ tên"), Col("company", "Pháp nhân"),
           Col("department", "Phòng ban"), Col("position", "Chức vụ"), Col("contract_type", "Loại HĐ"),
           Col("base_salary", "Lương cơ bản", "money"), Col("allowance", "Phụ cấp", "money"),
           Col("insurance_salary", "Lương đóng BHXH", "money")]


def _build_spec(company_name: dict, department_name: dict) -> tuple[ReportSpec, dict[str, DimensionSpec]]:
    def money(key, label, fn):
        return MetricSpec(key, label, kind="money", value_of=fn)

    metrics = [MetricSpec("people_paid", METRICS["people_paid"], kind="int", value_of=lambda r: 1),
               money("base_total", "Tổng lương cơ bản", lambda r: r.base_salary),
               money("allowance_total", "Tổng phụ cấp", lambda r: r.allowance),
               money("payroll_total", "Quỹ lương (lương + phụ cấp)", lambda r: r.base_salary + r.allowance),
               money("insurance_total", "Tổng lương đóng BHXH", lambda r: r.insurance_salary)]
    derived = [DerivedSpec("avg_payroll", "Bình quân / người", num="payroll_total", den="people_paid",
                           kind="money", scale=1, ndigits=0)]
    dims = {
        "company": DimensionSpec("company", "Pháp nhân", key_of=lambda r: (
            [(r.company_id, company_name.get(r.company_id, ""))] if r.company_id else [])),
        "department": DimensionSpec("department", "Phòng ban", key_of=lambda r: (
            [(r.department_id, department_name.get(r.department_id, ""))] if r.department_id else [])),
        "position": DimensionSpec("position", "Chức vụ", key_of=lambda r: (
            [(r.position, r.position)] if r.position else [])),
        "job_category": DimensionSpec("job_category", "Nhóm vị trí việc làm", key_of=lambda r: [(
            r.job_category, JOB_CATEGORY_LABELS.get(r.job_category, JOB_CATEGORY_LABELS[JOB_CATEGORY_OTHER]))]),
        "contract_type": DimensionSpec("contract_type", "Loại hợp đồng", key_of=lambda r: (
            [(r.contract_type, type_label(r.contract_type))] if r.contract_type else [])),
    }
    spec = ReportSpec(date_of=lambda r: None, metrics=metrics, derived=derived, dimensions=dims,
                      rank_by="payroll_total")
    return spec, dims


def _as_of(d_to: date, today: date) -> date:
    return min(d_to, today)


def _load(db: Session, contracts_q, period: Period, today: date, company_id, department_id) -> list[PayRecord]:
    lo, hi = period.date_from, period.date_to
    if period.compare != "none" and period.compare_from and period.compare_to:
        lo, hi = min(lo, period.compare_from), max(hi, period.compare_to)
    return load_records(db, contracts_q, lo, hi, today, company_id, department_id)


def _summary(db: Session, records: list[PayRecord], period: Period, group_by: str | None, today: date,
             plan_sets: dict | None = None) -> dict:
    company_name, department_name = load_group_names(db, group_by)
    spec, dims = _build_spec(company_name, department_name)
    seen: dict[date, list[PayRecord]] = {}

    def fetch(d_from, d_to):
        t = _as_of(d_to, today)
        seen[d_to] = rows_at(records, t)
        return seen[d_to]

    data = build_report(fetch, spec, period, group_by=group_by)
    has_cmp = data["totals"]["compare"] is not None
    gb = group_by if group_by in dims else None
    add_minmax(data, dims.get(gb) if gb else None, seen[period.date_to],
               seen.get(period.compare_to) if has_cmp else None)
    add_plan_columns(data, plan_sets, group_by, company_name if group_by == "company" else department_name)   # TRƯỚC khi che nhóm nhỏ: còn dư = kế hoạch − lương thật
    data["trend"] = build_trend(records, period, today)
    data["meta"]["drilldown_metrics"] = list(METRICS)
    data["notes"] = [
        "Lương là lương THỎA THUẬN ghi trên hợp đồng đã ký còn hiệu lực của người còn làm, không phải lương "
        "thực trả; quỹ lương = lương cơ bản + phụ cấp.",
        "Số liệu tính tại ngày cuối kỳ (hoặc hôm nay nếu kỳ chưa kết thúc); xu hướng lấy cuối mỗi tháng.",
        "Một người có hợp đồng còn hiệu lực ở hai pháp nhân được tính ở cả hai (số «người hưởng lương» "
        "đếm hợp đồng); dòng Tổng cộng cả hai.",
        "Quỹ lương kế hoạch lấy từ «Kế hoạch nhân sự» của năm cuối kỳ (chỉ hiện khi bạn có quyền xem kế hoạch): "
        "pháp nhân có dòng «Toàn pháp nhân» thì lấy dòng đó, không thì cộng các dòng phòng; chỉ gắn theo nhóm khi "
        "Xem theo Pháp nhân hoặc Phòng ban, còn lại chỉ có ở dòng Tổng. «—» = chưa khai quỹ lương kế hoạch.",
        "Chưa có khoản BHXH công ty đóng — báo cáo chỉ có lương đóng BHXH trên hợp đồng.",
    ]
    res = suppress_small_groups(data, lambda v: [int(v.get("people_paid") or 0)],
                                lambda v: int(v.get("people_paid") or 0), NOTE_SMALL, NOTE_EXTRA)
    if res.unsafe_sides:     # che xong Tổng vẫn lộ lương -> bỏ cả bảng «Xem theo»
        drop_unsafe_breakdown(data, gb, dims[gb].label)
    return data


def build_summary(db: Session, contracts_q, period: Period, group_by: str | None,
                  company_id: int | None = None, department_id: int | None = None,
                  plan_sets: dict | None = None) -> dict:
    """Hợp đồng chuẩn `build_report` cho `/api/payroll-fund/summary` (+ `/export`). `plan_sets` = dòng kế hoạch
    đã qua phạm vi (`payroll_report_plan.load_plan_sets`), `None` → không có cột kế hoạch."""
    today = vn_today()
    return _summary(db, _load(db, contracts_q, period, today, company_id, department_id), period, group_by, today,
                    plan_sets)


def _row_dict(r: PayRecord, company_name: dict, department_name: dict) -> dict:
    return {"employee_code": r.employee_code, "employee_name": r.employee_name,
            "company": company_name.get(r.company_id, ""), "department": department_name.get(r.department_id, ""),
            "position": r.position, "contract_type": type_label(r.contract_type), "base_salary": r.base_salary,
            "allowance": r.allowance, "insurance_salary": r.insurance_salary,
            "link": f"/hr/employees/{r.employee_id}?tab=labor-contracts"}


def build_rows(db: Session, contracts_q, period: Period, metric: str, group_by: str | None,
               group_key: str | None, company_id: int | None = None, department_id: int | None = None) -> dict:
    """Danh sách người hưởng lương đứng sau một con số. Danh sách của nhóm ĐANG BỊ CHE → 403 (nếu không,
    che số ở bảng là vô nghĩa)."""
    today = vn_today()
    records = _load(db, contracts_q, period, today, company_id, department_id)
    company_name, department_name = load_group_names(db, group_by, always=True)
    _, dims = _build_spec(company_name, department_name)
    if group_by and group_by not in dims:
        raise HTTPException(422, f"Xem theo không hợp lệ: {group_by}")
    if group_by and group_key is not None:
        groups = _summary(db, records, period, group_by, today).get("groups") or []
        visible = {g["key"] for g in groups if not g.get("suppressed")}
    rows = filter_group(rows_at(records, _as_of(period.date_to, today)),
                        dims.get(group_by) if group_by else None, group_key)
    if group_by and group_key is not None and rows and group_key not in visible:
        #  Nhóm bị che, hoặc cả bảng nhóm đã bị bỏ vì không che an toàn được -> không mở danh sách.
        raise HTTPException(403, "Nhóm dưới 3 người: không xem danh sách để tránh lộ lương từng người")
    rows.sort(key=lambda r: (r.employee_code, r.contract_id))
    return rows_response(metric, METRICS[metric], COLUMNS, [_row_dict(r, company_name, department_name) for r in rows])
