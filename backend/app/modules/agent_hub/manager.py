"""Bot quản lý — hai trạm TRIAGE và PLAN, chạy bằng Gemini.

Tệp này CHỈ lo phần "hỏi model và nhận về cấu trúc". Không đụng DB, không gửi
Telegram — `service.py` ráp. Nhờ vậy thay model hay đổi câu nhắc không phải mở tới
tầng luồng, và kiểm thử được bằng cách cắm một provider giả.

Luật §B của `doc/agent-hub/02-bo-quy-tac-bot.md` nằm trong hai câu nhắc dưới đây.
Hai luật KHÔNG giao cho câu nhắc giữ vì nhắc suông thì model quên:
  - B1 (phải ra JSON) — `parse_json` ném lỗi nếu không phải JSON, và `service.py`
    ghi `RUN_ERROR` chứ không đoán tiếp.
  - B2 (không có `plan_files` thì cấm sang CODE) — chốt thật nằm ở `service.py`.
"""
import json
import logging
import re

from app.core.config import settings
from app.modules.assistant.provider.base import ChatMessage, ChatResult, ProviderError
from app.modules.assistant.provider.gemini import GeminiProvider

log = logging.getLogger("app.agent_hub.manager")


class AgentGeminiProvider(GeminiProvider):
    """Gemini chạy bằng khóa RIÊNG của bot (QĐ-AI-7).

    Bot chạy nền và tự gọi model; dùng chung khóa với Trợ lý AI thì một ngày bot bận
    là hạn mức cạn, và thứ chết trước là trợ lý người dùng đang gõ trực tiếp — chết
    im lặng, giữa giờ làm.
    """

    name = "agent_gemini"

    def _api_key(self) -> str:
        return settings.AGENT_GEMINI_API_KEY

    def _gen_config(self, model: str, max_tokens: int, temperature: float, thinking: bool) -> dict:
        """Có suy nghĩ thì CHẶN TRẦN phần suy nghĩ và cộng nó vào trần đầu ra (ai-CR-021).

        Gemini tính token suy nghĩ vào `maxOutputTokens`. Không chặn thì có lượt nghĩ ~14 nghìn
        token, chạm trần 16384 và cắt cụt JSON giữa chuỗi (AI-0007, 23/09/2026). Chỉnh ở lớp RIÊNG
        của bot, không đụng provider dùng chung với Trợ lý AI trên web.
        """
        cfg = super()._gen_config(model, max_tokens, temperature, thinking)
        if thinking:
            cfg["thinkingConfig"] = {"thinkingBudget": THINKING_BUDGET}
            cfg["maxOutputTokens"] = max_tokens + THINKING_BUDGET
        return cfg


#  Trần phần suy nghĩ của bot quản lý. Đo 23/09: lượt lập kế hoạch nghĩ 6-14 nghìn token.
THINKING_BUDGET = 8192


def get_provider() -> AgentGeminiProvider:
    return AgentGeminiProvider()


_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


def parse_json(text: str) -> dict:
    """Bóc JSON khỏi câu trả lời. Không ra JSON thì NÉM LỖI, không đoán.

    Model rất hay bọc kết quả trong ```json … ``` dù đã dặn đừng — nên bóc rào trước,
    rồi mới cắt từ `{` đầu tới `}` cuối (phòng khi nó thêm một câu dẫn ở đầu).
    """
    raw = _FENCE.sub("", (text or "").strip()).strip()
    start, end = raw.find("{"), raw.rfind("}")
    if start >= 0 and end > start:
        raw = raw[start : end + 1]
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ProviderError(f"Model không trả JSON: {e}; 300 ký tự đầu: {raw[:300]}") from e
    if not isinstance(data, dict):
        raise ProviderError(f"Model trả JSON nhưng không phải object: {type(data).__name__}")
    return data


# ---------------------------------------------------------------------------
# Trạm TRIAGE — gom tin nhắn cùng loại thành đầu việc
# ---------------------------------------------------------------------------
TRIAGE_SYSTEM = """\
Bạn là trợ lý quản lý kỹ thuật của một hệ thống ERP nội bộ (FastAPI + React, tiếng Việt).
Bạn nhận một loạt tin nhắn rời của người quản lý và gom chúng thành các ĐẦU VIỆC.

Luật:
1. CHỈ gom những tin thật sự cùng loại: cùng phân hệ và cùng kiểu sửa. Nghi ngờ thì TÁCH.
   Gom cho ít đầu việc là tạo ra một việc không ai xem nổi.
2. Một tin không liên quan tới tin nào khác thì tự nó là một đầu việc.
3. `title` là câu tiếng Việt ngắn, dưới 80 ký tự, nói ĐÚNG việc phải làm.
4. `summary` gộp nội dung các tin trong nhóm, giữ nguyên mọi chi tiết cụ thể
   (tên màn hình, tên cột, số liệu). Không thêm suy đoán của bạn.
5. `risk_level`: 3 nếu việc đụng TIỀN, PHÂN QUYỀN, cấu trúc cơ sở dữ liệu, hoặc nhánh
   `main`; 1 nếu chỉ sửa chữ nghĩa/giao diện; còn lại 2.
6. Mọi `id` bạn nhận vào phải xuất hiện đúng MỘT lần trong kết quả. Không bịa id mới.

CHỈ trả JSON, không thêm chữ nào ngoài JSON:
{"groups": [{"title": "...", "summary": "...", "message_ids": [1,2], "risk_level": 2}]}
"""


def run_triage(items: list[dict]) -> tuple[dict, ChatResult]:
    """Gom `items` = [{"id": int, "text": str}] thành các nhóm.

    MỘT lượt gọi cho cả lô, không phải mỗi tin một lượt — gom là việc so tin này với
    tin kia, model phải nhìn thấy cả lô cùng lúc mới làm được.
    """
    payload = json.dumps(
        [{"id": it["id"], "text": it["text"]} for it in items],
        ensure_ascii=False,
    )
    result = get_provider().ask(
        [ChatMessage(role="user", content=f"Các tin nhắn cần gom:\n{payload}")],
        model=settings.AGENT_MANAGER_MODEL,
        system=TRIAGE_SYSTEM,
        max_tokens=4096,
        temperature=0.2,
    )
    data = parse_json(result.text)
    data["groups"] = _clean_groups(data.get("groups"), {it["id"] for it in items})
    return data, result


def _clean_groups(groups, valid_ids: set[int]) -> list[dict]:
    """Lọc kết quả TRIAGE về đúng khuôn, bỏ mọi id model bịa ra.

    Không lọc thì một id bịa sẽ thành `tab_agent_task_item.ref_id` trỏ vào hư không,
    còn tin nhắn thật thì kẹt lại INBOX mãi mãi.
    """
    cleaned: list[dict] = []
    seen: set[int] = set()
    for g in groups or []:
        if not isinstance(g, dict):
            continue
        ids = [i for i in g.get("message_ids") or []
               if isinstance(i, int) and i in valid_ids and i not in seen]
        if not ids:
            continue
        seen.update(ids)
        cleaned.append({
            "title": str(g.get("title") or "")[:255],
            "summary": str(g.get("summary") or ""),
            "message_ids": ids,
            "risk_level": _risk(g.get("risk_level")),
        })
    #  Tin nào model bỏ quên thì gom hết vào MỘT việc "chưa phân loại" — thả lại INBOX
    #  thì lượt sau lại gửi đúng chúng cho model và có thể lại bị quên, quay vòng mãi.
    missed = sorted(valid_ids - seen)
    if missed:
        log.warning("agent_hub: TRIAGE bỏ sót %d tin, gom vào một việc", len(missed))
        cleaned.append({
            "title": "Tin nhắn chưa phân loại được",
            "summary": "Bot quản lý không xếp được mấy tin này vào nhóm nào.",
            "message_ids": missed,
            "risk_level": 2,
        })
    return cleaned


def _risk(value) -> int:
    return value if value in (1, 2, 3) else 2


# ---------------------------------------------------------------------------
# Trạm PLAN — đề xuất cách sửa
# ---------------------------------------------------------------------------
PLAN_SYSTEM = """\
Bạn là Đậu Đậu, trợ lý quản lý kỹ thuật của một hệ thống ERP nội bộ. Bạn nhận MỘT đầu việc kèm
vài đoạn tài liệu của chính dự án, và phải viết BẢN ĐỀ XUẤT CÁCH SỬA cho lập trình viên.

Luật:
1. `plan_files` là danh sách đường dẫn tệp mà việc này sẽ đụng, tính từ gốc repo
   (ví dụ "backend/app/modules/leave/service.py"). CHỈ ghi tệp bạn thật sự tin là
   đúng, dựa trên tài liệu được cung cấp hoặc KẾT QUẢ RÀ SOÁT MÃ THẬT (nếu có ở cuối đề bài
   — khi nó khác tài liệu thì tin nó, và lấy đúng đường dẫn đầy đủ trong đó). KHÔNG đoán bừa
   đường dẫn, KHÔNG ghi tên tệp trơn thiếu thư mục.
   Rà soát cho thấy việc ĐÃ được sửa sẵn trên nhánh nền thì đặt `needs_clarification` = true và
   hỏi đại ca còn cần làm gì thêm, đừng lập kế hoạch sửa lại thứ đã có.
   Câu nghiệp vụ mà rà soát nêu và đại ca CHƯA trả lời (ví dụ có chặn gửi duyệt không, có cho
   sửa tay không): KHÔNG tự quyết thay. Bỏ phần phụ thuộc câu đó ra khỏi kế hoạch, và ghi vào
   `assumptions` dạng "Chưa làm: <phần đó> — chờ đại ca quyết: <câu hỏi>".
2. Chỗ chưa rõ: tra SỔ QUYẾT ĐỊNH CỦA ĐẠI CA (nếu có ở cuối đề bài) TRƯỚC khi hỏi.
   - Có mục khớp: làm theo, ghi vào `assumptions` dạng "Theo QĐ-07: ...".
   - Không có mục khớp nhưng có MỘT cách làm hợp lý, an toàn, dễ đảo lại: chọn nó, ghi vào
     `assumptions` dạng "Em giả định: ...".
   - CHỈ đặt `needs_clarification` = true (để `plan_files` RỖNG, câu hỏi vào `questions`) khi:
     không viết nổi `plan_files`; hoặc việc dính tiền, công nợ, thanh toán, phân quyền, cấu
     trúc cơ sở dữ liệu, prod, nhánh `main`; hoặc yêu cầu hiểu được theo hai cách dẫn tới hai
     việc khác hẳn nhau. Hỏi thì hỏi GỌN, mỗi câu một ý, tối đa 3 câu.
   - KHÔNG hỏi người quản lý đường dẫn tệp, tên hàm hay cấu trúc mã: anh ấy không trả lời
     được, đó là việc của bạn. Chỉ hỏi về NGHIỆP VỤ (màn nào, kết quả mong muốn là gì).
3. `plan` là các bước sửa, tiếng Việt, đánh số. Nói VÌ SAO làm vậy, không chỉ nói làm gì.
4. `test_plan` nói rõ kiểm cái gì, gồm ít nhất một bài canh chiều ngược lại
   ("cái đáng lẽ không được xảy ra thì không xảy ra").
5. `related_docs` chỉ được trích từ những đoạn tài liệu ĐƯỢC CUNG CẤP bên dưới, ghi
   đúng đường dẫn tệp của chúng. CẤM bịa mã CR hay tên tệp không có trong đó.
6. `risk_level`: 3 nếu đụng tiền, phân quyền, cấu trúc cơ sở dữ liệu, hay nhánh `main`;
   khi đó `plan` phải nói RÕ rủi ro nằm ở đâu, không được chỉ dán nhãn.

CHỈ trả JSON, không thêm chữ nào ngoài JSON:
{"plan": "...", "plan_files": ["..."], "test_plan": "...", "risk_level": 2,
 "needs_clarification": false, "questions": [], "assumptions": [],
 "related_docs": ["duong/dan/tep.md"]}
"""

#  Việc rủi ro cao (luật 3 của sổ, ai-CR-015): không nạp sổ và nói thẳng là phải hỏi.
_PLAN_STRICT_NOTE = (
    "VIỆC NÀY RỦI RO CAO: KHÔNG được tự giả định. Mọi chỗ chưa rõ phải vào `questions`, "
    "để `assumptions` rỗng."
)


def run_plan(title: str, summary: str, docs: list[dict], *, playbook: str = "",
             strict: bool = False, review: str = "") -> tuple[dict, ChatResult]:
    """Viết bản đề xuất cho một đầu việc. `docs` là kết quả `memory.recall()`.

    `playbook` = phần mục của sổ quyết định (rỗng khi việc rủi ro cao hoặc chưa có sổ);
    `strict` = việc rủi ro cao, cấm giả định (ai-CR-015)."""
    parts = [f"ĐẦU VIỆC: {title}", "", "MÔ TẢ:", summary]
    if docs:
        parts += ["", "TÀI LIỆU LIÊN QUAN CỦA DỰ ÁN (chỉ được trích từ đây):"]
        parts += [f"--- {d['path']} ---\n{d['text']}" for d in docs]
    else:
        #  Nói thẳng là không tra được, thay vì im lặng để model tưởng dự án không có
        #  tài liệu nào rồi tự tin bịa ra đường dẫn (luật B4).
        parts += ["", "KHÔNG tra được tài liệu liên quan. Đừng viện dẫn tệp nào cả."]
    if review:
        #  ai-CR-017: Claude Code đã đọc mã thật trên nhánh nền mới nhất. Tài liệu thì có thể cũ.
        parts += ["", "KẾT QUẢ RÀ SOÁT MÃ THẬT (Đậu Đậu vừa đọc mã trên nhánh nền mới nhất; khác "
                      "tài liệu thì tin cái này):", review]
    if strict:
        parts += ["", _PLAN_STRICT_NOTE]
    elif playbook:
        parts += ["", "SỔ QUYẾT ĐỊNH CỦA ĐẠI CA (tra trước khi hỏi, trích đúng số QĐ):", playbook]

    result = get_provider().ask(
        [ChatMessage(role="user", content="\n".join(parts))],
        model=settings.AGENT_MANAGER_MODEL,
        system=PLAN_SYSTEM,
        #  Trần cho PHẦN CHỮ; phần suy nghĩ có trần riêng THINKING_BUDGET cộng thêm (ai-CR-021).
        max_tokens=8192,
        temperature=0.3,
        thinking=True,
    )
    try:
        data = parse_json(result.text)
    except ProviderError as e:
        #  Vẫn cụt (hoặc model trả rác): thử lại MỘT lần, tắt suy nghĩ để cả trần dành cho chữ.
        log.warning("agent_hub: kế hoạch không ra JSON (%s), thử lại không suy nghĩ", str(e)[:120])
        result = get_provider().ask(
            [ChatMessage(role="user", content="\n".join(parts))],
            model=settings.AGENT_MANAGER_MODEL, system=PLAN_SYSTEM,
            max_tokens=8192, temperature=0.3, thinking=False,
        )
        data = parse_json(result.text)
    files = [str(f) for f in data.get("plan_files") or [] if str(f).strip()]
    questions = [str(q) for q in data.get("questions") or [] if str(q).strip()]
    assumptions = [str(a).strip() for a in data.get("assumptions") or [] if str(a).strip()]
    return {
        "plan": str(data.get("plan") or ""),
        "plan_files": files,
        "test_plan": str(data.get("test_plan") or ""),
        "risk_level": _risk(data.get("risk_level")),
        #  Rỗng `plan_files` LÀ mơ hồ, bất kể model tự đánh giá thế nào (luật B2).
        #  Để model một mình quyết cờ này thì nó gần như luôn trả false.
        "needs_clarification": bool(data.get("needs_clarification")) or not files,
        "questions": questions,
        "assumptions": assumptions,
        "related_docs": [
            {"path": d["path"], "score": d["score"]}
            for d in docs
            if d["path"] in set(data.get("related_docs") or [])
        ],
    }, result


# ---------------------------------------------------------------------------
# Trạm PHÂN LOẠI Ý ĐỊNH — tin chữ thường là HỎI hay GIAO VIỆC (ai-CR-003)

# ---------------------------------------------------------------------------
# Nháp một mục cho sổ quyết định (ai-CR-015)
# ---------------------------------------------------------------------------
RULE_SYSTEM = """\
Bạn giúp một người quản lý ghi lại những QUYẾT ĐỊNH QUEN THUỘC của anh ấy, để lần sau bot
lập trình gặp tình huống tương tự thì tự làm, khỏi hỏi lại.

Bạn nhận: tên đầu việc, câu bot đã hỏi, và câu người quản lý trả lời. Việc của bạn là xem
câu trả lời đó có phải một LUẬT DÙNG LẠI ĐƯỢC không, và nếu có thì viết nó thành một mục.

Luật:
1. `generalizable` = false khi câu trả lời chỉ đúng cho riêng việc này (một con số cụ thể,
   một tên phiếu, một lần ngoại lệ), hoặc khi nó trùng ý một mục đã có trong danh sách
   được cung cấp. Nghi ngờ thì false.
2. `generalizable` = false khi câu trả lời dính tiền, công nợ, thanh toán, phân quyền, cấu
   trúc cơ sở dữ liệu, prod, nhánh main, hay gộp mã — loại đó lần nào cũng phải hỏi.
3. `situation` tả TÌNH HUỐNG chung (không nêu tên việc này), `action` tả bot làm gì,
   `not_when` tả ranh giới: khi nào KHÔNG được áp luật này. Mỗi ý một câu tiếng Việt trọn
   vẹn, dưới 300 ký tự. `title` dưới 70 ký tự.
4. KHÔNG thêm điều người quản lý không nói. Chép ý của anh ấy, đừng suy rộng.

CHỈ trả JSON, không thêm chữ nào ngoài JSON:
{"generalizable": true, "title": "...", "situation": "...", "action": "...", "not_when": "..."}
"""


def run_rule_draft(title: str, questions: list[str], answer: str,
                   known: list[str]) -> tuple[dict, ChatResult]:
    """Nháp một mục sổ từ một lượt hỏi-đáp. Không dùng lại được thì `generalizable` = False."""
    parts = [f"ĐẦU VIỆC: {title}", "", "BOT ĐÃ HỎI:"]
    parts += [f"- {q}" for q in questions] or ["- (bot mời nói rõ thêm về kế hoạch)"]
    parts += ["", "NGƯỜI QUẢN LÝ TRẢ LỜI:", answer]
    if known:
        parts += ["", "CÁC MỤC ĐÃ CÓ TRONG SỔ (đừng đề xuất trùng):"] + [f"- {k}" for k in known]
    result = get_provider().ask(
        [ChatMessage(role="user", content="\n".join(parts))],
        model=settings.AGENT_MANAGER_MODEL,
        system=RULE_SYSTEM,
        max_tokens=1024,
        temperature=0.2,
    )
    data = parse_json(result.text)
    entry = {k: " ".join(str(data.get(k) or "").split()) for k in
             ("title", "situation", "action", "not_when")}
    ok = bool(data.get("generalizable")) and all(entry[k] for k in ("title", "situation", "action"))
    return {"generalizable": ok, **entry}, result


# ---------------------------------------------------------------------------
INTENT_ASK = "hoi"
INTENT_TASK = "viec"
INTENT_UNSURE = "mo_ho"

INTENT_SYSTEM = """\
Bạn phân loại MỘT tin nhắn của người quản lý gửi cho bot của hệ thống ERP nội bộ.
Bot có hai tay:
  - TRỢ LÝ AI: tra cứu VÀ làm nghiệp vụ ngay trên hệ thống bằng công cụ có sẵn — xem
    số liệu, tình trạng chứng từ, tạo đơn nghỉ phép, lập báo cáo, duyệt, gửi thông báo.
  - SỔ VIỆC SỬA PHẦN MỀM: ghi lại để lập trình viên sửa mã nguồn.

Chỉ có ba kết quả:

- "hoi": giao cho TRỢ LÝ AI. Gồm cả ba dạng: người ta MUỐN BIẾT một điều có sẵn
  (số liệu, tình trạng một chứng từ, ai giữ việc, cách dùng, nội dung tài liệu);
  người ta muốn LÀM NGAY một việc nghiệp vụ trên hệ thống (tạo / lập / gửi / duyệt
  một chứng từ, xuất một báo cáo); hoặc người ta đang TRẢ LỜI câu bot vừa hỏi, nói
  tiếp câu chuyện đang dở.
- "viec": nhờ SỬA PHẦN MỀM — thêm/bớt/sửa tính năng, báo một chỗ chạy sai, đổi giao
  diện, đổi cách tính, xin một màn hình mới, nhờ làm tài liệu.
- "mo_ho": đọc xong vẫn không chắc, hoặc tin quá ngắn/cụt để biết người ta muốn gì.

Vài ca dễ nhầm:
- "3 đơn mua hàng gần nhất" -> hoi (đòi số liệu).
- "tạo cho anh đơn nghỉ phép thứ 6 tuần này" -> hoi (nhờ làm nghiệp vụ, Trợ lý AI có
  công cụ làm được; KHÔNG phải sửa phần mềm).
- Bot vừa hỏi "nghỉ ngày nào, lý do gì?" và người ta nhắn "thứ 6, đi du lịch" -> hoi
  (đang trả lời bot).
- "màn đơn mua hàng không lọc được theo ngày" -> viec (báo chỗ chạy sai).
- "sao đơn PO00362 chưa duyệt" -> hoi (hỏi tình trạng một chứng từ cụ thể).
- "cho thêm cột ngày giao vào bảng đơn hàng" -> viec.
- "xem lại giúp anh" -> mo_ho (không biết xem cái gì).

Nếu có MẠCH TRƯỚC ĐÓ thì phải đọc nó trước khi phán: một tin ngắn cụt đứng ngay sau
câu hỏi của bot thường là câu nối tiếp (-> hoi), không phải mo_ho.

Nghi ngờ thì chọn "mo_ho". Đoán bừa tốn hơn hỏi lại một câu: đoán thành "viec" thì
người ta chờ một câu trả lời không bao giờ tới, đoán thành "hoi" thì việc cần làm
biến mất khỏi sổ.

CHỈ trả JSON, không thêm chữ nào ngoài JSON:
{"intent": "hoi", "reason": "lý do ngắn bằng tiếng Việt"}
"""


def run_intent(text: str, *, context: str = "") -> tuple[dict, ChatResult]:
    """Đọc một tin và nói nó là việc cho Trợ lý AI hay một đầu việc sửa mã.

    Một lượt gọi RẺ (vài trăm token) đứng trước mỗi tin chữ thường, để đại ca khỏi
    phải nhớ gõ tiền tố `/hoi`. Model trả kiểu lạ thì hạ xuống "mo_ho" — nhánh mập
    mờ là nhánh hỏi lại, tức chỗ an toàn nhất để rơi vào.

    `context` = vài lượt hỏi-đáp ngay trước đó (ai-CR-007). Không có nó, model chỉ thấy
    một câu trơ trọi: *"cho anh nghỉ thứ 6, lý do đi du lịch"* đọc rời thì giống một
    lời nhờ, đọc sau câu *"anh muốn nghỉ ngày nào?"* của bot thì rõ là câu trả lời.
    """
    if context:
        content = f"MẠCH TRƯỚC ĐÓ:\n{context}\n\nTin nhắn mới:\n{text}"
    else:
        content = f"Tin nhắn:\n{text}"
    result = get_provider().ask(
        [ChatMessage(role="user", content=content)],
        model=settings.AGENT_MANAGER_MODEL,
        system=INTENT_SYSTEM,
        max_tokens=256,
        temperature=0.0,
    )
    data = parse_json(result.text)
    intent = str(data.get("intent") or "").strip().lower()
    if intent not in (INTENT_ASK, INTENT_TASK, INTENT_UNSURE):
        log.warning("agent_hub: phân loại trả ý định lạ %r, coi như mập mờ", intent)
        intent = INTENT_UNSURE
    return {"intent": intent, "reason": str(data.get("reason") or "")[:200]}, result
