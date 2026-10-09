"""Adapter kiểu OpenAI (Chat Completions) — dùng cho OpenAI và mọi hãng nói cùng API: OpenRouter, DeepSeek, Groq…
(ai-CR-098, nhóm C-04). Gọi REST bằng `requests`, không thêm SDK, giống hai adapter Claude / Gemini.

Khóa đọc qua `_api_key()` để lớp con của bot (agent_hub/manager.py) đổi nguồn khóa sang khóa cá nhân của người
đang chat. Mặc định: dòng khóa CÔNG TY trong `tab_ai_key` (ưu tiên 1) → cấu hình hệ thống (nếu có khai).
"""
from __future__ import annotations

import json
import re

import requests

from app.core import app_settings

from .base import ChatMessage, ChatResult, Provider, ProviderError, ToolDef, ToolExecutor

TIMEOUT = 90
OPENAI_URL = "https://api.openai.com/v1"
OPENROUTER_URL = "https://openrouter.ai/api/v1"
MIN_OUTPUT_TOKENS = 8000
CUT_NOTE = "\n\n_(Câu trả lời chạm trần độ dài nên bị cắt — nhắn «viết tiếp» để em viết nốt.)_"


def _wire_content(content):
    """Chuỗi giữ nguyên; list block → block Chat Completions (ảnh = image_url data URI; PDF chưa hỗ trợ → ghi chú)."""
    if isinstance(content, str):
        return content
    out = []
    for b in content:
        if b.get("type") == "file":
            media = b.get("media_type", "")
            if media.startswith("image/"):
                out.append({"type": "image_url", "image_url": {"url": f"data:{media};base64,{b.get('data_b64', '')}"}})
            else:
                out.append({"type": "text", "text": f"[tệp đính kèm {media} — hãng này chưa đọc được tệp loại này]"})
        else:
            out.append({"type": "text", "text": b.get("text", "")})
    return out


#  ai-CR-151: 09/10 đại ca thấy tin bot mở đầu bằng «<thinking> </thinking>» — model đổi tên thẻ. Bắt cả think /
#  thinking / reasoning, và thẻ lẻ (mở không đóng hoặc ngược lại) còn sót sau khi bỏ khối.
_THINK_BLOCK = re.compile(r"<(think|thinking|reasoning)>.*?</\1>\s*", re.S | re.I)
_THINK_TAG = re.compile(r"</?(?:think|thinking|reasoning)>\s*", re.I)
#  Dấu chuyển sang câu trả lời thật: «Final answer:», «Final:», «Final?» ở đầu dòng (cho phép vài ký hiệu đứng trước).
_FINAL_MARK = re.compile(r"(?:^|\n)[^\w\n]{0,6}final(?: answer)?\s*[:?]", re.I)


def clean_reply(text: str) -> str:
    """Bỏ phần «nghĩ» mà model suy luận lỡ trả lẫn vào câu trả lời (ai-CR-112).

    07/10/2026 chạy thử biên bản họp bằng `deepseek-v4.1-flash` qua trạm modelapi: một lần trong bốn, nội dung mở đầu
    bằng cả đoạn rác («**:», «### Final? Let's prepare final…») rồi mới tới «Final answer:» và biên bản thật. Có khối
    <think>…</think> thì bỏ khối; có dấu «Final answer:» ở đầu dòng thì chỉ lấy phần sau dấu CUỐI CÙNG (bỏ nốt phần còn
    lại của dòng đó nếu chỉ là ký hiệu). Câu bình thường không có hai dấu này thì giữ nguyên.
    """
    if not text:
        return text
    out = _THINK_TAG.sub("", _THINK_BLOCK.sub("", text))
    marks = list(_FINAL_MARK.finditer(out))
    if marks:
        tail = out[marks[-1].end():]
        first, _, rest = tail.partition("\n")
        if not re.search(r"\w", first):
            tail = rest
        if tail.strip():
            out = tail
    return out.strip()


def _no_temperature(model: str) -> bool:
    """Dòng model suy luận của OpenAI (gpt-5*, o*) từ chối `temperature` khác 1 — bỏ tham số cho nó."""
    m = (model or "").lower()
    return m.startswith(("gpt-5", "o1", "o3", "o4"))


class OpenAICompatProvider(Provider):
    name = "openai"
    supports_tools = True
    base_url = OPENAI_URL
    setting_key = "openai_api_key"
    setting_model = "ai_openai_model"
    fallback_model = "gpt-5-mini"
    #  OpenAI mới đòi `max_completion_tokens`; OpenRouter và các hãng khác vẫn nhận `max_tokens`.
    max_tokens_field = "max_completion_tokens"

    @property
    def default_model(self) -> str:
        return app_settings.get(self.setting_model) or self.fallback_model

    def _api_key(self) -> str:
        from app.modules.agent_hub import ai_keys  # import muộn: tránh vòng import

        return ai_keys.company_key(self.name) or (app_settings.get(self.setting_key) or "")

    def is_configured(self) -> bool:
        return bool(self._api_key())

    def _headers(self) -> dict:
        h = {"authorization": f"Bearer {self._api_key()}", "content-type": "application/json"}
        if self.name == "openrouter":
            h["HTTP-Referer"] = "https://erp.degoholding.vn"
            h["X-Title"] = "DEGO ERP Assistant"
        return h

    def _post(self, payload: dict) -> dict:
        try:
            resp = requests.post(f"{self.base_url}/chat/completions", json=payload, headers=self._headers(),
                                 timeout=TIMEOUT)
        except requests.RequestException as e:
            raise ProviderError(f"Lỗi gọi {self.name}: {e}") from e
        if resp.status_code != 200:
            raise ProviderError(f"{self.name} trả lỗi {resp.status_code}: {resp.text[:500]}")
        return resp.json()

    def _payload(self, model: str, msgs: list[dict], system: str | None, max_tokens: int, temperature: float) -> dict:
        #  ai-CR-115: model suy luận (DeepSeek v4, gpt-5, o*…) tính cả phần «nghĩ» vào trần đầu ra — trần 1536 của Trợ lý
        #  cắt cụt câu trả lời giữa chừng (08/10 bot phân tích báo cáo dừng ở «Chi phí 2026: bán hàng 28,6 · QLDN»). Trần
        #  chỉ là mức chặn trên, tiền tính theo token thật dùng, nên nâng sàn lên MIN_OUTPUT_TOKENS.
        payload: dict = {"model": model, "messages": ([{"role": "system", "content": system}] if system else []) + msgs,
                         self.max_tokens_field: max(int(max_tokens or 0), MIN_OUTPUT_TOKENS)}
        if not _no_temperature(model):
            payload["temperature"] = temperature
        return payload

    def _result(self, data: dict, used_model: str, text: str, tool_calls: list[dict], acc: dict) -> ChatResult:
        choices = data.get("choices") or []
        if choices and choices[0].get("finish_reason") == "length" and text:
            text += CUT_NOTE
        return ChatResult(text=text, provider=self.name, model=data.get("model", used_model),
                          input_tokens=acc["input"], output_tokens=acc["output"], thinking_tokens=acc["thinking"],
                          cache_read_tokens=acc["cache_read"], tool_calls=tool_calls, raw=data)

    @staticmethod
    def _accumulate(acc: dict, usage: dict) -> None:
        acc["input"] += int(usage.get("prompt_tokens") or 0)
        acc["output"] += int(usage.get("completion_tokens") or 0)
        acc["thinking"] += int(((usage.get("completion_tokens_details") or {}).get("reasoning_tokens")) or 0)
        acc["cache_read"] += int(((usage.get("prompt_tokens_details") or {}).get("cached_tokens")) or 0)

    @staticmethod
    def _message_of(data: dict) -> dict:
        choices = data.get("choices") or []
        return (choices[0].get("message") or {}) if choices else {}

    def ask(self, messages: list[ChatMessage], *, model: str | None = None, system: str | None = None,
            max_tokens: int = 1024, temperature: float = 0.3, thinking: bool = False,
            cache_system: bool = False) -> ChatResult:
        if not self.is_configured():
            raise ProviderError(f"Chưa có khóa {self.name}.")
        used_model = model or self.default_model
        msgs = [{"role": m.role, "content": _wire_content(m.content)} for m in messages]
        data = self._post(self._payload(used_model, msgs, system, max_tokens, temperature))
        acc = {"input": 0, "output": 0, "thinking": 0, "cache_read": 0}
        self._accumulate(acc, data.get("usage") or {})
        return self._result(data, used_model, clean_reply(str(self._message_of(data).get("content") or "")), [], acc)

    def run_tools(self, messages: list[ChatMessage], *, tools: list[ToolDef], execute: ToolExecutor,
                  model: str | None = None, system: str | None = None, max_tokens: int = 1024,
                  temperature: float = 0.3, thinking: bool = False, cache_system: bool = False,
                  max_iters: int = 6) -> ChatResult:
        if not self.is_configured():
            raise ProviderError(f"Chưa có khóa {self.name}.")
        used_model = model or self.default_model
        msgs: list[dict] = [{"role": m.role, "content": _wire_content(m.content)} for m in messages]
        tool_decl = [{"type": "function", "function": {"name": t.name, "description": t.description,
                                                       "parameters": t.parameters}} for t in tools]
        acc = {"input": 0, "output": 0, "thinking": 0, "cache_read": 0}
        tool_calls: list[dict] = []
        data: dict = {}
        for _ in range(max_iters):
            payload = self._payload(used_model, msgs, system, max_tokens, temperature)
            payload["tools"] = tool_decl
            data = self._post(payload)
            self._accumulate(acc, data.get("usage") or {})
            message = self._message_of(data)
            calls = message.get("tool_calls") or []
            if not calls:
                return self._result(data, used_model, clean_reply(str(message.get("content") or "")), tool_calls, acc)
            #  Vọng lại nguyên lượt assistant (gồm tool_calls) rồi trả kết quả từng tool theo tool_call_id.
            msgs.append({"role": "assistant", "content": message.get("content") or None, "tool_calls": calls})
            for tc in calls:
                fn = tc.get("function") or {}
                fname = str(fn.get("name") or "")
                try:
                    fargs = json.loads(fn.get("arguments") or "{}")
                except ValueError:
                    fargs = {}
                if not isinstance(fargs, dict):
                    fargs = {}
                result = execute(fname, fargs)
                call: dict = {"name": fname, "args": fargs, "rows": _row_count(result)}
                for k in ("draft", "file", "proposal"):
                    if isinstance(result.get(k), dict):
                        call[k] = result[k]
                tool_calls.append(call)
                msgs.append({"role": "tool", "tool_call_id": tc.get("id"),
                             "content": json.dumps(result, ensure_ascii=False)})
        #  Hết vòng: ép một lượt chốt không kèm tool.
        data = self._post(self._payload(used_model, msgs, system, max_tokens, temperature))
        self._accumulate(acc, data.get("usage") or {})
        return self._result(data, used_model, clean_reply(str(self._message_of(data).get("content") or "")), tool_calls, acc)


class OpenRouterProvider(OpenAICompatProvider):
    """Một khóa dùng nhiều hãng; tên model theo OpenRouter, vd `google/gemini-2.5-flash`, `anthropic/claude-sonnet-4.5`."""

    name = "openrouter"
    base_url = OPENROUTER_URL
    setting_key = "openrouter_api_key"
    setting_model = "ai_openrouter_model"
    fallback_model = "google/gemini-2.5-flash"
    max_tokens_field = "max_tokens"


class DeepSeekProvider(OpenAICompatProvider):
    """DeepSeek (ai-CR-107) — API kiểu OpenAI. `deepseek-chat` gọi công cụ được; `deepseek-reasoner` suy luận sâu, không
    nên giao việc cần gọi công cụ ERP."""

    name = "deepseek"
    base_url = "https://api.deepseek.com/v1"
    setting_key = "deepseek_api_key"
    setting_model = "ai_deepseek_model"
    fallback_model = "deepseek-chat"
    max_tokens_field = "max_tokens"


class XaiProvider(OpenAICompatProvider):
    """Grok của xAI (ai-CR-107) — API kiểu OpenAI tại api.x.ai."""

    name = "xai"
    base_url = "https://api.x.ai/v1"
    setting_key = "xai_api_key"
    setting_model = "ai_xai_model"
    fallback_model = "grok-4-fast"
    max_tokens_field = "max_tokens"


def _row_count(result: dict) -> int | None:
    for k in ("total", "count"):
        if isinstance(result.get(k), int):
            return result[k]
    items = result.get("items")
    return len(items) if isinstance(items, list) else None
