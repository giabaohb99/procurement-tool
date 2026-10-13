"""ai-CR-193 (13/10) — «giá bitcoin hôm nay» mất 31 s vì bot viết nguyên báo cáo; Google Search Gemini 429 nhưng mỗi lượt vẫn
thử. Nay: câu tra nhanh → bản ngắn (≤ 600 token ra, không nhóm La Mã), 429 → bỏ qua Google Search 10 phút."""
import time

from app.modules.agent_hub import research as rs


def test_nhan_cau_tra_nhanh():
    """ai-CR-194: đường tắt chỉ cho thứ chắc chắn NGOÀI ERP (tỷ giá, vàng, xăng, crypto, thời tiết, lãi suất, chứng khoán)."""
    for q in ("giá vàng hôm nay", "Giá bitcoin hôm nay", "tỷ giá USD hiện nay", "thời tiết Cần Thơ", "cho anh hỏi giá xăng hôm nay",
              "lãi suất ngân hàng tháng này bao nhiêu"):
        assert rs.is_quick(q), q
    for q in ("giá vàng hôm nay, phân tích xu hướng tuần tới", "giá thép chi tiết theo từng nhà máy", "vì sao giá vàng tăng",
              "tìm hiểu giúp anh thuế nhập khẩu thép năm nay", "so sánh giá xăng Việt Nam và Thái Lan", "Giá thép Hòa Phát",
              "giá thép hôm nay", "công nợ Hòa Phát"):
        assert not rs.is_quick(q), q
    #  Bản ngắn chỉ khi người dùng xin (đại ca 13/10 16:55: bản dài là mặc định).
    assert rs.wants_brief("giá vàng hôm nay, nhanh thôi") and rs.wants_brief("ngắn gọn giúp anh tỷ giá usd")
    assert not rs.wants_brief("giá vàng hôm nay")


def test_tra_nhanh_dung_loi_dan_ngan_va_tran_token(monkeypatch):
    from app.modules.agent_hub import manager, web_search
    from app.modules.assistant.provider.base import ChatResult

    seen: list[dict] = []

    class P:
        name = "p"

        def ask(self, messages, **kw):
            seen.append(kw)
            return ChatResult(text="**2.600 USD**", provider="p", model="m")

    monkeypatch.setattr(manager, "get_provider", lambda: P())
    monkeypatch.setattr(web_search, "gather", lambda q: ([{"title": "t", "url": "https://x.vn"}], "[1] giá 2.600"))
    rs.search_web_any("giá vàng hôm nay, nhanh thôi")
    assert seen[-1]["max_tokens"] == rs.QUICK_MAX_TOKENS and "TRẢ LỜI NGẮN" in seen[-1]["system"] and "La Mã" in seen[-1]["system"]
    rs.search_web_any("giá vàng hôm nay")                      # mặc định: bản đầy đủ như trước ai-CR-193
    assert seen[-1]["max_tokens"] == 1500 and "TRẢ LỜI NGẮN" not in seen[-1]["system"]


def _raise(msg):
    raise RuntimeError(msg)


def test_google_search_429_thi_bo_qua_10_phut(monkeypatch):
    from app.modules.agent_hub import user_keys
    from app.modules.assistant.provider.base import ChatResult

    monkeypatch.setattr(user_keys, "gemini_key", lambda: "AIza")
    calls: list[str] = []
    ok = ("ok", [], ChatResult(text="ok", provider="p", model="m"))
    monkeypatch.setattr(rs, "search_web", lambda q, *, mode: (calls.append("google"), _raise("Gemini trả lỗi 429: You exceeded your current quota")))
    monkeypatch.setattr(rs, "search_web_any", lambda q, *, mode: (calls.append("web"), ok)[1])
    rs._search_blocked_until = 0.0
    assert rs.run("giá vàng hôm nay", rs.MODE_WEB)[0] == "ok" and calls == ["google", "web"]
    assert rs._search_blocked_until > time.time() + 500
    assert rs.run("giá bạc hôm nay", rs.MODE_WEB)[0] == "ok" and calls == ["google", "web", "web"]      # không thử Google nữa
    rs._search_blocked_until = 0.0
    monkeypatch.setattr(rs, "search_web", lambda q, *, mode: (calls.append("google"), _raise("503 high demand")))
    rs.run("giá vàng", rs.MODE_WEB)
    assert rs._search_blocked_until == 0.0                   # lỗi tạm khác không chặn
