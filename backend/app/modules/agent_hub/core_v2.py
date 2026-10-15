"""Lõi hội thoại mới của bot (ai-CR-198, doc/agent-hub/20 — đại ca chốt 14/10/2026: «đập đi xây lại… ổn định và con
người hơn»).

Một tin chữ vào = MỘT vòng tác tử: model nhìn thấy ngày giờ, người đang nhắn, sổ nhớ, VIỆC ĐANG DỞ (nháp, kế hoạch đang
hỏi, hoàn tác chờ, vé sửa mã) và 30–40 lượt gần nhất; tự quyết hỏi lại, gợi ý, gọi công cụ nhiều vòng, hay ghi. Không
còn regex làm cổng chính, không còn bước đọc ý định, không cắt sau khi soạn nháp.

Chạy song song với đường cũ dưới cờ `AGENT_CORE_V2_ENABLED` (+ `AGENT_CORE_V2_CHATS` để bật theo từng chat thử).
Đường cũ không đụng: `service.py` chỉ rẽ ở hai chỗ gọi `_route_*_text`. Mọi thứ ghi xuống ERP vẫn đi qua các công cụ
và `erp.py` (cổng B) như cũ — lõi mới chỉ thay cách NÓI CHUYỆN và cách QUYẾT ĐỊNH.

Bước B1 (tệp này): vòng tác tử + ngữ cảnh đủ + prompt phong cách + ba công cụ nháp (`update_draft`, `commit_draft`,
`drop_draft`) + đo lượt. B2 dời kế hoạch việc / hoàn tác / sửa mã lên lõi; B3 phase 24 phía sếp (doc 20 §6).
"""
from __future__ import annotations

import json
import re
import logging
import time
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.assistant.provider.base import ToolDef

from . import erp, manager, telegram, user_keys
from .constants import (ACT_ANSWER, ACT_ASKED, ACT_DRAFT_WAIT, ACT_PLAN_ASK_WAIT, ACT_RESEARCH_WAIT, ACT_UNDO_WAIT, DIR_IN,
                        SCOPE_COMPANY, SRC_TELEGRAM, ST_DONE, STAGE_ANSWER)
from .model import AgentMessage, AgentTask, AgentTaskItem
from .timeutil import fmt_local, now_local

log = logging.getLogger("app.agent_hub.core_v2")

HISTORY_WINDOW = timedelta(hours=24)
#  14/10 lượt #206: «hello em» nạp 39.211 token vì 17 lượt lịch sử chứa nguyên các bản tra giá dài (vàng, bitcoin)
#  → trạm không có prompt caching nên mỗi lượt đọc lại hết, chờ ~7 s. Nay mỗi tin cũ cắt ngắn, tổng trần 12k ký tự;
#  câu xã giao chỉ mang 6 lượt.
HISTORY_MAX_CHARS = 12_000
HISTORY_MSG_CHARS = 900
SMALLTALK_TURNS = 6
DRAFT_WINDOW = timedelta(minutes=15)
PLAN_WAIT_WINDOW = timedelta(hours=48)
MAX_ITERS = 6
MAX_TOKENS = 1500
TEMPERATURE = 0.4

#  Mười hai hành vi «con người» của doc 20 §3b, viết thành lời dặn. Ngắn, không câu mẫu, không emoji.
STYLE_RULES = (
    "CÁCH NÓI CHUYỆN (bắt buộc):\n"
    "- Nói tiếng Việt tự nhiên như một trợ lý người thật đã biết việc; câu ngắn; 1–2 ý thì viết thành câu, không gạch "
    "đầu dòng; KHÔNG dùng emoji, KHÔNG lặp câu mẫu, KHÔNG mở đầu bằng «Chào anh/chị» ở mỗi câu.\n"
    "- Thiếu thông tin quan trọng (dự án nào, giao ai, hạn, số tiền, loại phiếu…) thì HỎI LẠI đúng cái thiếu, tối đa 2 "
    "câu hỏi, kèm 2–3 lựa chọn gợi ý lấy từ dữ liệu thật (tra công cụ trước nếu cần). Không đoán bừa, không ra nháp rỗng.\n"
    "- Người dùng sửa bằng lời («đổi hạn thứ năm», «giao Giang thay Được», «bỏ việc 2») thì gọi update_draft, đừng bắt "
    "họ gõ lại từ đầu.\n"
    "- Hiểu đồng ý / không đồng ý theo MỌI cách nói, kể cả sai chính tả, viết tắt, nói vòng («ok», «được đó», «tao task "
    "đó giúp anh», «chốt» = đồng ý; «khoan», «thôi», «để anh xem» = chưa). Đồng ý thì gọi commit_draft; chưa thì giữ nháp.\n"
    "- Trước khi ghi việc lớn (kế hoạch nhiều việc, xóa, gửi duyệt) nhắc lại ngắn cái sắp ghi: «Em hiểu là… đúng không?»\n"
    "- Xong một việc thì gợi ĐÚNG MỘT bước kế hợp lý («em báo anh Được luôn nhé?»); không hỏi han thừa.\n"
    "- Không biết hay công cụ lỗi thì nói thật nguyên nhân một câu và cách khác; không bịa số liệu, không bịa trạng thái.\n"
    "- Không bắt người dùng nhớ cú pháp lệnh; chỉ nhắc lệnh khi họ hỏi cách dùng.\n"
    "- Gọi người đang nhắn theo cách xưng hô ở mục NGƯỜI ĐANG NHẮN (tên, anh/chị), không dùng «anh/chị» chung chung khi "
    "đã biết tên.\n"
    "- Ngày tháng trong mọi nháp phải tính từ HÔM NAY ở mục THỜI ĐIỂM (năm hiện tại), viết dạng YYYY-MM-DD."
)

#  Bản gọn của policy.ASSISTANT_RULES (3,7k ký tự) cho lõi mới: giữ luật an toàn + phạm vi trợ lý cá nhân, bỏ phần dặn
#  dùng từng công cụ (đã nằm trong mô tả công cụ). Bản cũ còn mâu thuẫn với STYLE_RULES («làm luôn, hỏi tối đa MỘT câu»
#  so với «thiếu thì hỏi lại kèm gợi ý») — model nhận hai luật ngược nhau là lý do hay trả lời lúc thế này lúc thế khác.
CORE_RULES = (
    "PHẠM VI VÀ AN TOÀN:\n"
    "- Bạn là trợ lý CÁ NHÂN của người đang nhắn, không chỉ trợ lý ERP: việc làm được bằng chữ (lịch trình, kế hoạch, "
    "gợi ý, soạn thảo, tính toán) thì làm ngay trong câu trả lời; công cụ chỉ để đọc/ghi ERP, Google, tìm trên mạng. "
    "Không bao giờ gợi ý phiếu ERP cho nhu cầu cá nhân.\n"
    "- Đủ rõ thì làm luôn; mơ hồ nhẹ thì chọn cách hợp lý nhất và nói rõ giả định. Câu phụ thuộc nơi đang ở (quán, "
    "đường, thời tiết) mà chưa biết khu thì hỏi khu trước.\n"
    "- Chỉ nói «đã làm» khi công cụ trả thành công; không có công cụ đúng việc thì nói thẳng chưa làm được, không dùng "
    "công cụ khác làm thay. Công cụ báo thiếu quyền thì nói thiếu quyền gì và gợi ý nhắn «quyền của tôi».\n"
    "- Không bao giờ bảo người dùng gõ SQL, lệnh máy chủ hay mã nguồn. Không ghi mật khẩu, khóa, số thẻ vào sổ nhớ.\n"
    "- Sổ nhớ: theo đúng khối sổ ghi nhớ riêng (kể cả xưng hô); nghe điều ỔN ĐỊNH về họ thì remember_fact và thêm một "
    "dòng «Em ghi nhớ: …»; họ bảo quên thì forget_fact; nhắc chuyện cũ thì search_notes / search_chat_history trước."
)

DRAFT_FACTS = (
    "NHÁP CHỨNG TỪ / VIỆC (đại ca 14/10: «cho vào chat thôi, dễ đọc dễ xác nhận»): bot KHÔNG gửi thẻ riêng nữa. Gọi công cụ "
    "draft_* hoặc update_draft xong thì CHÍNH câu trả lời của bạn là bản nháp: mở bằng một câu ngắn, rồi mỗi ô một dòng "
    "lấy ĐÚNG giá trị ở trường «tom_tat_se_luu» công cụ trả về (không tự tính lại ngày, không thêm ô không có), cuối cùng "
    "MỘT câu hỏi: muốn đổi gì không, ưng thì nhắn «tạo» hoặc bảo em tạo luôn. Người dùng hỏi xem lại nháp («nháp đâu», "
    "«cho anh xem bản nháp») thì trình bày lại đúng nháp ở mục ĐANG DỞ; hỏi phiếu nháp đã lưu trên ERP thì gọi my_saved_drafts. Không gọi công cụ thì không có nháp nào — "
    "không viết như thể đã soạn. Cần hỏi thêm thì viết thẳng câu hỏi (kèm 2–3 lựa chọn). Đủ tên việc thì cứ soạn với giá trị "
    "hợp lý cho ô còn thiếu rồi hỏi đổi. Nháp đang chờ nằm ở mục ĐANG DỞ. Đồng ý → commit_draft (submit=true nếu bảo gửi "
    "duyệt luôn); sửa → update_draft đúng ô cần đổi; thôi → drop_draft. Chữ tiếng Việt điền vào nháp phải CÓ DẤU đầy đủ."
)
NEWS_RULES = (
    "TỔNG HỢP TIN / THÔNG TIN: viết như chuyên viên phân tích cho ban giám đốc một công ty phân bón, nông nghiệp, thu mua "
    "(DEGO). Chỉ dùng dữ liệu công cụ trả về. Bố cục: (1) Tóm tắt 2–3 câu nêu xu hướng chính; (2) Số liệu then chốt — con "
    "số, % tăng giảm, mốc thời gian, ai công bố; (3) Diễn biến theo nhóm (giá, cung cầu, chính sách, doanh nghiệp, quốc tế) "
    "— mỗi ý một dòng, có nguồn [n]; (4) Ý nghĩa với DEGO nếu liên quan (giá đầu vào, thời điểm mua, rủi ro); (5) Nguồn: "
    "[n] trang — link. Ít nguồn hoặc nguồn cũ thì nói rõ. Không viết chung chung kiểu «thị trường có nhiều biến động»."
)

#  14/10 16:41–16:43 (lượt #211, #212, Kimi): bot hai lần viết «em đang hỏi lại ở thẻ dưới» mà không gọi công cụ nào → đại
#  ca chờ một thẻ không bao giờ tới. Nói tới thẻ mà lượt này không có nháp → bắt model viết lại một lần.
PHANTOM_CARD = re.compile(r"(?<!\w)(?:(?:the|o the|xem the)\s+(?:ben\s+)?(?:duoi|nhap)|"
                          r"da soan (?:xong )?(?:ban )?nhap|em soan (?:xong|roi) (?:ban )?nhap)(?!\w)")
#  14/10 17:17 (Gemini lite): «em đã bỏ task nghiên cứu đó rồi» — không gọi drop_draft nào. Nói đã làm mà lượt này không
#  có công cụ nào chạy → viết lại một lần.
CLAIMED_DONE = re.compile(r"(?<!\w)(?:em )?da (?:bo|tao|xoa|huy|gui|luu|cap nhat|doi|sua)(?: xong| roi)?(?!\w)")
PHANTOM_FIX = ("(Hệ thống: tin vừa rồi nói như đã làm / đã có thẻ, nhưng lượt này CHƯA có công cụ nào chạy. Viết lại: "
               "muốn làm thì gọi đúng công cụ (drop_draft, commit_draft, update_draft, draft_*…) rồi mới báo; chưa làm "
               "được thì hỏi thẳng hoặc nói rõ chưa làm.)")

LOCAL_TOOLS: tuple[ToolDef, ...] = (
    ToolDef(name="search_web",
            description="Tìm trên mạng và đọc các trang đầu (bài báo, trang tin, trang hãng). Dùng cho câu hỏi cần thông tin "
                        "ngoài ERP: tin tức, giá thị trường, thông tin doanh nghiệp, quy định. Trả về nội dung các trang "
                        "đánh số [n] kèm đường link — tổng hợp lại bằng lời của bạn và ghi nguồn [n].",
            parameters={"type": "object", "properties": {"query": {"type": "string", "description": "Câu tìm, tiếng Việt"}},
                        "required": ["query"]}),
    ToolDef(name="news_today",
            description="Đọc báo: tin MỚI (trong ~48 giờ) theo từng chủ đề, đã bỏ tin trùng, ưu tiên báo tiếng Việt. Dùng khi "
                        "người dùng hỏi «hôm nay có tin gì về…», «đọc báo giúp anh…», «điểm tin…». Trả về tiêu đề, đoạn trích, "
                        "trang, link — tổng hợp thành vài ý chính mỗi chủ đề kèm link.",
            parameters={"type": "object", "properties": {"topics": {"type": "array", "items": {"type": "string"},
                                                                    "description": "1–4 chủ đề, ví dụ [\"giá thép\", \"phân bón\"]"},
                                         "days": {"type": "integer", "description": "Số ngày gần nhất: 2 mặc định, «tuần này» = 7"}},
                        "required": ["topics"]}),
    ToolDef(name="my_saved_drafts",
            description="Các phiếu / đơn NHÁP người dùng đã lưu trên ERP (chưa gửi duyệt): mã, loại, tên. Nháp đang chờ trong "
                        "chat thì đã có ở mục ĐANG DỞ, không cần gọi công cụ này.",
            parameters={"type": "object", "properties": {}, "required": []}),
    ToolDef(name="update_draft",
            description="Sửa bản nháp đang chờ của chat này (nháp mới nhất trong 15 phút) theo lời người dùng, rồi gửi "
                        "lại thẻ. Chỉ truyền các ô cần đổi; ô không nhắc thì giữ nguyên.",
            parameters={"type": "object",
                        "properties": {"changes": {"type": "object", "description": "Các ô của nháp cần đổi, "
                                                                                       "ví dụ {\"due_date\": \"2026-10-16\", \"assignee\": \"Nguyễn Văn A\"}"}},
                        "required": ["changes"]}),
    ToolDef(name="commit_draft",
            description="Người dùng đã đồng ý: tạo thật bản nháp đang chờ (lưu Nháp trên ERP). submit=true khi họ muốn "
                        "gửi duyệt luôn.",
            parameters={"type": "object", "properties": {"submit": {"type": "boolean"}}, "required": []}),
    ToolDef(name="drop_draft",
            description="Người dùng không muốn tạo nữa: bỏ bản nháp đang chờ.",
            parameters={"type": "object", "properties": {}, "required": []}),
    #  ai-CR-201 (B2, doc 20 §10): nối hoàn tác / nhắc việc / sửa mã vào lõi — model gọi bằng lời tự nhiên.
    ToolDef(name="bot_changes",
            description="Các lần bot đã ghi vào ERP cho người dùng (mới nhất trước): id, phiếu, việc, tóm tắt, còn hoàn tác "
                        "được không (24 giờ). Dùng khi hỏi «bot vừa làm gì», «em đã ghi gì», hoặc trước khi hoàn tác.",
            parameters={"type": "object", "properties": {}, "required": []}),
    ToolDef(name="undo_change",
            description="Rút lại (hoàn tác) MỘT lần bot ghi, theo id lấy từ bot_changes. CHỈ gọi sau khi người dùng đã xác "
                        "nhận rút lại đúng dòng đó.",
            parameters={"type": "object", "properties": {"change_id": {"type": "integer"}}, "required": ["change_id"]}),
    ToolDef(name="set_reminder",
            description="Đặt lời nhắc: đúng giờ bot nhắn lại vào chat này. luc = giờ theo lời người dùng («15h», «8h sáng "
                        "mai», «30 phút nữa»); viec = nội dung nhắc.",
            parameters={"type": "object", "properties": {"luc": {"type": "string"}, "viec": {"type": "string"}},
                        "required": ["luc", "viec"]}),
)
#  Chỉ đưa cho chat được giao việc sửa mã (chủ bot + người được cấp quyền).
CODE_TASK_TOOL = ToolDef(
    name="create_code_task",
    description="Ghi một yêu cầu SỬA PHẦN MỀM (vé AI-xxxx gửi máy sửa mã; máy sẽ gửi kế hoạch để duyệt). CHỈ gọi khi người "
                "dùng nói rõ muốn sửa / thêm tính năng phần mềm VÀ đã đồng ý với câu bạn nhắc lại cách hiểu («em hiểu là "
                "sửa màn X để Y, đúng không?»). mo_ta: đầy đủ màn nào, sai gì, muốn gì. Việc nghiệp vụ (task Dự án, phiếu) "
                "KHÔNG phải sửa phần mềm.",
    parameters={"type": "object", "properties": {"mo_ta": {"type": "string"}}, "required": ["mo_ta"]})
LOCAL_TOOL_NAMES = frozenset(t.name for t in LOCAL_TOOLS) | {CODE_TASK_TOOL.name}


# ---------------------------------------------------------------------------
# Cờ bật
# ---------------------------------------------------------------------------
LANE_SMALLTALK, LANE_QUICK, LANE_NORMAL, LANE_HEAVY = "xa_giao", "tra_nhanh", "thuong", "nang"
LANE_LABELS = {LANE_SMALLTALK: "xã giao", LANE_QUICK: "tra nhanh", LANE_NORMAL: "thường", LANE_HEAVY: "việc nặng"}
#  Việc nặng nhận bằng CHỮ của câu (đã bỏ dấu), không bằng công cụ được đưa — nhóm «work» luôn kèm draft_work_plan nên
#  đo 14/10 «tạo task …» bị đẩy nhầm sang Claude.
HEAVY_TEXT = re.compile(r"(?<!\w)(?:lap ke hoach|len ke hoach|ke hoach (?:viec|thu|chi tiet|tuan|thang)|viet bao cao|"
                        r"bao cao (?:tong|chi tiet|ket thuc)|phan tich|so sanh .{0,40} va |nghien cuu sau|viet lai bien ban|"
                        r"soan (?:van ban|hop dong|de xuat|to trinh))(?!\w)")
HEAVY_TEXT_CHARS = 600
#  «đọc báo / điểm tin / tổng hợp tin» cần công cụ news_today của lõi (nhiều chủ đề, bỏ trùng, có link), không đi đường tra
#  nhanh một câu.
NEWS_TEXT = re.compile(r"(?<!\w)(?:doc bao|diem (?:bao|tin)|tong hop (?:tin|thong tin|bao)|tin tuc|co tin gi|ban tin)(?!\w)")


def lane_of(text: str, tool_names: set[str] | None = None) -> str:
    """ai-CR-199: chọn luồng model bằng LUẬT, không gọi model (bước đọc ý định đã bỏ vì tốn 5–10 s)."""
    from app.modules.assistant.glossary import fold

    from . import research

    if _is_smalltalk(text):
        return LANE_SMALLTALK
    folded = " ".join(fold(text or "").split())
    if "\n" not in (text or "") and research.is_quick(text) and not NEWS_TEXT.search(folded):
        return LANE_QUICK
    if len(text or "") >= HEAVY_TEXT_CHARS or HEAVY_TEXT.search(folded) or NEWS_TEXT.search(folded):
        return LANE_HEAVY
    return LANE_NORMAL


def _chat_draft(tool_name) -> bool:
    """Nháp trình bày trong chat được (đề nghị thanh toán vẫn đi link form web như cũ)."""
    from . import draft_create

    kind = draft_create.kind_of(str(tool_name or ""))
    return bool(kind) and kind != "payment"


def _summary(tool_name: str, draft: dict) -> list[str]:
    from . import draft_create

    kind = draft_create.kind_of(str(tool_name or ""))
    try:
        return list(draft_create.summarize(kind, draft)) if kind else []
    except Exception:  # noqa: BLE001
        return []


def _card_talk(text: str) -> bool:
    from app.modules.assistant.glossary import fold

    return bool(PHANTOM_CARD.search(" ".join(fold(text or "").split())))


def _phantom_card(result) -> bool:
    """Câu trả lời nói tới «thẻ dưới / thẻ nháp» mà lượt này không có công cụ nào trả nháp."""
    from app.modules.assistant.glossary import fold

    has_draft = any(isinstance(c, dict) and (isinstance(c.get("draft"), dict) or c.get("name") in LOCAL_TOOL_NAMES)
                    for c in (result.tool_calls or []))
    folded = " ".join(fold(result.text or "").split())
    if not (result.tool_calls or []) and CLAIMED_DONE.search(folded):
        return True
    return not has_draft and bool(PHANTOM_CARD.search(folded))


def route_providers(lane: str) -> list[str]:
    for part in str(settings.AGENT_CORE_V2_ROUTES or "").split(";"):
        name, _, provs = part.partition("=")
        if name.strip() == lane:
            return [p.strip() for p in provs.split(",") if p.strip()]
    return []


def _is_smalltalk(text: str) -> bool:
    from app.modules.assistant import tool_router

    return tool_router.is_smalltalk(text)


def enabled_for(chat_id: str) -> bool:
    if not settings.AGENT_CORE_V2_ENABLED:
        return False
    chats = {c.strip() for c in str(settings.AGENT_CORE_V2_CHATS or "").split(",") if c.strip()}
    return not chats or str(chat_id).strip() in chats


# ---------------------------------------------------------------------------
# Ngữ cảnh
# ---------------------------------------------------------------------------
def _pending_draft(db: Session, chat_id: str, before_id: int, now) -> tuple[AgentMessage | None, dict]:
    row = db.scalar(select(AgentMessage).where(AgentMessage.chat_id == chat_id, AgentMessage.action == ACT_DRAFT_WAIT,
                                               AgentMessage.id < before_id).order_by(AgentMessage.id.desc()).limit(1))
    if row is None or (now and row.created_at and now - row.created_at > DRAFT_WINDOW):
        return None, {}
    try:
        return row, json.loads(row.body or "{}")
    except ValueError:
        return row, {}


def _open_code_tasks(db: Session, chat_id: str) -> list[AgentTask]:
    """Vé sửa mã (AI-000x) do chính chat này gửi, còn mở."""
    q = (select(AgentTask).join(AgentTaskItem, AgentTaskItem.task_id == AgentTask.id)
         .join(AgentMessage, AgentMessage.id == AgentTaskItem.ref_id)
         .where(AgentMessage.chat_id == chat_id, AgentTaskItem.source == SRC_TELEGRAM, AgentTask.status < ST_DONE)
         .order_by(AgentTask.id.desc()).limit(5))
    seen, out = set(), []
    for t in db.scalars(q):
        if t.id not in seen:
            seen.add(t.id)
            out.append(t)
    return out


def pending_block(db: Session, chat_id: str, before_id: int, now) -> str:
    """Khối ĐANG DỞ — thứ model phải nhìn thấy để không trả lời «không có dấu vết» như hôm 14/10."""
    from . import draft_create, service

    lines: list[str] = []
    pending, info = _pending_draft(db, chat_id, before_id, now)
    if pending is not None:
        label = draft_create.LABELS.get(str(info.get("kind") or ""), "phiếu")
        draft = info.get("draft") or {}
        age = int((now - pending.created_at).total_seconds() // 60) if now and pending.created_at else 0
        summary = _summary(str(info.get("tool") or ""), draft)
        lines.append(f"- Nháp {label} đang chờ người dùng quyết (soạn {age} phút trước), sẽ lưu đúng như sau: "
                     + ("; ".join(summary) if summary else json.dumps(draft, ensure_ascii=False, default=str)[:900]))
    waits = db.scalars(select(AgentMessage).where(AgentMessage.chat_id == chat_id,
                                                  AgentMessage.action == ACT_PLAN_ASK_WAIT, AgentMessage.id < before_id)
                       .order_by(AgentMessage.id.desc()).limit(3))
    for w in waits:
        if now and w.created_at and now - w.created_at > PLAN_WAIT_WINDOW:
            continue
        try:
            body = json.loads(w.body or "{}")
        except ValueError:
            body = {}
        lines.append(f"- Việc kế hoạch #{body.get('task_id')} đang chờ người dùng nhắn giờ làm / lý do "
                     f"({body.get('kind') or 'phản hồi'}).")
    undo = db.scalar(select(AgentMessage).where(AgentMessage.chat_id == chat_id, AgentMessage.action == ACT_UNDO_WAIT,
                                                AgentMessage.id < before_id).order_by(AgentMessage.id.desc()).limit(1))
    if undo is not None and now and undo.created_at and now - undo.created_at <= DRAFT_WINDOW:
        lines.append("- Đang chờ người dùng xác nhận một lệnh hoàn tác («đúng» / «thôi»).")
    research = db.scalar(select(AgentMessage).where(AgentMessage.chat_id == chat_id,
                                                    AgentMessage.action == ACT_RESEARCH_WAIT,
                                                    AgentMessage.id < before_id).order_by(AgentMessage.id.desc()).limit(1))
    if research is not None and now and research.created_at and now - research.created_at <= timedelta(hours=2):
        lines.append("- Đang chờ người dùng đồng ý chi phí một lượt nghiên cứu sâu («ok» / «thôi»).")
    for t in _open_code_tasks(db, chat_id):
        try:
            lines.append(f"- Vé sửa phần mềm {t.code}: {service.task_status_line(db, t)[:300]}")
        except Exception:  # noqa: BLE001
            lines.append(f"- Vé sửa phần mềm {t.code}: {t.title[:120]}")
    return "ĐANG DỞ (việc chưa khép của cuộc này):\n" + ("\n".join(lines) if lines else "- (không có)")


def history(db: Session, chat_id: str, before_id: int, now, *, smalltalk: bool = False) -> list[dict]:
    """Tối đa 40 lượt trong 24 giờ, mỗi tin cắt còn HISTORY_MSG_CHARS, tổng trần HISTORY_MAX_CHARS (doc 20 §3.3).
    Chỉ lấy hỏi / trả lời / nghiên cứu."""
    from . import service

    turns_max = SMALLTALK_TURNS if smalltalk else max(4, int(settings.AGENT_CORE_V2_HISTORY_TURNS or 40))
    q = (select(AgentMessage)
         .where(AgentMessage.chat_id == chat_id,
                AgentMessage.action.in_((ACT_ASKED, ACT_ANSWER, service.ACT_RESEARCH)),
                AgentMessage.id < before_id)
         .order_by(AgentMessage.id.desc()).limit(turns_max * 2))
    turns: list[dict] = []
    total = 0
    for r in db.scalars(q):
        if now and r.created_at and now - r.created_at > HISTORY_WINDOW:
            break
        body = r.body or ""
        if r.direction != DIR_IN and _card_talk(body):
            #  Tin cũ của bot kiểu «(đã soạn bản nháp, xem thẻ bên dưới)» (đường cũ ghi thay cho thẻ) hay «em hỏi lại ở thẻ
            #  dưới»: model CHÉP LẠI câu đó thay vì gọi công cụ (đo 14/10 16:50, Kimi). Thay bằng ghi chú trung tính.
            continue                  # bỏ hẳn: thay bằng ghi chú thì Kimi chép nguyên ghi chú (đo 14/10 16:55)
        if len(body) > HISTORY_MSG_CHARS:
            body = body[:HISTORY_MSG_CHARS] + " …(đã rút gọn)"
        total += len(body)
        if total > HISTORY_MAX_CHARS:
            break
        turns.append({"role": "user" if r.direction == DIR_IN else "assistant", "content": body})
    turns.reverse()
    return turns


WEEKDAYS_VI = ("thứ Hai", "thứ Ba", "thứ Tư", "thứ Năm", "thứ Sáu", "thứ Bảy", "Chủ nhật")


def calendar_block(now) -> str:
    """Hôm nay + 14 ngày tới kèm thứ. 14/10 model ghi «hạn thứ Sáu (17/10)» trong khi 17/10/2026 là thứ Bảy — model tự
    tính thứ là sai, phải đưa sẵn lịch."""
    days = [now.date() + timedelta(days=i) for i in range(15)]
    cells = [f"{WEEKDAYS_VI[d.weekday()]} {d:%d/%m/%Y}" + (" (hôm nay)" if i == 0 else " (mai)" if i == 1 else "")
             for i, d in enumerate(days)]
    return "giờ Việt Nam. LỊCH (dùng đúng bảng này khi đổi «thứ sáu», «tuần sau»… ra ngày): " + "; ".join(cells) + "."


def build_system(db: Session, chat_id: str, row: AgentMessage, user, text: str) -> str:
    from . import intent_ledger, personal_memory, service
    from .constants import BOT_LOGIN_FACTS

    now = now_local()
    name, role = "", ""
    try:
        name, role = erp.describe(db, user)
    except Exception:  # noqa: BLE001
        pass
    who = f"NGƯỜI ĐANG NHẮN: {name or 'người dùng ERP'}" + (f" — {role}" if role else "")
    who += ("; đây là chat CHỦ BOT (đại ca)." if telegram.is_allowed_chat(chat_id) else
            "; gọi theo tên hoặc anh/chị, KHÔNG gọi «đại ca».")
    parts = [
        service._persona(chat_id),
        STYLE_RULES,
        f"THỜI ĐIỂM: bây giờ là {fmt_local(now, '%H:%M')} {calendar_block(now)}",
        who,
        CORE_RULES,
        DRAFT_FACTS,
        NEWS_RULES,
        BOT_LOGIN_FACTS,
        pending_block(db, chat_id, row.id, row.created_at),
    ]
    for fn in (lambda: erp.caller_context(db, user), lambda: erp.glossary_block(db, [text]),
               #  Tìm ghi chú theo câu hỏi tốn ~1,8 s (gọi nhúng véc-tơ) — câu xã giao chỉ cần phần lõi sổ nhớ.
               (lambda: personal_memory.load_core(db, user.id)) if _is_smalltalk(text)
               else (lambda: _clip(personal_memory.prompt_block(db, user.id, text), MEMORY_BLOCK_CHARS)),
               lambda: intent_ledger.habit_block(db, user.id)):
        try:
            block = fn()
        except Exception:  # noqa: BLE001
            block = ""
        if block:
            parts.append(str(block))
    return "\n\n".join(p for p in parts if p)


# ---------------------------------------------------------------------------
# Công cụ
# ---------------------------------------------------------------------------
PLAN_ONLY_TOOLS = frozenset({"draft_work_plan"})
#  Ghi chú riêng liên quan câu hỏi: 14/10 khối này 2,6k ký tự (tóm tắt nguyên các buổi chat cũ) — giữ phần đầu.
MEMORY_BLOCK_CHARS = 1200


def _clip(text: str, limit: int) -> str:
    text = str(text or "")
    return text if len(text) <= limit else text[:limit].rsplit("\n", 1)[0] + "\n…(còn nữa, hỏi search_notes nếu cần)"


def select_tools(db: Session, user, text: str, chat_id: str = "") -> list[ToolDef]:
    """Công cụ ERP theo nhóm của câu (tool_router, ai-CR-183/192) + công cụ nháp của lõi."""
    from app.modules.assistant import tool_router

    #  Câu xã giao («hello em», «cảm ơn») không cần 70+ công cụ ERP — hôm 14/10 «hello em» nạp 76 công cụ.
    if tool_router.is_smalltalk(text):
        return list(LOCAL_TOOLS)
    try:
        defs = list(erp.tool_defs(db, user) or [])
    except Exception:  # noqa: BLE001
        log.exception("core_v2: không lấy được bộ công cụ ERP")
        defs = []
    try:
        picked = tool_router.select(text, tool_router.recent_tools(db, getattr(user, "id", 0)))
    except Exception:  # noqa: BLE001
        picked = None
    if picked is not None:
        keep = set(picked) | set(tool_router.CORE)
        defs = [d for d in defs if d.name in keep]
    #  draft_work_plan (3,5k ký tự mô tả — công cụ lớn nhất) chỉ khi câu thật sự nói «kế hoạch»: nhóm «work» luôn kèm nó
    #  nên 14/10 câu «tạo task …» nào cũng gánh thêm.
    from app.modules.assistant.glossary import fold

    if "ke hoach" not in " ".join(fold(text or "").split()):
        defs = [d for d in defs if d.name not in PLAN_ONLY_TOOLS]
    names = {d.name for d in defs}
    out = defs + [t for t in LOCAL_TOOLS if t.name not in names]
    if chat_id:
        from . import service

        try:
            if service._can_order_code(db, chat_id):
                out.append(CODE_TASK_TOOL)
        except Exception:  # noqa: BLE001
            pass
    return out


NEWS_TOPICS_MAX = 4


def _search_web(query: str) -> dict:
    from . import web_search

    sources, context = web_search.gather(query)
    if not sources:
        return {"error": "Máy tìm kiếm không trả kết quả nào lúc này."}
    return {"noi_dung": context[:9000], "nguon": [{"n": i, "title": s_.get("title"), "url": s_.get("url")}
                                                   for i, s_ in enumerate(sources[:8], 1)]}


NEWS_PER_TOPIC = 6
NEWS_FETCH_PER_TOPIC = 3
NEWS_ARTICLE_CHARS = 1800


def _news_today(topics: list, days: int = 2) -> dict:
    """Tin theo chủ đề trong `days` ngày (tuần = 7), bỏ trùng, kèm NỘI DUNG 3 bài đầu mỗi chủ đề — 14/10 bản chỉ có tiêu
    đề + đoạn trích 400 ký tự cho ra bản tổng hợp hời hợt «như nói chuyện với con nít» (đại ca)."""
    from concurrent.futures import ThreadPoolExecutor

    from . import news_digest, web_search

    now = now_local()
    max_hours = max(1, min(int(days or 2), 14)) * 24
    seen_u, seen_t, taken = set(), set(), []
    out = {}
    for t in [str(x).strip() for x in topics or [] if str(x).strip()][:NEWS_TOPICS_MAX]:
        items = []
        for r in news_digest._search(f"{t} tin tức"):
            url, title = str(r.get("url") or ""), " ".join(str(r.get("title") or "").split())
            if not url.startswith("http") or not title:
                continue
            uh, th = news_digest.url_hash(url), news_digest.title_hash(title)
            if uh in seen_u or th in seen_t or any(news_digest.similar_title(title, x) for x in taken):
                continue
            it = {"title": title[:200], "url": url, "snippet": " ".join(str(r.get("snippet") or "").split())[:400],
                  "site": news_digest._host(url)}
            it["age_hours"] = news_digest.age_hours(it, now)
            if it["age_hours"] is not None and it["age_hours"] > max_hours:
                continue
            seen_u.add(uh)
            seen_t.add(th)
            taken.append(title)
            items.append(it)
        items.sort(key=news_digest._rank)
        items = items[:NEWS_PER_TOPIC]
        with ThreadPoolExecutor(max_workers=NEWS_FETCH_PER_TOPIC) as pool:
            bodies = list(pool.map(lambda i: web_search.fetch(i["url"]), items[:NEWS_FETCH_PER_TOPIC]))
        out[t] = [{"tieu_de": i["title"], "trich": i["snippet"], "trang": i["site"], "link": i["url"],
                   "cach_day_gio": None if i.get("age_hours") is None else round(i["age_hours"]),
                   **({"noi_dung": bodies[k][:NEWS_ARTICLE_CHARS]} if k < len(bodies) and bodies[k] else {})}
                  for k, i in enumerate(items)]
    if not any(out.values()):
        return {"error": f"Không tìm được tin nào trong {max_hours // 24} ngày cho các chủ đề này.", "chu_de": list(out)}
    return {"tin": out, "khoang_ngay": max_hours // 24}


def _run_local(db: Session, chat_id: str, row: AgentMessage, user, name: str, args: dict) -> dict:
    """Ba công cụ nháp của lõi: dùng lại nguyên đường «tạo» / «thôi» của service để không lệch luật (quyền, gửi duyệt,
    hỏi nhận việc sau kế hoạch…)."""
    from . import service

    now = row.created_at
    if name == "search_web":
        return _search_web(str(args.get("query") or ""))
    if name == "news_today":
        return _news_today(args.get("topics") or [], int(args.get("days") or 2))
    if name == "my_saved_drafts":
        return {"nhap_da_luu": erp.my_drafts(db, user)[:20]}
    if name == "update_draft":
        pending, info = _pending_draft(db, chat_id, row.id, now)
        if pending is None:
            return {"error": "Không còn bản nháp nào đang chờ (quá 15 phút hoặc chưa soạn). Soạn lại bằng công cụ draft_*."}
        changes = args.get("changes") if isinstance(args.get("changes"), dict) else {}
        if not changes:
            return {"error": "Chưa có ô nào cần đổi."}
        draft = dict(info.get("draft") or {})
        draft.update(changes)
        service._offer_draft(db, chat_id, user, {"name": info.get("tool") or "", "draft": draft}, silent=True)
        return {"ok": True, "draft": draft, "tom_tat_se_luu": _summary(info.get("tool") or "", draft),
                "note": "Đã sửa nháp. Trình bày lại bản nháp trong câu trả lời theo tom_tat_se_luu."}
    if name in ("commit_draft", "drop_draft"):
        pending, info = _pending_draft(db, chat_id, row.id, now)
        if pending is None:
            return {"error": "Không còn bản nháp nào đang chờ."}
        phrase = "thôi" if name == "drop_draft" else ("tạo và gửi duyệt" if args.get("submit") else "tạo")
        ok = bool(service._draft_by_text(db, chat_id, row, phrase))
        row.action = ACT_ASKED                       # _draft_by_text đổi thành lệnh; giữ mạch hội thoại
        db.commit()
        if not ok:
            return {"error": "Không ghi được nháp (có thể đã hết hạn)."}
        done = {"ok": True}
        if name == "commit_draft":
            try:
                created = (json.loads(db.get(AgentMessage, pending.id).body or "{}") or {}).get("created") or {}
            except Exception:  # noqa: BLE001
                created = {}
            done.update({"created": created, "note": "Bot đã tự báo kết quả tạo cho người dùng; bạn chỉ cần một câu ngắn, "
                                                     "không lặp lại mã phiếu."})
        else:
            done["note"] = "Bot đã báo «không tạo»; bạn chỉ cần một câu ngắn."
        return done
    if name == "bot_changes":
        keep = ("id", "when", "entity_label", "doc_code", "action_label", "summary", "can_undo", "undo_reason",
                "undo_status_label")
        return {"thay_doi": [{k: r.get(k) for k in keep} for r in (erp.my_changes(db, user, 10) or [])]}
    if name == "undo_change":
        from fastapi import HTTPException

        try:
            out = erp.undo_change(db, user, int(args.get("change_id") or 0))
        except HTTPException as e:
            return {"error": f"Không hoàn tác được: {e.detail}"}
        url = str(out.get("url") or "")
        return {"ok": True, "da_hoan_tac": out.get("summary"), "phieu": out.get("doc_code"),
                "link": telegram.absolute_url(url) if url else ""}
    if name == "set_reminder":
        return _set_reminder(db, chat_id, str(args.get("luc") or ""), str(args.get("viec") or ""))
    if name == "create_code_task":
        return _create_code_task(db, chat_id, str(args.get("mo_ta") or ""))
    return {"error": f"Công cụ lạ {name}"}


def _set_reminder(db: Session, chat_id: str, luc: str, viec: str) -> dict:
    """ai-CR-201: «nhắc anh 3h chiều gọi NCC» nói vòng mà lối tắt chữ không bắt được → model gọi công cụ này."""
    from . import chat_link, reminders, service
    from .timeutil import to_utc

    what = " ".join(viec.split())[:300]
    if not what:
        return {"error": "Chưa có nội dung cần nhắc."}
    when = service.parse_schedule_time(luc, now_local())
    if when is None:
        return {"error": f"Chưa đọc được giờ «{luc}». Hỏi lại người dùng giờ cụ thể (vd 15h, 8h sáng mai)."}
    if len(reminders.open_for_chat(db, chat_id)) >= reminders.MAX_OPEN:
        return {"error": f"Chat này đã có {reminders.MAX_OPEN} lời nhắc chờ; bảo người dùng bỏ bớt («nhắc gì»)."}
    link = chat_link.get_active_link(db, chat_id)
    reminders.create(db, chat_id, link.user_id if link else 0, what, when)
    db.commit()
    return {"ok": True, "luc": fmt_local(to_utc(when)), "viec": what,
            "note": "Đã đặt. Báo lại một câu ngắn giờ nhắc; xem / bỏ nhắc: nhắn «nhắc gì»."}


def _create_code_task(db: Session, chat_id: str, mo_ta: str) -> dict:
    """ai-CR-201 (doc 20 §3c): ghi yêu cầu sửa phần mềm thành một tin INBOX — vòng gom (triage) tạo vé AI-xxxx và
    máy sửa mã gửi kế hoạch như đường cũ «ghi việc: …» (ai-CR-096). Chỉ chat được giao việc sửa mã."""
    from . import service

    if not service._can_order_code(db, chat_id):
        return {"error": "Tài khoản này chưa được cấp quyền giao việc sửa phần mềm; nói người dùng nhờ đại ca cấp quyền."}
    desc = " ".join(mo_ta.split())[:3000]
    if len(desc) < 15:
        return {"error": "Mô tả quá ngắn — hỏi rõ màn nào, sai gì, muốn gì rồi gọi lại."}
    msg = service.log_message(db, DIR_IN, chat_id, 0, desc, action="", scope=SCOPE_COMPANY)
    db.commit()
    return {"ok": True, "tin": int(msg.id),
            "note": "Đã ghi yêu cầu. Máy sửa mã sẽ gom thành vé AI-xxxx và gửi kế hoạch để duyệt trong ít phút; báo "
                    "người dùng một câu, không bịa mã vé."}


# ---------------------------------------------------------------------------
# Lối tắt chữ (B2)
# ---------------------------------------------------------------------------
def shortcut(db: Session, chat_id: str, row: AgentMessage, text: str) -> bool:
    """ai-CR-201 (doc 20 §4: regex giữ làm LỐI TẮT không bắt buộc). B1 rẽ cả chat sang lõi mới nên mọi câu lệnh /
    thẻ chờ của đường cũ (bản tin, nhắc việc, hoàn tác, nghiên cứu sâu, biên bản họp, kế hoạch việc, vé sửa mã, xác nhận
    đề xuất, đúng / thôi của các thẻ…) không còn ai nhận. Chạy đúng chuỗi của đường cũ, BỎ `_draft_by_text` (nháp do
    model quyết qua commit_draft) và bỏ bước đọc ý định. Trả True nếu đã xử xong, không gọi model."""
    from . import change_undo, meeting_actions, meeting_drive, ops, service as s, work_plan

    if telegram.is_allowed_chat(chat_id):
        if (s._deep_research_by_text(db, chat_id, row, text) or s._doc_followup(db, chat_id, row, text)
                or s._guide_by_text(db, chat_id, row, text) or s._link_by_text(db, chat_id, row, text)):
            return True
        if task_id := s._deploy_time_target(db, chat_id, row):
            s._schedule_deploy(db, chat_id, row, text, task_id)
            return True
        if task_id := s._patch_question_target(db, chat_id, row):
            s._ask_patch(db, chat_id, row, text, task_id)
            return True
        chain = (s._ok_by_text, s._grant_by_text, s._runner_by_text, ops.handle_text, s._memory_by_text, s._brief_by_text,
                 s._work_due_by_text, s._ghi_viec_by_text, s._dev_request_by_text, s._keys_by_text, s._glossary_by_text,
                 s._bell_by_text, s._reminder_by_text, meeting_actions.handle_text, meeting_drive.handle_text,
                 change_undo.handle_text, work_plan.handle_text, s._proposal_by_text, s._my_drafts_by_text,
                 s._choice_by_text, s._confirm_by_text, s._word_by_text, s._cost_by_text, s.route_task_command)
        if any(fn(db, chat_id, row, text) for fn in chain):
            return True
        if not s.is_greeting(text) and (task_id := s._plan_answer_target(db, chat_id, row)):
            s._answer_plan(db, chat_id, row, text, task_id)
            return True
        return False
    chain = (s._deep_research_by_text, s._doc_followup, s._guide_by_text, meeting_actions.handle_text,
             meeting_drive.handle_text, change_undo.handle_text, work_plan.handle_text, s._proposal_by_text,
             s._my_drafts_by_text, s._word_by_text, s._cost_by_text, s._bell_by_text, s._reminder_by_text,
             s._memory_by_text, s._brief_by_text, s._work_due_by_text, s._dev_request_by_text, s._keys_by_text)
    if any(fn(db, chat_id, row, text) for fn in chain):
        return True
    return bool(s._over_daily_cap(db, chat_id, row) or s._link_by_text(db, chat_id, row, text))


# ---------------------------------------------------------------------------
# Vòng tác tử
# ---------------------------------------------------------------------------
def handle(db: Session, chat_id: str, row: AgentMessage, text: str) -> None:
    from app.modules.assistant.provider.base import ChatMessage

    from . import service

    #  ai-CR-201: lối tắt chữ của đường cũ chạy TRƯỚC (không tốn model). Chúng tự đóng dấu tin («lenh», hay để trống cho
    #  vòng gom như «ghi việc: …»), nên phải chạy khi tin còn dấu rỗng.
    if shortcut(db, chat_id, row, text):
        db.commit()
        return
    #  Đường cũ ghi tin chủ bot với action="" (để gom việc). Lõi mới KHÔNG gom việc từ tin thường → đóng dấu «hỏi» ngay,
    #  kẻo _triage_inbox biến mỗi câu chào thành một vé sửa mã.
    row.action = ACT_ASKED
    db.commit()
    user = service._assistant_user(db, chat_id)
    if user is None:
        service.reply(db, chat_id, "Chat này chưa liên kết tài khoản ERP. Nhắn <code>/dangnhap &lt;mã&gt;</code> "
                                   "(mã lấy ở Trang cá nhân → Telegram) rồi hỏi lại giúp em.")
        return
    if not user_keys.active_key():
        service.reply(db, chat_id, user_keys.NO_KEY_HELP)
        return
    if lane_of(text) == LANE_QUICK:
        #  Tra nhanh (giá, tỷ giá, thời tiết…) đi đường tra mạng đã kiểm kỹ (ai-CR-193/194), trên model nhanh.
        from . import research

        with user_keys.prefer(route_providers(LANE_QUICK)):
            service.run_research(db, chat_id, text, research.MODE_WEB)
        return
    run = service.start_run(db, 0, STAGE_ANSWER)
    db.commit()                                  # giữ dòng sổ kể cả khi lượt hỏng phải rollback
    try:
        from app.modules.assistant import tool_router

        t0 = time.monotonic()
        system = build_system(db, chat_id, row, user, text)
        turns = history(db, chat_id, row.id, row.created_at, smalltalk=tool_router.is_smalltalk(text))
        tools = select_tools(db, user, text, chat_id)
        log.info("core_v2: dựng ngữ cảnh %.1f s", time.monotonic() - t0)
        msgs = [ChatMessage(role=t["role"], content=t["content"]) for t in turns] + [ChatMessage(role="user", content=text)]
        log.info("core_v2: system=%d ký tự · công cụ=%d · lịch sử=%d lượt", len(system), len(tools), len(turns))

        def execute(name: str, args: dict) -> dict:
            try:
                if name in LOCAL_TOOL_NAMES:
                    return _run_local(db, chat_id, row, user, name, args or {})
                out = erp.run_tool(db, user, name, args or {})
                if isinstance(out, dict) and isinstance(out.get("draft"), dict):
                    out = {**out, "tom_tat_se_luu": _summary(name, out["draft"])}
                return out
            except Exception as e:  # noqa: BLE001
                log.exception("core_v2: công cụ %s hỏng", name)
                return {"error": f"Công cụ {name} lỗi: {type(e).__name__}: {str(e)[:200]}"}

        lane = lane_of(text, {t.name for t in tools})
        with user_keys.prefer(route_providers(lane)):
            ref = user_keys.active_ref()
            log.info("core_v2: luồng %s → %s", lane, getattr(ref, "model", "") or getattr(ref, "provider", ""))
            result = manager.get_provider().run_tools(
                msgs, tools=tools, execute=execute, system=system, max_tokens=MAX_TOKENS, temperature=TEMPERATURE,
                max_iters=MAX_ITERS, cache_system=True)
            if _phantom_card(result):
                log.warning("core_v2: model nói tới thẻ mà không có nháp — viết lại một lần")
                first = result
                result = manager.get_provider().run_tools(
                    msgs + [ChatMessage(role="assistant", content=result.text or ""),
                            ChatMessage(role="user", content=PHANTOM_FIX)],
                    tools=tools, execute=execute, system=system, max_tokens=MAX_TOKENS, temperature=TEMPERATURE,
                    max_iters=MAX_ITERS, cache_system=True)
                result.input_tokens += first.input_tokens
                result.output_tokens += first.output_tokens
            service.finish_run(db, run, result=result)
        answer = (result.text or "").strip() or "Em đã làm xong phần đó."
        service.reply(db, chat_id, answer, markdown=True, action=ACT_ANSWER)
        calls = [c for c in (result.tool_calls or []) if isinstance(c, dict) and c.get("name") not in LOCAL_TOOL_NAMES]
        drafts = [c for c in calls if isinstance(c.get("draft"), dict) and _chat_draft(c.get("name"))]
        for c in drafts:                     # nháp đã nằm trong câu trả lời — chỉ ghi dòng chờ «tạo», không gửi thẻ
            service._offer_draft(db, chat_id, user, c, silent=True)
        service.deliver_tool_results(db, chat_id, user, [c for c in calls if c not in drafts])
        run.artifact = {"core": "v2", "lane": lane, "tools": [str(c.get("name") or "") for c in (result.tool_calls or [])
                                                              if isinstance(c, dict)][:20], "tools_offered": len(tools)}
        db.commit()
    except Exception as e:  # noqa: BLE001
        db.rollback()
        log.exception("core_v2: lượt hỏng")
        try:
            run = db.get(service.AgentRun, run.id) or run
            service.finish_run(db, run, error=f"{type(e).__name__}: {e}")
            db.commit()
        except Exception:  # noqa: BLE001
            db.rollback()
        service.reply(db, chat_id, f"Em gọi AI bị lỗi (mã lượt #{run.id} · {telegram.esc(type(e).__name__)}). "
                                   "Anh/chị nhắn lại sau một phút giúp em; lặp lại thì báo em xem sổ chạy.")
