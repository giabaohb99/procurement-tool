"""Khung `/summary` + `/summary/rows` dùng chung cho Sổ quản lý lao động và mẫu 01/PLI (duoc-CR-687).

Hai báo cáo cùng tập người (`people_data.load_people`), chỉ khác bộ chỉ số (`ReportKind`). Chỉ số là
ĐẾM CỜ của từng người nên cộng được ở cả Tổng lẫn từng nhóm «Xem theo» (công ty · phòng ban · nhóm vị
trí việc làm); không có trục thời gian nên `trend = []`, `totals.compare` vẫn tính lại ở kỳ so sánh.

`/rows` dùng đúng `load_people` + đúng `key_of` của chiều gom nên khớp con số. Danh sách KHÔNG có giá trị
nhạy cảm (CCCD, BHXH, ngày sinh, địa chỉ, lương) — chỉ có trong tệp Excel.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.labor_contract_codes import LABOR_CONTRACT_TYPE_LABELS, LaborContractType
from app.core.report_aggregate import DimensionSpec, MetricSpec, ReportSpec, build_report
from app.core.report_drilldown import Col, filter_group, rows_response
from app.core.report_period import Period
from app.core.vn_time import vn_today
from app.modules.employee.constants import (JOB_CATEGORY_HIGH_SKILL, JOB_CATEGORY_LABELS, JOB_CATEGORY_MANAGER,
                                            JOB_CATEGORY_MID_SKILL, JOB_CATEGORY_OTHER)
from app.modules.employee.profile_gaps_report_data import load_group_names

from .people_data import PersonRow, hire_fallback_note, is_civil_contract, load_people

_T = LaborContractType


@dataclass(frozen=True)
class ReportKind:
    """Bộ chỉ số của một báo cáo: khóa -> (nhãn, chiều tốt, hàm đếm cờ)."""
    metrics: dict[str, tuple[str, str | None, Callable[[PersonRow], bool]]]
    notes: tuple[str, ...]
    #  Mẫu 01/PLI chỉ báo cáo HĐLĐ: khoán việc / cộng tác viên (hợp đồng dân sự) bị loại khỏi số và danh sách.
    exclude_civil: bool = False


def _cat(c: int) -> Callable[[PersonRow], bool]:
    return lambda r: r.job_category == c


_COMMON_NOTES = (
    "Người trong báo cáo = nhân sự làm việc ở bất kỳ lúc nào trong kỳ; người có tình trạng «Đã nghỉ» mà "
    "không ghi ngày nghỉ việc không được tính.",
    "Hợp đồng áp cho mỗi người = HĐ đã ký còn hiệu lực tại ngày cuối kỳ (hoặc hôm nay nếu kỳ chưa kết thúc), "
    "không có thì HĐ bắt đầu gần nhất trước đó.",
    "Báo cáo có CCCD, mã số BHXH, ngày sinh, địa chỉ và lương nên chỉ người có quyền xem thông tin nhạy cảm "
    "và quyền xem HĐLĐ mới mở được; danh sách bấm số không hiện các giá trị đó, chỉ tệp Excel mới có.",
)
BOOK = ReportKind(
    metrics={
        "people": ("Người trong sổ", None, lambda r: True),
        "working": ("Đang làm cuối kỳ", None, lambda r: r.working_at_end),
        "left_in_period": ("Nghỉ việc trong kỳ", "down", lambda r: r.left_in_period),
        "missing_required": ("Thiếu thông tin bắt buộc", "down", lambda r: bool(r.missing)),
    },
    notes=_COMMON_NOTES + (
        "«Thiếu thông tin bắt buộc» = thiếu một trong: ngày sinh, CCCD, nơi cư trú, trình độ, ngày "
        "vào làm (hồ sơ chưa ghi), loại HĐ.",))
USAGE = ReportKind(
    exclude_civil=True,
    metrics={
        "people": ("Tổng lao động", None, lambda r: True),
        "female": ("Nữ", None, lambda r: r.is_female),
        "job_manager": ("Nhà quản lý", None, _cat(JOB_CATEGORY_MANAGER)),
        "job_high": ("Chuyên môn kỹ thuật bậc cao", None, _cat(JOB_CATEGORY_HIGH_SKILL)),
        "job_mid": ("Chuyên môn kỹ thuật bậc trung", None, _cat(JOB_CATEGORY_MID_SKILL)),
        "job_other": ("Vị trí việc làm khác", None, _cat(JOB_CATEGORY_OTHER)),
        "ct_indefinite": ("HĐ không xác định thời hạn", None, lambda r: r.contract_type == int(_T.INDEFINITE)),
        "ct_fixed": ("HĐ xác định thời hạn", None, lambda r: r.contract_type == int(_T.FIXED_TERM)),
        "ct_other": ("HĐ khác (thử việc, chưa có HĐ)", None,
                     lambda r: r.contract_type not in (int(_T.INDEFINITE), int(_T.FIXED_TERM))),
    },
    notes=_COMMON_NOTES + (
        "Nộp Sở Nội vụ qua Cổng Dịch vụ công: báo cáo 6 tháng trước ngày 05/6, báo cáo năm trước ngày 05/12 "
        "(mỗi pháp nhân một bản), rồi báo cơ quan BHXH khu vực.",
        "Nhóm vị trí việc làm tự suy từ cấp bậc và trình độ: Phó phòng trở lên = Nhà quản lý; Đại học / "
        "Sau đại học = bậc cao; Trung cấp / Cao đẳng = bậc trung; còn lại = Khác.",
        "Các cột chưa có dữ liệu trong ERP (phụ cấp chi tiết, ngành nghề nặng nhọc, thời gian đóng BHXH) "
        "để trống trong tệp Excel, Nhân sự điền tay."))

COLUMNS = [Col("employee_code", "Mã NV"), Col("employee_name", "Họ tên"), Col("company", "Công ty"),
           Col("department", "Phòng ban"), Col("position", "Chức vụ"), Col("job_category", "Nhóm vị trí việc làm"),
           Col("contract_type", "Loại HĐ"), Col("contract_start", "HĐ bắt đầu", "date"),
           Col("contract_end", "HĐ kết thúc", "date"), Col("hire_date", "Ngày vào làm", "date"),
           Col("resign_date", "Ngày nghỉ việc", "date"), Col("missing", "Thiếu")]


def contract_type_label(code: int) -> str:
    try:
        return LABOR_CONTRACT_TYPE_LABELS[_T(int(code))] if code else ""
    except ValueError:
        return LABOR_CONTRACT_TYPE_LABELS[_T.OTHER]


def _dimensions(company_name: dict, department_name: dict) -> dict[str, DimensionSpec]:
    return {
        "company": DimensionSpec("company", "Công ty", key_of=lambda r: (
            [(r.company_id, company_name.get(r.company_id, ""))] if r.company_id else [])),
        "department": DimensionSpec("department", "Phòng ban", key_of=lambda r: (
            [(r.department_id, department_name.get(r.department_id, ""))] if r.department_id else [])),
        "job_category": DimensionSpec("job_category", "Nhóm vị trí việc làm", key_of=lambda r: [
            (r.job_category, JOB_CATEGORY_LABELS[r.job_category])]),
    }


def _load(kind: ReportKind, employees_q, contracts_q, d_from, d_to, company_id, department_id) -> list[PersonRow]:
    people = load_people(employees_q, contracts_q, d_from, d_to, vn_today(), company_id, department_id)
    return [p for p in people if not is_civil_contract(p)] if kind.exclude_civil else people


def build_summary(db: Session, kind: ReportKind, employees_q, contracts_q, period: Period,
                  group_by: str | None, company_id: int | None = None, department_id: int | None = None) -> dict:
    dims = _dimensions(*load_group_names(db, group_by))
    metrics = [MetricSpec(k, label, good=good, value_of=(lambda r, f=f: 1 if f(r) else 0))
               for k, (label, good, f) in kind.metrics.items()]
    spec = ReportSpec(date_of=lambda r: None, metrics=metrics, dimensions=dims,
                      breakdowns={"job_category": dims["job_category"]}, rank_by="people")
    seen: dict[str, list[PersonRow]] = {}

    def fetch(d_from, d_to):
        everyone = load_people(employees_q, contracts_q, d_from, d_to, vn_today(), company_id, department_id)
        if d_from == period.date_from and d_to == period.date_to:
            seen["everyone"] = everyone                      # ghi chú tính trên kỳ đang xem, không phải kỳ so sánh
        return [p for p in everyone if not is_civil_contract(p)] if kind.exclude_civil else everyone

    data = build_report(fetch, spec, period, group_by=group_by)
    data["trend"] = []
    data["meta"]["drilldown_metrics"] = list(kind.metrics)
    everyone = seen.get("everyone", [])
    data["notes"] = list(kind.notes) + [n for n in (
        hire_fallback_note(everyone),
        civil_excluded_note(sum(1 for p in everyone if is_civil_contract(p))) if kind.exclude_civil else "") if n]
    return data


def civil_excluded_note(n: int) -> str:
    return (f"{n} người ký hợp đồng khoán việc / cộng tác viên không đưa vào mẫu 01/PLI vì không phải hợp đồng "
            "lao động — Nhân sự xem lại nếu cần") if n else ""


def _row_dict(r: PersonRow, company_name: dict, department_name: dict) -> dict:
    return {"employee_code": r.employee_code, "employee_name": r.employee_name,
            "company": company_name.get(r.company_id, ""), "department": department_name.get(r.department_id, ""),
            "position": r.position, "job_category": JOB_CATEGORY_LABELS[r.job_category],
            "contract_type": contract_type_label(r.contract_type), "contract_start": r.contract_start,
            "contract_end": r.contract_end, "hire_date": None if r.hire_missing else r.hire_date,
            "resign_date": r.resign_date, "missing": ", ".join(r.missing),
            "link": f"/hr/employees/{r.employee_id}"}


def build_rows(db: Session, kind: ReportKind, employees_q, contracts_q, period: Period, metric: str,
               group_by: str | None, group_key: str | None, company_id: int | None = None,
               department_id: int | None = None) -> dict:
    """Danh sách người đứng sau một con số (`metric` đã được controller kiểm)."""
    company_name, department_name = load_group_names(db, group_by, always=True)
    dims = _dimensions(company_name, department_name)
    if group_by and group_by != "none" and group_by not in dims:
        raise HTTPException(422, f"Xem theo không hợp lệ: {group_by}")
    label, _good, flag = kind.metrics[metric]
    rows = [r for r in _load(kind, employees_q, contracts_q, period.date_from, period.date_to, company_id,
                             department_id) if flag(r)]
    rows = filter_group(rows, dims.get(group_by) if group_by else None, group_key)
    rows.sort(key=lambda r: r.employee_code)
    return rows_response(metric, label, COLUMNS, [_row_dict(r, company_name, department_name) for r in rows])
