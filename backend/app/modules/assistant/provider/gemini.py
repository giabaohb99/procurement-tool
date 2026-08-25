"""Adapter Gemini (Google Generative Language API) qua REST.

Cùng khuôn với Claude nhưng khác định dạng: role 'assistant' -> 'model', system truyền qua
`systemInstruction`, token suy nghĩ ở `usageMetadata.thoughtsTokenCount`.

Tắt "suy nghĩ" để tiết kiệm cho câu tra cứu đơn giản, NHƯNG chỉ dòng 2.x nhận
`thinkingConfig.thinkingBudget = 0`; dòng 3.x TỪ CHỐI giá trị 0 (trả 400). Với 3.x thì bỏ
qua cờ này — flash-lite 3.x vốn gần như không suy nghĩ nên chi phí đã thấp.
"""
import requests

from app.core.config import settings

from .base import (
    ChatMessage,
    ChatResult,
    Provider,
    ProviderError,
    ToolDef,
    ToolExecutor,
)

BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
TIMEOUT = 60


def _accepts_budget_zero(model: str) -> bool:
    """Chỉ dòng Gemini 2.x nhận thinkingBudget=0; 3.x trả 400 nếu gửi 0."""
    return model.startswith("gemini-2.")


class GeminiProvider(Provider):
    name = "gemini"
    default_model = settings.AI_GEMINI_MODEL or "gemini-flash-latest"
    supports_tools = True

    def is_configured(self) -> bool:
        return bool(settings.GEMINI_API_KEY)

    # ── Hạ tầng dùng chung ────────────────────────────────────────────────────────────
    def _gen_config(self, model: str, max_tokens: int, temperature: float, thinking: bool) -> dict:
        cfg: dict = {"temperature": temperature, "maxOutputTokens": max_tokens}
        if not thinking and _accepts_budget_zero(model):
            cfg["thinkingConfig"] = {"thinkingBudget": 0}
        return cfg

    def _post(self, model: str, payload: dict) -> dict:
        headers = {
            "content-type": "application/json",
            "x-goog-api-key": settings.GEMINI_API_KEY,
        }
        url = BASE_URL.format(model=model)
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=TIMEOUT)
        except requests.RequestException as e:
            raise ProviderError(f"Lỗi gọi Gemini: {e}") from e
        if resp.status_code != 200:
            raise ProviderError(f"Gemini trả lỗi {resp.status_code}: {resp.text[:500]}")
        return resp.json()

    @staticmethod
    def _contents(messages: list[ChatMessage]) -> list[dict]:
        # Gemini dùng role 'user'/'model'; map 'assistant' -> 'model'.
        return [
            {"role": "model" if m.role == "assistant" else "user",
             "parts": [{"text": m.content}]}
            for m in messages
        ]

    @staticmethod
    def _text_of(candidate: dict) -> str:
        parts = candidate.get("content", {}).get("parts", [])
        return "".join(p.get("text", "") for p in parts if "text" in p)

    def _result(self, data: dict, used_model: str, text: str, tool_calls: list[dict],
                acc: dict) -> ChatResult:
        return ChatResult(
            text=text,
            provider=self.name,
            model=data.get("modelVersion", used_model),
            input_tokens=acc["input"],
            output_tokens=acc["output"],
            thinking_tokens=acc["thinking"],
            cache_read_tokens=acc["cache_read"],
            tool_calls=tool_calls,
            raw=data,
        )

    @staticmethod
    def _accumulate(acc: dict, usage: dict) -> None:
        acc["input"] += usage.get("promptTokenCount", 0)
        acc["output"] += usage.get("candidatesTokenCount", 0)
        acc["thinking"] += usage.get("thoughtsTokenCount", 0)
        acc["cache_read"] += usage.get("cachedContentTokenCount", 0)

    # ── Hỏi thường (Phase 1) ──────────────────────────────────────────────────────────
    def ask(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        system: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.3,
        thinking: bool = False,
        cache_system: bool = False,
    ) -> ChatResult:
        # cache_system: Gemini 2.5+ tự cache ngầm phần prefix lặp lại (gồm systemInstruction),
        # không cần đánh dấu như Claude, nên ở đây bỏ qua cờ này.
        if not self.is_configured():
            raise ProviderError("Chưa cấu hình GEMINI_API_KEY")
        used_model = model or self.default_model
        payload: dict = {
            "contents": self._contents(messages),
            "generationConfig": self._gen_config(used_model, max_tokens, temperature, thinking),
        }
        if system:
            payload["systemInstruction"] = {"parts": [{"text": system}]}
        data = self._post(used_model, payload)
        acc = {"input": 0, "output": 0, "thinking": 0, "cache_read": 0}
        self._accumulate(acc, data.get("usageMetadata", {}))
        candidates = data.get("candidates", [])
        text = self._text_of(candidates[0]) if candidates else ""
        return self._result(data, used_model, text, [], acc)

    # ── Vòng lặp tool-calling (Phase 2, loại A) ───────────────────────────────────────
    def run_tools(
        self,
        messages: list[ChatMessage],
        *,
        tools: list[ToolDef],
        execute: ToolExecutor,
        model: str | None = None,
        system: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.3,
        thinking: bool = False,
        cache_system: bool = False,
        max_iters: int = 6,
    ) -> ChatResult:
        if not self.is_configured():
            raise ProviderError("Chưa cấu hình GEMINI_API_KEY")
        used_model = model or self.default_model
        contents = self._contents(messages)
        tool_decl = [{"functionDeclarations": [
            {"name": t.name, "description": t.description, "parameters": t.parameters}
            for t in tools
        ]}]
        acc = {"input": 0, "output": 0, "thinking": 0, "cache_read": 0}
        tool_calls: list[dict] = []
        data: dict = {}

        for _ in range(max_iters):
            payload: dict = {
                "contents": contents,
                "generationConfig": self._gen_config(used_model, max_tokens, temperature, thinking),
                "tools": tool_decl,
            }
            if system:
                payload["systemInstruction"] = {"parts": [{"text": system}]}
            data = self._post(used_model, payload)
            self._accumulate(acc, data.get("usageMetadata", {}))
            candidates = data.get("candidates", [])
            if not candidates:
                break
            content = candidates[0].get("content", {}) or {}
            parts = content.get("parts", []) or []
            fcalls = [p["functionCall"] for p in parts if p.get("functionCall")]
            if not fcalls:
                return self._result(data, used_model, self._text_of(candidates[0]), tool_calls, acc)

            # Vọng lại nguyên lượt 'model' (chứa functionCall) rồi trả kết quả tool.
            contents.append({"role": "model", "parts": parts})
            resp_parts = []
            for fc in fcalls:
                fname = fc.get("name", "")
                fargs = dict(fc.get("args") or {})
                result = execute(fname, fargs)
                tool_calls.append({"name": fname, "args": fargs, "rows": _row_count(result)})
                resp_parts.append({"functionResponse": {"name": fname, "response": result}})
            contents.append({"role": "user", "parts": resp_parts})

        # Hết vòng mà model vẫn đòi gọi tool: ép một lượt CHỐT không kèm tool để lấy câu chữ.
        final_payload: dict = {
            "contents": contents,
            "generationConfig": self._gen_config(used_model, max_tokens, temperature, thinking),
        }
        if system:
            final_payload["systemInstruction"] = {"parts": [{"text": system}]}
        data = self._post(used_model, final_payload)
        self._accumulate(acc, data.get("usageMetadata", {}))
        candidates = data.get("candidates", [])
        text = self._text_of(candidates[0]) if candidates else ""
        return self._result(data, used_model, text, tool_calls, acc)


def _row_count(result: dict) -> int | None:
    """Đếm số dòng tool trả (để ghi vết audit). Không có thì None."""
    for k in ("total", "count"):
        if isinstance(result.get(k), int):
            return result[k]
    items = result.get("items")
    return len(items) if isinstance(items, list) else None
