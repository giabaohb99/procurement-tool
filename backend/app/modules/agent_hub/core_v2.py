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
                        DIR_OUT, SCOPE_COMPANY, SRC_TELEGRAM, ST_DONE, STAGE_ANSWER)
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
    "- Số liệu ERP đổi theo ngày (ngày phép còn, công nợ, trạng thái đơn / phiếu, tồn kho, việc) LUÔN tra công cụ ở lượt "
    "này; không lấy từ sổ nhớ, ghi chú hay lịch sử chat. Chưa có công cụ thì gọi more_tools.\n"
    "- Cần nhiều công cụ không phụ thuộc nhau thì gọi CÙNG LÚC trong một lượt (mỗi vòng gọi tốn vài giây). Một công cụ đã "
    "trả đủ thì đừng gọi thêm công cụ trùng nội dung (my_requests_status đã gồm đơn nghỉ phép).\n"
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
            description="Người dùng đã đồng ý (tin ngắn kiểu «ok», «tạo đi», «chốt»): tạo thật bản nháp đang chờ (lưu Nháp "
                        "trên ERP). Câu yêu cầu đầy đủ gửi lại KHÔNG phải đồng ý. submit=true khi họ muốn gửi duyệt luôn.",
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
#  ai-CR-202 (Agent 1 đo run #232): «thôi bỏ nháp đó đi em» không khớp nhóm nào → tool_router trả None → nạp ĐỦ 73 công cụ
#  (66k ký tự, 230k token). Nay không khớp nhóm thì chỉ nạp CORE + công cụ lõi; model cần thêm thì gọi more_tools, lõi nạp
#  nhóm đó rồi chạy lại MỘT lần.
MORE_TOOLS = "more_tools"


def _more_tools_tool() -> ToolDef:
    from app.modules.assistant import tool_router

    groups = [name for name, _tools, _rx in tool_router.GROUPS]
    return ToolDef(
        name=MORE_TOOLS,
        description="Bộ công cụ lượt này đã lọc theo câu. Cần tra / tạo thứ chưa có công cụ thì gọi với nhóm cần — hệ thống "
                    "nạp thêm rồi chạy lại. Nhóm: purchase (tra mua hàng, NCC, giá), make_purchase (lập YCMH / YCBG), "
                    "payable (công nợ, thanh toán), approval (duyệt), leave (nghỉ phép), work (việc Dự án), ticket (hỗ "
                    "trợ IT), edit (sửa / xóa phiếu), account (tài khoản, quyền), employee (nhân sự), customs (hải quan), "
                    "document (văn bản), google (lịch, Drive), meeting (biên bản), group (nhóm chat), personal (việc "
                    "riêng, ghi chú), brief (bản tin), research (nghiên cứu sâu), export (xuất tệp), analytics (thống kê).",
        parameters={"type": "object", "properties": {"nhom": {"type": "array", "items": {"type": "string", "enum": groups}}},
                    "required": ["nhom"]})


LOCAL_TOOL_NAMES = frozenset(t.name for t in LOCAL_TOOLS) | {CODE_TASK_TOOL.name, MORE_TOOLS}


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


#  Agent 1 đo 15/10 (run #227): gửi lại NGUYÊN câu «tạo cho anh task nghiên cứu luồng agent, dự án ERP v2, giao Được, hạn
#  thứ sáu» khi nháp đang chờ → model hiểu là «đồng ý», gọi commit_draft, TẠO THẬT việc #788 + báo chuông người được giao.
#  Ghi thật chỉ khi tin là lời đồng ý NGẮN («ok», «tạo đi», «chốt», «tạo task đó giúp anh đi»…) và không phải câu yêu cầu
#  đã sinh ra nháp gửi lại.
COMMIT_MAX_WORDS = 10
COMMIT_CUE = re.compile(r"(?<!\w)(?:ok|oke|okay|okie|chot|dong y|duoc|uh|um|u|yes|tao|lam|gui|luu|ghi|di|luon|nhe|xac nhan|"
                        r"chuan|dung roi|vay di|the di)(?!\w)")
NOT_A_CONFIRM = ("Tin này KHÔNG phải lời đồng ý (là câu yêu cầu đầy đủ, hoặc gửi lại đúng câu đã sinh ra nháp) — CHƯA ghi gì. "
                 "Đừng ghi. Nếu tin khớp nháp đang chờ thì hỏi một câu: tạo luôn nháp đang chờ hay soạn lại; nếu tin khác "
                 "nháp thì soạn lại (update_draft hoặc draft_* mới).")


def _folded(text: str) -> str:
    from app.modules.assistant.glossary import fold

    return " ".join(fold(text or "").split())


def _is_repeat(db: Session, chat_id: str, pending: AgentMessage, text: str) -> bool:
    """Tin này trùng câu người dùng gửi ngay trước khi nháp được soạn (gửi lại y nguyên)."""
    asked = db.scalar(select(AgentMessage.body).where(AgentMessage.chat_id == chat_id, AgentMessage.direction == DIR_IN,
                                                      AgentMessage.id < pending.id)
                      .order_by(AgentMessage.id.desc()).limit(1))
    return bool(asked) and _folded(asked) == _folded(text)


def _is_commit_reply(db: Session, chat_id: str, pending: AgentMessage, text: str) -> bool:
    folded = _folded(text)
    if not folded or len(folded.split()) > COMMIT_MAX_WORDS or not COMMIT_CUE.search(folded):
        return False
    return not _is_repeat(db, chat_id, pending, text)


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


DRAFT_HEADS = ("Em soạn nháp ", "Em sửa nháp ")


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
        if r.direction != DIR_IN and (body.startswith(DRAFT_HEADS) or "đang chờ, em chưa tạo:" in body.split("\n", 1)[0]):
            #  ai-CR-202: tin nháp cũ chỉ giữ dòng đầu — nội dung nháp còn chờ đã có ở khối ĐANG DỞ; giữ nguyên thì mỗi
            #  lượt trạm phải ghi lại cache cho cả đoạn dài (Agent 1 đo YCMH: ~15k token ghi mỗi lượt).
            body = body.split("\n", 1)[0] + " (chi tiết nháp đã lược)"
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
    return ("giờ Việt Nam. LỊCH (dùng đúng bảng này khi đổi «thứ sáu», «tuần sau»… ra ngày): " + "; ".join(cells) + ". "
            "«thứ X» không kèm «tuần sau / tuần tới» = ngày thứ X GẦN NHẤT tính từ mai; có «tuần sau» mới sang tuần kế. "
            "Tin có khối NGÀY ĐÃ TÍNH thì dùng đúng ngày trong đó.")


WEEKDAY_NUM = {"hai": 0, "2": 0, "ba": 1, "3": 1, "tu": 2, "4": 2, "nam": 3, "5": 3, "sau": 4, "6": 4, "bay": 5, "7": 5}
WEEKDAY_RX = re.compile(r"(?<!\w)(?:thu (hai|ba|tu|nam|sau|bay|[2-7])|(chu nhat))(?!\w)(?: (tuan (?:sau|toi|nay)))?")


def resolve_weekdays(text: str, today) -> list[tuple[str, object]]:
    """«thứ sáu» → ngày cụ thể (Agent 1 15/10: hôm thứ Năm 15/10 model ghi «hạn thứ sáu» = 23/10). Luật: không kèm tuần
    = thứ đó GẦN NHẤT tính từ mai; «tuần sau / tuần tới» = thứ đó của tuần lịch kế tiếp; «tuần này» = thứ đó tuần này."""
    out: list[tuple[str, object]] = []
    for m in WEEKDAY_RX.finditer(_folded(text)):
        wd = 6 if m.group(2) else WEEKDAY_NUM[m.group(1)]
        week = m.group(3) or ""
        monday = today - timedelta(days=today.weekday())
        if week in ("tuan sau", "tuan toi"):
            day = monday + timedelta(days=7 + wd)
        elif week == "tuan nay":
            day = monday + timedelta(days=wd)
        else:
            day = today + timedelta(days=(wd - today.weekday() - 1) % 7 + 1)
        label = (f"thứ {m.group(1)}" if m.group(1) else "chủ nhật") + (f" {week}" if week else "")
        if (label, day) not in out:
            out.append((label, day))
    return out[:4]


CONTEXT_HEAD = "[BỐI CẢNH LƯỢT NÀY — hệ thống chèn, không phải lời người dùng]"
CONTEXT_TAIL = "[HẾT BỐI CẢNH — dưới đây là tin người dùng]"
CONTEXT_RULE = (f"Tin người dùng mới nhất mở đầu bằng khối {CONTEXT_HEAD} (giờ hiện tại, việc ĐANG DỞ, ghi nhớ, thuật "
                "ngữ liên quan) do hệ thống chèn: dùng như sự thật, đừng nhắc lại hay trích nó trong câu trả lời.")


def build_system(db: Session, chat_id: str, row: AgentMessage, user, text: str) -> str:
    """Phần TĨNH của lời nhắc — giống hệt nhau giữa các lượt cùng ngày của một người để trạm đọc lại từ cache (ai-CR-202:
    trạm đi qua Anthropic Messages, cache theo tiền tố công cụ → system → lịch sử; đổi một chữ ở system là ghi lại cả
    ~20k token công cụ + system giá 1,25×, đọc cache chỉ 0,1×). Phần đổi mỗi lượt nằm ở `turn_context`."""
    from . import service
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
        f"NGÀY: {calendar_block(now)}",
        who,
        CORE_RULES,
        DRAFT_FACTS,
        NEWS_RULES,
        BOT_LOGIN_FACTS,
        CONTEXT_RULE,
    ]
    try:
        profile = erp.caller_context(db, user)          # chân dung người hỏi — không đổi giữa các lượt
    except Exception:  # noqa: BLE001
        profile = ""
    if profile:
        parts.append(str(profile))
    return "\n\n".join(p for p in parts if p)


def turn_context(db: Session, chat_id: str, row: AgentMessage, user, text: str) -> str:
    """Phần ĐỔI mỗi lượt (giờ, ĐANG DỞ, thuật ngữ + ghi nhớ theo câu, thói quen) — chèn vào ĐẦU tin người dùng mới nhất,
    sau toàn bộ phần tĩnh, để tiền tố công cụ → system → lịch sử vẫn trúng cache."""
    from . import intent_ledger, personal_memory

    now = now_local()
    parts = [f"THỜI ĐIỂM: bây giờ là {fmt_local(now, '%H:%M')} ngày {now:%d/%m/%Y}.",
             pending_block(db, chat_id, row.id, row.created_at)]
    days = resolve_weekdays(text, now.date())
    if days:
        parts.append("NGÀY ĐÃ TÍNH (theo chữ trong tin, dùng đúng): " + "; ".join(
            f"{label} = {WEEKDAYS_VI[d.weekday()]} {d:%d/%m/%Y}" for label, d in days) + ".")
    for fn in (lambda: erp.glossary_block(db, [text]),
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
    body = "\n\n".join(p for p in parts if p)
    return f"{CONTEXT_HEAD}\n{body}\n{CONTEXT_TAIL}\n\n"


# ---------------------------------------------------------------------------
# Công cụ
# ---------------------------------------------------------------------------
PLAN_ONLY_TOOLS = frozenset({"draft_work_plan"})
#  ai-CR-202 (Agent 1 đo 15/10, run #223): «tạo YCMH mua 10 thùng giấy A4 cho phòng IT» nạp 37 công cụ (26k ký tự) →
#  83k token cho MỘT lần gọi, gấp đôi câu «tạo task» (17 công cụ, 44k) — trạm tính nặng theo SỐ công cụ. Câu LẬP phiếu mua
#  thì chỉ giữ công cụ nháp + vài công cụ tra cứu cần khi soạn; nhóm tra cứu thu mua (16 công cụ) chỉ nạp khi câu còn hỏi
#  thêm giá / NCC / lịch sử…; «phòng IT» không kéo theo nhóm phiếu hỗ trợ.
DRAFT_PURCHASE_KEEP = frozenset({"product_search", "my_procurement_requests"})
PURCHASE_LOOKUP = re.compile(r"\bgia\b|\bncc\b|nha cung cap|lich su|so sanh|cham diem|bao nhieu|tot nhat|re nhat|hop dong"
                             r"|da mua|lan truoc|thong ke|\btop\b")
TICKET_WORDS = re.compile(r"ho tro|ticket|bao loi|su co|may in|\bhong\b|\bloi\b")


def _focus_draft_tools(text: str, defs: list[ToolDef]) -> list[ToolDef]:
    """Câu lập YCMH / YCBG mà không hỏi thêm gì: bỏ nhóm tra cứu thu mua (trừ DRAFT_PURCHASE_KEEP) và nhóm hỗ trợ IT."""
    from app.modules.assistant import tool_router
    from app.modules.assistant.glossary import fold

    groups = set(tool_router.groups_for(text))
    if "make_purchase" not in groups:
        return defs
    folded = " " + " ".join(fold(text or "").split()) + " "
    drop: set[str] = set()
    by_group = {name: tools for name, tools, _rx in tool_router.GROUPS}
    if not PURCHASE_LOOKUP.search(folded):
        drop |= set(by_group.get("purchase", ())) - DRAFT_PURCHASE_KEEP - set(by_group.get("make_purchase", ()))
    if "ticket" in groups and not TICKET_WORDS.search(folded):
        drop |= set(by_group.get("ticket", ()))
    return [d for d in defs if d.name not in drop]
#  Ghi chú riêng liên quan câu hỏi: 14/10 khối này 2,6k ký tự (tóm tắt nguyên các buổi chat cũ) — giữ phần đầu.
MEMORY_BLOCK_CHARS = 1200


def _clip(text: str, limit: int) -> str:
    text = str(text or "")
    return text if len(text) <= limit else text[:limit].rsplit("\n", 1)[0] + "\n…(còn nữa, hỏi search_notes nếu cần)"


#  Agent 1 đo 15/10 (run #237–239): câu không khớp nhóm đi qua more_tools tốn 2–3 lần gọi, 82–132k token, 15–24 s. Cách
#  nói thường gặp thì gắn nhóm ngay ở lõi (không sửa tool_router dùng chung với Trợ lý web).
CORE_GROUP_HINTS: tuple[tuple[re.Pattern, tuple[str, ...]], ...] = (
    (re.compile(r"ke hoach"), ("work",)),     # «lập kế hoạch …» cần draft_work_plan
    (re.compile(r"(?<!\w)off(?!\w)|nghi them|may (hom|bua|ngay) (nghi|off)|nghi duoc|con may (hom|bua)"), ("leave",)),
    (re.compile(r"(?<!\w)(don|phieu|de xuat|yeu cau)(?!\w).{0,40}(toi dau|sao roi|the nao|duyet chua|xong chua|"
                r"den dau)|(?<!\w)(don|phieu) cua (anh|em|toi|chi|minh)(?!\w)"), ("approval",)),   # my_requests_status gồm cả đơn nghỉ
    (re.compile(r"ho so (cua|nhan su|nhan vien)|ai dang (giu|phu trach|lo)"), ("employee",)),
)


def select_tools(db: Session, user, text: str, chat_id: str = "", extra_groups: list[str] | None = None) -> list[ToolDef]:
    """Công cụ ERP theo nhóm của câu (tool_router, ai-CR-183/192) + công cụ nháp của lõi. `extra_groups`: nhóm model xin
    thêm qua more_tools (lượt chạy lại) — khi đó không đưa more_tools nữa."""
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
    keep = set(picked or ()) | set(tool_router.CORE)        # không khớp nhóm nào: chỉ CORE (trước: nạp đủ 73)
    groups = list(extra_groups or ())
    folded = " " + _folded(text) + " "
    for rx, names in CORE_GROUP_HINTS:        # cách nói thường gặp mà tool_router chưa bắt — đi thẳng, khỏi more_tools
        if rx.search(folded):
            groups += [n for n in names if n not in groups]
    asked = set()
    for name, tools, _rx in tool_router.GROUPS:
        if name in groups:
            asked |= set(tools)
    all_defs = defs
    defs = [d for d in defs if d.name in keep]
    #  draft_work_plan (3,5k ký tự mô tả — công cụ lớn nhất) chỉ khi câu thật sự nói «kế hoạch»: nhóm «work» luôn kèm nó
    #  nên 14/10 câu «tạo task …» nào cũng gánh thêm.
    from app.modules.assistant.glossary import fold

    if "ke hoach" not in " ".join(fold(text or "").split()):
        defs = [d for d in defs if d.name not in PLAN_ONLY_TOOLS]
    defs = _focus_draft_tools(text, defs)
    if asked:
        have = {d.name for d in defs}
        defs += [d for d in all_defs if d.name in asked and d.name not in have]
    defs = compact_defs(defs)                    # ai-CR-202: mô tả viết cho chat + tham số còn câu đầu
    names = {d.name for d in defs}
    out = defs + [t for t in LOCAL_TOOLS if t.name not in names]
    if extra_groups is None:
        out.append(_more_tools_tool())
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
        return {"ok": True, "tool": info.get("tool") or "", "draft": draft,
                "tom_tat_se_luu": _summary(info.get("tool") or "", draft),
                "note": "Đã sửa nháp. Trình bày lại bản nháp trong câu trả lời theo tom_tat_se_luu."}
    if name == MORE_TOOLS:
        return {"ok": True, "nhom": [str(g) for g in (args.get("nhom") or []) if str(g).strip()][:4]}
    if name in ("commit_draft", "drop_draft"):
        pending, info = _pending_draft(db, chat_id, row.id, now)
        if pending is None:
            return {"error": "Không còn bản nháp nào đang chờ."}
        if name == "commit_draft" and not _is_commit_reply(db, chat_id, pending, row.body or ""):
            out = {"error": NOT_A_CONFIRM}
            if _is_repeat(db, chat_id, pending, row.body or ""):
                #  Gửi lại y câu cũ: bot tự hỏi «tạo luôn hay soạn lại» (dừng vòng, không gọi model lần hai — run #231 21 s).
                tool = info.get("tool") or ""
                out.update(ask_confirm=True, tool=tool, tom_tat_se_luu=_summary(tool, info.get("draft") or {}))
            return out
        phrase ="thôi" if name == "drop_draft" else ("tạo và gửi duyệt" if args.get("submit") else "tạo")
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
# Gọn token (ai-CR-202, doc 20 §10 việc 2)
# ---------------------------------------------------------------------------
#  Mô tả công cụ ERP viết cho Trợ lý WEB («giao diện hiện nút mở form… báo người dùng bấm nút») — sai với chat (nháp nằm
#  trong chat, ghi bằng commit_draft) và là phần lớn nhất của lời nhắc (~12k ký tự với 15 công cụ). Lõi mới dùng bản
#  ngắn viết cho chat; web giữ nguyên bản cũ.
V2_TOOL_DESC: dict[str, str] = {
    "draft_purchase_request": (
        "Soạn NHÁP Yêu cầu mua hàng (YCMH) — chưa ghi gì. Người yêu cầu, phòng, công ty nhận hóa đơn tự điền theo hồ sơ (đừng "
        "hỏi). Phải có mặt hàng, số lượng (+ đơn vị), mục đích; thiếu thì hỏi MỘT lượt kèm luôn ngày cần hàng, kho nhận, thông "
        "số, có mua cho pháp nhân khác không (có thì điền company). Không bịa giá trị chưa nói. Đủ thì gọi ngay."),
    "draft_survey_request": (
        "Soạn NHÁP Yêu cầu báo giá (YCBG) — chưa ghi gì. Người yêu cầu, phòng, công ty tự điền (đừng hỏi). Phải có mặt hàng cần "
        "hỏi giá, số lượng dự kiến (+ đơn vị; chưa biết thì 0), mục đích; thiếu thì hỏi MỘT lượt kèm ngày cần kết quả "
        "(result_due_date), thông số, yêu cầu khác, pháp nhân khác. Không bịa. Đủ thì gọi ngay."),
    "draft_leave_request": (
        "Soạn NHÁP đơn nghỉ phép của CHÍNH người hỏi — chưa ghi gì. «nghỉ việc ngày X» = xin nghỉ phép ngày đó. Gọi khi đã biết "
        "NGÀY nghỉ; lý do / loại nghỉ chưa nói thì để trống, tool trả need_info để hỏi một lượt. Nửa ngày thì hỏi buổi. Có "
        "warnings (trùng đơn, thiếu quỹ phép) thì đọc nguyên. Không dùng cho Giấy nghỉ phép ở Văn thư (hệ tự sinh)."),
    "draft_payment_request": (
        "Soạn NHÁP Yêu cầu thanh toán (YCTT) từ khoản CÔNG NỢ CÒN PHẢI TRẢ — không tạo trong chat; bot gửi link form web điền "
        "sẵn. Đã gọi payable_lookup thì truyền payable_ids; chưa thì truyền supplier (+ company + một cặp ngày: due_from/due_to "
        "= hạn trả, invoice_from/invoice_to = ngày hóa đơn, date_from/date_to = ngày phát sinh). NCC có tiền trả trước treo "
        "thì nháp chia sẵn phần cấn trừ."),
    "propose_document_update": (
        "ĐỀ XUẤT sửa một phiếu ĐÃ CÓ — chưa ghi; bot gửi thẻ cũ → mới, người dùng nhắn «xác nhận» (hoặc bấm nút) mới ghi. Sửa "
        "được: YCMH mục đích / ngày cần hàng / ghi chú; YCBG mục đích / ghi chú; dòng hàng YCMH, YCBG qua line_ops; đơn nghỉ từ "
        "ngày / đến ngày / loại / lý do (chỉ Nháp hoặc Bị trả lại); YCTT 3 câu chữ bản in. KHÔNG sửa giá, NCC, số tiền, trạng "
        "thái, hạn chi — nói rõ phải sửa tay trên form. Chỉ điền trường được đổi với giá trị MỚI; thiếu thì hỏi."),
    "export_report_file": (
        "Xuất nội dung đã tổng hợp thành tệp Word (.docx) chuẩn DEGO, bot gửi tệp vào chat. Muốn Excel thì export_excel_file. "
        "Chỉ đổ số liệu THẬT đã tra trong hội thoại vào sections; được dùng <strong> và <br>."),
    "payable_lookup": (
        "Tra CÔNG NỢ PHẢI TRẢ nhà cung cấp. Mặc định chỉ khoản CÒN PHẢI TRẢ; summary tính trên toàn bộ kết quả lọc; mỗi khoản "
        "có payable_id (cho draft_payment_request). Ba cặp ngày: date_from/date_to = ngày PHÁT SINH; due_from/due_to = HẠN TRẢ "
        "(«cần trả tháng này»); invoice_from/invoice_to = NGÀY HÓA ĐƠN. «Bao nhiêu NCC / ai nợ nhiều nhất» → group_by="
        "supplier|company, đừng tự đếm danh sách. Có prepay_hanging thì đọc hint gợi ý cấn trừ."),
    "supplier_scorecard": (
        "CHẤM ĐIỂM nhà cung cấp 0–100 cho một mặt hàng từ dữ liệu ERP (giá 40 · ổn định 20 · giao đúng hạn 20 · pháp lý 20). "
        "Truyền product / product_code, hoặc supplier_codes / supplier_names để so NCC cụ thể. Trả lời: bảng điểm từ items, "
        "nêu weights, data_gaps là thiếu dữ liệu chứ không phải NCC kém, luôn nhắc note (AI chỉ gợi ý). with_web=true khi muốn "
        "tìm hiểu thêm trên web (uy tín, ISO) — chỉ tham khảo, không cộng điểm, dẫn nguồn."),
    "customs_buy_timing": (
        "Tư vấn THỜI ĐIỂM MUA một mặt hàng / hoạt chất theo giá nhập khẩu từng tháng (tờ khai hải quan). Trả lời bắt buộc: giá "
        "tháng gần nhất thấp / trung bình / cao so các tháng và xu hướng 3 tháng (now.*); now.reliable=false thì lấy "
        "now.reference_month; now.stale thì nói dữ liệu cũ; chỉ đề xuất recommended_month; nhắc caveat + confidence (thấp thì "
        "không khẳng định mùa vụ); nói đây chỉ là góc nhìn giá, chưa xét tồn kho / nhu cầu; nêu alerts."),
}
PARAM_DESC_MAX = 120


def _short_param(desc: str) -> str:
    """Mô tả tham số: giữ câu đầu, trần PARAM_DESC_MAX ký tự."""
    desc = " ".join(str(desc or "").split())
    if len(desc) <= PARAM_DESC_MAX:
        return desc
    for sep in (". ", " — ", "; "):
        head = desc.split(sep, 1)[0]
        if 20 <= len(head) <= PARAM_DESC_MAX:
            return head
    return desc[:PARAM_DESC_MAX - 1].rsplit(" ", 1)[0] + "…"


def _compact_schema(node):
    if isinstance(node, dict):
        out = {}
        for k, v in node.items():
            if k == "description" and isinstance(v, str):
                out[k] = _short_param(v)
            else:
                out[k] = _compact_schema(v)
        return out
    if isinstance(node, list):
        return [_compact_schema(x) for x in node]
    return node


def compact_defs(defs: list[ToolDef]) -> list[ToolDef]:
    """Bản ngắn cho lõi mới: mô tả viết riêng cho chat (V2_TOOL_DESC) + mô tả tham số còn câu đầu."""
    return [ToolDef(name=d.name, description=V2_TOOL_DESC.get(d.name, d.description),
                    parameters=_compact_schema(d.parameters)) for d in defs]


def _stop_after(name: str, result) -> bool:
    """ai-CR-202: dừng vòng công cụ NGAY sau khi soạn / sửa / ghi / bỏ nháp — câu trả lời do bot dựng từ tom_tat_se_luu
    (soạn, sửa) hoặc đường cũ đã báo kết quả (ghi, bỏ). Trước đây model được gọi thêm một lượt chỉ để chép lại bản tóm tắt
    — một lượt soạn nháp tốn 2 × (14k token trạm + ~30k của mình)."""
    if not isinstance(result, dict):
        return False
    if name == "commit_draft" and result.get("ask_confirm"):
        return True                          # gửi lại y câu cũ → bot tự hỏi tạo luôn hay soạn lại (confirm_reply)
    if name == MORE_TOOLS:
        return bool(result.get("nhom"))      # nạp thêm nhóm rồi chạy lại
    if result.get("error") or result.get("need_info"):
        return False
    if name in ("update_draft", "commit_draft", "drop_draft"):
        return bool(result.get("ok"))
    return isinstance(result.get("draft"), dict) and _chat_draft(name) and bool(result.get("tom_tat_se_luu"))


def _clip_line(text: str, limit: int) -> str:
    text = " ".join(str(text).split()).rstrip(".")
    return text if len(text) <= limit else text[:limit - 1].rsplit(" ", 1)[0] + "…"


def _bold_label(line: str) -> str:
    label, sep, value = str(line).partition(": ")
    return f"**{label}:** {value}" if sep and len(label) <= 30 else str(line)


def draft_reply(chat_id: str, name: str, result: dict) -> str:
    """Tin nháp do bot dựng (không gọi model lần hai): một câu mở, mỗi ô một dòng, điều em tự hiểu, lưu ý, một câu hỏi."""
    from . import draft_create

    tool = str(result.get("tool") or name)
    label = draft_create.LABELS.get(draft_create.kind_of(tool), "phiếu")
    draft = result.get("draft") or {}
    head = f"Em sửa nháp {label} rồi:" if name == "update_draft" else f"Em soạn nháp {label} như sau:"
    lines = [head] + [f"- {_bold_label(x)}" for x in result.get("tom_tat_se_luu") or []]
    assumed = [str(a) for a in draft.get("assumptions") or [] if str(a).strip()]
    if assumed:                              # Agent 1 15/10: câu này dài — tối đa 3 ý, mỗi ý 80 ký tự
        lines += ["", "Em tạm hiểu: " + "; ".join(_clip_line(a, 80) for a in assumed[:3]) + "."]
    warns = [str(w) for w in result.get("warnings") or [] if str(w).strip()]
    if warns:
        lines += ["", "Lưu ý: " + " ".join(warns[:4])]
    who = "Đại ca" if telegram.is_allowed_chat(chat_id) else "Anh/chị"
    lines += ["", f"{who} muốn đổi gì không? Ưng thì nhắn **tạo**, hoặc bảo em tạo luôn."]
    return "\n".join(lines)


def confirm_reply(chat_id: str, result: dict) -> str:
    """Người dùng gửi lại y câu đã sinh nháp: hỏi một câu thay vì tạo thật (run #227) hay gọi model lần hai (run #231)."""
    from . import draft_create

    label = draft_create.LABELS.get(draft_create.kind_of(str(result.get("tool") or "")), "phiếu")
    who = "đại ca" if telegram.is_allowed_chat(chat_id) else "anh/chị"
    lines = [f"Nháp {label} này đang chờ, em chưa tạo:"] + [f"- {_bold_label(x)}" for x in result.get("tom_tat_se_luu") or []]
    lines += ["", f"Em tạo luôn nháp này, hay {who} muốn em soạn lại?"]
    return "\n".join(lines)


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
#  Run #242 (15/10): model truyền nguyên «chị Mi» vào employee_lookup → «không tìm thấy»; lần trước truyền «Mi» thì ra đúng.
HONORIFIC = re.compile(r"^(?:anh|chị|chi|em|cô|co|chú|chu|bác|bac|ông|ong|bà|ba|bạn|ban|sếp|sep|mr\.?|ms\.?|mrs\.?)\s+",
                       re.IGNORECASE)
NAME_ARGS = {"employee_lookup": ("query",)}


def _clean_args(name: str, args: dict) -> dict:
    """Bỏ xưng hô đứng đầu tên người trước khi tra («chị Mi» → «Mi»)."""
    keys = NAME_ARGS.get(name)
    if not keys:
        return args
    out = dict(args)
    for k in keys:
        value = str(out.get(k) or "").strip()
        cleaned = HONORIFIC.sub("", value).strip()
        if value and cleaned:
            out[k] = cleaned
    return out


def _add_usage(result, first) -> None:
    result.input_tokens += first.input_tokens
    result.output_tokens += first.output_tokens
    result.cache_read_tokens += first.cache_read_tokens
    result.cache_write_tokens += first.cache_write_tokens


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
        context = turn_context(db, chat_id, row, user, text)
        msgs = [ChatMessage(role=t["role"], content=t["content"]) for t in turns] + [
            ChatMessage(role="user", content=context + text)]
        log.info("core_v2: system=%d ký tự · công cụ=%d · lịch sử=%d lượt", len(system), len(tools), len(turns))

        def execute(name: str, args: dict) -> dict:
            try:
                if name in LOCAL_TOOL_NAMES:
                    return _run_local(db, chat_id, row, user, name, args or {})
                out = erp.run_tool(db, user, name, _clean_args(name, args or {}))
                if isinstance(out, dict) and isinstance(out.get("draft"), dict):
                    out = {**out, "tom_tat_se_luu": _summary(name, out["draft"])}
                return out
            except Exception as e:  # noqa: BLE001
                log.exception("core_v2: công cụ %s hỏng", name)
                return {"error": f"Công cụ {name} lỗi: {type(e).__name__}: {str(e)[:200]}"}

        stopped: dict = {}

        def stop_when(name: str, res) -> bool:
            if _stop_after(name, res):
                stopped.update(name=name, result=res)
                return True
            return False

        lane = lane_of(text, {t.name for t in tools})
        with user_keys.prefer(route_providers(lane)):
            ref = user_keys.active_ref()
            log.info("core_v2: luồng %s → %s", lane, getattr(ref, "model", "") or getattr(ref, "provider", ""))
            result = manager.get_provider().run_tools(
                msgs, tools=tools, execute=execute, system=system, max_tokens=MAX_TOKENS, temperature=TEMPERATURE,
                max_iters=MAX_ITERS, cache_system=True, stop_when=stop_when)
            more: list[str] = []
            prior_calls: list = []                # công cụ của lần chạy đầu (more_tools) — gộp vào artifact
            if stopped.get("name") == MORE_TOOLS:
                #  Model xin thêm nhóm công cụ: nạp nhóm đó, chạy lại MỘT lần (không đưa more_tools nữa).
                more = list(stopped["result"].get("nhom") or [])
                log.info("core_v2: model xin thêm nhóm %s", more)
                stopped.clear()
                first = result
                prior_calls = list(first.tool_calls or [])
                tools = select_tools(db, user, text, chat_id, extra_groups=more)
                result = manager.get_provider().run_tools(
                    msgs, tools=tools, execute=execute, system=system, max_tokens=MAX_TOKENS, temperature=TEMPERATURE,
                    max_iters=MAX_ITERS, cache_system=True, stop_when=stop_when)
                _add_usage(result, first)
            if not stopped and _phantom_card(result):
                log.warning("core_v2: model nói tới thẻ mà không có nháp — viết lại một lần")
                first = result
                result = manager.get_provider().run_tools(
                    msgs + [ChatMessage(role="assistant", content=result.text or ""),
                            ChatMessage(role="user", content=PHANTOM_FIX)],
                    tools=tools, execute=execute, system=system, max_tokens=MAX_TOKENS, temperature=TEMPERATURE,
                    max_iters=MAX_ITERS, cache_system=True)
                _add_usage(result, first)
            service.finish_run(db, run, result=result)
        #  Đã dừng sau công cụ nháp thì chữ model (nếu có) chỉ là câu dạo trước khi gọi — bỏ, bot tự dựng tin.
        if stopped.get("name") == "commit_draft" and stopped["result"].get("ask_confirm"):
            service.reply(db, chat_id, confirm_reply(chat_id, stopped["result"]), markdown=True, action=ACT_ANSWER)
        elif stopped.get("name") in ("commit_draft", "drop_draft"):
            #  Đường cũ đã báo «Đã tạo …» / «không tạo» — chỉ ghi một dòng sổ để lịch sử còn lượt của bot.
            service.log_message(db, DIR_OUT, chat_id, 0,
                                "(em đã tạo xong theo nháp)" if stopped["name"] == "commit_draft" else "(em đã bỏ nháp)",
                                action=ACT_ANSWER)
        else:
            answer = (draft_reply(chat_id, stopped["name"], stopped["result"]) if stopped
                      else (result.text or "").strip())
            service.reply(db, chat_id, answer or "Em đã làm xong phần đó.", markdown=True, action=ACT_ANSWER)
        calls = [c for c in (result.tool_calls or []) if isinstance(c, dict) and c.get("name") not in LOCAL_TOOL_NAMES]
        drafts = [c for c in calls if isinstance(c.get("draft"), dict) and _chat_draft(c.get("name"))]
        for c in drafts:                     # nháp đã nằm trong câu trả lời — chỉ ghi dòng chờ «tạo», không gửi thẻ
            service._offer_draft(db, chat_id, user, c, silent=True)
        service.deliver_tool_results(db, chat_id, user, [c for c in calls if c not in drafts])
        run.artifact = {"core": "v2", "lane": lane, "tools": [str(c.get("name") or "") for c in prior_calls + list(
                            result.tool_calls or []) if isinstance(c, dict)][:20], "tools_offered": len(tools),
                        "stopped": stopped.get("name") or "", "more": more, "system_chars": len(system), "context_chars": len(context),
                        "cache_read": int(result.cache_read_tokens or 0), "cache_write": int(result.cache_write_tokens or 0),
                        "tools_chars": sum(len(t.description) + len(json.dumps(t.parameters, ensure_ascii=False)) for t in tools)}
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
