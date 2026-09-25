"""CỔNG MCP của ERP (ai-CR-063, M-01 · M-03 · M-04 · M-05 của `doc/agent-hub/04`).

Một cửa `POST /api/mcp` nói JSON-RPC 2.0 theo Model Context Protocol (transport Streamable HTTP, trả JSON
thường — không cần luồng SSE cho bộ tool gọi-rồi-trả). Ứng dụng AI của từng người (Claude Desktop, Cursor,
ChatGPT…) gắn khóa MCP cá nhân (`mcp_keys`) vào `Authorization: Bearer …` và gọi ĐÚNG bộ tool loại A mà Trợ lý
web và bot Telegram đang dùng (`assistant.tools`): không viết lại tool, không mở đường mới vào dữ liệu.

Mỗi lượt `tools/call` chạy `run_tool` dưới danh tính CHỦ KHÓA — hai lớp quyền (`can` + `apply_scope`) và audit
của tool giữ nguyên. Khóa CHỈ ĐỌC chỉ thấy tool tra cứu; khóa ĐƯỢC GHI thấy thêm tool soạn nháp, và hai tool riêng
của cổng: `confirm_draft` (tạo / gửi duyệt hai bước — bản nháp phải được người dùng xem rồi mới xác nhận) và
`report_issue` (báo lỗi → phiếu hỗ trợ → Đậu Đậu). Đề nghị thanh toán không tạo qua đây (chỉ web).
"""
from __future__ import annotations

import json
import logging

from fastapi import APIRouter, Depends, Header, Request, Response
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db

from . import draft_create, mcp_keys

log = logging.getLogger("app.agent_hub.mcp")

PROTOCOL_VERSION = "2025-06-18"
SERVER_INFO = {"name": "dego-erp", "version": "1.0"}
INSTRUCTIONS = ("Bộ công cụ ERP nội bộ DEGO Holding. Mọi tool chạy dưới quyền của chủ khóa: dữ liệu trả về đã lọc theo "
                "phạm vi người đó được xem. Muốn tạo phiếu: gọi tool draft_* để có bản nháp, đưa người dùng xem, rồi gọi "
                "confirm_draft với đúng bản nháp đó (submit=true để gửi duyệt luôn). Báo lỗi hệ thống: report_issue.")
#  Tool GHI: chỉ khóa «được ghi» mới thấy. Đề xuất sửa phiếu / lập bộ tài khoản (propose_*) cố ý KHÔNG mở qua MCP:
#  hai tool đó xác nhận bằng nút trên web/Telegram, cổng này chưa có nút.
WRITE_PREFIXES = ("draft_",)
WRITE_NAMES = {"ticket_create", "export_report_file", "export_excel_file"}
HIDDEN = {"propose_document_update", "propose_account_setup"}

CONFIRM_DRAFT_DEF = {
    "name": "confirm_draft",
    "description": ("Tạo thật phiếu từ bản nháp do tool draft_* trả về (leave = đơn nghỉ phép, survey = yêu cầu báo giá, "
                    "purchase = yêu cầu mua hàng, ticket = phiếu hỗ trợ). CHỈ gọi sau khi người dùng đã xem bản nháp và "
                    "đồng ý. submit=true thì gửi duyệt ngay sau khi tạo (leave/survey/purchase)."),
    "inputSchema": {"type": "object", "properties": {
        "kind": {"type": "string", "enum": ["leave", "survey", "purchase", "ticket"]},
        "draft": {"type": "object", "description": "Đúng đối tượng draft mà tool draft_* trả về."},
        "submit": {"type": "boolean", "default": False}}, "required": ["kind", "draft"]},
}
REPORT_ISSUE_DEF = {
    "name": "report_issue",
    "description": ("Báo một lỗi hoặc yêu cầu sửa phần mềm ERP: mở phiếu hỗ trợ cho nhóm kỹ thuật (bot sửa mã Đậu Đậu "
                    "nhận việc từ phiếu này). Ghi rõ màn hình, thao tác, kết quả mong đợi và kết quả thực tế."),
    "inputSchema": {"type": "object", "properties": {
        "title": {"type": "string", "maxLength": 200}, "detail": {"type": "string", "maxLength": 4000},
        "screen_url": {"type": "string", "description": "Đường dẫn màn hình đang lỗi, nếu có."}},
        "required": ["title", "detail"]},
}


def is_write_tool(name: str) -> bool:
    return name.startswith(WRITE_PREFIXES) or name in WRITE_NAMES


def list_tools(db: Session, scope: int) -> list[dict]:
    from app.modules.assistant.tools import tool_defs

    out = []
    for d in tool_defs(db):
        if d.name in HIDDEN:
            continue
        if scope != mcp_keys.SCOPE_WRITE and is_write_tool(d.name):
            continue
        out.append({"name": d.name, "description": d.description, "inputSchema": d.parameters})
    if scope == mcp_keys.SCOPE_WRITE:
        out += [CONFIRM_DRAFT_DEF, REPORT_ISSUE_DEF]
    else:
        out.append(REPORT_ISSUE_DEF)      # báo lỗi thì ai cũng được (M-05)
    return out


def call_tool(db: Session, user, scope: int, name: str, args: dict) -> dict:
    """Trả dict kết quả (JSON-hóa được). Lỗi nghiệp vụ → {"error": ...}, không ném."""
    from app.modules.assistant.tools import run_tool

    if name == "report_issue":
        return _report_issue(db, user, args)
    if name == "confirm_draft":
        if scope != mcp_keys.SCOPE_WRITE:
            return {"error": "Khóa này chỉ đọc; tạo phiếu cần khóa «được ghi» (tạo ở Trang cá nhân → Khóa AI)."}
        return _confirm_draft(db, user, args)
    if name in HIDDEN or (scope != mcp_keys.SCOPE_WRITE and is_write_tool(name)):
        return {"error": f"Công cụ '{name}' không mở cho khóa này."}
    return run_tool(db, user, name, args or {})


def _confirm_draft(db: Session, user, args: dict) -> dict:
    kind = str(args.get("kind") or "")
    draft = args.get("draft") if isinstance(args.get("draft"), dict) else None
    if kind not in draft_create.LABELS or draft is None:
        return {"error": "Cần kind (leave/survey/purchase/ticket) và draft là đối tượng do tool draft_* trả về."}
    if kind == "payment":
        return {"error": "Đề nghị thanh toán chỉ tạo trên web: " + draft_create.payment_link(draft)}
    submit = bool(args.get("submit"))
    if submit and kind in draft_create.SUBMITTABLE:
        if missing := draft_create.missing_for_submit(kind, draft):
            return {"error": f"Chưa gửi duyệt được: {missing} Chưa tạo gì."}
    try:
        code, oid = draft_create.create(db, user, kind, draft)
        if submit and kind in draft_create.SUBMITTABLE:
            draft_create.submit(db, user, kind, oid)
    except draft_create.DraftError as e:
        return {"error": str(e)}
    return {"ok": True, "code": code, "id": oid, "submitted": bool(submit and kind in draft_create.SUBMITTABLE),
            "details": draft_create.created_details(db, kind, oid),
            "link": draft_create.DETAIL_PATHS.get(kind, "").format(id=oid) if hasattr(draft_create, "DETAIL_PATHS") else ""}


def _report_issue(db: Session, user, args: dict) -> dict:
    from app.modules.ticket import service as ticket_service
    from app.modules.ticket.schema import TicketCreate

    title = str(args.get("title") or "").strip()[:200]
    detail = str(args.get("detail") or "").strip()[:4000]
    if not title or not detail:
        return {"error": "Cần title và detail."}
    dept = (settings.AGENT_TICKET_DEPARTMENTS or "").split(",")[0].strip()
    body = detail + (f"\n\nMàn hình: {args.get('screen_url')}" if args.get("screen_url") else "") + "\n\n(Gửi qua cổng MCP.)"
    t = ticket_service.create_ticket(db, TicketCreate(subject=title, department=dept, body=body),
                                     user_id=user.id, requester_emp_id=int(getattr(user, "employee_id", 0) or 0))
    db.commit()
    return {"ok": True, "ticket": t.code, "department": dept,
            "note": "Nhóm kỹ thuật (và bot sửa mã) sẽ nhận phiếu này." if dept else "Phiếu đã tạo, chưa gắn bộ phận."}


# ---------------------------------------------------------------------------
# JSON-RPC
# ---------------------------------------------------------------------------
def _err(rid, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": rid, "error": {"code": code, "message": message}}


def _ok(rid, result) -> dict:
    return {"jsonrpc": "2.0", "id": rid, "result": result}


def handle(db: Session, user, key, msg: dict) -> dict | None:
    """Một thông điệp JSON-RPC → một trả lời (None với notification)."""
    if not isinstance(msg, dict) or msg.get("jsonrpc") != "2.0" or not isinstance(msg.get("method"), str):
        return _err(msg.get("id") if isinstance(msg, dict) else None, -32600, "Không phải yêu cầu JSON-RPC 2.0 hợp lệ")
    method, rid, params = msg["method"], msg.get("id"), msg.get("params") or {}
    if method.startswith("notifications/"):
        return None
    if method == "initialize":
        return _ok(rid, {"protocolVersion": PROTOCOL_VERSION, "capabilities": {"tools": {"listChanged": False}},
                         "serverInfo": SERVER_INFO, "instructions": INSTRUCTIONS})
    if method == "ping":
        return _ok(rid, {})
    if method == "tools/list":
        return _ok(rid, {"tools": list_tools(db, int(key.scope or 0))})
    if method == "tools/call":
        name = str(params.get("name") or "")
        args = params.get("arguments") if isinstance(params.get("arguments"), dict) else {}
        if not name:
            return _err(rid, -32602, "Thiếu tên tool")
        try:
            result = call_tool(db, user, int(key.scope or 0), name, args)
        except Exception as e:  # noqa: BLE001 — lỗi tool không được thành 500 của cổng
            log.exception("agent_hub mcp: tool %s hỏng", name)
            result = {"error": f"Lỗi khi chạy công cụ: {e}"}
        text = json.dumps(result, ensure_ascii=False, default=str)
        return _ok(rid, {"content": [{"type": "text", "text": text}], "isError": bool(isinstance(result, dict) and result.get("error"))})
    return _err(rid, -32601, f"Không có phương thức '{method}'")


router = APIRouter(prefix="/api/mcp", tags=["mcp"])


def _auth(db: Session, authorization: str | None):
    from app.modules.user.model import User

    raw = authorization.split(" ", 1)[1] if authorization and authorization.lower().startswith("bearer ") else ""
    key = mcp_keys.authenticate(db, raw) if raw else None
    if key is None:
        return None, None
    user = db.get(User, key.user_id)
    if user is None or not user.is_active:
        return None, None
    return key, user


@router.post("")
async def mcp_endpoint(request: Request, authorization: str | None = Header(None), db: Session = Depends(get_db)):
    key, user = _auth(db, authorization)
    if key is None:
        return Response(status_code=401, content=json.dumps({"error": "Khóa MCP không hợp lệ hoặc đã hết hạn"}),
                        media_type="application/json", headers={"WWW-Authenticate": "Bearer"})
    try:
        body = json.loads((await request.body()) or b"null")
    except ValueError:
        return Response(status_code=200, content=json.dumps(_err(None, -32700, "JSON hỏng")), media_type="application/json")
    mcp_keys.touch(db, key)
    msgs = body if isinstance(body, list) else [body]
    out = [r for r in (handle(db, user, key, m) for m in msgs) if r is not None]
    if not out:
        return Response(status_code=202)
    payload = out if isinstance(body, list) else out[0]
    return Response(status_code=200, content=json.dumps(payload, ensure_ascii=False), media_type="application/json")


@router.get("")
def mcp_get():
    #  Không có luồng SSE: cổng này chỉ trả JSON theo từng yêu cầu.
    return Response(status_code=405, content=json.dumps({"error": "Cổng MCP chỉ nhận POST (JSON-RPC)."}),
                    media_type="application/json")


@router.delete("")
def mcp_delete():
    return Response(status_code=204)
