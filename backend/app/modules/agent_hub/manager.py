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
import time

from app.core.config import settings
from app.modules.assistant.provider.base import ChatMessage, ChatResult, ProviderError
from app.modules.assistant.provider.base import Provider
from app.modules.assistant.provider.claude import ClaudeProvider
from app.modules.assistant.provider.gemini import GeminiProvider
from app.modules.assistant.provider.openai_compat import (DeepSeekProvider, OpenAICompatProvider, OpenRouterProvider,
                                                         XaiProvider)

from .constants import BOT_NAME

log = logging.getLogger("app.agent_hub.manager")


#  Trần phần suy nghĩ của bot quản lý. Đo 23/09: lượt lập kế hoạch nghĩ 6-14 nghìn token, và token
#  suy nghĩ tính giá như đầu ra — phần tốn nhất của một lượt. Hạ về 4096 (ai-CR-022).
THINKING_BUDGET = 4096
TRANSIENT_WAIT_SEC = 2      # ai-CR-099: chờ trước khi thử lại một lần khi hãng quá tải


def _server_side(error: str) -> bool:
    """ai-CR-198: lỗi do HÃNG / TRẠM (5xx, quá tải, upstream) — khác lỗi mạng phía mình (timeout)."""
    e = (error or "").lower()
    return any(k in e for k in (" 500:", " 502", " 503", " 504", "lỗi 503", "unavailable", "overloaded",
                                "high demand", "upstream"))


def fallback_model() -> str:
    """ai-CR-106: model Gemini dự phòng khi model chính quá tải."""
    from app.core import app_settings

    return settings.AGENT_FALLBACK_MODEL or app_settings.get("ai_gemini_model") or "gemini-flash-lite-latest"
NO_KEY_MSG = "Chưa có khóa AI nào dùng được cho chat này (Trang cá nhân → Khóa AI)."


class AgentGeminiProvider(GeminiProvider):
    """Provider của bot: Gemini bằng khóa của NGƯỜI đang chat (QĐ-AI-7, ai-CR-053) + bộ định tuyến chuỗi khóa nhiều
    hãng (ai-CR-098, C-04). Giữ tên «agent_gemini» cho mọi chỗ gọi cũ.

    Bot chạy nền và tự gọi model; dùng chung khóa với Trợ lý AI thì một ngày bot bận là hạn mức cạn, và thứ chết
    trước là trợ lý người dùng đang gõ trực tiếp — chết im lặng, giữa giờ làm.

    Mỗi lượt: lấy khóa đang dùng trong chuỗi (`user_keys.active_ref()`); khóa Gemini thì chạy chính lớp này, hãng khác
    giao cho adapter tương ứng (`_DELEGATES`). Hãng trả lỗi vì CHUYỆN CỦA KHÓA (hết tiền 402, hạn mức 429, khóa sai
    401/403 — `ai_keys.key_problem`) thì nhảy sang khóa kế và gọi lại, im lặng (đại ca 07/10: «khỏi cần báo»). Hết
    chuỗi thì ném lỗi cuối cho người gọi nói thẳng. Model: khóa khai `model` thì dùng; khóa Gemini không khai thì theo
    model người gọi đưa (cấu hình bot); hãng khác không khai thì mặc định của hãng.
    """

    name = "agent_gemini"

    @staticmethod
    def _send(url: str, payload: dict, headers: dict):
        """ai-CR-106: trần chờ riêng của bot (AGENT_GEMINI_TIMEOUT), ngắn hơn 60 s của Trợ lý web."""
        import requests

        try:
            from app.modules.assistant.provider.base import request_timeout

            return requests.post(url, json=payload, headers=headers,
                                 timeout=request_timeout(settings.AGENT_GEMINI_TIMEOUT))   # ai-CR-192
        except requests.RequestException as e:
            raise ProviderError(f"Lỗi gọi Gemini: {e}") from e

    def _api_key(self) -> str:
        #  ai-CR-053: khóa của NGƯỜI đang chat (ngữ cảnh do service mở); ngoài ngữ cảnh mới là khóa `.env`.
        from . import user_keys

        return user_keys.active_key()

    def is_configured(self) -> bool:
        #  Chỉ «có khóa» khi đang ở trong ngữ cảnh của bot: đăng ký vào registry của Trợ lý web nhưng
        #  đường chọn nhà mặc định của web không bao giờ được rơi vào provider này.
        from . import user_keys

        return user_keys.in_context() and bool(user_keys.active_key())

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
        elif not model.startswith("gemini-3"):
            #  Tắt HẲN (ai-CR-022). Lớp dùng chung chỉ gửi 0 cho model nó biết chắc nhận 0, nên với
            #  bí danh flash-latest nó bỏ trống và model vẫn tự nghĩ ~2,5 nghìn token mỗi lượt. Đo
            #  23/09: model của bot nhận `thinkingBudget: 0`. Dòng Gemini 3 thì TRẢ 400 với 0
            #  (ai-CR-056, dev đặt `gemini-3.5-flash-lite` cho Trợ lý) — với nó để trống như lớp chung.
            cfg["thinkingConfig"] = {"thinkingBudget": 0}
        return cfg

    # ── Bộ định tuyến chuỗi khóa (ai-CR-098) ──────────────────────────────────────────
    @staticmethod
    def _model_for(ref, model: str | None) -> str | None:
        if ref.model:
            return ref.model
        if ref.provider == "gemini":
            return model
        #  ai-CR-145: tên model KHÔNG phải Gemini (vd AGENT_PLAN_MODEL cho Claude) thì chuyển tiếp; tên Gemini thì không.
        return model if model and not model.startswith("gemini") else None

    def _call(self, method: str, *args, model: str | None = None, **kw):  # noqa: C901
        from . import ai_keys, user_keys

        last: ProviderError | None = None
        retried = False
        while True:
            ref = user_keys.active_ref()
            if ref is None or not ref.key:
                raise last or ProviderError(NO_KEY_MSG)
            if ref.provider == "gemini":
                fn = getattr(GeminiProvider, method).__get__(self, AgentGeminiProvider)
            else:
                fn = getattr(_DELEGATES.get(ref.provider) or _DELEGATES["claude"], method)
            try:
                wanted = self._model_for(ref, model)
                return fn(*args, model=_swapped(ref, wanted) or wanted, **kw)
            except ProviderError as e:
                swap = _swap_missing_model(ref, str(e), self._model_for(ref, model))
                if swap:
                    #  ai-CR-149: khóa trạm tùy chỉnh ghi model trạm không còn bán (đại ca đổi nhóm trên modelapi.vn) →
                    #  lấy model trạm đang có, cùng họ trước — bot không chết chỉ vì ô Model cũ.
                    log.warning("agent_hub: trạm không có model %s, dùng tạm %s (khóa …%s)", ref.model, swap, ref.hint)
                    _MODEL_SWAP[(ref.row_id, self._model_for(ref, model))] = (swap, time.time() + MODEL_SWAP_TTL_SEC)
                    continue
                if ai_keys.is_transient(str(e)):
                    if not retried:
                        #  ai-CR-099: 07/10 «alo how are u» chết vì Gemini 503 «high demand» → thẻ hỏi lại vô duyên.
                        #  ai-CR-106: Gemini thì đổi sang model DỰ PHÒNG (model chính đang quá tải, thử lại y nguyên vẫn treo).
                        retried = True
                        current = self._model_for(ref, model) or ""
                        if ref.provider == "gemini" and not ref.model and fallback_model() != current:
                            model = fallback_model()
                            log.warning("agent_hub: gemini %s quá tải, chuyển sang %s", current or "mặc định", model)
                            continue
                        log.warning("agent_hub: %s quá tải, thử lại sau %ss", ref.provider, TRANSIENT_WAIT_SEC)
                        time.sleep(TRANSIENT_WAIT_SEC)
                        continue
                    #  ai-CR-198 (14/10): khóa Gemini-trạm trả 500 «upstream error» hai lần liền → trước đây ném lỗi luôn
                    #  dù đại ca còn 3 khóa khác phía sau. HÃNG quá tải (5xx, «overloaded», «upstream») SAU khi đã thử lại
                    #  thì nhảy sang khóa kế. Lỗi mạng phía mình (timeout) vẫn KHÔNG nhảy — đổi khóa không chữa được.
                    if _server_side(str(e)) and user_keys.advance():
                        log.warning("agent_hub: %s …%s vẫn quá tải sau khi thử lại, nhảy sang khóa kế",
                                    ref.provider, ref.hint)
                        retried, last, model = False, e, None
                        continue
                if ai_keys.is_key_problem(str(e)):
                    from . import key_alerts

                    #  ai-CR-200: báo chủ khóa (gom theo trạm + loại lỗi, 3 giờ một lần) — 14/10 ví trạm âm tiền, bot
                    #  lặng lẽ rơi xuống Gemini lite và không ai biết.
                    moved = user_keys.advance()
                    key_alerts.notify(ref, str(e), has_next=moved)
                    if moved:
                        log.warning("agent_hub: khóa %s …%s hỏng (%s), nhảy sang khóa kế", ref.provider, ref.hint,
                                    str(e)[:80])
                        last = e
                        continue
                raise

    def ask(self, messages, *, model=None, system=None, max_tokens=1024, temperature=0.3, thinking=False,
            cache_system=False):
        return self._call("ask", messages, model=model, system=system, max_tokens=max_tokens,
                          temperature=temperature, thinking=thinking, cache_system=cache_system)

    def run_tools(self, messages, *, tools, execute, model=None, system=None, max_tokens=1024, temperature=0.3,
                  thinking=False, cache_system=False, max_iters=6, stop_when=None):
        #  ai-CR-183 (vá 13/10 15:20): quên nối `stop_when` ở provider của bot → mọi lượt Telegram chết TypeError.
        return self._call("run_tools", messages, tools=tools, execute=execute, model=model, system=system,
                          max_tokens=max_tokens, temperature=temperature, thinking=thinking,
                          cache_system=cache_system, max_iters=max_iters, stop_when=stop_when)


#  ai-CR-149: id khóa → model thay thế khi model ghi trên khóa không còn ở trạm (sống tới lúc tiến trình khởi động lại).
#  (khóa, model được xin) → (model thay, hết hạn). ai-CR-204 (15/10): trạm bày giá claude-haiku-5-5 nhưng nhóm «claude» chưa
#  có tài khoản nguồn → 404 model_not_found. Bản cũ gắn theo KHÓA và sống tới khi khởi động lại: một lần Haiku hỏng là
#  MỌI lượt của khóa đó (cả việc nặng) đổi model, và trạm mở Haiku rồi cũng không thử lại. Nay gắn theo (khóa, model xin),
#  hết hạn sau MODEL_SWAP_TTL_SEC; model thay chọn bản RẺ NHẤT đã biết giá cùng họ (tránh rơi vào Opus).
MODEL_SWAP_TTL_SEC = 3600
_MODEL_SWAP: dict[tuple[int, str], tuple[str, float]] = {}


def _swapped(ref, wanted: str) -> str:
    hit = _MODEL_SWAP.get((ref.row_id, wanted))
    if not hit:
        return ""
    if hit[1] < time.time():
        _MODEL_SWAP.pop((ref.row_id, wanted), None)
        return ""
    return hit[0]


def _swap_missing_model(ref, error: str, wanted: str = "") -> str:
    """Lỗi «model_not_found» của khóa trạm tùy chỉnh → model trạm đang có (cùng họ, rẻ nhất đã biết giá trước). Rỗng nếu
    không đổi được."""
    from . import ai_keys
    from .constants import MODEL_PRICES_USD
    from .user_keys import model_family

    wanted = wanted or ref.model or ""
    if ref.provider != "openai_compat" or "model_not_found" not in error or _swapped(ref, wanted):
        return ""
    try:
        models = ai_keys.custom_models(ref.base_url, ref.key)
    except Exception:  # noqa: BLE001
        return ""
    family = model_family(wanted)
    same = [m for m in models if model_family(m) == family and m != wanted]
    #  Ưu tiên model của khóa (ô Model) nếu cùng họ, rồi tới bản rẻ nhất đã biết giá; chưa biết giá xếp cuối.
    same.sort(key=lambda m: (m != ref.model, (MODEL_PRICES_USD.get(m) or (1e9, 0))[0]))
    return (same or [m for m in models if m != wanted] or [""])[0]


class _AgentGeminiOnly(AgentGeminiProvider):
    """Gemini thuần bằng khóa Gemini TRONG chuỗi (việc chỉ Gemini làm được: tìm Google ở `research.py`)."""

    def _api_key(self) -> str:
        from . import user_keys

        return user_keys.gemini_key()


class _AgentClaude(ClaudeProvider):
    def _api_key(self) -> str:
        from . import user_keys

        return user_keys.active_key()


class _AgentOpenAI(OpenAICompatProvider):
    def _api_key(self) -> str:
        from . import user_keys

        return user_keys.active_key()


class _AgentOpenRouter(OpenRouterProvider):
    def _api_key(self) -> str:
        from . import user_keys

        return user_keys.active_key()


class _AgentDeepSeek(DeepSeekProvider):
    def _api_key(self) -> str:
        from . import user_keys

        return user_keys.active_key()


class _AgentXai(XaiProvider):
    def _api_key(self) -> str:
        from . import user_keys

        return user_keys.active_key()


class _AgentCustom(OpenAICompatProvider):
    """ai-CR-108: trạm tùy chỉnh kiểu OpenAI — địa chỉ trạm lấy từ khóa đang dùng trong chuỗi."""

    name = "openai_compat"
    max_tokens_field = "max_tokens"

    @property
    def base_url(self) -> str:  # type: ignore[override]
        from . import user_keys

        ref = user_keys.active_ref()
        return ref.base_url if ref is not None else ""

    def _api_key(self) -> str:
        from . import user_keys

        return user_keys.active_key()


_DELEGATES: dict[str, Provider] = {"claude": _AgentClaude(), "openai": _AgentOpenAI(), "openrouter": _AgentOpenRouter(),
                                   "deepseek": _AgentDeepSeek(), "xai": _AgentXai(), "openai_compat": _AgentCustom()}


def get_provider() -> AgentGeminiProvider:
    return AgentGeminiProvider()


def gemini_provider() -> _AgentGeminiOnly:
    """Gemini thuần bằng khóa Gemini trong chuỗi — cho tìm Google (`research.search_web`)."""
    return _AgentGeminiOnly()


def register_with_assistant() -> None:
    """Cho Trợ lý AI gọi được bằng `provider="agent_gemini"` — tức bằng khóa cá nhân của người đang chat."""
    from app.modules.assistant import provider as registry

    registry._REGISTRY.setdefault(AgentGeminiProvider.name, AgentGeminiProvider())


register_with_assistant()


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


def extract_json_with(text: str, key: str) -> dict | None:
    """Object JSON CUỐI CÙNG trong `text` có khóa `key` khác rỗng, hoặc None.

    ai-CR-144 (AI-0006, 09/10/2026): model rẻ (DeepSeek flash qua openai_compat) xả cả đoạn suy nghĩ tiếng Anh vào phần
    chữ, trong đó có mảnh `{…}` lẻ — `parse_json` cắt từ `{` đầu tới `}` cuối ra một object RỖNG, kế hoạch thành chuỗi
    rỗng mà vẫn đi tiếp: thẻ trắng trơn kèm «nhắn duyệt», còn việc thì kẹt ở «đang hỏi lại» nên «duyệt» báo không có
    việc nào. Nay đọc từng object, chỉ nhận object có đúng khóa cần."""
    raw = _FENCE.sub("", text or "")
    dec = json.JSONDecoder()
    found = None
    i = raw.find("{")
    while i >= 0:
        try:
            obj, end = dec.raw_decode(raw, i)
        except ValueError:
            i = raw.find("{", i + 1)
            continue
        if isinstance(obj, dict) and str(obj.get(key) or "").strip():
            found = obj
        i = raw.find("{", end)
    return found


_JSON_ONLY = ("\n\nCHỈ trả MỘT object JSON đúng khuôn đã dặn, bắt đầu bằng { và kết thúc bằng }. KHÔNG viết phân tích, "
              "suy nghĩ hay câu dẫn nào ngoài JSON.")


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
7. `quick`: true CHỈ KHI việc vừa NHỎ vừa RÕ — đổi một đoạn chữ/nhãn/màu/thứ tự/ẩn hiện một ô trên
   giao diện, người nhắn nói rõ màn hình và chữ cũ/mới, không cần nghĩ thiết kế, không đụng backend,
   cơ sở dữ liệu, quyền, tiền, luồng duyệt (risk_level phải là 1). Mơ hồ, nhiều màn, hoặc «sửa lỗi»
   chưa rõ nguyên nhân → false. Người nhắn ghi «làm kỹ» → false; «làm luôn» / «làm nhanh» → true nếu risk 1.

CHỈ trả JSON, không thêm chữ nào ngoài JSON:
{"groups": [{"title": "...", "summary": "...", "message_ids": [1,2], "risk_level": 2, "quick": false}]}
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
            "quick": bool(g.get("quick")) and _risk(g.get("risk_level")) == 1,
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
Bạn là __BOT_NAME__, trợ lý quản lý kỹ thuật của một hệ thống ERP nội bộ. Bạn nhận MỘT đầu việc kèm
vài đoạn tài liệu của chính dự án, và phải viết BẢN ĐỀ XUẤT CÁCH SỬA cho lập trình viên.

Luật:
1. `plan_files` là danh sách đường dẫn tệp mà việc này sẽ đụng, tính từ gốc repo
   (ví dụ "backend/app/modules/leave/service.py"). CHỈ ghi tệp bạn thật sự tin là
   đúng, dựa trên tài liệu được cung cấp hoặc KẾT QUẢ RÀ SOÁT MÃ THẬT (nếu có ở cuối đề bài
   — khi nó khác tài liệu thì tin nó, và lấy đúng đường dẫn đầy đủ trong đó). KHÔNG đoán bừa
   đường dẫn, KHÔNG ghi tên tệp trơn thiếu thư mục.
   Rà soát cho thấy việc ĐÃ được sửa sẵn trên nhánh nền thì đặt `needs_clarification` = true và
   hỏi đại ca còn cần làm gì thêm, đừng lập kế hoạch sửa lại thứ đã có.
   Câu nghiệp vụ PHỤ mà rà soát nêu (ví dụ có gửi thư báo không, xử lý lịch lặp thế nào): TỰ CHỌN
   cách an toàn nhất, ít bất ngờ nhất, dễ đảo lại; ghi vào `assumptions` dạng "Em giả định: ...".
   (ai-CR-086, đại ca 05/10: «gọn gàng rồi sửa code luôn, xong a review lại».) Chỉ khi câu đó dính
   tiền, công nợ, phân quyền thì mới bỏ phần đó ra và ghi "Chưa làm: <phần đó> — chờ đại ca quyết: <câu>".
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
3. `plan` là các bước sửa, tiếng Việt, đánh số, TỐI ĐA 5 bước, mỗi bước MỘT câu ngắn (dưới 30
   chữ). Không mở đầu bằng đoạn nói về rủi ro, không nhắc lại yêu cầu, không giải thích dài —
   người đọc là quản lý, đọc trên điện thoại.
4. `test_plan` TỐI ĐA 3 gạch đầu dòng, mỗi dòng một câu, gồm ít nhất một bài canh chiều ngược
   lại ("cái đáng lẽ không được xảy ra thì không xảy ra").
5. `related_docs` chỉ được trích từ những đoạn tài liệu ĐƯỢC CUNG CẤP bên dưới, ghi
   đúng đường dẫn tệp của chúng. CẤM bịa mã CR hay tên tệp không có trong đó.
6. `risk_level`: 3 nếu đụng tiền, phân quyền, cấu trúc cơ sở dữ liệu, hay nhánh `main`;
   khi đó thêm vào `plan` MỘT câu nói rủi ro nằm ở đâu.

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
        parts += ["", "KẾT QUẢ RÀ SOÁT MÃ THẬT (" + BOT_NAME + " vừa đọc mã trên nhánh nền mới nhất; khác "
                      "tài liệu thì tin cái này):", review]
    if strict:
        parts += ["", _PLAN_STRICT_NOTE]
    elif playbook:
        parts += ["", "SỔ QUYẾT ĐỊNH CỦA ĐẠI CA (tra trước khi hỏi, trích đúng số QĐ):", playbook]

    from . import user_keys

    #  ai-CR-145: lập kế hoạch ưu tiên khóa hãng mạnh (Claude…) nếu chuỗi khóa có — DeepSeek flash xả suy nghĩ ra chữ.
    with user_keys.prefer(plan_providers(), model=plan_model_setting()):
        return _run_plan(parts, review, docs)


def plan_model_setting() -> str:
    """AGENT_PLAN_MODEL — đổi trên sổ cấu hình (`agent_plan_model`) không cần deploy."""
    from app.core import app_settings

    try:
        return str(app_settings.get("agent_plan_model") or "").strip()
    except Exception:  # noqa: BLE001
        return settings.AGENT_PLAN_MODEL


def plan_providers() -> list[str]:
    return [p.strip() for p in (settings.AGENT_PLAN_PROVIDERS or "").split(",") if p.strip()]


def _plan_model() -> str:
    """Khóa hãng khác Gemini mà để trống ô Model → dùng AGENT_PLAN_MODEL (nếu khai); còn lại như cũ."""
    from . import user_keys

    ref = user_keys.active_ref()
    if ref is not None and ref.provider != "gemini" and not ref.model and plan_model_setting():
        return plan_model_setting()
    return settings.AGENT_MANAGER_MODEL


def _run_plan(parts: list[str], review: str, docs: list[dict]) -> tuple[dict, ChatResult]:
    result = get_provider().ask(
        [ChatMessage(role="user", content="\n".join(parts))],
        model=_plan_model(),
        system=PLAN_SYSTEM.replace("__BOT_NAME__", BOT_NAME),
        #  Trần cho PHẦN CHỮ; phần suy nghĩ có trần riêng THINKING_BUDGET cộng thêm (ai-CR-021).
        max_tokens=4096,
        temperature=0.3,
        #  Đã có kết quả rà soát thì Claude đã suy luận trên mã thật rồi; lượt này chỉ xếp lại thành
        #  kế hoạch — tắt suy nghĩ, khỏi trả tiền nghĩ lại lần hai (ai-CR-022).
        thinking=not review,
    )
    data = extract_json_with(result.text, "plan")
    if data is None:
        #  Cụt, rác, hoặc model xả suy nghĩ ra phần chữ: thử lại MỘT lần, tắt suy nghĩ, dặn thẳng chỉ trả JSON.
        log.warning("agent_hub: kế hoạch không ra JSON có «plan» (%s), thử lại", (result.text or "")[:120])
        result = get_provider().ask(
            [ChatMessage(role="user", content="\n".join(parts) + _JSON_ONLY)],
            model=_plan_model(), system=PLAN_SYSTEM.replace("__BOT_NAME__", BOT_NAME),
            max_tokens=4096, temperature=0.2, thinking=False,
        )
        data = extract_json_with(result.text, "plan")
    if data is None:
        #  Ném lỗi để người gọi báo «lập kế hoạch lỗi» kèm nút lập lại — KHÔNG đi tiếp với kế hoạch rỗng.
        raise ProviderError("model không trả kế hoạch đúng khuôn JSON hai lần liền (có thể đang xả suy nghĩ ra chữ); "
                            f"đầu câu trả lời: {(result.text or '')[:160]}")
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

INTENT_DATA = "du_lieu"
INTENT_RESEARCH = "tra_cuu"

INTENT_ACT = "thao_tac"


VOICE_SYSTEM = ("Bạn là bộ chép lời. Nghe đoạn ghi âm tiếng Việt và chép lại ĐÚNG lời nói thành chữ có dấu, "
                "đúng chính tả, không thêm bớt, không bình luận, không tiêu đề. Chỉ trả về phần chữ.")


def transcribe(data: bytes, mime: str) -> tuple[str, ChatResult]:
    """Tin thoại Telegram (ogg/opus) → chữ (ai-CR-061, T-07): một lượt Gemini nhận audio kèm lời nhắc chép lời."""
    import base64

    provider = get_provider()
    model = settings.AGENT_MANAGER_MODEL
    payload = {
        "contents": [{"role": "user", "parts": [
            {"inlineData": {"mimeType": mime or "audio/ogg", "data": base64.b64encode(data).decode()}},
            {"text": "Chép lại lời trong đoạn ghi âm này."}]}],
        "systemInstruction": {"parts": [{"text": VOICE_SYSTEM}]},
        "generationConfig": provider._gen_config(model, 1024, 0.1, False),
    }
    out = provider._post(model, payload)
    candidates = out.get("candidates") or []
    first = candidates[0] if candidates else {}
    text = "".join(p.get("text", "") for p in (first.get("content") or {}).get("parts", []) if "text" in p)
    usage = out.get("usageMetadata") or {}
    result = ChatResult(text=text, provider=provider.name, model=out.get("modelVersion", model),
                        input_tokens=int(usage.get("promptTokenCount", 0)),
                        output_tokens=int(usage.get("candidatesTokenCount", 0)),
                        thinking_tokens=int(usage.get("thoughtsTokenCount", 0)))
    return text.strip(), result
