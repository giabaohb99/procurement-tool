"""ai-CR-232 — prod 28/10/2026: model Claude đời mới trả 400 «`temperature` is deprecated for this model» → bot Telegram ERP hỏng
mọi lượt luồng nặng. Canh: gặp lỗi đó thì gửi lại MỘT lần không có temperature và nhớ model; lượt sau không gửi temperature nữa;
lỗi 400 khác vẫn báo như cũ; model cũ vẫn nhận temperature."""
import pytest

from app.modules.assistant.provider import claude as claude_mod
from app.modules.assistant.provider.base import ProviderError

OK = {"content": [{"type": "text", "text": "ok"}], "usage": {"input_tokens": 1, "output_tokens": 1}, "stop_reason": "end_turn"}
DEPRECATED = '{"type":"error","error":{"type":"invalid_request_error","message":"`temperature` is deprecated for this model."}}'


class _Resp:
    def __init__(self, status: int, body):
        self.status_code = status
        self._body = body
        self.text = body if isinstance(body, str) else "{}"

    def json(self):
        return self._body


@pytest.fixture
def provider(monkeypatch):
    monkeypatch.setattr(claude_mod, "_NO_TEMPERATURE_MODELS", set())
    p = claude_mod.ClaudeProvider.__new__(claude_mod.ClaudeProvider)
    monkeypatch.setattr(claude_mod.ClaudeProvider, "_headers", lambda self: {})
    return p


def _record(monkeypatch, answers):
    sent = []

    def fake_post(url, json=None, headers=None, timeout=None):
        sent.append(json)
        return answers.pop(0)

    monkeypatch.setattr(claude_mod.requests, "post", fake_post)
    return sent


def test_tu_choi_temperature_thi_gui_lai_mot_lan_va_nho_model(provider, monkeypatch):
    sent = _record(monkeypatch, [_Resp(400, DEPRECATED), _Resp(200, OK), _Resp(200, OK)])
    assert provider._post({"model": "claude-opus-5-5", "temperature": 0.3, "messages": []}) == OK
    assert "temperature" in sent[0] and "temperature" not in sent[1]
    provider._post({"model": "claude-opus-5-5", "temperature": 0.3, "messages": []})
    assert "temperature" not in sent[2], "lượt sau không phí một lượt gọi hỏng"
    assert len(sent) == 3


def test_loi_400_khac_van_bao_loi_khong_gui_lai(provider, monkeypatch):
    sent = _record(monkeypatch, [_Resp(400, '{"error":{"message":"max_tokens: too large"}}')])
    with pytest.raises(ProviderError, match="400"):
        provider._post({"model": "claude-sonnet-5", "temperature": 0.3, "messages": []})
    assert len(sent) == 1


def test_model_cu_van_giu_temperature(provider, monkeypatch):
    sent = _record(monkeypatch, [_Resp(200, OK)])
    provider._post({"model": "claude-haiku-4-5", "temperature": 0.3, "messages": []})
    assert sent[0]["temperature"] == 0.3
