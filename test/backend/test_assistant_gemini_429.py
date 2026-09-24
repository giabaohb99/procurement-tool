"""Gemini 429 — thử lại ĐÚNG MỘT lần, và chỉ khi Google bảo chờ ngắn (ai-CR-008).

Bot Telegram gọi hai lượt sát nhau (phân loại ý định rồi Trợ lý AI); gói miễn phí hay trả
429 kèm `retryDelay` vài giây ở lượt thứ hai. Chờ vài giây rồi gọi lại đỡ được ca đó; còn
"chờ 40 giây" thì báo lỗi ngay — người dùng không ngồi đợi từng ấy.
"""
import pytest

from app.modules.assistant.provider import gemini
from app.modules.assistant.provider.base import ProviderError


class _Resp:
    def __init__(self, status: int, body: dict):
        self.status_code = status
        self._body = body
        self.text = str(body)

    def json(self):
        return self._body


def _429(delay: str | None):
    details = [{"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": delay}] \
        if delay else []
    return _Resp(429, {"error": {"code": 429, "message": "quota", "details": details}})


@pytest.fixture
def khoa(monkeypatch):
    #  Khóa nay đọc từ cấu hình hệ thống (bao-CR-428/429) qua `_api_key` — cài thẳng ở đó.
    monkeypatch.setattr(gemini.GeminiProvider, "_api_key", lambda self: "x")
    ngu: list[float] = []
    monkeypatch.setattr(gemini.time, "sleep", ngu.append)
    return ngu


def _cam(monkeypatch, responses: list):
    goi: list[int] = []

    def post(url, json, headers, timeout):
        goi.append(1)
        return responses.pop(0)

    monkeypatch.setattr(gemini.requests, "post", post)
    return goi


def test_429_bao_cho_ngan_thi_thu_lai_mot_lan(monkeypatch, khoa):
    goi = _cam(monkeypatch, [_429("2s"), _Resp(200, {"candidates": []})])
    assert gemini.GeminiProvider()._post("m", {}) == {"candidates": []}
    assert len(goi) == 2
    assert khoa == [2.0]


def test_429_bao_cho_lau_thi_bao_loi_ngay(monkeypatch, khoa):
    goi = _cam(monkeypatch, [_429("40s"), _Resp(200, {})])
    with pytest.raises(ProviderError, match="429"):
        gemini.GeminiProvider()._post("m", {})
    assert len(goi) == 1
    assert khoa == []


def test_429_hai_lan_lien_thi_thoi(monkeypatch, khoa):
    """Thử lại một lần là hết — không tự xoay vòng đốt thêm hạn mức."""
    goi = _cam(monkeypatch, [_429("1s"), _429("1s"), _Resp(200, {})])
    with pytest.raises(ProviderError, match="429"):
        gemini.GeminiProvider()._post("m", {})
    assert len(goi) == 2


def test_429_khong_noi_cho_bao_lau_thi_khong_doan(monkeypatch, khoa):
    goi = _cam(monkeypatch, [_429(None), _Resp(200, {})])
    with pytest.raises(ProviderError):
        gemini.GeminiProvider()._post("m", {})
    assert len(goi) == 1
