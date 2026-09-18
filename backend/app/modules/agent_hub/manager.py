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
Bạn là trợ lý quản lý kỹ thuật của một hệ thống ERP nội bộ. Bạn nhận MỘT đầu việc kèm
vài đoạn tài liệu của chính dự án, và phải viết BẢN ĐỀ XUẤT CÁCH SỬA cho lập trình viên.

Luật:
1. `plan_files` là danh sách đường dẫn tệp mà việc này sẽ đụng, tính từ gốc repo
   (ví dụ "backend/app/modules/leave/service.py"). CHỈ ghi tệp bạn thật sự tin là
   đúng, dựa trên tài liệu được cung cấp. KHÔNG đoán bừa đường dẫn.
2. Không đủ thông tin để viết `plan_files` cụ thể thì đặt `needs_clarification` = true,
   để `plan_files` RỖNG, và viết câu hỏi vào `questions`. Việc mơ hồ là nguồn gốc của
   mọi thảm họa trong loại hệ thống này — hỏi lại tốn vài phút, đoán sai tốn cả buổi.
3. `plan` là các bước sửa, tiếng Việt, đánh số. Nói VÌ SAO làm vậy, không chỉ nói làm gì.
4. `test_plan` nói rõ kiểm cái gì, gồm ít nhất một bài canh chiều ngược lại
   ("cái đáng lẽ không được xảy ra thì không xảy ra").
5. `related_docs` chỉ được trích từ những đoạn tài liệu ĐƯỢC CUNG CẤP bên dưới, ghi
   đúng đường dẫn tệp của chúng. CẤM bịa mã CR hay tên tệp không có trong đó.
6. `risk_level`: 3 nếu đụng tiền, phân quyền, cấu trúc cơ sở dữ liệu, hay nhánh `main`;
   khi đó `plan` phải nói RÕ rủi ro nằm ở đâu, không được chỉ dán nhãn.

CHỈ trả JSON, không thêm chữ nào ngoài JSON:
{"plan": "...", "plan_files": ["..."], "test_plan": "...", "risk_level": 2,
 "needs_clarification": false, "questions": [], "related_docs": ["duong/dan/tep.md"]}
"""


def run_plan(title: str, summary: str, docs: list[dict]) -> tuple[dict, ChatResult]:
    """Viết bản đề xuất cho một đầu việc. `docs` là kết quả `memory.recall()`."""
    parts = [f"ĐẦU VIỆC: {title}", "", "MÔ TẢ:", summary]
    if docs:
        parts += ["", "TÀI LIỆU LIÊN QUAN CỦA DỰ ÁN (chỉ được trích từ đây):"]
        parts += [f"--- {d['path']} ---\n{d['text']}" for d in docs]
    else:
        #  Nói thẳng là không tra được, thay vì im lặng để model tưởng dự án không có
        #  tài liệu nào rồi tự tin bịa ra đường dẫn (luật B4).
        parts += ["", "KHÔNG tra được tài liệu liên quan. Đừng viện dẫn tệp nào cả."]

    result = get_provider().ask(
        [ChatMessage(role="user", content="\n".join(parts))],
        model=settings.AGENT_MANAGER_MODEL,
        system=PLAN_SYSTEM,
        max_tokens=4096,
        temperature=0.3,
        thinking=True,
    )
    data = parse_json(result.text)
    files = [str(f) for f in data.get("plan_files") or [] if str(f).strip()]
    questions = [str(q) for q in data.get("questions") or [] if str(q).strip()]
    return {
        "plan": str(data.get("plan") or ""),
        "plan_files": files,
        "test_plan": str(data.get("test_plan") or ""),
        "risk_level": _risk(data.get("risk_level")),
        #  Rỗng `plan_files` LÀ mơ hồ, bất kể model tự đánh giá thế nào (luật B2).
        #  Để model một mình quyết cờ này thì nó gần như luôn trả false.
        "needs_clarification": bool(data.get("needs_clarification")) or not files,
        "questions": questions,
        "related_docs": [
            {"path": d["path"], "score": d["score"]}
            for d in docs
            if d["path"] in set(data.get("related_docs") or [])
        ],
    }, result
