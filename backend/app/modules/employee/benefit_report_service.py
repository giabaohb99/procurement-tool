"""Báo cáo H1 «Phúc lợi & sự kiện» (khóa 22, duoc-CR-688) — `GET /api/benefit-audience/summary`.

Ngày dịp = cuối kỳ (`date_to`). Đơn vị tính: người, hoặc CON khi đặt `child_max_age`.
`managers` / `staff` đếm theo đơn vị ấy, nên `budget` = managers × mức quản lý + staff × mức nhân viên.
Không có trục thời gian (`trend = []`, không kỳ so sánh). `/rows` và Excel dùng đúng `load_rows` nên khớp con số.
"""
from __future__ import annotations

from dataclasses import replace

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.report_aggregate import DimensionSpec, MetricSpec, ReportSpec, build_report
from app.core.report_drilldown import Col, filter_group, rows_response
from app.core.report_period import Period

from . import benefit_report_data as data_mod
from .benefit_report_data import BenefitRow
from .benefit_report_inputs import Filters
from .constants import JOB_LEVEL_LABELS
from .profile_gaps_report_data import load_group_names

DEFAULT_GROUP = "company"
LABELS = {"people": "Số người", "children": "Số con", "managers": "Quản lý", "staff": "Nhân viên",
          "budget": "Tổng kinh phí"}


def _dims(company_name: dict, department_name: dict) -> dict[str, DimensionSpec]:
    return {
        "company": DimensionSpec("company", "Pháp nhân", key_of=lambda r: (
            [(r.company_id, company_name.get(r.company_id, ""))] if r.company_id else [])),
        "department": DimensionSpec("department", "Phòng ban", key_of=lambda r: (
            [(r.department_id, department_name.get(r.department_id, ""))] if r.department_id else [])),
        "position": DimensionSpec("position", "Chức vụ", key_of=lambda r: (
            [(r.position_id, r.position)] if r.position_id else [])),
        "job_level": DimensionSpec("job_level", "Cấp bậc", key_of=lambda r: (
            [(r.job_level, JOB_LEVEL_LABELS.get(r.job_level, ""))] if r.job_level else [])),
    }


def _spec(flt: Filters, dims: dict[str, DimensionSpec]) -> ReportSpec:
    metrics = [MetricSpec("people", LABELS["people"], value_of=lambda r: 1)]
    if flt.child_max_age is not None:
        metrics.append(MetricSpec("children", LABELS["children"], value_of=lambda r: r.units))
    metrics += [MetricSpec("managers", LABELS["managers"], value_of=lambda r: r.units if r.is_manager else 0),
                MetricSpec("staff", LABELS["staff"], value_of=lambda r: 0 if r.is_manager else r.units),
                MetricSpec("budget", LABELS["budget"], kind="money", value_of=lambda r: r.amount)]
    return ReportSpec(date_of=lambda r: None, metrics=metrics, dimensions=dims, rank_by="budget")


def _group_by(raw: str | None) -> str | None:
    g = (raw or "").strip() or DEFAULT_GROUP
    return None if g == "none" else g


def build_summary(db: Session, employees_q, period: Period, group_by: str | None, flt: Filters) -> dict:
    group_by = _group_by(group_by)
    names = load_group_names(db, group_by)
    dims = _dims(*names)
    if group_by and group_by not in dims:
        raise HTTPException(422, f"Xem theo không hợp lệ: {group_by}")
    rows = data_mod.load_rows(db, employees_q, period.date_to, flt)
    flat = replace(period, compare="none", compare_from=None, compare_to=None)
    data = build_report(lambda _f, _t: rows, _spec(flt, dims), flat, group_by=group_by)
    data["period"] = period.as_dict()
    data["trend"] = []
    data["meta"]["drilldown_metrics"] = ["people"]
    unit = "con" if flt.child_max_age is not None else "người"
    data["notes"] = [
        f"Tính theo ngày dịp {period.date_to:%d/%m/%Y} (cuối kỳ đã chọn): chỉ nhân sự đang làm vào ngày đó.",
        f"Quản lý = cấp bậc từ Phó phòng trở lên. «Quản lý» và «Nhân viên» đếm theo {unit}; "
        "Tổng kinh phí = số lượng × mức quà tương ứng."]
    no_hire = sum(1 for r in rows if r.hire_estimated)
    if no_hire:
        data["notes"].append(f"Có {no_hire} người thiếu ngày vào làm — báo cáo tạm lấy ngày TẠO hồ sơ làm ngày "
                             "vào (đủ điều kiện «đã vào làm» và tính thâm niên có thể lệch), cần Nhân sự bổ sung.")
    if flt.child_max_age is not None:
        notes = "Đơn vị tính là CON (con trai, con gái) có tuổi không quá mức đã chọn tại ngày dịp, theo hồ sơ người thân."
        data["notes"].append(notes)
    return data


def _columns(flt: Filters) -> list[Col]:
    cols = [Col("employee_code", "Mã NV"), Col("employee_name", "Họ tên"), Col("company", "Pháp nhân"),
            Col("department", "Phòng ban"), Col("position", "Chức vụ")]
    if flt.child_max_age is not None:
        cols.append(Col("children", "Số con", "int"))
    return cols + [Col("amount", "Mức quà", "money"), Col("signature", "Ký nhận")]


def _row_dict(r: BenefitRow, flt: Filters, company_name: dict, department_name: dict) -> dict:
    out = {"employee_code": r.employee_code, "employee_name": r.employee_name,
           "company": company_name.get(r.company_id, ""), "department": department_name.get(r.department_id, ""),
           "position": r.position}
    if flt.child_max_age is not None:
        out["children"] = r.units
    out.update(amount=r.amount, signature="", link=f"/hr/employees/{r.employee_id}")
    return out


def load_list(db: Session, employees_q, period: Period, flt: Filters, group_by: str | None = None,
              group_key: str | None = None) -> tuple[list[BenefitRow], dict, dict]:
    """Hàng đứng sau con số (đã lọc nhóm) + tên pháp nhân + tên phòng ban."""
    company_name, department_name = load_group_names(db, None, always=True)
    dims = _dims(company_name, department_name)
    if group_by and group_by != "none" and group_by not in dims:
        raise HTTPException(422, f"Xem theo không hợp lệ: {group_by}")
    rows = data_mod.load_rows(db, employees_q, period.date_to, flt)
    rows = filter_group(rows, dims.get(group_by) if group_by else None, group_key)
    return rows, company_name, department_name


def build_rows(db: Session, employees_q, period: Period, flt: Filters, metric: str,
               group_by: str | None, group_key: str | None) -> dict:
    rows, cn, dn = load_list(db, employees_q, period, flt, group_by, group_key)
    return rows_response(metric, LABELS[metric], _columns(flt), [_row_dict(r, flt, cn, dn) for r in rows])
