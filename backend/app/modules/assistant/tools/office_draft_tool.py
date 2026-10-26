"""Soạn nháp PHIẾU ĐẶT XE và PHIẾU DUYỆT DẤU cho Trợ lý web / bot / cổng MCP (kh-AI2-6).

Khuôn draft_* + confirm_draft: tool chỉ SOẠN NHÁP (tìm người duyệt, công ty theo tên / mã, đọc giờ), không ghi gì. Tạo thật ở
`agent_hub/draft_create` (kind `vehicle_booking` / `seal_request`) bằng ĐÚNG service tạo phiếu của màn web — lúc đó kiểm lại
quyền create, công ty, người duyệt (luật duoc-CR-681: người duyệt phải còn quyền Duyệt đặt xe, không tự chọn mình).
Phiếu duyệt dấu chỉ lưu NHÁP: gửi duyệt cần tệp chứng từ đính kèm, mà tệp tải lên ở web.
"""
from __future__ import annotations

import re
from datetime import datetime

from . import confirm_fields
from .base import ToolContext, ToolSpec, denied

_TIME = re.compile(r"^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}$")
MAX_TEXT = 255


def _text(v, limit: int = MAX_TEXT) -> str:
    return " ".join(str(v or "").split())[:limit]


def _fold(v: str) -> str:
    from app.modules.assistant.glossary import fold

    return fold(v)


def _pick(options: list[dict], raw: str, keys: tuple[str, ...], what: str) -> tuple[dict | None, dict | None]:
    """Một lựa chọn theo mã đúng hoặc tên chứa chữ; không thấy / nhiều → câu hỏi lại cho model."""
    want = _text(raw, 120)
    exact = [o for o in options if any(str(o.get(k) or "").lower() == want.lower() for k in keys)]
    hit = exact or [o for o in options if _fold(want) and any(_fold(want) in _fold(str(o.get(k) or "")) for k in keys)]
    if len(hit) == 1:
        return hit[0], None
    names = [str(o.get("name") or "") + (f" ({o['code']})" if o.get("code") else "") for o in (hit or options)][:10]
    return None, {"need_choice": what, "options": names,
                  "note": f"{'Không thấy' if not hit else 'Có nhiều'} {what} khớp «{want}». Hỏi người dùng MỘT câu, đưa danh "
                          "sách đánh số, rồi gọi lại tool với đúng tên / mã."}


def _iso_minute(raw) -> str:
    v = _text(raw, 20)
    if not v:
        return ""
    if not _TIME.match(v):
        raise ValueError(v)
    return datetime.fromisoformat(v.replace(" ", "T")).isoformat(timespec="minutes")


def _companies(ctx: ToolContext) -> list[dict]:
    from app.modules.vehicle_booking import approver_picker

    return [{**c, "code": c.get("short_name") or ""} for c in approver_picker.company_options(ctx.db)]


def _my_company(ctx: ToolContext) -> int:
    from app.modules.employee.model import Employee

    emp_id = int(getattr(ctx.user, "employee_id", 0) or 0)
    return int(ctx.db.query(Employee.company_id).filter(Employee.id == emp_id).scalar() or 0) if emp_id else 0


def _draft_vehicle_booking(ctx: ToolContext, args: dict) -> dict:
    from app.modules.vehicle_booking import approver_picker
    from app.modules.vehicle_booking.model import TYPE_CAR, TYPE_DELIVERY

    if not ctx.can("vehicle_booking", "create"):
        return denied("lập phiếu đặt xe")
    _user_text, asked = confirm_fields.take_context(args)
    delivery = str(args.get("request_type") or "").strip().lower() in ("giao_hang", "delivery", "2")
    purpose = _text(args.get("purpose"), 1000)
    try:
        start, end = _iso_minute(args.get("start_time")), _iso_minute(args.get("end_time"))
    except ValueError as e:
        return {"error": f"Giờ «{e}» phải dạng YYYY-MM-DD HH:MM (giờ Việt Nam)."}
    missing = [{"field": f, "question": q} for f, q, ok in (
        ("purpose", "Đi đâu, việc gì (mục đích chuyến)?", purpose),
        ("start_location", "Đón ở đâu?", _text(args.get("start_location"))),
        ("end_location", "Đến đâu?", _text(args.get("end_location"))),
        ("start_time", "Đi lúc mấy giờ, ngày nào?", start),
        ("end_time", "Dự kiến về / xong lúc nào?", end),
        ("approver", "Ai phê duyệt phiếu này?", _text(args.get("approver")))) if not ok and f not in asked]
    if missing:
        return confirm_fields.need(missing)
    if start and end and end <= start:
        return {"error": "Giờ kết thúc phải sau giờ bắt đầu."}
    approver, problem = (None, None)
    if _text(args.get("approver")):
        options = [o for o in approver_picker.approver_options(ctx.db) if o["user_id"] != ctx.user.id]
        approver, problem = _pick(options, args.get("approver"), ("code", "name"), "người phê duyệt")
        if problem:
            return problem
    company_id, company_name = _my_company(ctx), ""
    companies = _companies(ctx)
    if _text(args.get("company")):
        picked, problem = _pick(companies, args.get("company"), ("code", "name", "tax_code"), "công ty")
        if problem:
            return problem
        company_id = int(picked["id"])
    company_name = next((c["name"] for c in companies if c["id"] == company_id), "")
    passengers = max(1, min(int(args.get("passenger_count") or 1), 100)) if str(args.get("passenger_count") or "1").isdigit() else 1
    draft = {
        "request_type": TYPE_DELIVERY if delivery else TYPE_CAR,
        "request_type_label": "Đặt xe giao hàng" if delivery else "Đặt xe công tác",
        "purpose": purpose, "start_location": _text(args.get("start_location")), "end_location": _text(args.get("end_location")),
        "start_time": start, "end_time": end, "passenger_count": passengers,
        "is_round_trip": bool(args.get("is_round_trip")), "attendees": _text(args.get("attendees"), 1000),
        "goods_name": _text(args.get("goods_name")) if delivery else "",
        "receiver_name": _text(args.get("receiver_name")) if delivery else "",
        "special_instructions": _text(args.get("special_instructions"), 1000), "note": _text(args.get("note"), 1000),
        "company_id": company_id, "company_name": company_name,
        "first_approver_id": int(approver["user_id"]) if approver else 0,
        "approver_name": f"{approver['code']} - {approver['name']}" if approver else "",
    }
    return {"draft": draft, "kind": "vehicle_booking",
            "note": ("Đã soạn nháp, CHƯA tạo. Đưa người dùng xem; họ đồng ý thì xác nhận nháp (kind=vehicle_booking; "
                     "submit=true để gửi duyệt luôn tới người phê duyệt đã chọn). Đừng tự báo là đã tạo.")}


def _draft_seal_request(ctx: ToolContext, args: dict) -> dict:
    from app.modules.seal_request import service as seal_service

    if not ctx.can("seal_request", "create"):
        return denied("lập phiếu duyệt dấu")
    _user_text, asked = confirm_fields.take_context(args)
    purpose = _text(args.get("purpose"), 1000)
    names = [n for n in (args.get("companies") or []) if _text(n)][:10] if isinstance(args.get("companies"), list) else []
    missing = [{"field": f, "question": q} for f, q, ok in (
        ("purpose", "Đóng dấu cho giấy tờ gì, dùng vào việc gì?", purpose),
        ("companies", "Đóng dấu của công ty nào?", names)) if not ok and f not in asked]
    if missing:
        return confirm_fields.need(missing)
    companies, picked = _companies(ctx), []
    for n in names:
        one, problem = _pick(companies, n, ("code", "name", "tax_code"), "công ty")
        if problem:
            return problem
        if one["id"] not in [c["id"] for c in picked]:
            picked.append(one)
    opts = seal_service.approver_options(ctx.db, ctx.user)
    approver = next((o for o in opts["items"] if o["id"] == opts["default_id"]), None)
    if _text(args.get("approver")):
        approver, problem = _pick(opts["items"], args.get("approver"), ("name", "email"), "người phê duyệt")
        if problem:
            return problem
    copies = int(args.get("copies")) if str(args.get("copies") or "").isdigit() else 1
    draft = {"title": _text(args.get("title")), "purpose": purpose, "copies": max(1, min(copies, 100)),
             "company_ids": [c["id"] for c in picked], "company_names": [c["name"] for c in picked],
             "first_approver_id": int(approver["id"]) if approver else 0,
             "approver_name": approver["name"] if approver else "", "note": _text(args.get("note"), 1000)}
    return {"draft": draft, "kind": "seal_request",
            "note": ("Đã soạn nháp, CHƯA tạo. Người dùng đồng ý thì xác nhận nháp (kind=seal_request) — phiếu lưu ở trạng "
                     "thái Nháp; nhắc họ mở phiếu trên web tải tệp chứng từ cần đóng dấu rồi bấm Gửi duyệt (gửi duyệt cần "
                     "tệp đính kèm nên không gửi qua AI).")}


DRAFT_VEHICLE_BOOKING_SPEC = ToolSpec(
    name="draft_vehicle_booking",
    description=("SOẠN NHÁP phiếu ĐẶT XE ('đặt xe đi Cần Thơ sáng thứ 6', 'xe giao hàng cho khách X'). Cần mục đích, điểm đón, "
                 "điểm đến, giờ đi / giờ về (YYYY-MM-DD HH:MM giờ VN) và người phê duyệt (tên hoặc mã nhân sự — phải là "
                 "người có quyền duyệt đặt xe, không chọn chính mình). Công ty bỏ trống = công ty của người hỏi. Thiếu gì "
                 "tool trả câu hỏi; tên mơ hồ tool trả lựa chọn — hỏi người dùng MỘT câu."),
    parameters={"type": "object", "properties": {
        "request_type": {"type": "string", "enum": ["cong_tac", "giao_hang"], "description": "Công tác (chở người, mặc định) hay giao hàng."},
        "purpose": {"type": "string"}, "start_location": {"type": "string"}, "end_location": {"type": "string"},
        "start_time": {"type": "string", "description": "YYYY-MM-DD HH:MM"}, "end_time": {"type": "string", "description": "YYYY-MM-DD HH:MM"},
        "passenger_count": {"type": "integer"}, "is_round_trip": {"type": "boolean"},
        "attendees": {"type": "string", "description": "Người đi cùng (tùy chọn)."},
        "goods_name": {"type": "string", "description": "Hàng cần chở (xe giao hàng)."},
        "receiver_name": {"type": "string", "description": "Người nhận (xe giao hàng)."},
        "special_instructions": {"type": "string"}, "note": {"type": "string"},
        "approver": {"type": "string", "description": "Tên hoặc mã nhân sự người phê duyệt."},
        "company": {"type": "string", "description": "Tên / tên viết tắt / MST công ty (tùy chọn)."},
        "asked_fields": confirm_fields.ASKED_PARAM}},
    handler=_draft_vehicle_booking,
)

DRAFT_SEAL_REQUEST_SPEC = ToolSpec(
    name="draft_seal_request",
    description=("SOẠN NHÁP phiếu DUYỆT DẤU ('xin đóng dấu hợp đồng đại lý cho công ty X, 2 bản'). Cần mục đích và công ty cần "
                 "đóng dấu (một hoặc nhiều). Người phê duyệt bỏ trống = trưởng bộ phận mặc định. Phiếu chỉ lưu NHÁP — người "
                 "dùng tải tệp chứng từ và gửi duyệt trên web."),
    parameters={"type": "object", "properties": {
        "purpose": {"type": "string"}, "title": {"type": "string", "description": "Tên chứng từ cần đóng dấu."},
        "copies": {"type": "integer", "description": "Số bản (mặc định 1)."},
        "companies": {"type": "array", "items": {"type": "string"}, "description": "Tên / MST các công ty cần đóng dấu."},
        "approver": {"type": "string", "description": "Tên người phê duyệt (tùy chọn)."},
        "note": {"type": "string"}, "asked_fields": confirm_fields.ASKED_PARAM}},
    handler=_draft_seal_request,
)

OFFICE_DRAFT_SPECS = [DRAFT_VEHICLE_BOOKING_SPEC, DRAFT_SEAL_REQUEST_SPEC]
