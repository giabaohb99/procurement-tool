"""ai-CR-179 (phase 23.3) — ĐIỂM BÁO theo chủ đề: kiểu con của bản tin chủ đề (`sub_code == "news"`), tạo qua tool
`manage_briefs` (add_news, hoặc add_topic với câu xin tin tức); tới giờ tìm tin mới trên web, bỏ trùng URL / tiêu đề với
tin đã gửi 7 ngày, tối đa 5 tin / chủ đề, đánh dấu `[nd:…]` vào sổ; không khóa AI vẫn gửi bản thô; bản tin chủ đề
thường vẫn chạy qua Trợ lý như cũ. Không bài nào ra mạng (chặn `requests`)."""
from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest

from app.modules.agent_hub import brief_subs as bs
from app.modules.agent_hub import news_digest as nd
from app.modules.agent_hub import web_search
from app.modules.agent_hub.timeutil import LOCAL_OFFSET

MONDAY_0732 = datetime(2026, 10, 12, 7, 32)


def _utc(local: datetime) -> datetime:
    return local - LOCAL_OFFSET


def _link(db, user_id: int, chat_id: str, notify_mode: int = 1):
    from app.modules.agent_hub.model import AgentChatLink

    db.add(AgentChatLink(user_id=user_id, chat_id=chat_id, linked_at=datetime.now(), notify_mode=notify_mode,
                         expires_at=datetime.now() + timedelta(days=30), created_by=0, updated_by=0))
    db.commit()


@pytest.fixture(autouse=True)
def _chan_mang(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("bài kiểm không được ra mạng")

    monkeypatch.setattr(web_search.requests, "get", boom)
    monkeypatch.setattr(web_search.requests, "post", boom)


@pytest.fixture
def sent(db, monkeypatch):
    """`service.reply` giả: ghi sổ như thật (để mã [nd:…] đọc lại được), gom chữ đã gửi. Trợ lý AI giả cho bản tin thường."""
    from app.modules.agent_hub import service, user_keys
    from app.modules.agent_hub.constants import DIR_OUT

    out: list[tuple[str, str]] = []

    def fake_reply(db_, chat_id, text, **kw):
        out.append((chat_id, text))
        row = service.log_message(db_, DIR_OUT, chat_id, 0, text, action=kw.get("action", ""))
        row.created_at = datetime.now()
        return row

    monkeypatch.setattr(service, "reply", fake_reply)
    asked: list[tuple[str, str]] = []
    monkeypatch.setattr(service, "answer_question", lambda db_, chat_id, q, **kw: asked.append((chat_id, q)))
    monkeypatch.setattr(user_keys, "active_key", lambda: "")          # mặc định: KHÔNG có khóa AI
    return out, asked


def _fake_search(calls: list[str], day: str = "12/10/2026"):
    """Máy tìm giả: «giá thép» ra 8 tin (1 trùng URL khác utm, 1 trùng tiêu đề, 1 tin cũ 5 ngày), «phân bón» ra 1 tin."""
    def search(q, limit=8, **kw):
        calls.append(q)
        if q.startswith("giá thép"):
            items = [
                {"title": "Giá thép hôm nay 12/10: tăng 200 đồng/kg", "url": "https://vnexpress.net/gia-thep-12-10.html",
                 "snippet": f"{day} · Giá thép xây dựng trong nước tăng 200 đồng/kg tại miền Bắc."},
                {"title": "Giá thép hôm nay 12/10: tăng 200 đồng/kg - VnExpress",
                 "url": "https://www.vnexpress.net/gia-thep-12-10.html?utm_source=zalo", "snippet": "trùng URL"},
                {"title": "Giá thép hôm nay 12/10 tăng 200 đồng/kg | CafeF", "url": "https://cafef.vn/gia-thep-tang.chn",
                 "snippet": "3 giờ trước · Thép tăng giá"},                                    # trùng tiêu đề
                {"title": "Hòa Phát báo lãi quý III", "url": "https://cafef.vn/hoa-phat-lai.chn",
                 "snippet": "5 ngày trước · Hòa Phát công bố kết quả kinh doanh"},            # cũ → bỏ
                {"title": "Thép Trung Quốc giảm giá", "url": "https://tuoitre.vn/thep-tq.htm",
                 "snippet": f"{day} · Giá thép Trung Quốc giảm 1,5%"},
                {"title": "Steel prices rise in Asia", "url": "https://reuters.com/steel-asia",
                 "snippet": "Oct 12, 2026 — Asian steel prices rose"},
                {"title": "Nhu cầu thép xây dựng cuối năm", "url": "https://baodautu.vn/nhu-cau-thep.html",
                 "snippet": "Hôm nay · Nhu cầu thép tăng trở lại"},
                {"title": "Thép cuộn cán nóng tăng nhẹ", "url": "https://vneconomy.vn/hrc.htm",
                 "snippet": "Giá HRC tăng nhẹ"},                                                 # không ghi ngày → giữ
                {"title": "Thị trường thép tuần qua", "url": "https://congthuong.vn/thep-tuan.html",
                 "snippet": "1 ngày trước · Tổng hợp thị trường thép"},
            ]
            return items[:limit]
        if q.startswith("phân bón"):
            return [{"title": "Giá phân urê tăng", "url": "https://nongnghiep.vn/ure-tang.html",
                     "snippet": f"{day} · Giá urê tăng 300 đồng/kg"}]
        return []
    return search


# ── Nhận diện + chuẩn hóa (không cần DB) ──────────────────────────────────────────────────
def test_nhan_dien_cau_xin_diem_bao():
    assert nd.detect_topics("mỗi sáng gửi anh tin giá thép, phân bón") == "giá thép, phân bón"
    assert nd.detect_topics("điểm báo về tỷ giá USD và giá xăng lúc 7h") == "tỷ giá USD, giá xăng"
    assert nd.detect_topics("tin tức ngành phân bón hằng ngày") == "ngành phân bón"
    assert nd.detect_topics("sáng thứ hai gửi anh tin tức thị trường cà phê") == "thị trường cà phê"
    assert nd.detect_topics("báo về thị trường thép") == "thị trường thép"
    assert nd.detect_topics("Điểm báo giá thép, phân bón, tỷ giá USD/VND") == "giá thép, phân bón, tỷ giá USD/VND"
    #  Câu hỏi nghiệp vụ / từ khóa không đứng đầu → không phải điểm báo.
    assert nd.detect_topics("công nợ quá hạn của DEGO") == ""
    assert nd.detect_topics("báo cáo mua hàng tuần") == ""
    assert nd.detect_topics("công nợ quá hạn tin tức") == ""
    assert nd.detect_topics("thông tin NCC Hòa Phát") == ""
    assert nd.parse_topics("a, b và c; a") == ["a", "b", "c"]
    assert len(nd.parse_topics(", ".join(f"t{i}" for i in range(9)))) == nd.MAX_TOPICS


def test_chuan_hoa_url_tieu_de_va_tuoi_tin():
    a = "https://www.VnExpress.net/kinh-doanh/gia-thep.html?utm_source=x&fbclid=1#top"
    b = "http://vnexpress.net/kinh-doanh/gia-thep.html/"
    assert nd.norm_url(a) == nd.norm_url(b) == "vnexpress.net/kinh-doanh/gia-thep.html"
    assert nd.url_hash(a) == nd.url_hash(b) and len(nd.url_hash(a)) == 12
    assert nd.norm_url("https://m.cafef.vn/x.chn?id=2&utm_medium=y") == "cafef.vn/x.chn?id=2"
    assert nd.similar_title("Giá thép hôm nay 12/10: tăng 200 đồng/kg - VnExpress",
                            "Giá thép hôm nay 12/10 tăng 200 đồng/kg | CafeF")
    assert not nd.similar_title("Giá thép tăng", "Giá phân bón giảm")
    now = datetime(2026, 10, 12, 7, 30)
    assert nd.age_hours({"snippet": "3 giờ trước · x", "title": "", "url": ""}, now) == 3
    assert nd.age_hours({"snippet": "Ngày 07/10/2026 giá", "title": "", "url": ""}, now) == 120.0
    assert nd.age_hours({"snippet": "", "title": "", "url": "https://a.vn/2026/10/12/bai"}, now) == 0.0
    assert nd.age_hours({"snippet": "Oct 11, 2026 — steel", "title": "", "url": ""}, now) == 24.0
    assert nd.age_hours({"snippet": "không có ngày", "title": "", "url": ""}, now) is None


# ── Tạo điểm báo qua tool manage_briefs ───────────────────────────────────────────────────
def test_tao_diem_bao_qua_tool_va_tu_nhan_dien_tu_add_topic(db, seed):
    from app.modules.assistant.tools.base import ToolContext
    from app.modules.assistant.tools.brief_tool import MANAGE_BRIEFS_SPEC

    uid = seed.u_req_id
    ctx = ToolContext(db=db, user=SimpleNamespace(id=uid))
    out = MANAGE_BRIEFS_SPEC.handler(ctx, {"action": "add_news", "topics": ["giá thép", "phân bón"], "time": "7h30",
                                           "days": ["ngày thường"]})
    news = [b for b in out["briefs"] if b.get("news")]
    assert len(news) == 1 and news[0]["sub_code"] == nd.NEWS_CODE and news[0]["topic"] == "giá thép, phân bón"
    assert news[0]["label"] == "Điểm báo" and (news[0]["hour"], news[0]["minute"], news[0]["days"]) == (7, 30, 31)

    #  add_topic với câu xin tin tức → tự thành điểm báo; câu nghiệp vụ → bản tin chủ đề thường (sub_code rỗng).
    out = MANAGE_BRIEFS_SPEC.handler(ctx, {"action": "add_topic", "question": "mỗi sáng gửi anh tin tỷ giá USD"})
    out = MANAGE_BRIEFS_SPEC.handler(ctx, {"action": "add_topic", "question": "công nợ quá hạn của DEGO"})
    topics = [b for b in out["briefs"] if b["kind"] == bs.Kind.TOPIC]
    assert [(b["topic"], b["sub_code"]) for b in topics] == [("giá thép, phân bón", "news"), ("tỷ giá USD", "news"),
                                                              ("công nợ quá hạn của DEGO", "")]
    assert "error" in MANAGE_BRIEFS_SPEC.handler(ctx, {"action": "add_news", "topics": []})
    assert "add_news" in MANAGE_BRIEFS_SPEC.parameters["properties"]["action"]["enum"]
    assert "Điểm báo" in bs.render_list(db, uid) and "giá thép, phân bón" in bs.render_list(db, uid)


# ── Gửi điểm báo ───────────────────────────────────────────────────────────────────────────
def test_gui_diem_bao_bo_trung_toi_da_5_tin_danh_dau_va_khong_lap_lan_sau(db, seed, sent, monkeypatch):
    from app.modules.agent_hub.model import AgentMessage

    out, asked = sent
    uid = seed.u_req_id
    _link(db, uid, "777")
    calls: list[str] = []
    monkeypatch.setattr(web_search, "search", _fake_search(calls))
    row = bs.add_news(db, uid, "giá thép, phân bón", hour=7, minute=30)

    assert bs.tick(db, now=_utc(MONDAY_0732)) == {"sent": 1, "failed": 0}
    assert asked == [], "điểm báo không chạy qua Trợ lý"
    assert calls == ["giá thép tin tức", "phân bón tin tức"]
    chat, text = out[-1]
    assert chat == "777" and text.startswith("<b>Điểm báo 12/10/2026</b>")
    assert "<b>giá thép</b>" in text and "<b>phân bón</b>" in text
    assert text.count('<a href="') == 6, "5 tin giá thép (trần) + 1 tin phân bón"
    assert "utm_source" not in text and "CafeF" not in text, "trùng URL / trùng tiêu đề bị bỏ"
    assert "Hòa Phát báo lãi" not in text, "tin 5 ngày trước bị bỏ"
    #  Xếp hạng: báo Việt có ngày → báo Việt không ghi ngày → nước ngoài; trần 5 nên Reuters (hạng cuối) bị cắt.
    assert text.index("vnexpress.net") < text.index("vneconomy.vn") and "reuters.com" not in text
    assert "Giá thép xây dựng trong nước tăng 200" in text, "không khóa AI: dùng đoạn trích thô"
    assert "«" not in text and "»" not in text

    body = db.query(AgentMessage).filter(AgentMessage.chat_id == "777").order_by(AgentMessage.id.desc()).first().body
    assert body.count("[nd:") == 6 and body.count("[nt:") == 6
    assert nd.url_hash("https://vnexpress.net/gia-thep-12-10.html") in body
    assert db.get(type(row), row.id).last_sent_on == "2026-10-12"

    #  Hôm sau: cùng kết quả tìm → mọi tin đã gửi bị bỏ; chỉ Reuters (hôm qua bị cắt bởi trần 5, còn trong 24 giờ) được
    #  gửi; phân bón không có tin mới → một dòng báo trống.
    calls.clear()
    monkeypatch.setattr(web_search, "search", _fake_search(calls, day="13/10/2026"))
    assert bs.tick(db, now=_utc(MONDAY_0732 + timedelta(days=1)))["sent"] == 1
    text2 = out[-1][1]
    assert text2.count('<a href="') == 1 and "Steel prices rise in Asia" in text2
    assert "Không có tin mới về phân bón trong 24 giờ qua" in text2
    assert bs.tick(db, now=_utc(MONDAY_0732 + timedelta(days=1, minutes=20)))["sent"] == 0    # mỗi ngày một lần


def test_co_khoa_ai_thi_mot_luot_model_tom_ca_diem_bao(db, seed, sent, monkeypatch):
    from app.modules.agent_hub import manager, user_keys
    from app.modules.assistant.provider.base import ChatResult

    out, _ = sent
    uid = seed.u_req_id
    _link(db, uid, "777")
    monkeypatch.setattr(web_search, "search", _fake_search([]))
    monkeypatch.setattr(user_keys, "active_key", lambda: "k")
    prompts: list[str] = []

    class FakeProvider:
        name = "agent_gemini"

        def ask(self, messages, **kw):
            prompts.append(messages[0].content)
            n = messages[0].content.count("\n[") + 1
            return ChatResult(text="\n".join(f"[{i}] Tóm tắt số {i}." for i in range(1, n + 1)),
                              provider="gemini", model="gemini-test", input_tokens=10, output_tokens=5)

    monkeypatch.setattr(manager, "get_provider", lambda: FakeProvider())
    row = bs.add_news(db, uid, "giá thép, phân bón")
    #  Truyền mốc giờ cố định như các bài khác: thiếu `now` thì lấy hôm nay THẬT, tin giả ghi ngày 12/10 thành tin cũ và bị
    #  lọc mất — bài này đỏ từ 13/10 chỉ vì lịch trôi (bắt được 19/10 khi chạy full test trước prod).
    assert bs.send_one(db, uid, row, now=MONDAY_0732)
    assert len(prompts) == 1, "một lượt model cho cả điểm báo (hai chủ đề)"
    assert "Giá thép hôm nay 12/10" in prompts[0] and "Giá phân urê tăng" in prompts[0]
    text = out[-1][1]
    assert "Tóm tắt số 1." in text and "Tóm tắt số 6." in text and "Tóm tắt số 7." not in text


def test_khong_co_tin_moi_van_gui_mot_dong_va_may_tim_hong_khong_sap(db, seed, sent, monkeypatch):
    out, _ = sent
    uid = seed.u_req_id
    _link(db, uid, "777")

    def broken(q, limit=8, **kw):
        raise RuntimeError("máy tìm chết")

    monkeypatch.setattr(web_search, "search", broken)
    row = bs.add_news(db, uid, "giá cà phê")
    assert bs.send_one(db, uid, row)
    assert "Không có tin mới về giá cà phê trong 24 giờ qua" in out[-1][1]


def test_ban_tin_chu_de_thuong_van_chay_qua_tro_ly_nhu_cu(db, seed, sent, monkeypatch):
    from app.modules.agent_hub import user_keys

    out, asked = sent
    uid = seed.u_req_id
    _link(db, uid, "777")
    monkeypatch.setattr(user_keys, "active_key", lambda: "k")
    monkeypatch.setattr(web_search, "search", lambda *a, **k: pytest.fail("bản tin thường không tìm web"))
    bs.add_topic(db, uid, "công nợ quá hạn của DEGO", hour=7, minute=30)
    assert bs.tick(db, now=_utc(MONDAY_0732))["sent"] == 1
    assert asked == [("777", "công nợ quá hạn của DEGO")] and "Bản tin:" in out[-1][1]
    items = bs.list_for(db, uid)
    assert not any(it.get("news") for it in items)
