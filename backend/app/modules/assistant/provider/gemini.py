"""Adapter Gemini (Google Generative Language API) qua REST.

Cùng khuôn với Claude nhưng khác định dạng: role 'assistant' -> 'model', system truyền qua
`systemInstruction`, token suy nghĩ ở `usageMetadata.thoughtsTokenCount`.

Tắt "suy nghĩ" để tiết kiệm cho câu tra cứu đơn giản, NHƯNG chỉ dòng 2.x nhận
`thinkingConfig.thinkingBudget = 0`; dòng 3.x TỪ CHỐI giá trị 0 (trả 400). Với 3.x thì bỏ
qua cờ này — flash-lite 3.x vốn gần như không suy nghĩ nên chi phí đã thấp.
"""
import re
import time

import requests

from app.core import app_settings

from .base import (
    ChatMessage,
    ChatResult,
    Provider,
    ProviderError,
    ToolDef,
    ToolExecutor,
)

NO_KEY_MSG = (
    "Chưa cấu hình Gemini API Key — vào Quản trị > Cấu hình hệ thống, thẻ Trợ lý AI để dán key."
)
BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
TIMEOUT = 60
#  Gemini trả 429 kèm `retryDelay` (vd "7s"). Thử lại ĐÚNG MỘT lần và chỉ khi Google bảo
#  chờ không quá chừng này giây — đợi lâu hơn thì người dùng đã bỏ đi, thà báo lỗi ngay.
#  Hạn mức theo phút của gói miễn phí thường bảo chờ 20-50 giây, tức KHÔNG thử lại; lớp này
#  chỉ đỡ ca hai lượt gọi sát nhau (bot Telegram: phân loại ý định rồi Trợ lý AI).
RETRY_429_MAX_WAIT = 10
_RETRY_DELAY = re.compile(r"(\d+(?:\.\d+)?)s")


def _retry_after_seconds(resp) -> float | None:
    """Số giây Gemini bảo chờ trong thân lỗi 429, không đọc được thì None."""
    try:
        details = resp.json().get("error", {}).get("details", [])
    except ValueError:
        return None
    for d in details:
        m = _RETRY_DELAY.fullmatch(str(d.get("retryDelay", "")))
        if m:
            return float(m.group(1))
    return None


def _gemini_schema(schema):
    """Dọn lược đồ tham số tool cho vừa khuôn OpenAPI rút gọn của Gemini.

    Gemini chỉ nhận `enum` là danh sách CHUỖI (kèm type STRING). Tool nào khai bộ mã SỐ —
    ví dụ `my_leave_summary.status` theo luật R2/QĐ-11 — thì Gemini trả 400 và HỎNG CẢ LƯỢT
    hỏi, không riêng tool đó. Giữ nguyên `type: integer` để tầng chạy tool vẫn nhận số, chỉ
    bỏ `enum` và nói danh sách giá trị cho phép bằng lời trong mô tả.
    """
    if not isinstance(schema, dict):
        return schema
    out = {k: v for k, v in schema.items()}
    values = out.get("enum")
    if isinstance(values, list) and any(not isinstance(v, str) for v in values):
        out.pop("enum")
        allowed = " | ".join(str(v) for v in values)
        desc = out.get("description") or ""
        out["description"] = f"{desc} Giá trị cho phép: {allowed}.".strip()
    props = out.get("properties")
    if isinstance(props, dict):
        out["properties"] = {k: _gemini_schema(v) for k, v in props.items()}
    if isinstance(out.get("items"), dict):
        out["items"] = _gemini_schema(out["items"])
    return out


def _accepts_budget_zero(model: str) -> bool:
    """Chỉ dòng Gemini 2.x nhận thinkingBudget=0; 3.x trả 400 nếu gửi 0."""
    return model.startswith("gemini-2.")


class GeminiProvider(Provider):
    name = "gemini"
    supports_tools = True

    @property
    def default_model(self) -> str:
        #  Property chứ không phải thuộc tính lớp — xem lời giải ở `claude.py`.
        return app_settings.get("ai_gemini_model") or "gemini-flash-latest"

    def _api_key(self) -> str:
        """Khóa dùng cho lượt gọi này. Tách thành hàm để lớp con đổi được nguồn khóa —
        Agent Hub chạy khóa RIÊNG (`AGENT_GEMINI_API_KEY`) chứ không tiêu chung hạn mức
        với Trợ lý AI, xem `agent_hub/manager.py`. Trợ lý AI đọc khóa từ cấu hình hệ thống
        (`tab_setting`, bao-CR-428/429)."""
        return app_settings.get("gemini_api_key")

    def is_configured(self) -> bool:
        return bool(self._api_key())

    # ── Hạ tầng dùng chung ────────────────────────────────────────────────────────────
    def _gen_config(self, model: str, max_tokens: int, temperature: float, thinking: bool) -> dict:
        cfg: dict = {"temperature": temperature, "maxOutputTokens": max_tokens}
        if not thinking and _accepts_budget_zero(model):
            cfg["thinkingConfig"] = {"thinkingBudget": 0}
        return cfg

    def _post(self, model: str, payload: dict) -> dict:
        headers = {
            "content-type": "application/json",
            "x-goog-api-key": self._api_key(),
        }
        url = BASE_URL.format(model=model)
        resp = self._send(url, payload, headers)
        if resp.status_code == 429:
            wait = _retry_after_seconds(resp)
            if wait is not None and wait <= RETRY_429_MAX_WAIT:
                time.sleep(wait)
                resp = self._send(url, payload, headers)
        if resp.status_code != 200:
            raise ProviderError(f"Gemini trả lỗi {resp.status_code}: {resp.text[:500]}")
        return resp.json()

    @staticmethod
    def _send(url: str, payload: dict, headers: dict):
        try:
            return requests.post(url, json=payload, headers=headers, timeout=TIMEOUT)
        except requests.RequestException as e:
            raise ProviderError(f"Lỗi gọi Gemini: {e}") from e

    @staticmethod
    def _parts_of(content) -> list[dict]:
        """Content trung lập (chuỗi hoặc list block — xem ChatMessage) -> parts Gemini.

        Block file (ảnh/PDF) thành `inline_data` base64 — Gemini nhận chung một khuôn
        cho mọi mime, không tách image/document như Claude.
        """
        if isinstance(content, str):
            return [{"text": content}]
        parts: list[dict] = []
        for b in content:
            if b.get("type") == "file":
                parts.append({"inline_data": {
                    "mime_type": b.get("media_type", ""),
                    "data": b.get("data_b64", ""),
                }})
            else:
                parts.append({"text": b.get("text", "")})
        return parts

    @staticmethod
    def _contents(messages: list[ChatMessage]) -> list[dict]:
        # Gemini dùng role 'user'/'model'; map 'assistant' -> 'model'.
        return [
            {"role": "model" if m.role == "assistant" else "user",
             "parts": GeminiProvider._parts_of(m.content)}
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
            raise ProviderError(NO_KEY_MSG)
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
            raise ProviderError(NO_KEY_MSG)
        used_model = model or self.default_model
        contents = self._contents(messages)
        tool_decl = [{"functionDeclarations": [
            {"name": t.name, "description": t.description,
             "parameters": _gemini_schema(t.parameters)}
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
                call: dict = {"name": fname, "args": fargs, "rows": _row_count(result)}
                # Tool soạn nháp trả bản draft ĐÃ CHUẨN HÓA (vd "cái" -> "Cái" khớp danh mục
                # ĐVT) — FE phải dùng bản này thay vì args thô model gõ vào.
                if isinstance(result.get("draft"), dict):
                    call["draft"] = result["draft"]
                # Tool xuất file trả metadata file đã tạo — FE dựng nút "Tải báo cáo" từ đây.
                if isinstance(result.get("file"), dict):
                    call["file"] = result["file"]
                # Tool đề xuất sửa phiếu (CR-218) trả khối proposal — FE dựng thẻ so sánh
                # cũ/mới + nút 'Xác nhận sửa' (token nằm trong khối này).
                if isinstance(result.get("proposal"), dict):
                    call["proposal"] = result["proposal"]
                tool_calls.append(call)
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
