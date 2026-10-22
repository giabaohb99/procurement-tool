"""Lớp tool loại A cho Trợ lý AI: allowlist + bộ chạy có gác quyền + audit.

Điểm vào duy nhất cho tầng service:
- `tool_defs()` -> danh sách khai báo TRUNG LẬP (`ToolDef`) để đưa cho provider.
- `run_tool(db, user, name, args)` -> chạy một tool DƯỚI danh tính người hỏi, ghi audit.

Bot KHÔNG chạm hàm nào ngoài allowlist này (tầng 2 của 7 tầng bảo mật).
"""
import json
import logging

from app.core.config import settings

from ..provider import ToolDef
from .approval_tool import MY_APPROVAL_TASKS_SPEC, MY_REQUESTS_STATUS_SPEC
from .base import ToolContext
from .catalog import SPECS
from .document_tool import (APPROVAL_FLOW_LOOKUP_SPEC, DOCUMENT_READ_SPEC,
                            DOCUMENT_SEARCH_SPEC, MY_DOCUMENTS_SPEC)
from .draft_tool import (DRAFT_LEAVE_REQUEST_SPEC, DRAFT_PURCHASE_REQUEST_SPEC,
                         DRAFT_SURVEY_REQUEST_SPEC)
from .employee_tool import EMPLOYEE_LOOKUP_SPEC
from .export_tool import EXPORT_EXCEL_FILE_SPEC, EXPORT_REPORT_FILE_SPEC
from .google_tool import GOOGLE_SPECS
from .learning_tool import LEARNING_SPECS
from .personal_tool import PERSONAL_SPECS
from .group_tool import GROUP_SPECS
from .meeting_tool import MEETING_SPECS
from .work_tool import DRAFT_WORK_PLAN_SPEC, DRAFT_WORK_TASK_SPEC, MY_WORK_TASKS_SPEC
from .brief_tool import MANAGE_BRIEFS_SPEC
from .leave_tool import MY_LEAVE_SUMMARY_SPEC
from .payable_tool import (DRAFT_PAYMENT_REQUEST_SPEC, PAYABLE_LOOKUP_SPEC,
                           PAYMENT_REQUEST_READ_SPEC)
from .procurement_doc_tool import (MY_PROCUREMENT_REQUESTS_SPEC,
                                   PENDING_PROCUREMENT_APPROVALS_SPEC,
                                   PROCUREMENT_DOC_READ_SPEC)
from .rag_tool import SEARCH_DOCS_SPEC
from .ticket_tool import MY_TICKETS_SPEC, TICKET_CREATE_SPEC
from .update_tool import PROPOSE_DOCUMENT_DELETE_SPEC, PROPOSE_DOCUMENT_UPDATE_SPEC
from .account_setup_tool import PROPOSE_ACCOUNT_SETUP_SPEC
from .customs_tool import (CUSTOMS_BUY_TIMING_SPEC, CUSTOMS_LEGAL_CHECK_SPEC, CUSTOMS_MARKET_SPEC,
                          CUSTOMS_PRICE_STATS_SPEC)
from .market_tool import MARKET_SPECS
from .research_tool import RESEARCH_SPECS
from .report_summary_tool import REPORT_SUMMARY_SPEC
from .dataset_tool import DATASET_QUERY_SPEC
from .erp_read_tool import ERP_READ_SPEC
from .skill_tool import SKILL_SPECS
from .capability_tool import CAPABILITY_SPECS

log = logging.getLogger("app.assistant.tools")


def _active_specs() -> list:
    """Tool đang bật: loại A + soạn nháp YCBG + xuất báo cáo luôn có; `search_docs` (loại B)
    chỉ khi RAG bật.

    Đọc cờ mỗi lần gọi thay vì chốt lúc import: bật/tắt RAG chỉ cần restart tiến trình, và test
    lật `settings.AI_RAG_ENABLED` không bị kẹt giá trị cũ.
    """
    specs = list(SPECS) + [DRAFT_SURVEY_REQUEST_SPEC, DRAFT_PURCHASE_REQUEST_SPEC,
                           DRAFT_LEAVE_REQUEST_SPEC, EXPORT_REPORT_FILE_SPEC,
                           EXPORT_EXCEL_FILE_SPEC,
                           APPROVAL_FLOW_LOOKUP_SPEC, MY_DOCUMENTS_SPEC,
                           DOCUMENT_SEARCH_SPEC, DOCUMENT_READ_SPEC,
                           MY_APPROVAL_TASKS_SPEC, MY_REQUESTS_STATUS_SPEC,
                           PAYABLE_LOOKUP_SPEC, DRAFT_PAYMENT_REQUEST_SPEC,
                           PROCUREMENT_DOC_READ_SPEC,
                           PENDING_PROCUREMENT_APPROVALS_SPEC,
                           MY_PROCUREMENT_REQUESTS_SPEC,
                           PAYMENT_REQUEST_READ_SPEC,
                           TICKET_CREATE_SPEC, MY_TICKETS_SPEC,
                           MY_LEAVE_SUMMARY_SPEC, EMPLOYEE_LOOKUP_SPEC,
                           PROPOSE_DOCUMENT_UPDATE_SPEC,
                           PROPOSE_DOCUMENT_DELETE_SPEC,   # AI-0006: xóa phiếu nháp của chính mình, có xác nhận
                           PROPOSE_ACCOUNT_SETUP_SPEC,
                           CUSTOMS_PRICE_STATS_SPEC, CUSTOMS_BUY_TIMING_SPEC,
                           CUSTOMS_MARKET_SPEC, CUSTOMS_LEGAL_CHECK_SPEC,
                           *GOOGLE_SPECS,   # ai-CR-064: Lịch + Drive Google cá nhân
                           *LEARNING_SPECS,  # ai-CR-078: dò nghĩa từ nội bộ, đề xuất thuật ngữ, báo thiếu chức năng
                           DRAFT_WORK_TASK_SPEC,  # ai-CR-080: soạn nháp việc ở phân hệ Dự án
                           MY_WORK_TASKS_SPEC,    # ai-CR-140: việc Dự án tới hạn / quá hạn của tôi
                           DRAFT_WORK_PLAN_SPEC,  # bao-CR-616: lập kế hoạch việc (giai đoạn · việc cha / con) — phase 24.1
                           MANAGE_BRIEFS_SPEC,    # ai-CR-140: bật / tắt / hẹn bản tin trong chat
                           *PERSONAL_SPECS,       # ai-CR-095: sổ ghi nhớ riêng từng người (C-02)
                           *GROUP_SPECS,          # ai-CR-105: đọc nhóm Telegram bot đang ở
                           *MEETING_SPECS,        # ai-CR-112: viết lại biên bản họp theo mẫu, mẫu riêng
                           *MARKET_SPECS,         # ai-CR-173/174: giá + link trên web, chấm điểm NCC (phase 23.4/23.5)
                           *RESEARCH_SPECS,       # ai-CR-178: nghiên cứu sâu nhiều nguồn, chạy nền về chat riêng (phase 23.1)
                           REPORT_SUMMARY_SPEC,   # ai-CR-208: một cửa 13 báo cáo gom sẵn (K11 doc/erp/21 §T1)
                           DATASET_QUERY_SPEC,    # ai-CR-210: sổ bộ dữ liệu — mua hàng, công nợ, YCTT (K12 doc/erp/21 §T2)
                           ERP_READ_SPEC,         # ai-CR-211: đọc danh sách / chi tiết theo danh sách trắng (K13 §T3)
                           *SKILL_SPECS,          # ai-CR-220: đọc Kho skill (cẩm nang công ty) thay gói tri thức (K7)
                           *CAPABILITY_SPECS]     # kh-AI1-2: năng lực đội + thống kê loại việc (doc/erp/tai-lieu-ai/22 §4)
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


#  ai-CR-207 (đại ca 16/10 qua Agent 1): lớp gác thứ ba — quyền xem TỪNG báo cáo (duoc-CR-562, `report_access`) — trước
#  chỉ gác đường /summary của phân hệ Báo cáo, còn tool Trợ lý / bot / MCP trả cùng số liệu thì không. Tool nào tổng hợp
#  đúng dữ liệu của một báo cáo thì đòi cùng khóa báo cáo đó.
def _tool_report_keys() -> dict:
    from app.core.report_keys import ReportKey

    return {"purchase_report": ReportKey.PURCHASE_REPORT, "analytics_query": ReportKey.PURCHASE_REPORT,
            "top_suppliers_by_purchase": ReportKey.PURCHASE_REPORT,
            #  kh-AI1-2: cùng số với màn Năng lực theo loại việc (handler gác thêm setting.read như màn gốc).
            "task_type_stats": ReportKey.WORK_CAPABILITY}


def _report_denied(db, user, name: str) -> dict | None:
    key = _tool_report_keys().get(name)
    if key is None:
        return None
    from app.core.report_keys import REPORT_META
    from app.modules.report_access.service import can_view_report

    if can_view_report(db, user, key):
        return None
    return {"denied": True, "error": f"Chưa được giao xem báo cáo «{REPORT_META[key][0]}» — nhờ quản trị gán ở Phân quyền "
                                     "tài khoản → tab Báo cáo. Đừng thử công cụ khác để lấy cùng số liệu."}


def run_tool(db, user, name: str, args: dict) -> dict:
    """Chạy một tool theo tên, gác allowlist + ghi audit. Trả dict JSON-hóa được.

    Handler tự lo hai lớp quyền (`ctx.can` + `apply_scope`). Ở đây chỉ chặn tên ngoài
    allowlist và ghi vết ai gọi gì.
    """
    spec = {s.name: s for s in _active_specs()}.get(name)
    if spec is None:
        # Tên tool lạ = model bịa hoặc bị chèn — không chạy gì, báo lại để model tự sửa.
        return {"error": f"Không có công cụ tên '{name}'."}

    if denied := _report_denied(db, user, name):
        _audit(db, user, name, args, denied)
        return denied
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
    #  entity_id=0: tool không gắn với một bản ghi cụ thể.
    #
    #  Ghi trong SAVEPOINT, KHÔNG `db.rollback()` cả phiên khi hỏng (bao-CR-463). Bản cũ
    #  rollback nguyên phiên của người gọi: cột `action` chỉ rộng 20 ký tự nên mọi tên
    #  tool dài (`tool:recent_purchase_orders`) đều bị MySQL từ chối, rồi cú rollback
    #  đó cuốn theo mọi thứ đang chờ trong phiên — với bot Telegram là con trỏ đọc tin,
    #  nên cùng một câu hỏi được trả lời bốn lần. Nay hỏng thì chỉ mất đúng dòng audit,
    #  và phải có một dòng log để không hỏng trong im lặng lần nữa.
    #  ai-CR-226: đi qua `agent_hub.erp.audit` — chế độ nhúng / ERP ghi thẳng (vẫn SAVEPOINT như trên), chế độ tách đẩy
    #  sang ERP qua cổng B (công cụ chạy NGAY trong dịch vụ AI như lịch Google, sổ nhớ… trước mất trắng nhật ký).
    from app.modules.agent_hub import erp

    erp.audit(db, int(getattr(user, "id", 0) or 0), "assistant", 0, f"tool:{name}"[:50], msg)


__all__ = ["tool_defs", "run_tool"]
