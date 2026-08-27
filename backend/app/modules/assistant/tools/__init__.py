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
from .approval_tool import MY_APPROVAL_TASKS_SPEC, MY_REQUESTS_STATUS_SPEC
from .base import ToolContext
from .catalog import SPECS
from .document_tool import (APPROVAL_FLOW_LOOKUP_SPEC, DOCUMENT_READ_SPEC,
                            DOCUMENT_SEARCH_SPEC, MY_DOCUMENTS_SPEC)
from .draft_tool import (DRAFT_LEAVE_REQUEST_SPEC, DRAFT_PURCHASE_REQUEST_SPEC,
                         DRAFT_SURVEY_REQUEST_SPEC)
from .export_tool import EXPORT_REPORT_FILE_SPEC
from .payable_tool import DRAFT_PAYMENT_REQUEST_SPEC, PAYABLE_LOOKUP_SPEC
from .procurement_doc_tool import (MY_PROCUREMENT_REQUESTS_SPEC,
                                   PENDING_PROCUREMENT_APPROVALS_SPEC,
                                   PROCUREMENT_DOC_READ_SPEC)
from .rag_tool import SEARCH_DOCS_SPEC


def _active_specs() -> list:
    """Tool đang bật: loại A + soạn nháp YCBG + xuất báo cáo luôn có; `search_docs` (loại B)
    chỉ khi RAG bật.

    Đọc cờ mỗi lần gọi thay vì chốt lúc import: bật/tắt RAG chỉ cần restart tiến trình, và test
    lật `settings.AI_RAG_ENABLED` không bị kẹt giá trị cũ.
    """
    specs = list(SPECS) + [DRAFT_SURVEY_REQUEST_SPEC, DRAFT_PURCHASE_REQUEST_SPEC,
                           DRAFT_LEAVE_REQUEST_SPEC, EXPORT_REPORT_FILE_SPEC,
                           APPROVAL_FLOW_LOOKUP_SPEC, MY_DOCUMENTS_SPEC,
                           DOCUMENT_SEARCH_SPEC, DOCUMENT_READ_SPEC,
                           MY_APPROVAL_TASKS_SPEC, MY_REQUESTS_STATUS_SPEC,
                           PAYABLE_LOOKUP_SPEC, DRAFT_PAYMENT_REQUEST_SPEC,
                           PROCUREMENT_DOC_READ_SPEC,
                           PENDING_PROCUREMENT_APPROVALS_SPEC,
                           MY_PROCUREMENT_REQUESTS_SPEC]
    if settings.AI_RAG_ENABLED:
        specs.append(SEARCH_DOCS_SPEC)
    return specs


def tool_defs(db=None) -> list[ToolDef]:
    """Khai báo mọi tool đang bật cho provider (function calling).

    Có `db` thì gắn thêm enum danh mục thật (phân loại VTBB/NL, pháp nhân nhận hóa đơn)
    vào 2 tool soạn nháp — model thấy trước danh sách hợp lệ, khỏi bịa tên ngoài danh mục.
    """
    defs = [spec.to_def() for spec in _active_specs()]
    if db is not None:
        from .draft_tool import inject_catalog_enums

        inject_catalog_enums(defs, db)
    return defs


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
