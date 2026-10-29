"""Báo cáo A5 «Quỹ lương theo pháp nhân» (duoc-CR-693, khóa 21) — `GET /api/payroll-fund/summary`.

Nguồn số = ô lương trên hồ sơ nhân sự (`payroll_report_data.py`), gom theo pháp nhân · phòng ban · chức vụ · nhóm
vị trí; dòng Tổng = toàn bộ phạm vi người xem. Đây là ẢNH CHỤP HIỆN TẠI: `period` chỉ được trả lại cho khớp hợp đồng
chung, KHÔNG ảnh hưởng số; không có kỳ so sánh (`totals.compare = null`) và không có xu hướng (`trend = []`).

⚠️ Đây là số LƯƠNG. Chỉ có TỔNG theo nhóm — không lộ lương từng người: nhóm dưới 3 người bị che với MỌI người xem
(kể cả admin) bằng luật chung `core/report_small_group.py`, Tổng chỉ 1–2 người cũng bị che số tiền, danh sách
`/summary/rows` không có cột tiền.
"""
from __future__ import annotations

from dataclasses import replace

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.report_aggregate import DerivedSpec, DimensionSpec, MetricSpec, ReportSpec, build_report
from app.core.report_drilldown import Col, filter_group, rows_response
from app.core.report_period import Period
from app.core.report_small_group import MIN_GROUP, drop_unsafe_breakdown, suppress_small_groups
from app.modules.employee.constants import JOB_CATEGORY_LABELS, JOB_CATEGORY_OTHER
from app.modules.employee.profile_gaps_report_data import load_group_names

from .payroll_report_data import FundRow, load_rows

METRICS = {"people_paid": "Số người có lương"}   # chỉ số có danh sách `/rows`
MONEY_KEYS = ("base_total", "allowance_total", "payroll_total", "avg_payroll")
NOTE_SMALL = ("Nhóm dưới 3 người bị che số trên màn hình để không lộ lương từng người, kể cả với người có quyền xem báo cáo")
NOTE_EXTRA = ("Để số bị che không suy ngược được từ Tổng, báo cáo che thêm nhóm nhỏ kế tiếp; "
              "dòng Tổng vẫn đủ số")
NOTE_TOTAL_SMALL = "Toàn bộ phạm vi đang xem dưới 3 người có lương nên các số tiền bị che để không lộ lương từng người"
#  Cố ý KHÔNG có cột tiền: danh sách chỉ cho biết AI nằm sau con số, không bao giờ kèm lương.
COLUMNS = [Col("employee_code", "Mã NV"), Col("employee_name", "Họ tên"), Col("company", "Pháp nhân"),
           Col("department", "Phòng ban"), Col("position", "Chức vụ")]


def _build_spec(company_name: dict, department_name: dict) -> tuple[ReportSpec, dict[str, DimensionSpec]]:
    def money(key, label, fn):
        return MetricSpec(key, label, kind="money", value_of=fn)

    metrics = [MetricSpec("people_paid", METRICS["people_paid"], kind="int", value_of=lambda r: int(r.has_salary)),
               money("base_total", "Lương", lambda r: r.base_salary),
               money("allowance_total", "Phụ cấp", lambda r: r.allowance),
               money("payroll_total", "Quỹ lương (lương + phụ cấp)", lambda r: r.base_salary + r.allowance)]
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
    }
    spec = ReportSpec(date_of=lambda r: None, metrics=metrics, derived=derived, dimensions=dims,
                      rank_by="payroll_total")
    return spec, dims


def _summary(db: Session, rows: list[FundRow], period: Period, group_by: str | None) -> dict:
    company_name, department_name = load_group_names(db, group_by)
    spec, dims = _build_spec(company_name, department_name)
    #  Ảnh chụp hiện tại: bỏ kỳ so sánh để khung chỉ gọi `fetch` một lần; `period` vẫn trả lại nguyên.
    flat = replace(period, compare="none", compare_from=None, compare_to=None)
    data = build_report(lambda _f, _t: rows, spec, flat, group_by=group_by)
    data["period"] = period.as_dict()
    data["trend"] = []
    data["meta"]["drilldown_metrics"] = list(METRICS)
    missing = sum(1 for r in rows if not r.has_salary)
    data["meta"]["people_without_salary"] = missing
    data["notes"] = [
        "Số hiện tại theo hồ sơ nhân sự (ô Lương và Phụ cấp, đồng / tháng) của người đang làm — là ảnh chụp, không có "
        "lịch sử nên kỳ đang chọn không ảnh hưởng số liệu. Quỹ lương = lương + phụ cấp. Ký hợp đồng lao động sẽ tự cập "
        "nhật ô này theo hợp đồng.",
        "Dòng Tổng = toàn bộ phạm vi bạn được xem; «Xem theo» chia nhỏ số đó. Báo cáo chỉ có TỔNG, không có lương "
        "từng người; danh sách «bấm số» chỉ liệt kê người, không kèm số tiền.",
        f"Đang có {missing} người còn làm chưa nhập lương — chưa tính vào quỹ lương.",
    ]
    gb = group_by if group_by in dims else None
    res = suppress_small_groups(data, lambda v: [int(v.get("people_paid") or 0)],
                                lambda v: int(v.get("people_paid") or 0), NOTE_SMALL, NOTE_EXTRA)
    if res.unsafe_sides:     # che xong Tổng vẫn lộ lương -> bỏ cả bảng «Xem theo»
        drop_unsafe_breakdown(data, gb, dims[gb].label)
    cur = data["totals"]["current"]
    if 0 < int(cur.get("people_paid") or 0) < MIN_GROUP:      # Tổng chỉ 1–2 người: số tiền chính là lương của họ
        for k in MONEY_KEYS:
            cur[k] = None
        data["notes"].append(NOTE_TOTAL_SMALL)
    return data


def build_summary(db: Session, employees_q, period: Period, group_by: str | None,
                  company_id: int | None = None, department_id: int | None = None) -> dict:
    """Hợp đồng chuẩn `build_report` cho `/api/payroll-fund/summary` (+ `/export`). `employees_q` đã qua phạm vi."""
    return _summary(db, load_rows(db, employees_q, company_id, department_id), period, group_by)


def _row_dict(r: FundRow, company_name: dict, department_name: dict) -> dict:
    return {"employee_code": r.employee_code, "employee_name": r.employee_name,
            "company": company_name.get(r.company_id, ""), "department": department_name.get(r.department_id, ""),
            "position": r.position, "link": f"/hr/employees/{r.employee_id}"}


def build_rows(db: Session, employees_q, period: Period, metric: str, group_by: str | None,
               group_key: str | None, company_id: int | None = None, department_id: int | None = None) -> dict:
    """Danh sách người có lương đứng sau một con số (KHÔNG có cột tiền). Danh sách của nhóm ĐANG BỊ CHE → 403
    (nếu không, che số ở bảng là vô nghĩa: người ta đếm được nhóm 1–2 người rồi đoán lương)."""
    rows = load_rows(db, employees_q, company_id, department_id)
    company_name, department_name = load_group_names(db, group_by, always=True)
    _, dims = _build_spec(company_name, department_name)
    if group_by and group_by not in dims:
        raise HTTPException(422, f"Xem theo không hợp lệ: {group_by}")
    if group_by and group_key is not None:
        groups = _summary(db, rows, period, group_by).get("groups") or []
        visible = {g["key"] for g in groups if not g.get("suppressed")}
    paid = filter_group([r for r in rows if r.has_salary], dims.get(group_by) if group_by else None, group_key)
    if group_by and group_key is not None and paid and group_key not in visible:
        #  Nhóm bị che, hoặc cả bảng nhóm đã bị bỏ vì không che an toàn được -> không mở danh sách.
        raise HTTPException(403, "Nhóm dưới 3 người: không xem danh sách để tránh lộ lương từng người")
    paid.sort(key=lambda r: (r.employee_code, r.employee_id))
    return rows_response(metric, METRICS[metric], COLUMNS, [_row_dict(r, company_name, department_name) for r in paid])
