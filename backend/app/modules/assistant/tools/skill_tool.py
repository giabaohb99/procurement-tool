"""Ba tool đọc KHO SKILL cho trợ lý NỘI BỘ — Trợ lý web + bot core_v2 (ai-CR-220, K7 doc/erp/21 §7.2).

Thay việc nhồi `assistant/packs/*.md` vào lời nhắc: lời nhắc chỉ mang danh mục ngắn (`knowledge.handbook_block`), model đọc
đúng skill cần bằng `read_skill`. Cùng tên với ba tool của cổng MCP (`agent_hub/mcp.py` SKILL_TOOL_DEFS) nhưng chạy với
`internal=True`: vẫn đúng tập `visible_skills` của người hỏi, mức bảo mật của bộ chỉ chặn AI bên ngoài (nội bộ đọc cả bộ
Khóa / tệp của bộ Bảo vệ). Cổng MCP KHÔNG liệt kê bản này — nó giữ bản riêng gác theo mức bảo mật.
"""
from __future__ import annotations

from .base import ToolContext, ToolSpec

NAME_MAX = 160
PATH_MAX = 200
QUERY_MAX = 120
SET_MAX = 150


def _list(ctx: ToolContext, args: dict) -> dict:
    from app.modules.ai_skill import mcp_read

    return mcp_read.list_for_ai(ctx.db, ctx.user, str(args.get("query") or "")[:QUERY_MAX],
                                str(args.get("skill_set") or "")[:SET_MAX], internal=True)


def _read(ctx: ToolContext, args: dict) -> dict:
    from app.modules.ai_skill import mcp_read

    name = str(args.get("name") or "").strip()[:NAME_MAX]
    if not name:
        return {"error": "Thiếu `name` của skill — lấy từ danh mục cẩm nang hoặc list_skills."}
    return mcp_read.read_for_ai(ctx.db, ctx.user, name, internal=True, offset=args.get("offset"))


def _file(ctx: ToolContext, args: dict) -> dict:
    from app.modules.ai_skill import mcp_read

    name = str(args.get("name") or "").strip()[:NAME_MAX]
    path = str(args.get("path") or "").strip()[:PATH_MAX]
    if not name or not path:
        return {"error": "Cần `name` của skill và `path` của tệp — lấy từ danh sách tệp trong read_skill."}
    return mcp_read.file_for_ai(ctx.db, ctx.user, name, path, internal=True, offset=args.get("offset"))


LIST_SKILLS_SPEC = ToolSpec(
    name="list_skills",
    description=("Liệt kê cẩm nang (skill) của công ty mà người hỏi được đọc: tên gọi, tiêu đề, tóm tắt KHI NÀO dùng. "
                 "Danh mục ngắn đã có sẵn trong lời nhắc; gọi khi cần lọc theo chữ hoặc danh mục bị cắt."),
    parameters={"type": "object", "properties": {
        "query": {"type": "string", "maxLength": QUERY_MAX, "description": "Lọc theo chữ trong tên / tiêu đề / tóm tắt."},
        "skill_set": {"type": "string", "maxLength": SET_MAX, "description": "Lọc theo tên bộ skill."}}},
    handler=_list,
)
READ_SKILL_SPEC = ToolSpec(
    name="read_skill",
    description=("Đọc một cẩm nang (skill) của công ty theo đúng `name` trong danh mục: quy trình, quy định, cách dùng ERP. "
                 "Đọc TRƯỚC khi trả lời câu về quy trình / quy định hay trước khi soạn phiếu; dùng nội dung để trả lời "
                 "(tóm tắt, trích ý, áp dụng), chỉ không chép nguyên bài. Dài thì trả theo trang: có next_offset thì gọi "
                 "lại với offset đó."),
    parameters={"type": "object", "properties": {"name": {"type": "string", "maxLength": NAME_MAX},
                                                 "offset": {"type": "integer", "minimum": 0}}, "required": ["name"]},
    handler=_read,
)
READ_SKILL_FILE_SPEC = ToolSpec(
    name="read_skill_file",
    description="Đọc một tệp đính kèm dạng chữ của skill (đường dẫn lấy từ read_skill, vd references/quy-dinh.md).",
    parameters={"type": "object", "properties": {"name": {"type": "string", "maxLength": NAME_MAX},
                                                 "path": {"type": "string", "maxLength": PATH_MAX},
                                                 "offset": {"type": "integer", "minimum": 0}},
                "required": ["name", "path"]},
    handler=_file,
)
SKILL_SPECS = (LIST_SKILLS_SPEC, READ_SKILL_SPEC, READ_SKILL_FILE_SPEC)
