"""Báo cáo "Hồ sơ & tài khoản còn thiếu" kiểu Haravan (duoc-CR-686, khóa 18) —
`GET /api/employees/profile-gaps/summary`.

Tình trạng HIỆN TẠI của hồ sơ: `period` vẫn được trả để khớp hợp đồng chung nhưng KHÔNG ảnh hưởng
số liệu; `totals.compare = null`, `trend = []`. Chỉ số theo quyền người xem (xem
`profile_gaps_report_data.py`): nhóm nhạy cảm và nhóm tài khoản vắng hẳn khỏi `meta` khi thiếu quyền.

`/summary/rows` dùng đúng `load_rows` + đúng `key_of` của chiều gom nên danh sách khớp con số.
"""
from __future__ import annotations

from dataclasses import replace

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.report_aggregate import DerivedSpec, DimensionSpec, MetricSpec, ReportSpec, build_report
from app.core.report_drilldown import Col, filter_group, rows_response
from app.core.report_period import Period
from app.core.vn_time import vn_today

from . import profile_gaps_report_data as data_mod
from .profile_gaps_report_data import ACCOUNT_GAPS, BASE_GAPS, SENSITIVE_GAPS, GapRow

LABELS = {
    "active_total": "Đang làm", "complete": "Hồ sơ đủ",
    "missing_hire_date": "Thiếu ngày vào làm", "missing_position": "Chưa gán chức vụ",
    "missing_manager": "Chưa gán quản lý trực tiếp", "missing_department": "Chưa gán phòng ban",
    "missing_dob": "Thiếu ngày sinh", "missing_id_number": "Thiếu số CCCD",
    "missing_tax_code": "Thiếu mã số thuế", "missing_social_insurance": "Thiếu số BHXH",
    "missing_bank": "Thiếu tài khoản ngân hàng",
    "id_expiring_90": "CCCD hết hạn trong 90 ngày (kể cả đã hết)",
    "no_account": "Đang làm, chưa có tài khoản đang mở", "account_no_role": "Có tài khoản, chưa có vai trò",
    "resigned_active_account": "Đã nghỉ, tài khoản còn mở",
}
GOOD_DOWN = {k for k in LABELS if k not in ("active_total", "complete")}


def visible_gaps(with_sensitive: bool, with_account: bool) -> tuple[str, ...]:
    """Các cờ "thiếu" người xem được đếm, theo thứ tự cột."""
    return BASE_GAPS + (SENSITIVE_GAPS if with_sensitive else ()) + (ACCOUNT_GAPS if with_account else ())


def _build_spec(gaps: tuple[str, ...], company_name: dict, department_name: dict
                ) -> tuple[ReportSpec, dict[str, DimensionSpec]]:
    metrics = [MetricSpec("active_total", LABELS["active_total"], value_of=lambda r: int("active_total" in r.flags)),
               MetricSpec("complete", LABELS["complete"], helper=True, value_of=lambda r: int("complete" in r.flags))]
    metrics += [MetricSpec(k, LABELS[k], good="down", value_of=(lambda r, k=k: int(k in r.flags))) for k in gaps]
    #  Chỉ số PHỤ: hàng có ÍT NHẤT MỘT cờ thiếu — làm giá trị xếp hạng nhóm / breakdown.
    gap_set = frozenset(gaps)
    metrics.append(MetricSpec("gap_rows", "Hồ sơ có điểm thiếu", helper=True,
                              value_of=lambda r: int(bool(r.flags & gap_set))))
    gap_kind = DimensionSpec("gap_kind", "Loại thiếu sót", key_of=lambda r: [
        (k, LABELS[k]) for k in gaps if k in r.flags])
    dims = {
        "company": DimensionSpec("company", "Công ty", key_of=lambda r: (
            [(r.company_id, company_name.get(r.company_id, ""))] if r.company_id else [])),
        "department": DimensionSpec("department", "Phòng ban", key_of=lambda r: (
            [(r.department_id, department_name.get(r.department_id, ""))] if r.department_id else [])),
    }
    derived = [DerivedSpec("complete_rate", "Tỷ lệ hồ sơ đủ", num="complete", den="active_total", good="up")]
    spec = ReportSpec(date_of=lambda r: None, metrics=metrics, derived=derived, dimensions=dims,
                      breakdowns={"gap_kind": gap_kind}, rank_by="gap_rows")
    return spec, dims


def build_summary(db: Session, employees_q, period: Period, group_by: str | None, *,
                  with_sensitive: bool, with_account: bool, company_id: int | None = None,
                  department_id: int | None = None) -> dict:
    gaps = visible_gaps(with_sensitive, with_account)
    spec, _ = _build_spec(gaps, *data_mod.load_group_names(db, group_by))
    rows = data_mod.load_rows(db, employees_q, vn_today(), with_sensitive=with_sensitive,
                              with_account=with_account, company_id=company_id, department_id=department_id)
    #  Tình trạng hiện tại: bỏ kỳ so sánh để khung chỉ gọi `fetch` một lần.
    flat = replace(period, compare="none", compare_from=None, compare_to=None)
    data = build_report(lambda _f, _t: rows, spec, flat, group_by=group_by)
    data["period"] = period.as_dict()
    data["trend"] = []
    data["meta"]["drilldown_metrics"] = ["active_total", *gaps]
    notes = ["Báo cáo cho biết tình trạng HIỆN TẠI của hồ sơ; kỳ đang chọn không ảnh hưởng số liệu.",
             "\"Hồ sơ đủ\" = nhân sự đang làm không thiếu trường nào trong các trường ĐANG ĐƯỢC ĐẾM cho "
             "bạn (ngày vào làm, chức vụ, quản lý, phòng ban, và nhóm nhạy cảm nếu bạn có quyền); "
             "không xét tài khoản và CCCD sắp hết hạn."]
    if not with_sensitive:
        notes.append("Các chỉ số về giấy tờ cá nhân (ngày sinh, CCCD, mã số thuế, BHXH, ngân hàng) "
                     "không hiển thị vì bạn chưa có quyền xem dữ liệu nhạy cảm của nhân sự.")
    if not with_account:
        notes.append("Các chỉ số về tài khoản không hiển thị vì bạn chưa có quyền xem tài khoản.")
    else:
        notes.append("\"Chưa có tài khoản đang mở\" tính cả trường hợp tài khoản đã bị khóa.")
    data["notes"] = notes
    return data


def _columns(metric: str) -> list[Col]:
    cols = [Col("employee_code", "Mã NV"), Col("employee_name", "Họ tên"), Col("company", "Công ty"),
            Col("department", "Phòng ban"), Col("position", "Chức vụ"), Col("hire_date", "Ngày vào làm", "date")]
    return cols + ([Col("id_expiry_date", "Ngày hết hạn CCCD", "date")] if metric == "id_expiring_90" else [])


def _row_dict(r: GapRow, metric: str, company_name: dict, department_name: dict) -> dict:
    out = {"employee_code": r.employee_code, "employee_name": r.employee_name,
           "company": company_name.get(r.company_id, ""), "department": department_name.get(r.department_id, ""),
           "position": r.position, "hire_date": r.hire_date, "link": f"/hr/employees/{r.employee_id}"}
    if metric == "id_expiring_90":
        out["id_expiry_date"] = r.id_expiry_date
    return out


def build_rows(db: Session, employees_q, metric: str, group_by: str | None, group_key: str | None, *,
               with_sensitive: bool, with_account: bool, company_id: int | None = None,
               department_id: int | None = None) -> dict:
    """Danh sách nhân sự đứng sau một con số. `metric` đã được controller kiểm theo quyền."""
    company_name, department_name = data_mod.load_group_names(db, group_by, always=True)
    _, dims = _build_spec(visible_gaps(with_sensitive, with_account), company_name, department_name)
    if group_by and group_by != "none" and group_by not in dims:
        raise HTTPException(422, f"Xem theo không hợp lệ: {group_by}")
    rows = data_mod.load_rows(db, employees_q, vn_today(), with_sensitive=with_sensitive,
                              with_account=with_account, company_id=company_id, department_id=department_id)
    rows = [r for r in rows if metric in r.flags]
    rows = filter_group(rows, dims.get(group_by) if group_by else None, group_key)
    rows.sort(key=lambda r: r.employee_code)
    return rows_response(metric, LABELS[metric], _columns(metric),
                         [_row_dict(r, metric, company_name, department_name) for r in rows])
