"""Tool `report_summary` — một cửa vào các báo cáo gom sẵn của phân hệ Báo cáo (ai-CR-208, K11 của doc/erp/21 §T1).

Không viết lại phép tính, không gọi HTTP vòng: gọi THẲNG hàm route `/summary` của từng báo cáo, với một `Request` giả
mang bộ lọc làm chuỗi truy vấn. Gác quyền giống hệt màn web:
1. Lớp quyền xem TỪNG báo cáo (duoc-CR-562) — `report_access.can_view_report`, như `require_report` trên route.
2. Lớp quyền vai trò — chạy LẠI đúng dependency gắn ở tham số `user=` của route (`require(entity, "read")`, hay cổng OR
   `_require_progress` của Tiến độ mua hàng). Không chép tay tên entity: đổi cổng ở route là tool đổi theo.
`apply_scope` nằm sẵn trong hàm route nên phạm vi dữ liệu đúng như người đó mở màn báo cáo.

Luôn gửi `preset` (mặc định `this_month`) để mọi route đi nhánh hợp đồng chuẩn `report_aggregate.build_report`
(`period · meta · totals · trend · breakdowns · groups · notes`), không rơi về nhánh cũ theo `year`.
"""
from __future__ import annotations

import inspect
import json
from dataclasses import dataclass, field
from typing import Callable
from urllib.parse import urlencode

from fastapi import HTTPException
from fastapi import params as fastapi_params
from pydantic.fields import FieldInfo
from starlette.requests import Request

from app.core.report_keys import REPORT_META, RETIRED_REPORT_KEYS, ReportKey
from app.core.report_period import COMPARE_MODES, PRESET_KEYS

from .base import ToolContext, ToolSpec

GROUP_CAP = 50          # trần số nhóm trả cho model (route đã có trần riêng, đây là trần cho ngữ cảnh AI)
BREAKDOWN_CAP = 20      # trần số dòng mỗi bảng phân rã
VALUE_MAX_LEN = 200     # trần độ dài một giá trị lọc
COMMON_FILTERS = ("preset", "compare", "date_from", "date_to", "group_by", "company_id")


@dataclass(frozen=True)
class ReportRoute:
    key: ReportKey
    load: Callable[[], Callable]     # nạp trễ hàm route (tránh vòng import khi nạp lớp tool)
    path: str                        # màn báo cáo trên ERP v2
    extra: tuple[str, ...] = ()      # bộ lọc riêng của báo cáo, ngoài COMMON_FILTERS
    no_company: bool = False
    vat: dict = field(default_factory=dict)   # {mã chỉ số: căn cứ VAT} — chỉ ghi chỗ đã soi công thức


def _route(module: str, name: str) -> Callable[[], Callable]:
    def load():
        import importlib

        return getattr(importlib.import_module(f"app.modules.{module}"), name)

    return load


REPORTS: dict[str, ReportRoute] = {
    "purchase_report": ReportRoute(ReportKey.PURCHASE_REPORT, _route("report.summary_controller", "procurement_summary"),
                                   "/report/purchase", vat={"order_value": "sau VAT"}),
    "pr_lines": ReportRoute(ReportKey.PR_LINES, _route("report.controller", "pr_lines_summary"), "/report/pr-lines",
                            extra=("status", "line_status", "assignee", "search")),
    "survey_progress": ReportRoute(ReportKey.SURVEY_PROGRESS, _route("survey_progress.controller", "progress_summary"),
                                   "/report/survey-progress",
                                   extra=("department", "sr_status", "item_group", "assignee", "line_status", "q")),
    "purchase_progress": ReportRoute(ReportKey.PURCHASE_PROGRESS, _route("purchase_progress.controller", "progress_summary"),
                                     "/report/purchase-progress", extra=("department", "recv_state", "q")),
    "survey_report": ReportRoute(ReportKey.SURVEY_REPORT, _route("survey.controller", "report_summary_"), "/report/survey",
                                 extra=("kind", "item_group", "supplier", "q", "nspt")),
    "hr_headcount": ReportRoute(ReportKey.HR_HEADCOUNT, _route("employee.report_controller", "employee_summary"),
                                "/report/hr-headcount"),
    "leave_usage": ReportRoute(ReportKey.LEAVE_USAGE, _route("leave.report_controller", "leave_request_summary"),
                               "/report/leave-usage"),
    "leave_balance": ReportRoute(ReportKey.LEAVE_BALANCE, _route("leave.balance_report_controller", "leave_balance_summary"),
                                 "/report/leave-balance"),
    "vehicle_booking": ReportRoute(ReportKey.VEHICLE_BOOKING, _route("vehicle_booking.report_controller", "booking_summary"),
                                   "/report/vehicle-booking"),
    "seal_request": ReportRoute(ReportKey.SEAL_REQUEST, _route("seal_request.report_controller", "seal_summary"),
                                "/report/seal-request"),
    "document": ReportRoute(ReportKey.DOCUMENT, _route("document.report_controller", "document_summary"), "/report/document"),
    "approval": ReportRoute(ReportKey.APPROVAL, _route("approval.report_controller", "approval_summary"), "/report/approval",
                            no_company=True),
    "work": ReportRoute(ReportKey.WORK, _route("work.report_controller", "work_summary"), "/report/work",
                        extra=("list_id",)),
    #  duoc-CR-686: hai báo cáo Nhân sự mới. `/summary` chỉ trả số đếm (lương chỉ nằm ở `/summary/rows`,
    #  công cụ này không gọi tới) nên mở cho trợ lý như các báo cáo Nhân sự khác.
    "labor_contract": ReportRoute(ReportKey.LABOR_CONTRACT, _route("labor_contract.report_controller",
                                                                   "labor_contract_summary"), "/report/labor-contract"),
    "hr_profile_gaps": ReportRoute(ReportKey.HR_PROFILE_GAPS, _route("employee.profile_gaps_report_controller",
                                                                     "profile_gaps_summary"), "/report/hr-profile-gaps"),
    #  duoc-CR-687: sổ lao động + mẫu 01/PLI. `/summary` chỉ trả số đếm (CCCD, BHXH, lương chỉ ở tệp Excel); route tự
    #  đòi thêm `employee_sensitive.read` + `labor_contract.read` nên trợ lý không vượt được quyền người hỏi.
    "labor_book": ReportRoute(ReportKey.LABOR_BOOK, _route("labor_register.register_controller",
                                                           "labor_register_summary"), "/report/labor-register"),
    "labor_usage_report": ReportRoute(ReportKey.LABOR_USAGE_REPORT, _route("labor_register.usage_report_controller",
                                                                           "labor_usage_summary"), "/report/labor-usage-report"),
    #  duoc-CR-688: phúc lợi, cơ cấu quản lý, điều chuyển — `/summary` chỉ trả số đếm. «Quỹ lương theo pháp nhân»
    #  (khóa 21) CỐ Ý KHÔNG mở cho trợ lý: số lương, chỉ người được giao xem trên màn riêng. Từ duoc-CR-693 nó đọc ô
    #  lương trên hồ sơ (gác `employee.read|export` + khóa 21) — vẫn ĐÓNG, xem `CLOSED_FOR_AI`.
    #  Khóa 25 «Định biên kế hoạch so với thực tế» đã BỎ hẳn (duoc-CR-692, `RETIRED_REPORT_KEYS`) — không có ở đây.
    "benefit_audience": ReportRoute(ReportKey.BENEFIT_AUDIENCE, _route("employee.benefit_report_controller",
                                                                       "benefit_summary"), "/report/benefit-audience"),
    "management_span": ReportRoute(ReportKey.MANAGEMENT_SPAN, _route("employee.management_report_controller",
                                                                     "management_span_summary"), "/report/management-span"),
    "work_moves": ReportRoute(ReportKey.WORK_MOVES, _route("employee.work_move_report_controller",
                                                           "work_moves_summary"), "/report/work-moves"),
    #  duoc-CR-689: `/summary` chỉ trả số đếm; route tự đòi thêm quyền (nhạy cảm / đơn nghỉ) khi cần.
    "attendance_daily": ReportRoute(ReportKey.ATTENDANCE_DAILY, _route("work_schedule.attendance_report_controller",
                                                                       "attendance_summary"), "/report/attendance"),
    "profile_changes": ReportRoute(ReportKey.PROFILE_CHANGES, _route("employee.change_request_report_controller",
                                                                     "profile_change_summary"), "/report/profile-changes"),
    "room_usage": ReportRoute(ReportKey.ROOM_USAGE, _route("meeting_room.report_controller", "room_usage_summary"),
                              "/report/room-usage"),
    "legal_watch": ReportRoute(ReportKey.LEGAL_WATCH, _route("employee.legal_watch_report_controller",
                                                             "legal_watch_summary"), "/report/legal-watch"),
}
_BY_NUMBER = {int(r.key): name for name, r in REPORTS.items()}

#  Khóa CÓ THẬT ở phân hệ Báo cáo nhưng CỐ Ý không mở cho trợ lý / MCP, kèm lý do để model nói đúng thay vì «mã lạ».
#  Bài kiểm `test_moi_khoa_bao_cao_deu_co_route_va_dung_khoa_gac` giữ: REPORTS + CLOSED_FOR_AI = mọi ReportKey.
CLOSED_FOR_AI: dict[ReportKey, str] = {
    ReportKey.USAGE_PROFILE: "dữ liệu hành vi từng người, chỉ xem trên màn riêng",
    ReportKey.FEATURE_USAGE: "dữ liệu hành vi, chỉ xem trên màn riêng",
    ReportKey.WORK_CAPABILITY: "đã có công cụ riêng team_capacity / task_type_stats",
    ReportKey.PAYROLL_FUND: "số lương — trợ lý không đọc lương, chỉ người được giao xem trên màn Báo cáo",
}


def _not_open_reason(raw) -> str | None:
    """Khóa đã bỏ / cố ý đóng với trợ lý (số `21` hay tên `payroll_fund`) → câu giải thích; còn lại None (mã lạ thật)."""
    text = str(raw or "").strip()
    if text.isdigit() and int(text) in RETIRED_REPORT_KEYS:
        return f"Báo cáo số {int(text)} đã ngừng dùng (bỏ khỏi phân hệ Báo cáo)."
    key = next((k for k in CLOSED_FOR_AI if text == str(int(k)) or text.upper() == k.name), None)
    if key is None:
        return None
    return f"Báo cáo «{REPORT_META[key][0]}» không mở cho trợ lý AI: {CLOSED_FOR_AI[key]}."


def resolve_report_key(raw) -> str | None:
    """Nhận mã chữ (`leave_usage`) hoặc số khóa (7 / "7"); trả mã chữ, lạ thì None."""
    text = str(raw or "").strip().lower()
    if text in REPORTS:
        return text
    return _BY_NUMBER.get(int(text)) if text.isdigit() else None


def _allowed_filters(route: ReportRoute) -> tuple[str, ...]:
    common = tuple(k for k in COMMON_FILTERS if not (route.no_company and k == "company_id"))
    return common + route.extra


def _query_params(route: ReportRoute, filters: dict) -> tuple[dict, list[str]]:
    allowed = _allowed_filters(route)
    params, ignored = {}, []
    for k, v in (filters or {}).items():
        if k not in allowed:
            ignored.append(str(k))
            continue
        if v is None or v == "":
            continue
        params[k] = str(v).strip()[:VALUE_MAX_LEN]
    params.setdefault("preset", "this_month")
    return params, ignored


def _fake_request(params: dict) -> Request:
    return Request({"type": "http", "method": "GET", "path": "/", "headers": [],
                    "query_string": urlencode(params).encode("utf-8")})


def _run_dependency(dep: Callable, db, user):
    """Chạy một dependency cổng quyền (`require(...)`, `_require_progress`) với đúng người hỏi — nó ném 403 nếu thiếu."""
    kwargs = {}
    for name in inspect.signature(dep).parameters:
        if name == "db":
            kwargs[name] = db
        elif name == "user":
            kwargs[name] = user
    return dep(**kwargs)


def call_summary_route(fn: Callable, db, user, params: dict) -> dict:
    """Gọi hàm route `/summary` như FastAPI gọi: `request` giả, `db`, `user` qua cổng quyền của route, tham số `Query`
    lấy từ bộ lọc. Trả phần `data` của phong bì `success(...)`."""
    request = _fake_request(params)
    kwargs = {}
    for name, p in inspect.signature(fn).parameters.items():
        default = p.default
        if name == "request":
            kwargs[name] = request
        elif name == "db":
            kwargs[name] = db
        elif isinstance(default, fastapi_params.Depends):
            kwargs[name] = _run_dependency(default.dependency, db, user)
        elif isinstance(default, FieldInfo):
            kwargs[name] = params.get(name, default.default)
        else:
            kwargs[name] = params.get(name, "" if default is inspect.Parameter.empty else default)
    resp = fn(**kwargs)
    return json.loads(resp.body)["data"]


def _cap_list(rows, cap: int) -> tuple[list, int]:
    rows = list(rows or [])
    return rows[:cap], len(rows)


def _cap_breakdowns(breakdowns):
    """`breakdowns` = {chiều: [dòng]} (`report_aggregate.aggregate`)."""
    if not isinstance(breakdowns, dict):
        return breakdowns
    return {k: rows[:BREAKDOWN_CAP] if isinstance(rows, list) else rows for k, rows in breakdowns.items()}


def _shape(name: str, route: ReportRoute, data: dict, ignored: list[str]) -> dict:
    label, group = REPORT_META[route.key]
    meta = dict(data.get("meta") or {})
    if route.vat and isinstance(meta.get("metrics"), list):
        meta["metrics"] = [dict(m, vat=route.vat[m.get("key")]) if m.get("key") in route.vat else m
                           for m in meta["metrics"]]
    out = {"report_key": name, "report_key_id": int(route.key), "label": label, "group": group,
           "link": route.path, "currency": "VND", "period": data.get("period"), "meta": meta,
           "totals": data.get("totals"), "trend": data.get("trend"),
           "breakdowns": _cap_breakdowns(data.get("breakdowns")), "notes": data.get("notes")}
    if data.get("groups") is not None:
        groups, total = _cap_list(data["groups"], GROUP_CAP)
        out.update(groups=groups, total=total, has_more=total > len(groups))
    if ignored:
        out["ignored_filters"] = ignored
        out["allowed_filters"] = list(_allowed_filters(route))
    return out


def _report_summary(ctx: ToolContext, args: dict) -> dict:
    name = resolve_report_key(args.get("report_key"))
    if name is None and (reason := _not_open_reason(args.get("report_key"))):
        return {"denied": True, "error": reason + " Đừng thử công cụ khác để lấy cùng số liệu."}
    if name is None:
        choices = ", ".join(f"{k} ({REPORT_META[r.key][0]})" for k, r in REPORTS.items())
        return {"error": f"report_key không hợp lệ: {args.get('report_key')!r}. Chọn một trong: {choices}."}
    route = REPORTS[name]
    label = REPORT_META[route.key][0]
    filters = args.get("filters") if isinstance(args.get("filters"), dict) else {}

    from app.modules.report_access.service import can_view_report

    if not can_view_report(ctx.db, ctx.user, route.key):
        return {"denied": True, "error": f"Chưa được giao xem báo cáo «{label}» — nhờ quản trị gán ở Phân quyền tài khoản "
                                         "→ tab Báo cáo. Đừng thử công cụ khác để lấy cùng số liệu."}
    params, ignored = _query_params(route, filters)
    try:
        data = call_summary_route(route.load(), ctx.db, ctx.user, params)
    except HTTPException as e:
        if e.status_code == 403:
            return {"denied": True, "error": f"Báo cáo «{label}»: {e.detail} (thiếu quyền vai trò ở phân hệ gốc)."}
        return {"error": f"Báo cáo «{label}»: {e.detail}"}
    return _shape(name, route, data, ignored)


def _filters_schema() -> dict:
    extras = sorted({k for r in REPORTS.values() for k in r.extra})
    props = {
        "preset": {"type": "string", "enum": list(PRESET_KEYS), "default": "this_month",
                   "description": "Kỳ báo cáo. custom thì cần date_from + date_to."},
        "compare": {"type": "string", "enum": list(COMPARE_MODES), "default": "previous",
                    "description": "So với kỳ trước (previous), cùng kỳ năm trước (year) hay không so (none)."},
        "date_from": {"type": "string", "description": "YYYY-MM-DD, chỉ dùng với preset=custom."},
        "date_to": {"type": "string", "description": "YYYY-MM-DD, chỉ dùng với preset=custom."},
        "group_by": {"type": "string", "description": "Xem theo một chiều — mã lấy ở meta.dimensions của lần gọi trước."},
        "company_id": {"type": "integer", "description": "Lọc một pháp nhân (không áp cho approval)."},
    }
    for k in extras:
        props[k] = {"type": "string", "description": "Bộ lọc riêng: " + ", ".join(
            n for n, r in REPORTS.items() if k in r.extra) + "."}
    return {"type": "object", "properties": props, "additionalProperties": False}


REPORT_SUMMARY_SPEC = ToolSpec(
    name="report_summary",
    description=("Số liệu TỔNG HỢP của các báo cáo ở phân hệ Báo cáo (danh sách ở report_key), đúng số màn web hiện (kỳ + so sánh kỳ trước, xu hướng, "
                 "phân rã, Xem theo). Mã báo cáo: " + "; ".join(f"{k} = {REPORT_META[r.key][0]} ({REPORT_META[r.key][1]})"
                                                             for k, r in REPORTS.items())
                 + ". Cần được giao xem báo cáo đó VÀ có quyền xem phân hệ gốc; thiếu thì trả denied kèm lý do. Tiền là VND; "
                 "nhãn, loại, căn cứ VAT của từng chỉ số nằm ở meta.metrics; link là màn báo cáo trên ERP."),
    parameters={
        "type": "object",
        "properties": {
            "report_key": {"type": "string", "enum": list(REPORTS),
                           "description": "; ".join(f"{k}: {REPORT_META[r.key][0]}" for k, r in REPORTS.items())},
            "filters": _filters_schema(),
        },
        "required": ["report_key"],
    },
    handler=_report_summary,
)
