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
import time

from fastapi import APIRouter, Depends, Header, Request, Response
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db

from . import draft_create, mcp_keys, mcp_log

log = logging.getLogger("app.agent_hub.mcp")

PROTOCOL_VERSION = "2025-06-18"
SERVER_INFO = {"name": "dego-erp", "version": "1.0"}
INSTRUCTIONS = ("Bộ công cụ ERP nội bộ DEGO Holding. Mọi tool chạy dưới quyền của chủ khóa: dữ liệu trả về đã lọc theo "
                "phạm vi người đó được xem. TRƯỚC khi làm một việc nghiệp vụ (lập phiếu, lập báo cáo, trả lời về quy "
                "trình / quy định công ty), gọi list_skills để xem cẩm nang công ty liên quan rồi read_skill đúng cái "
                "cần và làm theo; áp dụng nội dung vào việc, không đọc lại nguyên văn cả skill. Muốn tạo phiếu: gọi tool "
                "draft_* để có bản nháp, đưa người dùng xem, rồi gọi confirm_draft với đúng bản nháp đó (submit=true để "
                "gửi duyệt luôn). Báo lỗi hệ thống: report_issue.")
#  ai-CR-207 (đại ca 16/10 qua Agent 1: «vá 4 lỗi đó luôn»): khóa CHỈ ĐỌC trước đây lọc theo danh sách ĐEN (draft_* + 3 tên)
#  nên vẫn thấy tạo / sửa / xóa lịch, ghi / quên sổ nhớ, ghi chú, bản tin, viết lại biên bản, nghiên cứu sâu (tốn tiền ví
#  công ty)… Nay ĐẢO LUẬT: khóa chỉ đọc chỉ thấy tool trong danh sách TRẮNG dưới đây; tool mới mặc định là «ghi» cho tới khi
#  được khai vào đây (bài kiểm canh: mọi tool khóa đọc thấy phải thuộc READ_TOOLS).
READ_TOOLS = frozenset({
    "approval_flow_lookup", "contract_count_by_status", "contract_list_by_expiry",
    "customs_buy_timing", "customs_legal_check", "customs_market", "customs_price_stats", "dataset_query",
    "document_read", "document_search", "drive_read", "drive_search", "employee_lookup", "erp_read", "glossary_lookup",
    "latest_meeting_report", "list_my_groups", "list_my_meetings", "list_personal_items", "market_price_search",
    "my_approval_tasks", "my_calendar_events", "my_documents", "my_leave_summary", "my_procurement_requests",
    "my_requests_status", "my_tickets", "my_work_tasks", "payable_lookup", "payment_request_read",
    "pending_procurement_approvals", "procurement_doc_read", "product_best_price", "product_purchase_history",
    "product_search", "read_group_file", "read_group_messages", "recent_purchase_orders",
    "recent_purchases", "report_summary", "search_chat_history", "search_docs", "search_notes", "supplier_contracts",
    "supplier_scorecard", "supplier_search", "suppliers_for_product",
})
#  ai-CR-216 (Agent 1 chuyển 17/10): ba tool báo cáo mua hàng cũ GỠ khỏi cổng MCP (vẫn giữ cho Trợ lý web / bot) — đã có
#  đường chuẩn §5.6 phủ đủ: report_summary (purchase_report) và dataset_query dataset=purchase (analytics_query,
#  top_suppliers_by_purchase). Không liệt kê, gọi thì trả lỗi chỉ sang đường mới — với MỌI mức khóa.
MCP_RETIRED = {
    "purchase_report": "report_summary với report_key=purchase_report (hoặc dataset_query dataset=purchase)",
    "analytics_query": "dataset_query với dataset=purchase",
    "top_suppliers_by_purchase": "dataset_query với dataset=purchase, dimensions=[\"supplier\"], measures=[\"total_amount\", \"count\"]",
}
#  ai-CR-208: report_summary mở đủ 13 báo cáo; purchase_report / analytics_query / top_suppliers_by_purchase còn giữ
#  tạm (Trợ lý web + bot đang dùng), dự kiến gỡ khỏi cổng khi app AI ngoài đã quen report_summary.
#  Đề xuất sửa phiếu / lập bộ tài khoản / thuật ngữ (propose_*) cố ý KHÔNG mở qua MCP: xác nhận bằng nút trên web /
#  Telegram, cổng này chưa có nút. report_missing_feature trùng việc với report_issue của cổng.
HIDDEN = {"propose_document_update", "propose_document_delete", "propose_account_setup", "propose_glossary_term",
          "report_missing_feature"}
#  ai-CR-213: tool đọc nhiều dòng — tính vào ngân sách dữ liệu mỗi phút mỗi khóa (`AGENT_MCP_ROW_BUDGET_PER_MIN`).
ROW_BUDGET_TOOLS = frozenset({"erp_read"})
#  Tool trả kèm `structuredContent` (kết quả gọn, có khuôn cố định) — ai-CR-208.
STRUCTURED_TOOLS = frozenset({"report_summary", "dataset_query", "erp_read"})
#  Thời hạn đường tải tệp xuất qua MCP (dùng MỘT lần, ký HMAC, không cần đăng nhập web).
DOWNLOAD_TTL_SEC = 15 * 60

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
#  bao-CR-622 (K2 doc/erp/21 §5.1): ba tool đọc KHO SKILL — cẩm nang công ty cho AI. Khóa chỉ đọc cũng có. Dữ liệu
#  ở ERP (`ai_skill`), đọc qua `erp.skill_*` (cổng B ở chế độ tách dịch vụ), luôn dưới quyền chủ khóa.
SKILL_TOOL_DEFS = [
    {"name": "list_skills",
     "description": ("Liệt kê cẩm nang (skill) của công ty mà người dùng được đọc: tên gọi, tiêu đề, tóm tắt KHI NÀO dùng. "
                     "Gọi trước khi làm việc nghiệp vụ để biết công ty có hướng dẫn nào liên quan."),
     "inputSchema": {"type": "object", "properties": {
         "query": {"type": "string", "maxLength": 120, "description": "Lọc theo chữ trong tên / tiêu đề / tóm tắt."},
         "skill_set": {"type": "string", "maxLength": 150, "description": "Lọc theo tên bộ skill."}}}},
    {"name": "read_skill",
     "description": ("Đọc nội dung một skill (bản đã xuất bản) theo đúng `name` từ list_skills, kèm danh sách tệp đính kèm. "
                     "Làm theo hướng dẫn trong skill; không đọc lại nguyên văn cho người dùng."),
     "inputSchema": {"type": "object", "properties": {"name": {"type": "string", "maxLength": 160}},
                     "required": ["name"]}},
    {"name": "read_skill_file",
     "description": "Đọc một tệp đính kèm dạng chữ của skill (đường dẫn lấy từ read_skill, vd references/cot-bao-cao.md).",
     "inputSchema": {"type": "object", "properties": {"name": {"type": "string", "maxLength": 160},
                                                      "path": {"type": "string", "maxLength": 200}},
                     "required": ["name", "path"]}},
]
SKILL_TOOLS = frozenset(d["name"] for d in SKILL_TOOL_DEFS)
#  Tool RIÊNG của cổng (không nằm trong sổ tool của Trợ lý) — khóa nào cũng thấy.
GATEWAY_READ_TOOLS = SKILL_TOOLS | {"report_issue"}

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
    """Mọi tool KHÔNG nằm trong danh sách trắng chỉ đọc đều tính là ghi (an toàn khi thêm tool mới)."""
    return name not in READ_TOOLS


def list_tools(db: Session, user, scope: int) -> list[dict]:
    from . import erp

    from . import mcp_settings

    #  ai-CR-216: nhóm tool đang tắt qua MCP (màn G7) thì không liệt kê.
    out = [d for d in SKILL_TOOL_DEFS if mcp_settings.tool_listed(db, d["name"])]   # bao-CR-622: cẩm nang đứng đầu
    #  ai-CR-207 lỗi 1: trước gọi erp.tool_defs(db) KHÔNG kèm người dùng → chế độ tách dịch vụ gọi cổng B GET /tools với
    #  user_id rỗng → «Tài khoản không tồn tại» → danh sách chỉ còn tool cục bộ (mất purchase_report, payable_lookup…).
    for d in erp.tool_defs(db, user):
        if d.name in HIDDEN or d.name in MCP_RETIRED:
            continue
        if scope != mcp_keys.SCOPE_WRITE and is_write_tool(d.name):
            continue
        if not mcp_settings.tool_listed(db, d.name):
            continue
        out.append({"name": d.name, "description": d.description, "inputSchema": d.parameters})
    if scope == mcp_keys.SCOPE_WRITE:
        out += [CONFIRM_DRAFT_DEF, REPORT_ISSUE_DEF]
    else:
        out.append(REPORT_ISSUE_DEF)      # báo lỗi thì ai cũng được (M-05)
    return out


def call_tool(db: Session, user, scope: int, name: str, args: dict) -> dict:
    """Trả dict kết quả (JSON-hóa được). Lỗi nghiệp vụ → {"error": ...}, không ném."""
    from . import erp

    from . import mcp_settings

    if name == "report_issue":
        return _report_issue(db, user, args)
    if name in MCP_RETIRED:
        return {"error": f"Công cụ '{name}' không còn mở qua MCP — dùng {MCP_RETIRED[name]}."}
    if blocked := mcp_settings.tool_blocked(db, name, args):
        return {"denied": True, "error": blocked}
    if name in SKILL_TOOLS:
        return _skill_tool(db, user, name, args or {})
    if name == "confirm_draft":
        if scope != mcp_keys.SCOPE_WRITE:
            return {"denied": True,
                    "error": "Khóa này chỉ đọc; tạo phiếu cần khóa «được ghi» (tạo ở Trang cá nhân → Khóa AI)."}
        return _confirm_draft(db, user, args)
    if name in HIDDEN or (scope != mcp_keys.SCOPE_WRITE and is_write_tool(name)):
        return {"denied": True, "error": f"Công cụ '{name}' không mở cho khóa này."}
    return _mark_paging(_absolute_downloads(erp.run_tool(db, user, name, args or {})))


def _absolute_downloads(result):
    """ai-CR-207 lỗi 4: tệp xuất (export_*) trả đường tải TƯƠNG ĐỐI cần đăng nhập web → ứng dụng AI ngoài không tải được.
    Tool ERP trả kèm `download_once_path` (ký HMAC, một lần, 15 phút) — ở đây nối thành đường tuyệt đối."""
    from . import telegram

    f = result.get("file") if isinstance(result, dict) else None
    if isinstance(f, dict) and f.get("download_once_path"):
        f["download_url"] = telegram.absolute_url(str(f["download_once_path"]))
        f["note"] = "Đường tải dùng được MỘT lần, hết hạn sau 15 phút, không cần đăng nhập."
    #  ai-CR-208 / 211 / 216 (§5.6): MỌI đường dẫn màn ERP trong kết quả (khóa `url`, `link`, `*_url`, ở bất kỳ tầng nào —
    #  đầu phiếu, từng dòng, danh sách lồng) nối thành tuyệt đối, khỏi sửa từng tool.
    _absolutize(result, telegram.absolute_url)
    return result


def _mark_paging(result):
    """ai-CR-216 (§5.6): tool trả `items` + `total` là TỔNG THẬT mà chưa có `has_more` → gắn `has_more` để ứng dụng AI biết
    còn dòng chưa trả (tool đã có cờ riêng thì giữ nguyên)."""
    paged = (isinstance(result, dict) and isinstance(result.get("items"), list) and "has_more" not in result
             and isinstance(result.get("total"), int))
    if paged:
        result["has_more"] = result["total"] > len(result["items"])
    return result


LINK_DEPTH = 6
#  search_docs trả đường của Trung tâm hướng dẫn (`/articles/{id}`, `/faq`) — không phải màn ERP; nối gốc ERP vào là ra
#  đường chết, nên giữ nguyên (chưa có biến cấu hình gốc Help Center cho dịch vụ AI).
HELP_CENTER_ROOTS = frozenset({"articles", "faq"})


def _absolutize(node, absolute, depth: int = 0) -> None:
    if depth > LINK_DEPTH:
        return
    if isinstance(node, dict):
        for k, v in node.items():
            is_link = k in ("url", "link") or k.endswith("_url")
            root = v.lstrip("/").split("/", 1)[0].split("?", 1)[0] if isinstance(v, str) else ""
            if isinstance(v, str) and is_link and v.startswith("/") and not v.startswith("//") \
                    and root not in HELP_CENTER_ROOTS:
                node[k] = absolute(v)
            elif isinstance(v, (dict, list)):
                _absolutize(v, absolute, depth + 1)
    elif isinstance(node, list):
        for v in node:
            _absolutize(v, absolute, depth + 1)


def _skill_tool(db: Session, user, name: str, args: dict) -> dict:
    from . import erp

    if name == "list_skills":
        return erp.skill_list(db, user, str(args.get("query") or "")[:120], str(args.get("skill_set") or "")[:150])
    skill = str(args.get("name") or "").strip()[:160]
    if not skill:
        return {"error": "Thiếu `name` của skill — lấy từ list_skills."}
    if name == "read_skill":
        return erp.skill_read(db, user, skill)
    path = str(args.get("path") or "").strip()[:200]
    if not path:
        return {"error": "Thiếu `path` của tệp — lấy từ danh sách tệp trong read_skill."}
    return erp.skill_file(db, user, skill, path)


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
    from . import erp

    try:
        code, oid = erp.create_draft(db, user, kind, draft)
        if submit and kind in draft_create.SUBMITTABLE:
            erp.submit_draft(db, user, kind, oid)
    except draft_create.DraftError as e:
        return {"error": str(e)}
    return {"ok": True, "code": code, "id": oid, "submitted": bool(submit and kind in draft_create.SUBMITTABLE),
            "details": erp.created_details(db, kind, oid),
            "link": draft_create.DETAIL_PATHS.get(kind, "").format(id=oid) if hasattr(draft_create, "DETAIL_PATHS") else ""}


def _report_issue(db: Session, user, args: dict) -> dict:
    from . import erp

    title = str(args.get("title") or "").strip()[:200]
    detail = str(args.get("detail") or "").strip()[:4000]
    if not title or not detail:
        return {"error": "Cần title và detail."}
    dept = (settings.AGENT_TICKET_DEPARTMENTS or "").split(",")[0].strip()
    body = detail + (f"\n\nMàn hình: {args.get('screen_url')}" if args.get("screen_url") else "") + "\n\n(Gửi qua cổng MCP.)"
    t = erp.create_ticket(db, user, subject=title, department=dept, body=body)
    return {"ok": True, "ticket": t.get("code"), "department": dept,
            "note": "Nhóm kỹ thuật (và bot sửa mã) sẽ nhận phiếu này." if dept else "Phiếu đã tạo, chưa gắn bộ phận."}


# ---------------------------------------------------------------------------
# JSON-RPC
# ---------------------------------------------------------------------------
def _err(rid, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": rid, "error": {"code": code, "message": message}}


def _ok(rid, result) -> dict:
    return {"jsonrpc": "2.0", "id": rid, "result": result}


def handle(db: Session, user, key, msg: dict, trace: dict | None = None) -> dict | None:
    """Một thông điệp JSON-RPC → một trả lời (None với notification).

    `trace` (ai-CR-209): nơi `handle` ghi lại method / tool / kết quả / tên ứng dụng cho nhật ký MCP — bên gọi đọc sau."""
    trace = trace if trace is not None else {}
    if not isinstance(msg, dict) or msg.get("jsonrpc") != "2.0" or not isinstance(msg.get("method"), str):
        trace.update(status=mcp_log.CallStatus.ERROR, reason="Không phải yêu cầu JSON-RPC 2.0 hợp lệ")
        return _err(msg.get("id") if isinstance(msg, dict) else None, -32600, "Không phải yêu cầu JSON-RPC 2.0 hợp lệ")
    method, rid, params = msg["method"], msg.get("id"), msg.get("params") or {}
    trace["method"] = method
    if method.startswith("notifications/"):
        return None
    if method == "initialize":
        trace["client"] = mcp_log.client_from_initialize(params)
        from . import mcp_settings

        extra = mcp_settings.current(db)["extra_instructions"]          # ai-CR-216: câu dặn thêm của quản trị (G7)
        instructions = f"{INSTRUCTIONS}\n\n{extra}" if extra else INSTRUCTIONS
        return _ok(rid, {"protocolVersion": PROTOCOL_VERSION, "capabilities": {"tools": {"listChanged": False}},
                         "serverInfo": SERVER_INFO, "instructions": instructions})
    if method == "ping":
        return _ok(rid, {})
    if method == "tools/list":
        return _ok(rid, {"tools": list_tools(db, user, int(key.scope or 0))})
    if method == "tools/call":
        name = str(params.get("name") or "")
        args = params.get("arguments") if isinstance(params.get("arguments"), dict) else {}
        trace["tool"] = name
        if not name:
            trace.update(status=mcp_log.CallStatus.ERROR, reason="Thiếu tên tool")
            return _err(rid, -32602, "Thiếu tên tool")
        budget = int(mcp_settings_now(db)["row_budget_per_min"])
        if name in ROW_BUDGET_TOOLS and budget > 0 and mcp_log.rows_spent(key.id) >= budget:
            #  ai-CR-213: ngân sách DỮ LIỆU mỗi phút mỗi khóa — chặn trước khi chạy, không tốn một truy vấn nào.
            result = {"denied": True, "error": (f"Đã đủ {budget} dòng dữ liệu trong phút này cho khóa này. Hãy lọc hẹp lại "
                                                "(kỳ ngắn hơn, một phòng / NCC / trạng thái) hoặc dùng report_summary / "
                                                "dataset_query để lấy số tổng hợp; chờ sang phút sau nếu vẫn cần đọc tiếp.")}
            trace["budget"] = True
        else:
            try:
                result = call_tool(db, user, int(key.scope or 0), name, args)
            except Exception as e:  # noqa: BLE001 — lỗi tool không được thành 500 của cổng
                log.exception("agent_hub mcp: tool %s hỏng", name)
                result = {"error": f"Lỗi khi chạy công cụ: {e}"}
            if name in ROW_BUDGET_TOOLS and isinstance(result, dict):
                mcp_log.spend_rows(key.id, len(result.get("items") or []) + (1 if result.get("item") else 0))
        if name in SKILL_TOOLS and isinstance(result, dict) and result.get("skill_id"):
            trace["skill_id"] = int(result.pop("skill_id") or 0)     # bao-CR-622: nhật ký biết skill nào được đọc
        if trace.pop("budget", False):
            trace.update(status=mcp_log.CallStatus.DENIED, reason=mcp_log.REASON_ROW_BUDGET)
        elif isinstance(result, dict) and result.get("denied"):
            trace.update(status=mcp_log.CallStatus.DENIED, reason=str(result.get("error") or result.get("reason") or ""))
        elif isinstance(result, dict) and result.get("error"):
            trace.update(status=mcp_log.CallStatus.ERROR, reason=str(result["error"]))
        text = json.dumps(result, ensure_ascii=False, default=str)
        out = {"content": [{"type": "text", "text": text}], "isError": bool(isinstance(result, dict) and result.get("error"))}
        if name in STRUCTURED_TOOLS and isinstance(result, dict) and not out["isError"]:
            out["structuredContent"] = json.loads(text)     # MCP 2025-06-18: bản có cấu trúc, đi kèm bản chữ
        return _ok(rid, out)
    trace.update(status=mcp_log.CallStatus.ERROR, reason=f"Không có phương thức '{method}'")
    return _err(rid, -32601, f"Không có phương thức '{method}'")


def mcp_settings_now(db: Session) -> dict:
    """ai-CR-216: trần đang hiệu lực (màn G7 đè lên biến môi trường AGENT_MCP_*)."""
    from . import mcp_settings

    return mcp_settings.current(db)


router = APIRouter(prefix="/api/mcp", tags=["mcp"])


def _auth(db: Session, authorization: str | None):
    """(khóa, người dùng, (id khóa, lý do từ chối)). Khóa đúng thì phần lý do là (id, "")."""
    from . import erp

    raw = authorization.split(" ", 1)[1] if authorization and authorization.lower().startswith("bearer ") else ""
    key = mcp_keys.authenticate(db, raw) if raw else None
    if key is None:
        return None, None, (mcp_keys.why_rejected(db, raw) if raw else (0, mcp_log.REASON_BAD_KEY))
    user = erp.user_by_id(db, key.user_id)
    if user is None or not user.is_active:
        return None, None, (int(key.id), mcp_log.REASON_INACTIVE)
    return key, user, (int(key.id), "")


def _parse(raw: bytes) -> tuple[object, list, bool]:
    """(thân đã parse, danh sách thông điệp, JSON hỏng?)."""
    try:
        body = json.loads(raw or b"null")
    except ValueError:
        return None, [], True
    return body, (body if isinstance(body, list) else [body]), False


def _first_method(msgs: list) -> str:
    m = msgs[0] if msgs else None
    return str(m.get("method") or "")[:40] if isinstance(m, dict) else ""


def _too_many(msgs: list, per_min: int, what: str) -> Response:
    """ai-CR-209: vượt trần tần suất → HTTP 429 + lỗi JSON-RPC nói rõ trần, kèm Retry-After tới đầu phút sau."""
    m = msgs[0] if msgs else None
    rid = m.get("id") if isinstance(m, dict) else None
    wait = max(1, mcp_log.WINDOW_SEC - int(time.time()) % mcp_log.WINDOW_SEC)
    body = _err(rid, -32000, f"Quá tần suất: tối đa {per_min} lượt / phút cho mỗi {what}. Thử lại sau {wait} giây.")
    return Response(status_code=429, content=json.dumps(body, ensure_ascii=False), media_type="application/json",
                    headers={"Retry-After": str(wait)})


@router.post("")
async def mcp_endpoint(request: Request, authorization: str | None = Header(None), db: Session = Depends(get_db)):
    ip = mcp_log.client_ip(request)
    body, msgs, broken = _parse(await request.body())
    method = _first_method(msgs)
    #  Lớp 1: theo IP — chặn trước cả khi tra khóa (dội khóa sai cũng tốn một truy vấn mỗi lượt).
    limits = mcp_settings_now(db)
    if mcp_log.over_limit(f"ip:{ip}", int(limits["rate_per_ip"])):
        if mcp_log.may_log(f"ip:{ip}"):
            mcp_log.save(db, [mcp_log.new_row(method=method, status=mcp_log.CallStatus.DENIED,
                                               reason=mcp_log.REASON_RATE_IP, ip=ip)])
        return _too_many(msgs, int(limits["rate_per_ip"]), "địa chỉ IP")
    key, user, (key_id, reason) = _auth(db, authorization)
    if key is None:
        flood = mcp_log.over_limit(f"bad:{ip}", int(limits["bad_key_per_ip"]))
        if mcp_log.may_log(f"bad:{ip}"):
            mcp_log.save(db, [mcp_log.new_row(key_id=key_id, method=method, status=mcp_log.CallStatus.DENIED,
                                               reason=mcp_log.REASON_RATE_BAD if flood else reason, ip=ip)])
        if flood:
            return _too_many(msgs, int(limits["bad_key_per_ip"]), "địa chỉ IP gửi khóa sai")
        return Response(status_code=401, content=json.dumps({"error": "Khóa MCP không hợp lệ hoặc đã hết hạn"}),
                        media_type="application/json", headers={"WWW-Authenticate": "Bearer"})
    person = mcp_log.who(db, user)
    #  Lớp 2: theo khóa.
    if mcp_log.over_limit(f"key:{key.id}", int(limits["rate_per_key"])):
        if mcp_log.may_log(f"key:{key.id}"):
            mcp_log.save(db, [mcp_log.new_row(key_id=key.id, person=person, client_name=mcp_log.client_of(db, key.id),
                                               method=method, status=mcp_log.CallStatus.DENIED,
                                               reason=mcp_log.REASON_RATE_KEY, ip=ip)])
        return _too_many(msgs, int(limits["rate_per_key"]), "khóa")
    mcp_keys.touch(db, key)
    if broken:
        mcp_log.save(db, [mcp_log.new_row(key_id=key.id, person=person, client_name=mcp_log.client_of(db, key.id),
                                           status=mcp_log.CallStatus.ERROR, reason="JSON hỏng", ip=ip)])
        return Response(status_code=200, content=json.dumps(_err(None, -32700, "JSON hỏng")), media_type="application/json")
    out, traces = [], []
    for m in msgs:
        trace: dict = {}
        t0 = time.monotonic()
        r = handle(db, user, key, m, trace)
        trace["ms"] = int((time.monotonic() - t0) * 1000)
        traces.append(trace)
        if r is not None:
            out.append(r)
    client = next((t["client"] for t in traces if t.get("client")), "")
    if client:
        mcp_log.remember_client(key.id, client)
    client = client or mcp_log.client_of(db, key.id)
    mcp_log.save(db, [mcp_log.new_row(key_id=key.id, person=person, client_name=client, method=t.get("method", ""),
                                       tool=t.get("tool", ""), status=t.get("status", mcp_log.CallStatus.OK),
                                       reason=t.get("reason", ""), duration_ms=t["ms"], ip=ip,
                                       skill_id=t.get("skill_id", 0)) for t in traces])
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
