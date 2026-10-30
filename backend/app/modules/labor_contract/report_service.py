"""Báo cáo Hợp đồng lao động kiểu Haravan (duoc-CR-686, khóa 17) — `GET /api/labor-contracts/summary`.

Chỉ số là ĐẾM CỜ trạng thái của từng hàng (xem `report_data.py`), không phải số tại một thời điểm
(`snapshot`) — nhờ vậy có ở cả Tổng lẫn từng nhóm "Xem theo". Mốc tính trạng thái `as_of =
min(cuối kỳ, hôm nay)`; kỳ so sánh tính lại tại mốc cuối kỳ của chính nó. Không có trục thời gian
nên `trend = []` (giao diện ẩn biểu đồ).

`/summary/rows` ("bấm số ra danh sách") dùng đúng `load_rows` + đúng `key_of` của chiều gom nên
danh sách luôn khớp con số trên bảng.

⚠️ Danh sách có LƯƠNG (cơ bản · đóng BHXH · phụ cấp) — chốt: ai có `labor_contract.read` thì thấy,
cùng luật với màn HĐLĐ của nhân sự. Số liệu `/summary` không chứa lương.
"""
from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.report_aggregate import DimensionSpec, MetricSpec, ReportSpec, build_report
from app.core.report_drilldown import Col, filter_group, rows_response
from app.core.report_period import Period
from app.core.vn_time import vn_today
from app.modules.employee.profile_gaps_report_data import load_group_names

from .report_data import FLAGS, ContractRow, load_rows, type_label

#  Nhãn chỉ số: (nhãn, chiều tốt). Thứ tự = thứ tự cột trên bảng.
METRICS: dict[str, tuple[str, str | None]] = {
    "active": ("Đang hiệu lực", None),
    "expiring_30": ("Hết hạn trong 30 ngày", "down"),
    "expiring_60": ("Hết hạn trong 60 ngày", "down"),
    "expiring_90": ("Hết hạn trong 90 ngày", "down"),
    "probation_expiring_30": ("Thử việc hết trong 30 ngày", "down"),
    "overdue": ("Đã quá hạn, vẫn đi làm", "down"),
    "no_contract": ("Đang làm, chưa có HĐ", "down"),
    "missing_scan": ("Đã ký, chưa tải bản scan", "down"),
    "second_fixed_term": ("Đã ký 2 HĐ có thời hạn", None),
    "new_contracts": ("Ký mới trong kỳ", None),
    "terminated": ("Chấm dứt trong kỳ", "down"),
    "resigned_not_terminated": ("Người đã nghỉ, HĐ chưa chấm dứt", "down"),
}
assert tuple(METRICS) == FLAGS

COLUMNS = [Col("employee_code", "Mã NV"), Col("employee_name", "Họ tên"), Col("department", "Phòng ban"),
           Col("contract_code", "Mã HĐ"), Col("contract_type", "Loại HĐ"),
           Col("start_date", "Bắt đầu", "date"), Col("end_date", "Kết thúc", "date"),
           Col("days_left", "Còn (ngày)", "days"), Col("base_salary", "Lương cơ bản", "money"),
           Col("insurance_salary", "Lương đóng BHXH", "money"), Col("allowance", "Phụ cấp", "money")]


def _build_spec(company_name: dict, department_name: dict) -> tuple[ReportSpec, dict[str, DimensionSpec]]:
    metrics = [MetricSpec(k, label, kind="int", good=good,
                          value_of=(lambda r, k=k: 1 if k in r.flags else 0))
               for k, (label, good) in METRICS.items()]
    type_dim = DimensionSpec("contract_type", "Loại hợp đồng", key_of=lambda r: (
        [(r.contract_type, type_label(r.contract_type))]
        if r.contract_type else []))
    dims = {
        "company": DimensionSpec("company", "Công ty", key_of=lambda r: (
            [(r.company_id, company_name.get(r.company_id, ""))] if r.company_id else [])),
        "department": DimensionSpec("department", "Phòng ban", key_of=lambda r: (
            [(r.department_id, department_name.get(r.department_id, ""))] if r.department_id else [])),
        "contract_type": type_dim,
    }
    spec = ReportSpec(date_of=lambda r: None, metrics=metrics, dimensions=dims,
                      breakdowns={"contract_type": type_dim}, rank_by="active")
    return spec, dims


def build_summary(db: Session, contracts_q, employees_q, period: Period, group_by: str | None,
                  company_id: int | None = None, department_id: int | None = None) -> dict:
    """Hợp đồng chuẩn `build_report` cho `/api/labor-contracts/summary` (+ `/export`)."""
    spec, _ = _build_spec(*load_group_names(db, group_by))
    today = vn_today()

    def fetch(d_from, d_to):
        return load_rows(db, contracts_q, employees_q, d_from, d_to, today, company_id, department_id)

    data = build_report(fetch, spec, period, group_by=group_by)
    data["trend"] = []   # đếm cờ theo mốc `as_of`, không có trục ngày
    data["meta"]["drilldown_metrics"] = list(METRICS)
    data["notes"] = [
        "Trạng thái HĐ tính tại ngày cuối kỳ (hoặc hôm nay nếu kỳ chưa kết thúc); kỳ so sánh tính "
        "lại tại ngày cuối kỳ của chính nó.",
        "Chỉ số \"Hết hạn trong N ngày\" là tích lũy (30 ⊂ 60 ⊂ 90), không tính người đã có HĐ nối "
        "tiếp hoặc đã nghỉ việc — cùng luật với chuông cảnh báo HĐLĐ.",
        "\"Đang hiệu lực\" chỉ đếm HĐ của người còn làm; HĐ còn hạn của người đã nghỉ vào \"Người đã nghỉ, HĐ chưa chấm dứt\".",
        "\"Đang làm, chưa có HĐ\" tính theo tình trạng nhân sự HIỆN TẠI (chưa lưu lịch sử trạng thái).",
    ]
    return data


def _row_dict(r: ContractRow, department_name: dict) -> dict:
    ctype = type_label(r.contract_type) if r.contract_type else ""
    return {"employee_code": r.employee_code, "employee_name": r.employee_name,
            "department": department_name.get(r.department_id, ""), "contract_code": r.contract_code,
            "contract_type": ctype, "start_date": r.start_date, "end_date": r.end_date,
            "days_left": r.days_left, "base_salary": r.base_salary, "insurance_salary": r.insurance_salary,
            "allowance": r.allowance, "link": f"/hr/employees/{r.employee_id}?tab=labor-contracts"}


def build_rows(db: Session, contracts_q, employees_q, period: Period, metric: str,
               group_by: str | None, group_key: str | None, company_id: int | None = None,
               department_id: int | None = None) -> dict:
    """Danh sách người/HĐ đứng sau một con số của `/summary` (metric đã được controller kiểm)."""
    company_name, department_name = load_group_names(db, group_by, always=True)
    spec, dims = _build_spec(company_name, department_name)
    if group_by and group_by != "none" and group_by not in dims:
        raise HTTPException(422, f"Xem theo không hợp lệ: {group_by}")
    rows = load_rows(db, contracts_q, employees_q, period.date_from, period.date_to, vn_today(),
                     company_id, department_id)
    rows = [r for r in rows if metric in r.flags]
    rows = filter_group(rows, dims.get(group_by) if group_by else None, group_key)
    rows.sort(key=lambda r: (r.end_date is None, r.end_date, r.employee_code))
    return rows_response(metric, METRICS[metric][0], COLUMNS, [_row_dict(r, department_name) for r in rows])
