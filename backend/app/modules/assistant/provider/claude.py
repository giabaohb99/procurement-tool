"""Adapter Claude (Anthropic Messages API) qua REST.

Dùng `requests` cho gọn, không thêm SDK. Hỗ trợ cả hỏi thường (Phase 1) lẫn tool-calling
loại A (Phase 2) qua khối `tool_use` / `tool_result` chuẩn của Messages API.
"""
import json

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

API_URL = "https://api.anthropic.com/v1/messages"
API_VERSION = "2023-06-01"
TIMEOUT = 60


class ClaudeProvider(Provider):
    name = "claude"
    default_model = settings.AI_CLAUDE_MODEL or "claude-sonnet-5"
    supports_tools = True

    def is_configured(self) -> bool:
        return bool(settings.ANTHROPIC_API_KEY)

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
        if not self.is_configured():
            raise ProviderError("Chưa cấu hình ANTHROPIC_API_KEY")

        used_model = model or self.default_model
        payload: dict = {
            "model": used_model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            # Anthropic chỉ nhận role user/assistant; system truyền riêng.
            "messages": [{"role": m.role, "content": m.content} for m in messages],
        }
        if system:
            if cache_system:
                # Khối system dạng block + cache_control -> Anthropic cache prefix này; lượt sau
                # (cùng gói tri thức) chỉ tính tiền cache_read, rẻ ~90%.
                payload["system"] = [{
                    "type": "text",
                    "text": system,
                    "cache_control": {"type": "ephemeral"},
                }]
            else:
                payload["system"] = system
        # Ghi chú: bật extended thinking cho Claude là chuyện của P2 (đổi model + thinking config).
        # Phase 1 chưa bật để giữ chi phí thấp và tránh khác biệt định dạng giữa các model.

        headers = {
            "x-api-key": settings.ANTHROPIC_API_KEY,
            "anthropic-version": API_VERSION,
            "content-type": "application/json",
        }
        try:
            resp = requests.post(API_URL, json=payload, headers=headers, timeout=TIMEOUT)
        except requests.RequestException as e:
            raise ProviderError(f"Lỗi gọi Claude: {e}") from e

        if resp.status_code != 200:
            raise ProviderError(f"Claude trả lỗi {resp.status_code}: {resp.text[:500]}")

        data = resp.json()
        text = "".join(
            b.get("text", "") for b in data.get("content", []) if b.get("type") == "text"
        )
        usage = data.get("usage", {})
        return ChatResult(
            text=text,
            provider=self.name,
            model=data.get("model", used_model),
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
            cache_write_tokens=usage.get("cache_creation_input_tokens", 0),
            cache_read_tokens=usage.get("cache_read_input_tokens", 0),
            raw=data,
        )

    # ── Hạ tầng dùng chung ────────────────────────────────────────────────────────────
    @staticmethod
    def _headers() -> dict:
        return {
            "x-api-key": settings.ANTHROPIC_API_KEY,
            "anthropic-version": API_VERSION,
            "content-type": "application/json",
        }

    @staticmethod
    def _system_field(system: str | None, cache_system: bool):
        if not system:
            return None
        if cache_system:
            return [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}]
        return system

    def _post(self, payload: dict) -> dict:
        try:
            resp = requests.post(API_URL, json=payload, headers=self._headers(), timeout=TIMEOUT)
        except requests.RequestException as e:
            raise ProviderError(f"Lỗi gọi Claude: {e}") from e
        if resp.status_code != 200:
            raise ProviderError(f"Claude trả lỗi {resp.status_code}: {resp.text[:500]}")
        return resp.json()

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
            raise ProviderError("Chưa cấu hình ANTHROPIC_API_KEY")
        used_model = model or self.default_model
        msgs: list[dict] = [{"role": m.role, "content": m.content} for m in messages]
        tool_decl = [
            {"name": t.name, "description": t.description, "input_schema": t.parameters}
            for t in tools
        ]
        system_field = self._system_field(system, cache_system)
        acc = {"input": 0, "output": 0, "cache_write": 0, "cache_read": 0}
        tool_calls: list[dict] = []
        data: dict = {}

        for _ in range(max_iters):
            payload: dict = {
                "model": used_model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": msgs,
                "tools": tool_decl,
            }
            if system_field is not None:
                payload["system"] = system_field
            data = self._post(payload)
            _accumulate(acc, data.get("usage", {}))
            blocks = data.get("content", [])
            tool_uses = [b for b in blocks if b.get("type") == "tool_use"]
            if data.get("stop_reason") != "tool_use" or not tool_uses:
                return self._tool_result(data, used_model, blocks, tool_calls, acc)

            # Vọng lại nguyên lượt assistant (gồm tool_use) rồi trả tool_result cho từng khối.
            msgs.append({"role": "assistant", "content": blocks})
            results = []
            for tu in tool_uses:
                fname = tu.get("name", "")
                fargs = dict(tu.get("input") or {})
                result = execute(fname, fargs)
                tool_calls.append({"name": fname, "args": fargs, "rows": _row_count(result)})
                results.append({
                    "type": "tool_result",
                    "tool_use_id": tu.get("id"),
                    "content": json.dumps(result, ensure_ascii=False),
                })
            msgs.append({"role": "user", "content": results})

        # Hết vòng: ép một lượt CHỐT không kèm tool để lấy câu chữ.
        final_payload: dict = {
            "model": used_model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": msgs,
        }
        if system_field is not None:
            final_payload["system"] = system_field
        data = self._post(final_payload)
        _accumulate(acc, data.get("usage", {}))
        return self._tool_result(data, used_model, data.get("content", []), tool_calls, acc)

    def _tool_result(self, data: dict, used_model: str, blocks: list, tool_calls: list[dict],
                     acc: dict) -> ChatResult:
        text = "".join(b.get("text", "") for b in blocks if b.get("type") == "text")
        return ChatResult(
            text=text,
            provider=self.name,
            model=data.get("model", used_model),
            input_tokens=acc["input"],
            output_tokens=acc["output"],
            cache_write_tokens=acc["cache_write"],
            cache_read_tokens=acc["cache_read"],
            tool_calls=tool_calls,
            raw=data,
        )


def _accumulate(acc: dict, usage: dict) -> None:
    acc["input"] += usage.get("input_tokens", 0)
    acc["output"] += usage.get("output_tokens", 0)
    acc["cache_write"] += usage.get("cache_creation_input_tokens", 0)
    acc["cache_read"] += usage.get("cache_read_input_tokens", 0)


def _row_count(result: dict) -> int | None:
    for k in ("total", "count"):
        if isinstance(result.get(k), int):
            return result[k]
    items = result.get("items")
    return len(items) if isinstance(items, list) else None
