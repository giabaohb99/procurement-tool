"""Lớp tool loại A cho Trợ lý AI: allowlist + bộ chạy có gác quyền + audit.

Điểm vào duy nhất cho tầng service:
- `tool_defs()` -> danh sách khai báo TRUNG LẬP (`ToolDef`) để đưa cho provider.
- `run_tool(db, user, name, args)` -> chạy một tool DƯỚI danh tính người hỏi, ghi audit.

Bot KHÔNG chạm hàm nào ngoài allowlist này (tầng 2 của 7 tầng bảo mật).
"""
import json

from app.core.audit import record
from app.core.config import settings

from ..provider import ToolDef
from .base import ToolContext
from .catalog import SPECS
from .draft_tool import DRAFT_SURVEY_REQUEST_SPEC
from .export_tool import EXPORT_REPORT_FILE_SPEC
from .rag_tool import SEARCH_DOCS_SPEC


def _active_specs() -> list:
    """Tool đang bật: loại A + soạn nháp YCBG + xuất báo cáo luôn có; `search_docs` (loại B)
    chỉ khi RAG bật.

    Đọc cờ mỗi lần gọi thay vì chốt lúc import: bật/tắt RAG chỉ cần restart tiến trình, và test
    lật `settings.AI_RAG_ENABLED` không bị kẹt giá trị cũ.
    """
    specs = list(SPECS) + [DRAFT_SURVEY_REQUEST_SPEC, EXPORT_REPORT_FILE_SPEC]
    if settings.AI_RAG_ENABLED:
        specs.append(SEARCH_DOCS_SPEC)
    return specs


def tool_defs() -> list[ToolDef]:
    """Khai báo mọi tool đang bật cho provider (function calling)."""
    return [spec.to_def() for spec in _active_specs()]


def run_tool(db, user, name: str, args: dict) -> dict:
    """Chạy một tool theo tên, gác allowlist + ghi audit. Trả dict JSON-hóa được.

    Handler tự lo hai lớp quyền (`ctx.can` + `apply_scope`). Ở đây chỉ chặn tên ngoài
    allowlist và ghi vết ai gọi gì.
    """
    spec = {s.name: s for s in _active_specs()}.get(name)
    if spec is None:
        # Tên tool lạ = model bịa hoặc bị chèn — không chạy gì, báo lại để model tự sửa.
        return {"error": f"Không có công cụ tên '{name}'."}

    ctx = ToolContext(db=db, user=user)
    try:
        result = spec.handler(ctx, args or {})
    except Exception as e:  # noqa: BLE001 - lỗi tool không được làm sập cả lượt chat
        result = {"error": f"Lỗi khi chạy công cụ: {e}"}

    _audit(db, user, name, args, result)
    return result


def _audit(db, user, name: str, args: dict, result: dict) -> None:
    rows = None
    for k in ("total", "count"):
        if isinstance(result.get(k), int):
            rows = result[k]
            break
    msg = json.dumps({"args": args, "rows": rows, "denied": result.get("denied", False)},
                     ensure_ascii=False)[:480]
    # entity_id=0: tool không gắn với một bản ghi cụ thể. Bọc try để audit hỏng không làm sập chat.
    try:
        record(db, user.id, "assistant", 0, f"tool:{name}", msg)
    except Exception:  # noqa: BLE001
        db.rollback()


__all__ = ["tool_defs", "run_tool"]
